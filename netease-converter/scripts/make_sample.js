'use strict';
/* 生成一个示例「国际版存档」zip，用于本地端到端测试加密/解密链路。 */
const fs = require('fs');
const path = require('path');
const JSZip = require('jszip');

const OUT = path.join(__dirname, '..', 'sample_world.zip');

async function main() {
  const manifest = 'MANIFEST-abc123';
  const world = new JSZip();
  world.file('db/CURRENT', Buffer.from(manifest + '\n'));
  world.file('db/' + manifest, Buffer.from('manifest-content-placeholder-bytes'));
  world.file('db/000005.log', Buffer.from('LEVELDB_PAYLOAD_' + 'Z'.repeat(200) + '_END'));
  world.file('levelname.txt', Buffer.from('Sample World'));
  const buf = await world.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE' });
  fs.writeFileSync(OUT, buf);
  console.log('已生成示例存档:', OUT, buf.length, 'bytes');
}
main();
