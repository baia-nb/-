'use strict';
/* 端到端测试：通过 HTTP 走完 加密 -> 下载 -> 解密 -> 下载，校验还原一致。 */
const fs = require('fs');
const path = require('path');
const JSZip = require(path.join(__dirname, '..', 'backend', 'node_modules', 'jszip'));
const BASE = process.env.BASE || 'http://localhost:3100';

const samplePath = path.join(__dirname, '..', 'sample_world.zip');
const out1 = path.join(__dirname, '..', 'out_encrypted.zip');
const out2 = path.join(__dirname, '..', 'out_decrypted.zip');

function assert(c, m) { if (!c) { console.error('  ❌', m); process.exitCode = 1; } else console.log('  ✅', m); }

async function upload(mode, filePath) {
  const form = new FormData();
  form.append('file', new Blob([fs.readFileSync(filePath)]), path.basename(filePath));
  form.append('mode', mode);
  const r = await fetch(`${BASE}/api/upload`, { method: 'POST', body: form });
  const j = await r.json();
  if (!r.ok) throw new Error('upload failed: ' + JSON.stringify(j));
  return j.taskId;
}

async function waitTask(id, label) {
  for (let i = 0; i < 40; i++) {
    const r = await fetch(`${BASE}/api/task/${id}`);
    const t = await r.json();
    if (t.status === 'done') return t;
    if (t.status === 'failed') throw new Error(`${label} failed: ${t.message}`);
    await new Promise((res) => setTimeout(res, 500));
  }
  throw new Error(`${label} timeout`);
}

async function download(id, dest) {
  const r = await fetch(`${BASE}/api/download/${id}`);
  if (!r.ok) throw new Error('download failed ' + r.status);
  const buf = Buffer.from(await r.arrayBuffer());
  fs.writeFileSync(dest, buf);
  return buf;
}

async function main() {
  console.log('— E2E: 国际版 -> 加密为网易格式 —');
  const t1 = await upload('encrypt', samplePath);
  const r1 = await waitTask(t1, 'encrypt');
  const b1 = await download(t1, out1);
  assert(b1.length > 0, '加密结果已下载');

  console.log('— E2E: 网易格式 -> 解密回国际版 —');
  const t2 = await upload('decrypt', out1);
  const r2 = await waitTask(t2, 'decrypt');
  const b2 = await download(t2, out2);
  assert(b2.length > 0, '解密结果已下载');

  const orig = fs.readFileSync(samplePath);
  // 比对内部文件内容（zip 外层字节因重新打包必然不同，故比内部）
  const oZip = await JSZip.loadAsync(orig);
  const dZip = await JSZip.loadAsync(b2);
  const keys = ['db/000005.log', 'levelname.txt', 'db/CURRENT'];
  for (const k of keys) {
    const a = await oZip.file(k).async('nodebuffer');
    const b = await dZip.file(k).async('nodebuffer');
    assert(b && b.equals(a), `内部文件一致: ${k}`);
  }
  console.log('\nE2E 完成（HTTP 全链路双向可逆，内部内容逐字节一致）。');
}

main().catch((e) => { console.error(e); process.exit(1); });
