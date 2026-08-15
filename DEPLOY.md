# 部署指南 · 我的世界格式转换器 在线版

把"本地能跑的转换器网站"部署到 VPS / 云平台，并绑定域名 `baianb.kdns.fr`。

> 架构：FastAPI（Python 后端，复用 `core/` 真实转换引擎）+ React 前端（构建后由 FastAPI 托管）。
> 转换依赖 Python，因此**必须能跑 Python 的后端**，纯静态托管（如 CloudStudio 静态页）只能放前端、转换功能不可用。

---

## 方式 A：Docker（推荐，Render / Railway / Fly / 任意 VPS 通用）

仓库根目录已提供 `Dockerfile`、`.dockerignore`、`web/requirements.txt`。

### 1) 任意 VPS（有 Docker）
```bash
git clone <你的仓库> mc-converter && cd mc-converter
docker compose up -d --build
# 访问 http://<服务器公网IP>:8000
```

### 2) Render
- New → Web Service → 连仓库。
- Runtime 选 **Docker**（会自动用仓库里的 `Dockerfile`）。
- 不必填 Build Command / Start Command，监听端口设 `8000`。
- 免费/付费实例均可；Render 会自动注入 `PORT` 环境变量，启动脚本已支持。

### 3) Railway
- New Project → Deploy from GitHub repo。
- 检测到 `Dockerfile` 即按 Docker 部署。
- 在 Settings 里把 `PORT` 设为 `8000`（Railway 默认也传 `PORT`）。
- 生成的 `*.railway.app` 域名可后在 Cloudflare 用 CNAME 接入。

### 4) Fly.io
- `fly launch`（会生成 `fly.toml`，内部端口 `8000`）。
- `fly deploy`。
- 默认给一个 `*.fly.dev` 域名，可用 Cloudflare CNAME 接入 `baianb.kdns.fr`。

---

## 方式 B：直接在 VPS 上跑 Python（不用 Docker）

```bash
# 1) 准备 Python 3.13 虚拟环境
python3 -m venv .venv && source .venv/bin/activate
pip install -r web/requirements.txt

# 2) 构建前端
cd web/frontend && npm install && npm run build && cd ../..

# 3) 启动 (生产可用 gunicorn 或多 worker uvicorn)
PORT=8000 python web/serve.py
# 或: uvicorn web.backend.main:app --host 0.0.0.0 --port 8000 --workers 2
```
建议用 `systemd` 或 `supervisor` 保活，并前置 `nginx`（见仓库 `nginx.conf`）。

---

## 把 `baianb.kdns.fr` 指向服务器

该域名当前解析到 **Cloudflare**（说明已在 Cloudflare 后台）。最省事的做法是**让 Cloudflare 直接代理你的源站**，这样 TLS 证书由 Cloudflare 提供，源站无需自己申请证书。

### 方案 1：Cloudflare 代理（最简单，推荐）
1. 登录 Cloudflare → `baianb.kdns.fr` 所在站点 → **DNS** → 添加/编辑记录：
   - 类型 `A`，名称 `baianb`，内容 = **服务器公网 IP**，代理状态 = **开启（橙云）**。
2. **SSL/TLS** → 概述 → 模式设为 **Full** 或 **Full (strict)**。
   - 源站跑的是 HTTP（8000），Cloudflare 边缘到源站会加密（Full 即可；Full strict 需源站有证书，可选）。
3. 完成。访问 `https://baianb.kdns.fr` 即由 Cloudflare 转发到你的 `服务器IP:8000`。

> 注意：Cloudflare 免费版默认只代理 HTTP/HTTPS（80/443）。你的容器监听 8000，
> 需要在源站内部把 8000 接出来——最稳妥是 VPS 上用 `nginx` 反代
> （`nginx.conf`）：让 nginx 在 80/443 接收 Cloudflare 流量，再 `proxy_pass` 到 `127.0.0.1:8000`。
> 即：**Cloudflare(443) → 服务器 nginx(80/443) → 容器(8000)**。

### 方案 2：不用 Cloudflare，自己签证书
- 在 VPS 上用 `nginx.conf` + `certbot --nginx -d baianb.kdns.fr` 签发 Let's Encrypt 证书。
- 域名 DNS 直接 A 记录指向服务器 IP（可关闭 Cloudflare 代理，灰云）。

### 方案 3：Cloudflare Tunnel（无公网 IP / 无端口转发）
若服务器在家宽、无公网 IP 或不能开端口：
1. 服务器上装 `cloudflared`，登录 Cloudflare 创建 Tunnel。
2. 添加 Public Hostname：`baianb.kdns.fr` → `http://localhost:8000`。
3. 流量经 Cloudflare 隧道直达本机，无需开放任何端口、无需公网 IP。

---

## 运维提示
- **临时文件**：转换结果写在系统临时目录 `mcweb_convert/`，已做 1 小时自动清理，无需挂载持久卷。
- **并发/扩展**：每个转换请求独立（按 uuid 隔离目录），可放心多 worker / 多实例水平扩展。
- **镜像体积**：基础镜像 `python:3.13-slim`；若某依赖装不上（缺编译链），可改 `python:3.13`（完整版）或自行加 `build-essential`。
- **更新上线**：改完代码后 `docker compose up -d --build`（或重新 `fly deploy` / 重新部署 Render）即可。
