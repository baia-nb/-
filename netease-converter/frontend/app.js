'use strict';
/* 网易版↔国际版 我的世界基岩存档转换器 —— 前端逻辑（原生 JS，无构建依赖） */

function apiBase() {
  const q = new URLSearchParams(location.search).get('api');
  if (q) return q.replace(/\/+$/, '');
  return (window.API_BASE || '/api').replace(/\/+$/, '');
}

let mode = 'decrypt'; // decrypt: 网易→国际  encrypt: 国际→网易
let currentTaskId = null;
let pollTimer = null;
let currentFile = null;

const els = {};

function $(id) { return document.getElementById(id); }

function init() {
  els.drop = $('drop');
  els.file = $('file');
  els.run = $('run');
  els.progress = $('progress');
  els.progressBar = $('progressBar');
  els.status = $('status');
  els.result = $('result');
  els.fbText = $('fbText');
  els.fbSend = $('fbSend');
  els.fbMsg = $('fbMsg');

  document.querySelectorAll('.tab').forEach((t) => {
    t.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach((x) => x.classList.remove('active'));
      t.classList.add('active');
      mode = t.dataset.mode;
      $('modeHint').textContent = mode === 'decrypt'
        ? '将网易版加密存档（.zip）解密为可在国际版中使用的存档。'
        : '将国际版存档（.zip）加密为可在网易版中导入的格式。';
    });
  });

  els.drop.addEventListener('click', () => els.file.click());
  els.file.addEventListener('change', (e) => { setFile(e.target.files[0]); });
  ['dragover', 'dragenter'].forEach((ev) => els.drop.addEventListener(ev, (e) => { e.preventDefault(); els.drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach((ev) => els.drop.addEventListener(ev, (e) => { e.preventDefault(); els.drop.classList.remove('over'); }));
  els.drop.addEventListener('drop', (e) => { setFile(e.dataTransfer.files[0]); });

  els.run.addEventListener('click', upload);
  els.fbSend.addEventListener('click', sendFeedback);
}

function setFile(f) {
  if (!f) return;
  if (!f.name.toLowerCase().endsWith('.zip')) {
    setStatus('仅支持 .zip 压缩包', 'err'); return;
  }
  currentFile = f;
  els.drop.innerHTML = `已选择：<b>${escapeHtml(f.name)}</b><br><small>点击重新选择，或拖拽其他文件</small>`;
  setStatus('', '');
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function setStatus(msg, kind) {
  els.status.textContent = msg;
  els.status.className = 'status' + (kind ? ' ' + kind : '');
}

function upload() {
  if (!currentFile) { setStatus('请先选择 .zip 存档', 'err'); return; }
  const fd = new FormData();
  fd.append('file', currentFile);
  fd.append('mode', mode);

  els.run.disabled = true;
  setStatus('上传中…', '');
  els.progressBar.style.width = '0%';
  els.result.classList.add('hidden');

  const xhr = new XMLHttpRequest();
  xhr.open('POST', `${apiBase()}/api/upload`);
  xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) {
      const pct = Math.round((e.loaded / e.total) * 100);
      els.progressBar.style.width = pct + '%';
      setStatus(`上传中 ${pct}%`, '');
    }
  };
  xhr.onload = () => {
    els.progressBar.style.width = '100%';
    let data;
    try { data = JSON.parse(xhr.responseText); } catch (_) { data = {}; }
    if (xhr.status !== 200 || !data.taskId) {
      els.run.disabled = false;
      setStatus('上传失败：' + (data.error || xhr.status), 'err');
      return;
    }
    currentTaskId = data.taskId;
    setStatus('已提交，正在转换…', '');
    startPoll();
  };
  xhr.onerror = () => { els.run.disabled = false; setStatus('网络错误，无法连接后端', 'err'); };
  xhr.send(fd);
}

function startPoll() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(poll, 1200);
  poll();
}

async function poll() {
  if (!currentTaskId) return;
  try {
    const r = await fetch(`${apiBase()}/api/task/${currentTaskId}`);
    const t = await r.json();
    if (!r.ok) { setStatus(t.error || '任务查询失败', 'err'); stopPoll(); return; }
    const pct = Math.max(5, t.progress || 5);
    els.progressBar.style.width = pct + '%';
    if (t.status === 'processing') setStatus(t.message || '转换中…', '');
    else if (t.status === 'done') {
      stopPoll();
      els.run.disabled = false;
      setStatus(t.message || '转换完成', 'ok');
      showResult(t);
    } else if (t.status === 'failed') {
      stopPoll();
      els.run.disabled = false;
      setStatus('转换失败：' + t.message, 'err');
    }
  } catch (e) {
    setStatus('轮询失败：' + e.message, 'err');
  }
}

function stopPoll() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } }

function showResult(t) {
  els.result.classList.remove('hidden');
  els.result.innerHTML = `<div class="download"><a class="dl" href="${apiBase()}/api/download/${t.id}" download="${escapeHtml(t.filename)}">⬇ 下载 ${escapeHtml(t.filename)}</a></div>`;
}

async function sendFeedback() {
  const text = (els.fbText.value || '').trim();
  if (!text) { els.fbMsg.textContent = '请输入反馈内容'; els.fbMsg.className = 'status err'; return; }
  els.fbSend.disabled = true;
  try {
    const r = await fetch(`${apiBase()}/api/feedback`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }),
    });
    const d = await r.json();
    els.fbMsg.textContent = d.ok ? '感谢反馈，已收到！' : ('提交失败：' + (d.error || ''));
    els.fbMsg.className = 'status ' + (d.ok ? 'ok' : 'err');
    if (d.ok) els.fbText.value = '';
  } catch (e) {
    els.fbMsg.textContent = '提交失败：' + e.message; els.fbMsg.className = 'status err';
  } finally { els.fbSend.disabled = false; }
}

document.addEventListener('DOMContentLoaded', init);
