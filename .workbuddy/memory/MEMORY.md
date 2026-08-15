# 项目长期笔记

## 部署路线
- 域名 `baianb.kdns.fr` 已接入 Cloudflare。
- 目标：让 FastAPI 后端（端口 8000）通过该域名公网可访问。
- 当前路线：Cloudflare Tunnel（因为本机无公网 IP）。

## 环境限制
- 当前沙箱/会话内**无法访问 GitHub**（github.com 000，release assets 下载失败），因此不能直接下载 `cloudflared.exe`。
- 用户需在自己浏览器下载 `cloudflared-windows-amd64.exe`，并放到可执行路径。

## API 令牌需求
- 若要我全自动创建隧道并写 DNS，需要 Custom API Token 包含：
  - Zone → DNS → Edit（作用域 kdns.fr）
  - Account → Cloudflare Tunnel → Edit
- 仅有 `Zone DNS Edit` 不足以创建 Tunnel。
