#!/usr/bin/env bash
# 用 Cloudflare API 把 baianb.kdns.fr 指向服务器公网 IP (代理开启, SSL=full)
# 需环境变量:
#   CF_API_TOKEN   Cloudflare API Token (权限: Zone / DNS / Edit, 作用域含 kdns.fr)
#   SERVER_IP      服务器公网 IP
# 用法:
#   CF_API_TOKEN=xxxx SERVER_IP=1.2.3.4 bash setup_dns.sh
set -euo pipefail

: "${CF_API_TOKEN:?需要提供 CF_API_TOKEN (Cloudflare API Token, 权限 DNS:Edit)}"
: "${SERVER_IP:?需要提供 SERVER_IP (服务器公网 IP)}"

PY="python3"; command -v python3 >/dev/null 2>&1 || PY="python"

ZONE_NAME="kdns.fr"
RECORD_NAME="baianb.kdns.fr"

echo ">> 查询 zone id: $ZONE_NAME"
ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$ZONE_NAME" \
  -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" \
  | $PY -c "import sys,json;d=json.load(sys.stdin);print(d['result'][0]['id'])")
echo "   zone_id=$ZONE_ID"

echo ">> 查找已有 A 记录: $RECORD_NAME"
EXISTING=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=$RECORD_NAME&type=A" \
  -H "Authorization: Bearer $CF_API_TOKEN")
RID=$(echo "$EXISTING" | $PY -c "import sys,json;d=json.load(sys.stdin);print(d['result'][0]['id'] if d['result'] else '')")

if [ -n "$RID" ]; then
  echo "   已存在, 更新 id=$RID"
  curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RID" \
    -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" \
    --data "{\"type\":\"A\",\"name\":\"baianb\",\"content\":\"$SERVER_IP\",\"ttl\":1,\"proxied\":true}" >/dev/null
else
  echo "   新建 A 记录"
  curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
    -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" \
    --data "{\"type\":\"A\",\"name\":\"baianb\",\"content\":\"$SERVER_IP\",\"ttl\":1,\"proxied\":true}" >/dev/null
fi

echo ">> 设置 SSL 模式为 full"
curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/ssl" \
  -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" \
  --data '{"value":"full"}' >/dev/null

echo "OK: $RECORD_NAME -> $SERVER_IP (proxy 开启, SSL=full)"
