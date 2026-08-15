-- NetEase MC Converter —— Supabase 建表 SQL
-- 在 Supabase 控制台 -> SQL Editor 执行本文件即可。

-- 转换记录
create table if not exists records (
  id          bigint generated always as identity primary key,
  ip          text,
  mode        text,          -- 'decrypt' | 'encrypt'
  size        bigint,        -- 上传字节数
  status      text,          -- 'done' | 'failed'
  created_at  timestamptz default now()
);
create index if not exists records_ip_idx on records(ip);
create index if not exists records_created_idx on records(created_at desc);

-- 用户反馈
create table if not exists feedback (
  id          bigint generated always as identity primary key,
  ip          text,
  text        text,
  created_at  timestamptz default now()
);

-- 行级安全：服务端使用 service_role key 读写，前端匿名不直接访问表。
-- 若仅由后端 key 访问，可保持默认（不开启 RLS 也行，因为前端不直连）。
