# -*- coding: utf-8 -*-
"""优化类插件 / optimizer plugins.

对已有 .txt 指令文件进行压缩、分组或功能增强。
"""
from plugins.registry import register
from core.optimizers import (
    fill_optimize, chunkify, add_progress, fall_protection, generate_protection
)


def _read_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().splitlines()


@register("fill三维优化", "优化", "setblock → fill 三维合并压缩(RLE+纵向缝合)")
def plugin_fill_optimize(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    lines = _read_lines(inp)
    return fill_optimize(lines, out, inp)


@register("区块化", "优化", "按 16³ 区块分组并相对化坐标")
def plugin_chunkify(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    lines = _read_lines(inp)
    return chunkify(lines, out, inp)


@register("自动加进度", "优化", "插入 tellraw 进度提示")
def plugin_add_progress(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    lines = _read_lines(inp)
    return add_progress(lines, out, inp)


@register("掉落方块保护", "优化", "为重力方块下方添加 barrier 支撑")
def plugin_fall_protection(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    lines = _read_lines(inp)
    return fall_protection(lines, out, inp)


@register("生成保护（border+deny）", "优化",
          "自动识别建筑范围, 生成两层 border_block 和/或 deny 保护区域")
def plugin_generate_protection(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    lines = _read_lines(inp)
    border = True
    deny = True
    for a in args[2:]:
        if a == "--border":
            deny = False
        elif a == "--deny":
            border = False
    return generate_protection(lines, out, inp, border=border, deny=deny)
