# -*- coding: utf-8 -*-
"""其它类工具插件 / misc tool plugins."""
import os
from plugins.registry import register
from core.paths import default_output_path, get_subdir
from core.pixelart import convert_pixelart


@register("像素画转换", "其它", "图片 → setblock 羊毛画指令(单张)")
def plugin_pixelart(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    max_w = int(args[2]) if len(args) > 2 and args[2].isdigit() else None
    max_h = int(args[3]) if len(args) > 3 and args[3].isdigit() else None
    return convert_pixelart(inp, out, max_w, max_h, inp)


@register("心如止水式json转指令txt", "其它",
          "chunkedBlocks+namespaces 结构 JSON → setblock 指令集")
def json_to_txt(args):
    """将心如止水式结构 JSON 转为 setblock 指令集。"""
    inp = args[0]
    out_name = args[1] if len(args) > 1 else None
    import json
    with open(inp, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 心如止水格式: {chunkedBlocks: [{x,y,z,block:{name,states}}, ...], namespaces: {...}}
    blocks = data.get("chunkedBlocks") or data.get("blocks") or []
    lines = []
    for b in blocks:
        x, y, z = b.get("x", 0), b.get("y", 0), b.get("z", 0)
        blk = b.get("block", b)
        name = blk.get("name", "minecraft:stone")
        states = blk.get("states", {})
        if states:
            state_str = "[" + ",".join(f"{k}={v}" for k, v in states.items()) + "]"
        else:
            state_str = ""
        lines.append(f"setblock ~{x} ~{y} ~{z} {name}{state_str}")
    base = out_name or os.path.splitext(os.path.basename(inp))[0]
    out_dir = get_subdir("")  # 桌面/建筑txt
    out_path = os.path.join(out_dir, f"{base}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path
