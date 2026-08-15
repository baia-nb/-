'use strict';
/*
 * 数据层（可选 Supabase，缺省降级到本地 JSON 文件）。
 * 设计原则：零依赖也能跑；配置了 Supabase 环境变量后自动升级为云端存储。
 */
const fs = require('fs');
const path = require('path');
const { createClient } = require('@supabase/supabase-js');

const TEMP_DIR = path.join(__dirname, '..', 'temp');
const LOCAL_RECORDS = path.join(TEMP_DIR, 'records.json');
const LOCAL_FEEDBACK = path.join(TEMP_DIR, 'feedback.json');

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_KEY; // anon 或 service_role

let supabase = null;
if (SUPABASE_URL && SUPABASE_KEY) {
  try {
    supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
    console.log('[db] Supabase 已连接');
  } catch (e) {
    console.warn('[db] Supabase 连接失败，降级本地文件:', e.message);
    supabase = null;
  }
} else {
  console.log('[db] 未配置 Supabase，使用本地 JSON 文件存储（极简方案）');
}

function readJson(file, fallback) {
  try {
    if (fs.existsSync(file)) return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (_) {}
  return fallback;
}
function appendJson(file, obj) {
  const arr = readJson(file, []);
  arr.push(obj);
  try { fs.writeFileSync(file, JSON.stringify(arr, null, 2)); } catch (_) {}
}

async function insertRecord(rec) {
  const row = { ip: rec.ip, mode: rec.mode, size: rec.size, status: rec.status, created_at: new Date().toISOString() };
  if (supabase) {
    try { await supabase.from('records').insert(row); return; } catch (e) { console.warn('[db] insertRecord supabase 失败:', e.message); }
  }
  appendJson(LOCAL_RECORDS, row);
}

async function countRecentTasks(ip, windowMs) {
  const since = Date.now() - windowMs;
  if (supabase) {
    try {
      const { count, error } = await supabase
        .from('records')
        .select('*', { count: 'exact', head: true })
        .eq('ip', ip)
        .gte('created_at', new Date(since).toISOString());
      if (!error) return count || 0;
    } catch (e) { console.warn('[db] countRecent supabase 失败:', e.message); }
  }
  const arr = readJson(LOCAL_RECORDS, []);
  return arr.filter((r) => r.ip === ip && new Date(r.created_at).getTime() >= since).length;
}

async function insertFeedback(fb) {
  const row = { ip: fb.ip, text: fb.text, created_at: new Date().toISOString() };
  if (supabase) {
    try { await supabase.from('feedback').insert(row); return { ok: true }; } catch (e) { return { ok: false, error: e.message }; }
  }
  appendJson(LOCAL_FEEDBACK, row);
  return { ok: true };
}

module.exports = { insertRecord, countRecentTasks, insertFeedback, isSupabase: !!supabase };
