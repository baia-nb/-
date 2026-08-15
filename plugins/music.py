# -*- coding: utf-8 -*-
"""音乐类插件 / music plugins.

将 MIDI / NBS 转换为各种音乐格式。
"""
import os
from plugins.registry import register
from core.paths import default_output_path, get_subdir, ensure_dir
from core.writers import write_ldlmusic, write_musicjson


@register("mid/midi转指令txt", "音乐", "MIDI → 音符盒 setblock")
def midi_to_txt(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    from core.midi import read_midi
    from core.writers.txt import write_midi
    base = os.path.splitext(os.path.basename(inp))[0]
    midi = read_midi(inp)
    return write_midi(midi, out, base)


@register("mid/midi转ibi", "音乐", "MIDI → IBI 音符盒包")
def midi_to_ibi(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    from core.midi import read_midi
    from core.writers.ibi import write_midi
    base = os.path.splitext(os.path.basename(inp))[0]
    midi = read_midi(inp)
    return write_midi(midi, out, base)


@register("mid/midi转dsb", "音乐", "MIDI → DSB 音符盒结构(强制连锁)")
def midi_to_dsb(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    from core.midi import read_midi
    from core.writers.dsb import write_midi
    base = os.path.splitext(os.path.basename(inp))[0]
    midi = read_midi(inp)
    return write_midi(midi, out, base)


@register("mid/midi转ldlmusic", "音乐", "MIDI → .ldlmusic 音乐文件(压缩+Base64)")
def midi_to_ldlmusic(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    from core.midi import read_midi
    base = os.path.splitext(os.path.basename(inp))[0]
    midi = read_midi(inp)
    return write_ldlmusic(midi, out, base)


@register("mid/midi转音乐播放json", "音乐", "MIDI → playsound 命令 JSON")
def midi_to_json(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    from core.midi import read_midi
    base = os.path.splitext(os.path.basename(inp))[0]
    midi = read_midi(inp)
    return write_musicjson(midi, out, base)


@register("nbs转ibi", "音乐", "NBS → IBI 红石音乐包")
def nbs_to_ibi(args):
    inp = args[0]
    out = args[1] if len(args) > 1 else None
    from core.nbs import read_nbs
    from core.writers.ibi import write_nbs
    base = os.path.splitext(os.path.basename(inp))[0]
    nbs = read_nbs(inp)
    return write_nbs(nbs, out, base)
