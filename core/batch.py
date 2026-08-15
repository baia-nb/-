# -*- coding: utf-8 -*-
"""批量处理 / batch processing.

一键处理整个文件夹内的所有文件, 自动完成"转换 → 区块化 → 加进度"流水线。
"""
import os
from .paths import get_subdir, ensure_dir, get_desktop_dir
from .readers import read_structure, detect_format
from .writers import write_txt
from .optimizers import chunkify, add_progress


def batch_convert(folder, out_dir=None):
    """批量转化: 自动识别格式 → 转换 → 区块化 → 加进度 / batch convert pipeline.

    Args:
        folder: 输入文件夹
        out_dir: 输出目录(可选)
    Returns:
        list of (input_file, output_file, status)
    """
    if out_dir is None:
        out_dir = get_subdir("批量处理结果")
    results = []

    for fn in os.listdir(folder):
        fp = os.path.join(folder, fn)
        if not os.path.isfile(fp):
            continue
        ext = os.path.splitext(fn)[1].lower()
        if ext not in (".bdx", ".litematic", ".mcstructure", ".schematic", ".schem"):
            continue
        try:
            struct = read_structure(fp)
            base = os.path.splitext(fn)[0]
            txt_path = os.path.join(out_dir, f"{base}.txt")
            write_txt(struct, txt_path, base)
            # 区块化
            with open(txt_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
            chunk_path = os.path.join(out_dir, f"{base}_区块化.txt")
            chunkify(lines, chunk_path, fp)
            # 加进度
            with open(chunk_path, "r", encoding="utf-8") as f:
                lines2 = f.read().splitlines()
            final_path = os.path.join(out_dir, f"{base}_最终.txt")
            add_progress(lines2, final_path, fp)
            results.append((fp, final_path, "ok"))
        except Exception as e:
            results.append((fp, None, f"error: {e}"))
    return results


def batch_pixelart(folder, max_w=None, max_h=None, out_dir=None):
    """批量像素画转换 / batch pixel art conversion."""
    from .pixelart import convert_pixelart
    if out_dir is None:
        out_dir = get_subdir("批量像素画")
    results = []
    for fn in os.listdir(folder):
        fp = os.path.join(folder, fn)
        if not os.path.isfile(fp):
            continue
        ext = os.path.splitext(fn)[1].lower()
        if ext not in (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"):
            continue
        try:
            base = os.path.splitext(fn)[0]
            out_path = os.path.join(out_dir, f"{base}.txt")
            convert_pixelart(fp, out_path, max_w, max_h, fp)
            results.append((fp, out_path, "ok"))
        except Exception as e:
            results.append((fp, None, f"error: {e}"))
    return results


def batch_mcstructure_to_ibi(folder, out_dir=None):
    """批量 mcstructure 转 ibi / batch mcstructure to ibi."""
    from .writers.ibi import write as write_ibi
    from .readers.mcstructure import read_mcstructure
    if out_dir is None:
        out_dir = get_subdir("批量IBI")
    results = []
    for fn in os.listdir(folder):
        fp = os.path.join(folder, fn)
        if not os.path.isfile(fp) or not fn.lower().endswith(".mcstructure"):
            continue
        try:
            struct = read_mcstructure(fp)
            base = os.path.splitext(fn)[0]
            out_path = os.path.join(out_dir, f"{base}.ibi")
            write_ibi(struct, out_path, base)
            results.append((fp, out_path, "ok"))
        except Exception as e:
            results.append((fp, None, f"error: {e}"))
    return results


def batch_midi_to_ibi(folder, out_dir=None):
    """批量 midi 转 ibi / batch midi to ibi."""
    from .writers.ibi import write_midi
    from .midi import read_midi
    if out_dir is None:
        out_dir = get_subdir("批量音乐IBI")
    results = []
    for fn in os.listdir(folder):
        fp = os.path.join(folder, fn)
        if not os.path.isfile(fp):
            continue
        ext = os.path.splitext(fn)[1].lower()
        if ext not in (".mid", ".midi"):
            continue
        try:
            midi = read_midi(fp)
            base = os.path.splitext(fn)[0]
            out_path = os.path.join(out_dir, f"{base}.ibi")
            write_midi(midi, out_path, base)
            results.append((fp, out_path, "ok"))
        except Exception as e:
            results.append((fp, None, f"error: {e}"))
    return results


def batch_midi_to_txt(folder, out_dir=None):
    """批量 midi 转 txt / batch midi to txt."""
    from .writers.txt import write_midi
    from .midi import read_midi
    if out_dir is None:
        out_dir = get_subdir("批量mid指令txt")
    results = []
    for fn in os.listdir(folder):
        fp = os.path.join(folder, fn)
        if not os.path.isfile(fp):
            continue
        ext = os.path.splitext(fn)[1].lower()
        if ext not in (".mid", ".midi"):
            continue
        try:
            midi = read_midi(fp)
            base = os.path.splitext(fn)[0]
            out_path = os.path.join(out_dir, f"{base}.txt")
            write_midi(midi, out_path, base)
            results.append((fp, out_path, "ok"))
        except Exception as e:
            results.append((fp, None, f"error: {e}"))
    return results


def batch_midi_to_ldlmusic(folder, out_dir=None):
    """批量 midi 转 ldlmusic / batch midi to ldlmusic."""
    from .writers.ldlmusic import write as write_ldl
    from .midi import read_midi
    if out_dir is None:
        out_dir = get_subdir("批量ldlmusic")
    results = []
    for fn in os.listdir(folder):
        fp = os.path.join(folder, fn)
        if not os.path.isfile(fp):
            continue
        ext = os.path.splitext(fn)[1].lower()
        if ext not in (".mid", ".midi"):
            continue
        try:
            midi = read_midi(fp)
            base = os.path.splitext(fn)[0]
            out_path = os.path.join(out_dir, f"{base}.ldlmusic")
            write_ldl(midi, out_path, base)
            results.append((fp, out_path, "ok"))
        except Exception as e:
            results.append((fp, None, f"error: {e}"))
    return results


def batch_midi_to_json(folder, out_dir=None):
    """批量 midi 转 json / batch midi to json."""
    from .writers.musicjson import write as write_json
    from .midi import read_midi
    if out_dir is None:
        out_dir = get_subdir("批量音乐JSON")
    results = []
    for fn in os.listdir(folder):
        fp = os.path.join(folder, fn)
        if not os.path.isfile(fp):
            continue
        ext = os.path.splitext(fn)[1].lower()
        if ext not in (".mid", ".midi"):
            continue
        try:
            midi = read_midi(fp)
            base = os.path.splitext(fn)[0]
            out_path = os.path.join(out_dir, f"{base}_音乐.json")
            write_json(midi, out_path, base)
            results.append((fp, out_path, "ok"))
        except Exception as e:
            results.append((fp, None, f"error: {e}"))
    return results


def batch_chunkify(folder, out_dir=None):
    """批量区块化 / batch chunkify."""
    if out_dir is None:
        out_dir = get_subdir("批量区块化")
    results = []
    for fn in os.listdir(folder):
        fp = os.path.join(folder, fn)
        if not os.path.isfile(fp) or not fn.lower().endswith(".txt"):
            continue
        try:
            with open(fp, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
            base = os.path.splitext(fn)[0]
            out_path = os.path.join(out_dir, f"{base}_区块化.txt")
            chunkify(lines, out_path, fp)
            results.append((fp, out_path, "ok"))
        except Exception as e:
            results.append((fp, None, f"error: {e}"))
    return results
