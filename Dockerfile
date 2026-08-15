# syntax=docker/dockerfile:1
# 我的世界格式转换器 · 在线版 — 生产镜像
# 构建上下文必须是项目根目录 (dabao/)，因为镜像需要 core/ 与 web/ 两部分。
#
#   docker build -t mc-converter-web .
#   docker run -p 8000:8000 mc-converter-web
#
# 云平台 (Render / Railway / Fly) 直接把本仓库作为 Docker 服务即可，
# 它们会通过 PORT 环境变量告诉容器监听哪个端口。

# ---------- 1) 构建前端静态资源 ----------
FROM node:22-slim AS frontend
WORKDIR /src
COPY web/frontend/package.json ./
RUN npm install
COPY web/frontend/ ./
RUN npm run build

# ---------- 2) Python 运行环境 ----------
FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000
WORKDIR /app

COPY web/requirements.txt ./web/requirements.txt
RUN pip install --no-cache-dir -r web/requirements.txt

# 复制后端代码与核心转换库 (core/)
COPY core/ ./core/
COPY web/ ./web/

# 注入已在上一阶段构建好的前端静态文件
COPY --from=frontend /src/dist ./web/frontend/dist

EXPOSE 8000
CMD ["python", "web/serve.py"]
