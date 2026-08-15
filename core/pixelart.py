# -*- coding: utf-8 -*-
"""像素画转换 / pixel art conversion.

将图片像素化为羊毛/混凝土等方块指令。
"""
import os
from .paths import default_output_path, ensure_dir, get_subdir
from .blocks import PIXELART_BLOCKS, find_closest_block


def convert_pixelart(img_path, out_path=None, max_w=None, max_h=None, input_path=None):
    """图片转像素画 setblock 指令 / image to pixel art setblock commands.

    Args:
        img_path: 图片路径
        out_path: 输出路径(可选)
        max_w, max_h: 最大尺寸(按比例缩放)
    """
    from PIL import Image
    img = Image.open(img_path).convert("RGB")

    # 缩放
    w, h = img.size
    if max_w and w > max_w:
        ratio = max_w / w
        w, h = max_w, int(h * ratio)
    if max_h and h > max_h:
        ratio = max_h / h
        w, h = int(w * ratio), max_h
    img = img.resize((w, h), Image.LANCZOS)

    pixels = img.load()
    lines = []
    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            block = find_closest_block(r, g, b)
            lines.append(f"setblock ~{x} ~0 ~{y} {block}")

    if not out_path:
        if input_path:
            out_path = default_output_path(input_path, "", ".txt", subdir="图片转指令")
        else:
            import os
            base = os.path.splitext(os.path.basename(img_path))[0]
            out_path = os.path.join(get_subdir("图片转指令"), f"{base}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path
