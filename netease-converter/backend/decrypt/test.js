'use strict';
/*
 * 核心算法往返测试：加密 -> 解密 应还原原始存档。
 * 不依赖真实网易存档，仅验证加解密逻辑自洽、可逆。
 */
const JSZip = require('jszip');
const { decryptZip, encryptZip, checkEncrypted } = require('./netease');

function assert(cond, msg) {
  if (!cond) { console.error('  ❌ FAIL:', msg); process.exitCode = 1; }
  else { console.log('  ✅', msg); }
}

async function getEntry(zip, name) {
  const f = zip.files[name];
  if (!f) return null;
  return await f.async('nodebuffer');
}

async function run() {
  // 构造一个"国际版存档"（明文）
  const manifestName = 'MANIFEST-x7';
  const currentPlain = Buffer.from(manifestName + '\n');
  const dbPlain = Buffer.from('LEVELDB_SST_PAYLOAD_' + 'A'.repeat(137) + '_END');
  const levelname = Buffer.from('My Test World');

  const world = new JSZip();
  world.file('db/CURRENT', currentPlain);
  world.file('db/' + manifestName, Buffer.from('manifest-bytes-placeholder'));
  world.file('db/000003.log', dbPlain);
  world.file('levelname.txt', levelname);
  const original = await world.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE' });

  console.log('— 步骤1：国际版存档 -> 加密为网易格式 —');
  const enc = await encryptZip(original);
  assert(Buffer.isBuffer(enc) && enc.length > 0, '加密产出非空 Buffer');

  // 校验加密结果里 CURRENT 带魔数
  const encZip = await JSZip.loadAsync(enc);
  const encCurrent = await getEntry(encZip, 'db/CURRENT');
  assert(encCurrent && checkEncrypted(encCurrent), '加密后 db/CURRENT 带有加密魔数');

  console.log('— 步骤2：网易格式 -> 解密回国际版 —');
  const dec = await decryptZip(enc);
  assert(Buffer.isBuffer(dec) && dec.length > 0, '解密产出非空 Buffer');

  const decZip = await JSZip.loadAsync(dec);
  const dCurrent = await getEntry(decZip, 'db/CURRENT');
  const dDb = await getEntry(decZip, 'db/000003.log');
  const dLevel = await getEntry(decZip, 'levelname.txt');

  assert(dCurrent && dCurrent.equals(currentPlain), 'CURRENT 明文还原一致');
  assert(dDb && dDb.equals(dbPlain), 'db/000003.log 明文还原一致');
  assert(dLevel && dLevel.equals(levelname), 'levelname.txt 未被动（保持明文）');
  assert(!checkEncrypted(dDb), '解密后 db 文件不再带魔数');

  console.log('— 步骤3：解密后再加密，二次往返 —');
  const enc2 = await encryptZip(dec);
  const dec2 = await decryptZip(enc2);
  const dec2Zip = await JSZip.loadAsync(dec2);
  const d2Db = await getEntry(dec2Zip, 'db/000003.log');
  assert(d2Db && d2Db.equals(dbPlain), '二次往返 db 明文仍一致');

  if (process.exitCode === 1) {
    console.error('\n往返测试存在失败项。');
  } else {
    console.log('\n全部通过：加解密双向可逆 ✅');
  }
}

run().catch((e) => { console.error('测试异常:', e); process.exit(1); });
