# -*- coding: utf-8 -*-
"""转换类插件 / converter plugins.

将各种建筑格式转为 setblock 指令、IBI 或 DSB。
"""
import os
from plugins.registry import register
from core.paths import default_output_path, get_desktop_dir, ensure_dir
from core.readers import read_structure, detect_format
from core.writers import write_txt, write_ibi, write_dsb, write_mcstructure


@register("bdx转txt", "转换", "BDX → setblock 命令")
def bdx_to_txt(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    struct = read_structure(inp, "bdx")
    base = os.path.splitext(os.path.basename(inp))[0]
    return write_txt(struct, out, base)


@register("litematic转txt", "转换", "Litematic → setblock")
def litematic_to_txt(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    struct = read_structure(inp, "litematic")
    base = os.path.splitext(os.path.basename(inp))[0]
    return write_txt(struct, out, base)


@register("mcstructure转txt", "转换", "MCStructure → setblock")
def mcstructure_to_txt(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    struct = read_structure(inp, "mcstructure")
    base = os.path.splitext(os.path.basename(inp))[0]
    return write_txt(struct, out, base)


@register("schematic转txt", "转换", "旧版 Schematic → setblock")
def schematic_to_txt(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    struct = read_structure(inp, "schematic")
    base = os.path.splitext(os.path.basename(inp))[0]
    return write_txt(struct, out, base)


@register("schem转txt", "转换", "新版 Sponge .schem → setblock")
def schem_to_txt(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    struct = read_structure(inp, "schem")
    base = os.path.splitext(os.path.basename(inp))[0]
    return write_txt(struct, out, base)


@register("bdx转ibi", "转换", "BDX → 加密 IBI 命令方块包")
def bdx_to_ibi(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    struct = read_structure(inp, "bdx")
    base = os.path.splitext(os.path.basename(inp))[0]
    return write_ibi(struct, out, base)


@register("mcstructure转ibi", "转换", "MCStructure → IBI")
def mcstructure_to_ibi(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    struct = read_structure(inp, "mcstructure")
    base = os.path.splitext(os.path.basename(inp))[0]
    return write_ibi(struct, out, base)


@register("mcstructure转dsb", "转换", "MCStructure → DSB")
def mcstructure_to_dsb(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    struct = read_structure(inp, "mcstructure")
    base = os.path.splitext(os.path.basename(inp))[0]
    return write_dsb(struct, out, base)


@register("txt+json转ibi", "转换", "setblock 文本 + 命令方块 JSON → IBI 加密包")
def txt_json_to_ibi(args):
    """将 setblock 文本指令文件和命令方块 JSON 文件合并加密为 .ibi 导入包。"""
    inp_txt = args[0]
    inp_json = args[1] if len(args) > 1 else None
    out = args[2] if len(args) > 2 else None
    from core.writers.ibi import write_txt_json_ibi
    base = os.path.splitext(os.path.basename(inp_txt))[0]
    return write_txt_json_ibi(inp_txt, inp_json, out, base)
