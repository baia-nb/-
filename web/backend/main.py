# -*- coding: utf-8 -*-
"""我的世界格式转换器 · 在线版后端 / Web backend.

复用项目根目录的 core/ 完成真实格式转换, 通过 FastAPI 暴露为 Web API,
并托管构建后的前端静态文件 (web/frontend/dist)。
"""
import os
import sys
import time
import uuid
import io
import shutil
import tempfile
import contextlib
from pathlib import Path
from datetime import datetime

# 将项目根目录 (dabao) 加入 sys.path, 以便 import core / plugins
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from typing import List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import importlib

from core.readers import read_structure, detect_format
from core.writers import write_txt, write_ibi, write_dsb, write_mcstructure

# ---- 载入全部插件 (转换/音乐/优化/批量/加密) 以暴露完整功能 ----
for _pm in ("plugins.converters", "plugins.music", "plugins.optimizers",
            "plugins.batch", "plugins.tools", "plugins.crypto_service"):
    try:
        importlib.import_module(_pm)
    except Exception as _e:  # 某个插件缺依赖时不致命, 其余仍可用
        print(f"[warn] plugin import failed: {_pm}: {_e}", file=sys.stderr)
try:
    from plugins.registry import list_plugins as _list_plugins, get_plugin as _get_plugin
except Exception:
    _list_plugins = lambda: {}
    _get_plugin = lambda n: None

app = FastAPI(title="我的世界格式转换器 · 在线版")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 临时工作目录
WORKDIR = Path(tempfile.gettempdir()) / "mcweb_convert"
WORKDIR.mkdir(parents=True, exist_ok=True)

# 目标格式定义: writer 函数名, 扩展名, 中文名
TARGETS = {
    "txt":         ("write_txt", ".txt", "setblock 指令文本"),
    "ibi":         ("write_ibi", ".ibi", "IBI 加密命令方块包"),
    "dsb":         ("write_dsb", ".dsb", "DSB 结构文件"),
    "mcstructure": ("write_mcstructure", ".mcstructure", "基岩版 MCStructure"),
}

SOURCE_FORMATS = {
    "bdx": "BDX (基岩版操作流)",
    "litematic": "Litematic (Java 版)",
    "mcstructure": "MCStructure (基岩版)",
    "schematic": "Schematic (旧版 Java)",
    "schem": "Schem (Sponge 新版)",
}

WRITERS = {
    "write_txt": write_txt,
    "write_ibi": write_ibi,
    "write_dsb": write_dsb,
    "write_mcstructure": write_mcstructure,
}

SUPPORTED_EXT = {".bdx", ".litematic", ".mcstructure", ".schematic", ".schem"}


def _cleanup_old():
    """清理 1 小时前的临时目录 / cleanup old temp dirs."""
    now = datetime.now().timestamp()
    for d in WORKDIR.iterdir():
        if d.is_dir():
            try:
                if now - d.stat().st_mtime > 3600:
                    shutil.rmtree(d, ignore_errors=True)
            except Exception:
                pass


@app.get("/api/formats")
def get_formats():
    return {
        "source": [{"id": k, "label": v} for k, v in SOURCE_FORMATS.items()],
        "target": [{"id": k, "label": v[2], "ext": v[1]} for k, v in TARGETS.items()],
    }


@app.post("/api/convert")
async def convert(file: UploadFile = File(...), target: str = Form("txt")):
    if target not in TARGETS:
        raise HTTPException(status_code=400, detail=f"不支持的目标格式: {target}")
    _cleanup_old()

    fid = uuid.uuid4().hex
    work = WORKDIR / fid
    work.mkdir(parents=True, exist_ok=True)
    in_path = work / file.filename

    try:
        data = await file.read()
        if not data:
            raise ValueError("空文件")
        in_path.write_bytes(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件读取失败: {e}")

    fmt = detect_format(str(in_path))
    if not fmt:
        head = in_path.read_bytes(4)
        if head[:3] == b"BD@":
            fmt = "bdx"
        else:
            raise HTTPException(
                status_code=400,
                detail="无法识别的源文件格式 (支持 .bdx/.litematic/.mcstructure/.schematic/.schem)",
            )

    try:
        struct = read_structure(str(in_path), fmt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析失败: {e}")

    blocks = len(struct.blocks)
    stem = Path(file.filename).stem
    ext = TARGETS[target][1]
    out_name = f"{stem}{ext}"
    out_path = work / out_name

    try:
        writer = WRITERS[TARGETS[target][0]]
        writer(struct, str(out_path), stem)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转换写入失败: {e}")

    if not out_path.exists() or out_path.stat().st_size == 0:
        raise HTTPException(status_code=500, detail="转换未产生有效输出文件")

    size = out_path.stat().st_size
    return {
        "id": fid,
        "filename": out_name,
        "source_format": fmt,
        "target": target,
        "blocks": blocks,
        "size": size,
    }


@app.get("/api/download/{fid}/{filename}")
def download(fid: str, filename: str):
    work = WORKDIR / fid
    out_path = work / filename
    if not out_path.exists() or not out_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在或已过期, 请重新转换")
    return FileResponse(str(out_path), filename=filename)


# ---------------------------------------------------------------------------
# 全功能插件运行器: 把项目内置的插件系统直接暴露到 Web
# ---------------------------------------------------------------------------
PLUGIN_CAT_ORDER = ["转换", "指令txt", "音乐", "优化", "批量", "其它", "加密服务"]


def _scan_new_files(dirs, since_ts):
    """扫描目录下 mtime >= since_ts 的文件 (同时覆盖'新增'与'覆盖写'两种情况)."""
    found = []
    for d in dirs:
        if not d or not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    if os.path.getmtime(fp) >= since_ts:
                        found.append(fp)
                except OSError:
                    pass
    return found


@app.get("/api/plugins")
def api_plugins():
    cats = _list_plugins()
    out = {}
    for cat in PLUGIN_CAT_ORDER:
        if cat in cats:
            out[cat] = [{"name": p["name"], "desc": p["desc"]} for p in cats[cat]]
    for cat, ps in cats.items():
        if cat not in out:
            out[cat] = [{"name": p["name"], "desc": p["desc"]} for p in ps]
    return out


@app.post("/api/plugin/run")
async def plugin_run(
    plugin: str = Form(...),
    files: List[UploadFile] = File(default=[]),
    params: str = Form(""),
):
    p = _get_plugin(plugin)
    if not p:
        raise HTTPException(status_code=404, detail=f"未找到插件: {plugin}")

    fid = uuid.uuid4().hex
    work = WORKDIR / fid
    work.mkdir(parents=True, exist_ok=True)

    # 保存上传文件 (保留顺序)
    paths = []
    for f in files:
        data = await f.read()
        if not data:
            continue
        fp = work / f.filename
        fp.write_bytes(data)
        paths.append(str(fp))

    param_lines = [ln.strip() for ln in params.splitlines() if ln.strip()]

    # 批量类: 把上传文件放进一个文件夹, 作为单个目录参数传入
    is_batch = ("批量" in plugin) or (p.get("category") == "批量")
    if is_batch and paths:
        folder = work / "input_folder"
        folder.mkdir(exist_ok=True)
        for pth in paths:
            shutil.move(pth, folder / os.path.basename(pth))
        args = [str(folder)] + param_lines
    else:
        args = paths + param_lines

    # 受控扫描目录: 仅桌面/建筑txt (所有插件默认输出位置, 不含上传输入)
    desk = os.path.join(os.path.expanduser("~"), "Desktop", "建筑txt")
    scan_dirs = [desk]

    # 捕获 stdout (部分插件直接打印结果或路径); 不捕获 stderr 以免污染子进程线程输出
    buf = io.StringIO()
    start_ts = time.time()
    ret = None
    try:
        with contextlib.redirect_stdout(buf):
            ret = p["run"](args)
    except SystemExit:
        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"运行失败: {e}")

    # 1) 扫描受控目录 (mtime 判定: 同时覆盖'新增'与'覆盖写')
    new_files = _scan_new_files(scan_dirs, start_ts - 0.5)

    # 2) 插件返回值指向的路径 (文件或目录)
    if ret and isinstance(ret, str):
        rp = Path(ret.strip())
        if rp.exists():
            if rp.is_dir():
                for root, _, fs in os.walk(rp):
                    for f in fs:
                        nf = os.path.join(root, f)
                        if nf not in new_files:
                            new_files.append(nf)
            elif str(rp) not in new_files:
                new_files.append(str(rp))

    # 把产物复制到本次任务目录以便下载
    served = []
    for nf in new_files:
        nf = Path(nf)
        if not nf.is_file():
            continue
        dest = work / nf.name
        if dest.exists():
            dest = work / f"{len(served)}_{nf.name}"
        try:
            shutil.copy2(nf, dest)
        except Exception:
            continue
        served.append(dest.name)

    # 文本型结果 (插件返回说明字符串 / 打印输出) —— 不应视为失败
    messages = []
    if ret and isinstance(ret, str) and not Path(ret.strip()).exists():
        messages.append(ret.strip())
    out_log = buf.getvalue().strip()
    if out_log:
        messages.append(out_log)

    if not served:
        if messages:
            return {"id": fid, "plugin": plugin, "message": "\n".join(messages), "files": []}
        raise HTTPException(status_code=500, detail="未产生输出文件, 请检查输入与参数")

    return {
        "id": fid,
        "plugin": plugin,
        "message": ("\n".join(messages) if messages else None),
        "files": served,
    }


# 托管前端静态文件 (构建后)
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")
else:
    @app.get("/")
    def root():
        return JSONResponse({
            "name": "我的世界格式转换器 · 在线版 API",
            "status": "ok",
            "hint": "前端未构建, 请先执行 web/frontend 下的 npm install && npm run build。",
            "endpoints": ["/api/formats", "/api/convert", "/api/download/{fid}/{filename}"],
        })
