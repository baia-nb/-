# 我的世界【网易版 ↔ 国际版】存档转换器

纯开源方案：玩家自有本地存档的 **解密 / 加密** 工具网站。前端 + Node 后端 + 可选 Supabase 数据库，**零月租、不强制信用卡**。

> ⚠️ 法律边界：仅转换**玩家自己创建的本地存档**；资源工坊下载的加密地图大多无法解密；
> 禁止用于私服绕过网易账号验证、商业牟利、分发盗版资源。仅供个人学习使用。

---

## 功能
- **解密（网易 → 国际）**：上传网易版加密存档 `.zip` → 返回可在国际版使用的存档。
- **加密（国际 → 网易）**：上传国际版存档 `.zip` → 返回可在网易版导入的格式。
- 异步任务队列、IP 限流、临时文件 2 小时自动清理。
- 转换记录 / 反馈：配置 Supabase 后自动入库；未配置则降级到本地 JSON 文件。

## 算法
已逐字节核对开源实现（`ihaiming/NetEaseMC-Decryptor`、`HTMonkeyG/XOREncryptHelper`）：
加密文件以魔数 `80 1D 30 01` 开头；密钥由该世界 `CURRENT` 文件密文与 `MANIFEST` 文件名做 XOR 推导，
对所有带魔数的文件执行 `明文 = 密文[4:] XOR K`。加解密为同一套 XOR，可逆。

## 本地运行
```bash
cd netease-converter/backend
npm install
node scripts/make_sample.js        # 生成示例国际版存档（可选）
npm start                          # 监听 :3000

# 另开终端测试
cd netease-converter
curl -F "file=@sample_world.zip" -F "mode=encrypt" http://localhost:3000/api/upload
# 返回 {taskId,...} 后轮询
curl http://localhost:3000/api/task/<taskId>
curl -O -J http://localhost:3000/api/download/<taskId>
```
前端：用任意静态服务器打开 `frontend/index.html`（如 `npx serve frontend`），或把 `frontend/` 部署到 Cloudflare Pages。

单元测试（算法往返）：`cd backend && npm test`

## 部署（路线2：前后端 + 数据库）
### 1) 后端 → Render
1. 把 `backend/` 推到 GitHub 新仓库。
2. Render 新建 Web Service，连接仓库，`startCommand: node src/api.js`，`buildCommand: npm install`。
3. （可选）在 Render 环境变量填入 `SUPABASE_URL` / `SUPABASE_KEY`。
4. 免费层会休眠，可用 UptimeRobot 每 5 分钟 Ping `/api/health` 保活。

### 2) 前端 → Cloudflare Pages
1. 把 `frontend/` 推到 GitHub 仓库。
2. Cloudflare Pages 新建站点，框架选「无」，构建输出目录 `frontend`。
3. 部署后编辑 `frontend/config.js`，把 `window.API_BASE` 改为你的 Render 后端地址。
4. （可选）在 Cloudflare 接入你的域名，免费 SSL + CDN。

### 3) 数据库 → Supabase（可选）
1. 新建 Supabase 项目，打开 SQL Editor 执行 `supabase/schema.sql`。
2. 把 Project URL 与 service_role key 填入后端环境变量 `SUPABASE_URL` / `SUPABASE_KEY`。

## 与现有 baianb.kdns.fr 的关系
`baianb.kdns.fr` 是另一个**独立的**项目（Python FastAPI 的「我的世界格式转换器」桌面工具网页版，经 Cloudflare Tunnel 暴露）。
本目录是**全新独立的**网易版↔国际版转换器，可按上述路线2独立托管，互不干扰。

## 目录结构
```
netease-converter/
├─ backend/
│  ├─ src/{api,task,db,cleanup}.js
│  ├─ decrypt/{netease.js,test.js}   # 核心加解密
│  ├─ temp/                          # 运行时临时文件（自动清理）
│  ├─ package.json / render.yaml / .env.example
├─ frontend/{index.html,app.js,style.css,config.js}
├─ supabase/schema.sql
└─ scripts/make_sample.js
```
