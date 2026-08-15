# -*- coding: utf-8 -*-
"""setblock 命令文本写入器 / setblock command text writer.

将 Structure 转换为一行一个的 setblock 指令, 参考 Exchange Tool v13.0。
"""
import os
from ..paths import get_desktop_dir, ensure_dir


def _format_states(states):
    """渲染方块状态为 [k=v,k=v] / render block states."""
    if not states:
        return ""
    parts = [f"{k}={v}" for k, v in states.items()]
    return "[" + ",".join(parts) + "]"


def _get_pos(block, idx, size):
    """获取方块坐标 / get block position.

    优先使用 nbt_data["pos"] 或 block.pos; 否则按 YZX 顺序由索引和尺寸推算。
    """
    nbt = getattr(block, "nbt_data", None)
    if nbt and isinstance(nbt, dict) and "pos" in nbt:
        return nbt["pos"]
    pos = getattr(block, "pos", None)
    if pos is not None:
        return pos
    sx, sy, sz = size if size else (1, 1, 1)
    if sx <= 0 or sz <= 0:
        return (0, 0, 0)
    y = idx // (sx * sz)
    rem = idx % (sx * sz)
    z = rem // sx
    x = rem % sx
    return (x, y, z)


def write(structure, out_path=None, name=None):
    """将 Structure 写为 setblock 指令文本 / write structure as setblock commands.

    Args:
        structure: Structure 对象
        out_path: 输出路径(可选)
        name: 文件名(无扩展名, 可选)

    Returns:
        输出文件路径
    """
    size = getattr(structure, "size", (0, 0, 0))
    fmt = getattr(structure, "format", "")
    lines = []
    for idx, block in enumerate(structure.blocks):
        x, y, z = _get_pos(block, idx, size)
        states_str = _format_states(getattr(block, "states", {}))
        cmd = f"setblock ~{x} ~{y} ~{z} {block.name}{states_str}"
        data_val = getattr(block, "data", 0)
        if data_val:
            cmd += f" {data_val}"
        lines.append(cmd)

    if out_path is None:
        out_dir = ensure_dir(get_desktop_dir())
        fname = (name or "structure") + ".txt"
        out_path = os.path.join(out_dir, fname)

    if not lines:
        # 0 方块: 写入诊断说明 / write diagnostic notice
        notice_lines = ["# 我的世界格式转换器 - 转换结果为空"]
        if fmt == "bdx_error":
            err = getattr(structure, "_error", "未知错误")
            notice_lines.append(f"# 错误: BDX 解析失败 - {err}")
            notice_lines.append("#")
            notice_lines.append("# 可能原因:")
            notice_lines.append("# 1. BDXConverter 库未正确安装或打包")
            notice_lines.append("# 2. BDX 文件损坏或格式不标准")
            notice_lines.append("# 3. 缺少运行时依赖 (nbtlib, brotli)")
            tb = getattr(structure, "_traceback", "")
            if tb:
                notice_lines.append("#")
                notice_lines.append("# === 详细错误 ===")
                for tb_line in tb.splitlines():
                    notice_lines.append(f"# {tb_line}")
        elif fmt == "bdx_encrypted":
            notice_lines.append("# 错误: BDX 文件解析失败")
            notice_lines.append("# 建议: 请确认文件为标准 BDX 格式")
        elif fmt:
            notice_lines.append(f"# 信息: 输入文件 ({fmt}) 未解析出任何方块。")
            notice_lines.append("# 请确认文件内容有效且格式正确。")
        else:
            notice_lines.append("# 信息: 输入结构中不含任何方块。")
            notice_lines.append("# 请确认文件内容有效且格式正确。")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(notice_lines) + "\n")
        return out_path

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")
    return out_path


def write_midi(midi_data, out_path=None, name=None):
    """将 MIDI/NbsData 写为音符盒 setblock 指令 / write midi as note block setblock commands.

    参考 Exchange Tool: 音符按 tick 排序, 螺旋式排列命令方块。
    """
    from ..model import MidiData, NbsData

    notes = []
    tempo = 100
    if isinstance(midi_data, MidiData):
        notes = sorted(midi_data.notes, key=lambda n: n.tick)
        tempo = midi_data.tempo
    elif isinstance(midi_data, NbsData):
        notes = sorted(midi_data.notes, key=lambda n: n.tick)
        tempo = int(midi_data.tempo * 50000)  # NBS ticks/sec -> us/beat approx

    lines = []
    # 螺旋排布: 每 tick 一行方块, 水平铺开
    # 简化: 按 tick 顺序, x = tick, y = 0, z = 音符索引在 tick 内
    per_tick = {}
    for n in notes:
        per_tick.setdefault(n.tick, []).append(n)

    tick_list = sorted(per_tick.keys())
    for tick_idx, t in enumerate(tick_list):
        for j, n in enumerate(per_tick[t]):
            x = tick_idx
            y = j // 16
            z = j % 16
            # pitch: 乐器方块 + 音高 note (0-24)
            note_pitch = max(0, min(24, getattr(n, "pitch", 0)))
            inst = getattr(n, "instrument", "harp")
            block_name = f"minecraft:noteblock[instrument={inst},note={note_pitch}]"
            lines.append(f"setblock ~{x} ~{y} ~{z} {block_name}")

    if out_path is None:
        out_dir = ensure_dir(get_desktop_dir())
        fname = (name or "music") + ".txt"
        out_path = os.path.join(out_dir, fname)

    if not lines:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("# 我的世界格式转换器 - 音乐转换结果为空\n")
            f.write("# MIDI/NBS 文件未解析出任何有效音符。\n")
            f.write("# 请确认文件格式正确且包含音符数据。\n")
        return out_path

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")
    return out_path
