#!/usr/bin/env bash
# 我的世界格式转换器 · 在线版 —— 服务器一键部署脚本
# 在目标 VPS 上以 root 执行。会: 装 Docker(若无) -> 构建并启动容器(8000) -> 装 nginx 反代(80->8000) -> 开防火墙。
# 前置: 已把本仓库放到 $APP_DIR (含 Dockerfile / docker-compose.yml), 且域名已在 Cloudflare 指向本机公网 IP。
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/mc-converter}"
PORT=8000

echo ">> [1/4] 确保 Docker 可用"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "缺少 docker compose 插件, 请先安装"; exit 1
fi

echo ">> [2/4] 构建并启动容器 ($APP_DIR)"
mkdir -p "$APP_DIR"
cd "$APP_DIR"
docker compose up -d --build

echo ">> [3/4] 安装 nginx 反代 (80 -> $PORT)"
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -y && apt-get install -y nginx
fi
cat >/etc/nginx/conf.d/baianb.kdns.fr.conf <<EOF
server {
    listen 80;
    server_name baianb.kdns.fr;
    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        client_max_body_size 32m;
    }
}
EOF
nginx -t && (systemctl reload nginx || service nginx reload)

echo ">> [4/4] 开放防火墙 80/443"
(ufw allow 80/tcp; ufw allow 443/tcp; ufw --force enable) >/dev/null 2>&1 || true

echo "完成. Cloudflare(443) -> 本机 nginx(80) -> 容器($PORT)."
echo "浏览器访问 https://baianb.kdns.fr 即可。"
