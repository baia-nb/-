# 我的世界格式转换器 · 在线版

基于 **React + Tailwind** 的前端，配合 **FastAPI** 后端（直接复用项目根目录 `core/` 的真实转换引擎）构建的在线格式转换网站。

## 功能
- 上传建筑文件（`.bdx` / `.litematic` / `.mcstructure` / `.schematic` / `.schem`）
- 一键转换为：
  - `txt` — setblock 指令文本
  - `ibi` — IBI 加密命令方块包
  - `dsb` — DSB 结构文件
  - `mcstructure` — 基岩版 MCStructure
- 显示方块数、输出体积，并可直接下载

## 目录结构
```
web/
  backend/main.py   FastAPI 后端 (API + 托管前端静态文件)
  frontend/        Vite + React + Tailwind 前端源码
  serve.py         一键启动脚本
```

## 运行
### 方式一：一条命令（推荐）
```bash
cd C:\Users\ttnld\Documents\trae_projects\dabao
python web/serve.py
```
浏览器打开 http://localhost:8000

### 方式二：前后端分离开发
```bash
# 终端 1：后端
cd C:\Users\ttnld\Documents\trae_projects\dabao
python -m uvicorn web.backend.main:app --port 8000

# 终端 2：前端 (带热更新)
cd web/frontend
npm install
npm run dev
# 打开 http://localhost:5173 (开发服务器已代理 /api 到 8000)
```

## 构建前端（生产）
```bash
cd web/frontend
npm install
npm run build      # 输出到 web/frontend/dist，由 FastAPI 自动托管
```

## 后端 API
- `GET  /api/formats` — 支持的源/目标格式
- `POST /api/convert` — 上传文件（multipart: `file`, `target`）返回转换结果元数据
- `GET  /api/download/{id}/{filename}` — 下载转换后的文件

> 转换在服务器端使用与桌面版一致的核心引擎（BDXConverter / nbtlib），临时文件 1 小时后自动清理。
