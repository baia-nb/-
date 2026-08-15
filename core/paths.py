# -*- coding: utf-8 -*-
"""路径管理 / path management.

参考 Exchange Tool v13.0 的统一输出管理设计:
所有生成文件自动保存至桌面 建筑txt/ 目录, 不同插件细分到子文件夹。
"""
import os


def get_desktop_dir():
    """桌面/建筑txt 主输出目录 / main output directory."""
    return os.path.join(os.path.expanduser("~"), "Desktop", "建筑txt")


def ensure_dir(path):
    """确保目录存在 / ensure directory exists."""
    os.makedirs(path, exist_ok=True)
    return path


def get_subdir(name):
    """获取子目录(如 图片转指令/批量处理结果/) / get subdirectory by name."""
    p = os.path.join(get_desktop_dir(), name)
    return ensure_dir(p)


def default_output_path(input_path, suffix, ext, subdir=None):
    """根据输入文件生成默认输出路径 / generate default output path.

    Args:
        input_path: 输入文件路径
        suffix: 输出文件名后缀(如 _优化, _区块化)
        ext: 输出扩展名(如 .txt, .ibi)
        subdir: 子目录名(可选)
    """
    import os
    base = os.path.splitext(os.path.basename(input_path))[0]
    name = f"{base}{suffix}{ext}" if suffix else f"{base}{ext}"
    if subdir:
        out_dir = get_subdir(subdir)
    else:
        out_dir = ensure_dir(get_desktop_dir())
    return os.path.join(out_dir, name)
