# -*- coding: utf-8 -*-
"""一键启动脚本 / convenience launcher.

用法:
    cd C:\Users\ttnld\Documents\trae_projects\dabao
    python web/serve.py
然后浏览器打开 http://localhost:8000
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn

if __name__ == "__main__":
    # 云平台 (Render/Railway/Fly 等) 通常通过 PORT 环境变量指定监听端口
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("web.backend.main:app", host="0.0.0.0", port=port, reload=False)
