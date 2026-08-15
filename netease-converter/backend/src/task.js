'use strict';
/*
 * 任务队列 + 内存存储。
 * 顺序处理（同一时刻只跑一个），避免大文件并发转换把内存打爆。
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { insertRecord } = require('./db');

const TEMP = path.join(__dirname, '..', 'temp');
if (!fs.existsSync(TEMP)) fs.mkdirSync(TEMP, { recursive: true });

const tasks = new Map();
const queue = [];
let running = false;

function createTask(buffer, meta) {
  const id = crypto.randomUUID();
  const task = {
    id,
    mode: meta.mode === 'encrypt' ? 'encrypt' : 'decrypt',
    ip: meta.ip,
    filename: meta.filename || 'world.zip',
    size: buffer.length,
    status: 'queued',
    progress: 0,
    message: '',
    resultFile: null,
    createdAt: Date.now(),
    _buffer: buffer,
  };
  tasks.set(id, task);
  queue.push(id);
  pump();
  return task;
}

function getTask(id) {
  return tasks.get(id) || null;
}

function downloadName(task) {
  const base = (task.filename || 'world.zip').replace(/\.zip$/i, '');
  return task.mode === 'encrypt' ? `${base}_encrypted.zip` : `${base}_decrypted.zip`;
}

async function processTask(task) {
  const { processZip } = require('../decrypt/netease');
  task.status = 'processing';
  task.progress = 10;
  try {
    const inputPath = path.join(TEMP, `${task.id}.zip`);
    fs.writeFileSync(inputPath, task._buffer);
    task.progress = 30;

    const outBuf = await processZip(task._buffer, task.mode);
    task.progress = 85;

    const outPath = path.join(TEMP, `${task.id}_out.zip`);
    fs.writeFileSync(outPath, outBuf);
    task.resultFile = outPath;
    task.status = 'done';
    task.progress = 100;
    task.message = task.mode === 'encrypt' ? '已加密为网易格式，可直接导入网易版' : '已解密为国际版格式';
  } catch (e) {
    task.status = 'failed';
    task.message = e.message || String(e);
  } finally {
    task._buffer = null; // 释放内存
    if (!task.resultFile) {
      // 失败时清理输入
      const ip = path.join(TEMP, `${task.id}.zip`);
      try { fs.unlinkSync(ip); } catch (_) {}
    }
    insertRecord({ ip: task.ip, mode: task.mode, size: task.size, status: task.status }).catch(() => {});
  }
}

async function pump() {
  if (running) return;
  running = true;
  while (queue.length) {
    const id = queue.shift();
    const task = tasks.get(id);
    if (!task) continue;
    // 限制单次转换的最长运行时间保护（由进程级超时兜底）
    await processTask(task);
  }
  running = false;
}

module.exports = { createTask, getTask, downloadName, TEMP };
