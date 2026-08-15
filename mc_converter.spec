# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 / PyInstaller build spec.

我的世界格式转换器 - 参考架构
- 插件化架构 (plugins/)
- 核心 (core/)
- GUI (ui/)
"""
import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hidden = []
hidden += collect_submodules('PIL')
hidden += collect_submodules('BDXConverter')
hidden += collect_submodules('nbtlib')
hidden += collect_submodules('numpy')
hidden += ['tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
           'tkinter.dialog', 'tkinter.scrolledtext', '_tkinter',
           'ctypes', 'ctypes.wintypes',
           'BDXConverter', 'nbtlib', 'brotli', 'numpy', 'numpy.core']

datas = [
    ('core/block_runtime_ids.json', 'core'),
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'scipy', 'matplotlib', 'pandas',
        'PyQt5', 'PySide2', 'PyQt6', 'PySide6',
        'pytest', 'IPython', 'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='我的世界格式转换器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app.ico',
)
