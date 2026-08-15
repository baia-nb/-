'use strict';
/* 定时清理 2 小时以上的临时文件，避免磁盘爆满。 */
const fs = require('fs');
const path = require('path');
const { TEMP } = require('./task');

const MAX_AGE_MS = 2 * 60 * 60 * 1000;

function sweep() {
  try {
    const now = Date.now();
    for (const f of fs.readdirSync(TEMP)) {
      const fp = path.join(TEMP, f);
      let st;
      try { st = fs.statSync(fp); } catch (_) { continue; }
      if (now - st.mtimeMs > MAX_AGE_MS) {
        try { fs.unlinkSync(fp); } catch (_) {}
      }
    }
  } catch (_) {}
}

function start() {
  sweep();
  setInterval(sweep, 30 * 60 * 1000);
}

module.exports = { start, sweep };
