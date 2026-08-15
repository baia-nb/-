# -*- coding: utf-8 -*-
"""格式读取器 / format readers."""
from . import bdx, litematic, mcstructure, schematic, schem
from .mcstructure import read_mcstructure
from .bdx import read_bdx
from .litematic import read_litematic
from .schematic import read_schematic
from .schem import read_schem

def detect_format(path):
    """通过文件头和扩展名自动识别格式 / detect format by magic and extension."""
    import os
    ext = os.path.splitext(path)[1].lower()
    if ext == ".bdx":
        return "bdx"
    if ext == ".litematic":
        return "litematic"
    if ext == ".mcstructure":
        return "mcstructure"
    if ext == ".schematic":
        return "schematic"
    if ext == ".schem":
        return "schem"
    return None

def read_structure(path, fmt=None):
    """读取建筑文件为 Structure / read structure file."""
    if fmt is None:
        fmt = detect_format(path)
    if fmt == "bdx":
        return read_bdx(path)
    if fmt == "litematic":
        return read_litematic(path)
    if fmt == "mcstructure":
        return read_mcstructure(path)
    if fmt == "schematic":
        return read_schematic(path)
    if fmt == "schem":
        return read_schem(path)
    raise ValueError(f"不支持的格式: {fmt}")
