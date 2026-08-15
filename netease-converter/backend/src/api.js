'use strict';
/*
 * NetEase MC Converter —— 后端 API
 *  POST /api/upload       接收 zip 存档，入队，返回 taskId
 *  GET  /api/task/:id      轮询任务状态
 *  GET  /api/download/:id   下载成品
 *  POST /api/feedback      反馈表单
 *  GET  /api/health        健康检查
 */
const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');

const { createTask, getTask, downloadName } = require('./task');
const { countRecentTasks, insertFeedback } = require('./db');
const cleanup = require('./cleanup');

const app = express();
app.use(cors());
app.use(express.json());

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 100 * 1024 * 1024, files: 1 },
});

const RATE_LIMIT = { max: 20, windowMs: 60 * 60 * 1000 }; // 每 IP 每小时上限

function clientIp(req) {
  return String(req.headers['x-forwarded-for'] || req.socket.remoteAddress || '')
    .split(',')[0].trim() || 'unknown';
}

app.get('/api/health', (req, res) => res.json({ ok: true, time: Date.now() }));

app.post('/api/upload', upload.single('file'), async (req, res) => {
  try {
    const ip = clientIp(req);
    if (!req.file) return res.status(400).json({ error: '未收到文件，请上传 .zip 存档' });
    if (!req.file.originalname.toLowerCase().endsWith('.zip')) {
      return res.status(400).json({ error: '仅支持 .zip 存档压缩包' });
    }
    const recent = await countRecentTasks(ip, RATE_LIMIT.windowMs);
    if (recent >= RATE_LIMIT.max) {
      return res.status(429).json({ error: `请求过于频繁，请稍后再试（每小时上限 ${RATE_LIMIT.max} 次）` });
    }
    const mode = req.body.mode === 'encrypt' ? 'encrypt' : 'decrypt';
    const task = createTask(req.file.buffer, { mode, ip, filename: req.file.originalname });
    res.json({ taskId: task.id, mode: task.mode });
  } catch (e) {
    res.status(500).json({ error: e.message || '上传失败' });
  }
});

app.get('/api/task/:id', (req, res) => {
  const t = getTask(req.params.id);
  if (!t) return res.status(404).json({ error: '任务不存在或已过期' });
  res.json({
    id: t.id,
    mode: t.mode,
    status: t.status,
    progress: t.progress,
    message: t.message,
    filename: downloadName(t),
  });
});

app.get('/api/download/:id', (req, res) => {
  const t = getTask(req.params.id);
  if (!t || t.status !== 'done' || !t.resultFile) {
    return res.status(404).json({ error: '结果文件不存在' });
  }
  res.download(t.resultFile, downloadName(t));
});

app.post('/api/feedback', async (req, res) => {
  const text = (req.body && req.body.text) || '';
  if (!text.trim()) return res.status(400).json({ error: '反馈内容为空' });
  const r = await insertFeedback({ ip: clientIp(req), text: text.slice(0, 2000) });
  res.json(r);
});

// multer / 通用错误处理
app.use((err, req, res, next) => {
  if (err && err.code === 'LIMIT_FILE_SIZE') {
    return res.status(413).json({ error: '文件超过 100MB 限制，请使用本地客户端工具处理超大存档' });
  }
  res.status(500).json({ error: (err && err.message) || '服务器错误' });
});

const PORT = process.env.PORT || 3000;
cleanup.start();
app.listen(PORT, () => console.log(`[api] NetEase MC converter backend listening on :${PORT}`));

module.exports = app;
