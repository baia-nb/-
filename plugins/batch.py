# -*- coding: utf-8 -*-
"""批量处理类插件 / batch plugins."""
from plugins.registry import register
from core.batch import (
    batch_convert, batch_pixelart, batch_mcstructure_to_ibi, batch_midi_to_ibi,
    batch_midi_to_txt, batch_midi_to_ldlmusic, batch_midi_to_json, batch_chunkify
)


@register("批量转化", "批量", "自动识别格式 → 转换 → 区块化 → 加进度(流水线)")
def plugin_batch_convert(args):
    folder = args[0]
    results = batch_convert(folder)
    return f"完成 {sum(1 for r in results if r[2] == 'ok')}/{len(results)} 个文件"


@register("批量像素画转换", "批量", "文件夹内所有图片 → 羊毛画指令")
def plugin_batch_pixelart(args):
    folder = args[0]
    max_w = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    max_h = int(args[2]) if len(args) > 2 and args[2].isdigit() else None
    results = batch_pixelart(folder, max_w, max_h)
    return f"完成 {sum(1 for r in results if r[2] == 'ok')}/{len(results)} 个文件"


@register("批量mcstructure转ibi", "批量", "所有 .mcstructure → IBI")
def plugin_batch_mcstructure_to_ibi(args):
    folder = args[0]
    results = batch_mcstructure_to_ibi(folder)
    return f"完成 {sum(1 for r in results if r[2] == 'ok')}/{len(results)} 个文件"


@register("批量mid/midi转ibi", "批量", "所有 MIDI → IBI")
def plugin_batch_midi_to_ibi(args):
    folder = args[0]
    results = batch_midi_to_ibi(folder)
    return f"完成 {sum(1 for r in results if r[2] == 'ok')}/{len(results)} 个文件"


@register("批量mid/midi转指令txt", "批量", "所有 MIDI → 音符盒 setblock")
def plugin_batch_midi_to_txt(args):
    folder = args[0]
    results = batch_midi_to_txt(folder)
    return f"完成 {sum(1 for r in results if r[2] == 'ok')}/{len(results)} 个文件"


@register("批量mid/midi转ldlmusic", "批量", "所有 MIDI → .ldlmusic 音乐文件")
def plugin_batch_midi_to_ldlmusic(args):
    folder = args[0]
    results = batch_midi_to_ldlmusic(folder)
    return f"完成 {sum(1 for r in results if r[2] == 'ok')}/{len(results)} 个文件"


@register("批量mid/midi转音乐json", "批量", "所有 MIDI → playsound 命令 JSON")
def plugin_batch_midi_to_json(args):
    folder = args[0]
    results = batch_midi_to_json(folder)
    return f"完成 {sum(1 for r in results if r[2] == 'ok')}/{len(results)} 个文件"


@register("批量区块化", "批量", "批量将文件夹内所有 .txt 指令文件区块化")
def plugin_batch_chunkify(args):
    folder = args[0]
    results = batch_chunkify(folder)
    return f"完成 {sum(1 for r in results if r[2] == 'ok')}/{len(results)} 个文件"
