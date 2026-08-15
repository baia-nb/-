'use strict';
/*
 * 网易版 ↔ 国际版 我的世界基岩存档 解密/加密核心
 *
 * 算法来源（已逐字节核对，非自行臆测）：
 *   - ihaiming/NetEaseMC-Decryptor  (index.html 内 getKey / decryptFile)
 *   - HTMonkeyG/XOREncryptHelper    (XOREncryptHelper.js)
 *
 * 加密文件特征：前 4 字节为魔数 80 1D 30 01，其后为密文。
 * 密钥 K 由该世界的 CURRENT 文件密文 与 MANIFEST 文件名(UFT-8 + 换行 0x0A) 做 XOR 推出：
 *   K[i] = CURRENT密文[4+i] ^ source[i % source.length]
 *   其中 source = manifestName(UTF-8) + 0x0A
 * 因为 CURRENT 明文恰好就是 manifest 文件名串，故 K 可被稳定还原（同一世界内所有文件共用）。
 * 解密：明文[i] = 密文[4+i] ^ K[i % K.length]
 * 加密：密文 = 魔数 || (明文 ^ K)，K 长度取 CURRENT 明文长度，保证双向可逆。
 *
 * 法律边界：仅用于玩家自有本地存档的格式转换，不碰登录协议/联机绕过。
 */

const JSZip = require('jszip');

const MAGIC = Buffer.from([0x80, 0x1d, 0x30, 0x01]);
const GLOBAL_KEY = Buffer.from('88329851'); // XOREncryptHelper 默认密钥 / 社区共识全局密钥

function xorBuffer(data, key) {
  const out = Buffer.alloc(data.length);
  for (let i = 0; i < data.length; i++) {
    out[i] = data[i] ^ key[i % key.length];
  }
  return out;
}

function checkEncrypted(buf) {
  if (!buf || buf.length < 4) return false;
  return buf[0] === 0x80 && buf[1] === 0x1d && buf[2] === 0x30;
}

function basename(path) {
  const p = path.split('/').pop();
  return p.split('\\').pop();
}

function deriveKeyFromCurrent(currentEncryptedBuf, manifestName) {
  const enc = currentEncryptedBuf.subarray(4); // 去掉魔数
  const source = Buffer.concat([Buffer.from(manifestName, 'utf8'), Buffer.from([0x0a])]);
  const key = Buffer.alloc(enc.length);
  for (let i = 0; i < enc.length; i++) {
    key[i] = enc[i] ^ source[i % source.length];
  }
  // optimizeKey：若密钥长度恰为 16 且前后 8 字节相同，则压缩为 8 字节
  if (key.length === 16) {
    let same = true;
    for (let i = 0; i < 8; i++) {
      if (key[i] !== key[8 + i]) { same = false; break; }
    }
    if (same) return key.subarray(0, 8);
  }
  return key;
}

function decryptBuffer(buf, key) {
  return xorBuffer(buf.subarray(4), key);
}

function buildKey(len, base = GLOBAL_KEY) {
  const key = Buffer.alloc(len);
  for (let i = 0; i < len; i++) key[i] = base[i % base.length];
  return key;
}

function encryptBuffer(buf, key) {
  return Buffer.concat([MAGIC, xorBuffer(buf, key)]);
}

function shouldEncrypt(path) {
  const base = basename(path);
  if (/^CURRENT$/.test(base)) return true;
  if (/^MANIFEST/.test(base)) return true;
  if (/\.(log|sst|ldb)$/.test(base)) return true;
  if (path.includes('/db/') || path.includes('\\db\\')) return true;
  return false;
}

function findWorldEntries(zip) {
  let currentEntry = null;
  let manifestName = null;
  zip.forEach((path, entry) => {
    const base = basename(path);
    if (base === 'CURRENT') currentEntry = entry;
    if (/^MANIFEST/.test(base)) manifestName = base;
  });
  return { currentEntry, manifestName };
}

async function decryptZip(zipBytes) {
  const zip = await JSZip.loadAsync(zipBytes);
  const { currentEntry, manifestName } = findWorldEntries(zip);
  if (!currentEntry) throw new Error('压缩包中找不到 CURRENT 文件，可能不是有效的网易版存档');
  if (!manifestName) throw new Error('压缩包中找不到 MANIFEST 文件，无法推导密钥');

  const currentBuf = await currentEntry.async('nodebuffer');
  if (!checkEncrypted(currentBuf)) {
    throw new Error('CURRENT 文件未加密或使用旧版加密，无法解密（资源工坊下载的加密地图通常无法解密）');
  }

  const key = deriveKeyFromCurrent(currentBuf, manifestName);
  const out = new JSZip();
  const files = Object.keys(zip.files).filter((p) => !zip.files[p].dir);
  for (const path of files) {
    const data = await zip.files[path].async('nodebuffer');
    if (checkEncrypted(data)) {
      out.file(path, decryptBuffer(data, key));
    } else {
      out.file(path, data);
    }
  }
  return await out.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE', compressionOptions: { level: 6 } });
}

async function encryptZip(zipBytes) {
  const zip = await JSZip.loadAsync(zipBytes);
  const { currentEntry, manifestName } = findWorldEntries(zip);
  if (!currentEntry) throw new Error('压缩包中找不到 CURRENT 文件，无法加密（请上传国际版存档）');
  if (!manifestName) throw new Error('压缩包中找不到 MANIFEST 文件，无法加密');

  const currentPlain = await currentEntry.async('nodebuffer');
  const key = buildKey(currentPlain.length);

  const out = new JSZip();
  const files = Object.keys(zip.files).filter((p) => !zip.files[p].dir);
  for (const path of files) {
    const data = await zip.files[path].async('nodebuffer');
    if (shouldEncrypt(path)) {
      out.file(path, encryptBuffer(data, key));
    } else {
      out.file(path, data);
    }
  }
  return await out.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE', compressionOptions: { level: 6 } });
}

async function processZip(zipBytes, mode) {
  if (mode === 'encrypt') return encryptZip(zipBytes);
  return decryptZip(zipBytes); // default: decrypt
}

module.exports = {
  MAGIC,
  GLOBAL_KEY,
  checkEncrypted,
  deriveKeyFromCurrent,
  decryptBuffer,
  encryptBuffer,
  buildKey,
  shouldEncrypt,
  decryptZip,
  encryptZip,
  processZip,
};
