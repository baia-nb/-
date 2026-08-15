# -*- coding: utf-8 -*-
"""优化器 / optimizers.

参考 Exchange Tool v13.0 的优化功能:
- fill 三维合并压缩 (RLE + 纵向缝合)
- 区块化 (按 16³ 区块分组)
- 自动加进度 (插入 tellraw 进度提示)
- 掉落方块保护 (重力方块下方添加 barrier)
- 生成保护 (border_block + deny 区域)
"""
import os
import re
from collections import defaultdict
from .paths import default_output_path, ensure_dir, get_desktop_dir
from .blocks import GRAVITY_BLOCKS


def parse_txt(lines):
    """解析 setblock 指令列表 / parse setblock lines.

    返回 [(x, y, z, block_name, states_dict, data, full_line), ...]
    """
    out = []
    pat = re.compile(
        r"setblock\s+~?(-?\d+)\s+~?(-?\d+)\s+~?(-?\d+)\s+(\S+)"
    )
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = pat.search(s)
        if not m:
            continue
        x, y, z = int(m.group(1)), int(m.group(2)), int(m.group(3))
        block_part = m.group(4)
        # 去除方括号 states
        name = block_part.split("[")[0]
        states = {}
        sm = re.search(r"\[([^\]]*)\]", block_part)
        if sm:
            for kv in sm.group(1).split(","):
                kv = kv.strip()
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    states[k.strip()] = v.strip()
        out.append((x, y, z, name, states, 0, s))
    return out


def fill_optimize(lines, out_path=None, input_path=None):
    """fill 三维合并压缩 / fill 3D merge compression.

    基于 RLE + 纵向缝合算法, 将相邻同种方块合并为 fill 命令。
    """
    blocks = parse_txt(lines)
    if not blocks:
        return out_path or (default_output_path(input_path or "input.txt", "_优化", ".txt"))

    # 按方块名+states分组
    groups = defaultdict(list)
    for b in blocks:
        key = (b[3], tuple(sorted(b[4].items())))
        groups[key].append(b)

    result = []
    for (name, states_tuple), items in groups.items():
        # 在同种方块组内做纵向(y轴)合并
        # 按 (x, z) 分组, 每组内按 y 排序, 合并连续段
        by_xz = defaultdict(list)
        for b in items:
            by_xz[(b[0], b[2])].append(b[1])  # y 坐标
        states_str = ""
        if states_tuple:
            states_str = "[" + ",".join(f"{k}={v}" for k, v in states_tuple) + "]"
        for (x, z), ys in by_xz.items():
            ys.sort()
            # 合并连续的 y 段
            start = ys[0]
            prev = ys[0]
            for y in ys[1:]:
                if y == prev + 1:
                    prev = y
                else:
                    if start == prev:
                        result.append((x, start, z, name, states_str))
                    else:
                        result.append(f"fill ~{x} ~{start} ~{z} ~{x} ~{prev} ~{z} {name}{states_str}")
                    start = y
                    prev = y
            if start == prev:
                result.append((x, start, z, name, states_str))
            else:
                result.append(f"fill ~{x} ~{start} ~{z} ~{x} ~{prev} ~{z} {name}{states_str}")

    # 转换为输出行
    out_lines = []
    for r in result:
        if isinstance(r, tuple):
            x, y, z, name, states_str = r
            out_lines.append(f"setblock ~{x} ~{y} ~{z} {name}{states_str}")
        else:
            out_lines.append(r)

    if not out_path:
        out_path = default_output_path(input_path or "input.txt", "_优化", ".txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    return out_path


def chunkify(lines, out_path=None, input_path=None):
    """区块化: 按 16³ 区块分组并相对化坐标 / chunkify.

    将海量 setblock 按 16³ 区块分组, 配合 tp 指令动态加载。
    """
    blocks = parse_txt(lines)
    if not blocks:
        return out_path or default_output_path(input_path or "input.txt", "_区块化", ".txt")

    # 按 16³ 区块分组
    chunks = defaultdict(list)
    for b in blocks:
        cx = b[0] // 16
        cy = b[1] // 16
        cz = b[2] // 16
        chunks[(cx, cy, cz)].append(b)

    out_lines = []
    for (cx, cy, cz), items in sorted(chunks.items()):
        base_x = cx * 16
        base_y = cy * 16
        base_z = cz * 16
        out_lines.append(f"# 区块 ({cx},{cy},{cz}) 基址 ~{base_x} ~{base_y} ~{base_z}")
        out_lines.append(f"tp @s ~{base_x} ~{base_y} ~{base_z}")
        for b in items:
            rx = b[0] - base_x
            ry = b[1] - base_y
            rz = b[2] - base_z
            states_str = ""
            if b[4]:
                states_str = "[" + ",".join(f"{k}={v}" for k, v in b[4].items()) + "]"
            out_lines.append(f"setblock ~{rx} ~{ry} ~{rz} {b[3]}{states_str}")

    if not out_path:
        out_path = default_output_path(input_path or "input.txt", "_区块化", ".txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    return out_path


def add_progress(lines, out_path=None, input_path=None):
    """自动加进度: 在指令序列中插入 tellraw 进度提示 / add progress messages."""
    total = len([l for l in lines if l.strip() and not l.strip().startswith("#")])
    if total == 0:
        return out_path or default_output_path(input_path or "input.txt", "_加进度", ".txt")

    out_lines = []
    step = max(1, total // 10)  # 每 10% 报告一次
    count = 0
    for line in lines:
        s = line.strip()
        if s and not s.startswith("#"):
            count += 1
            if count % step == 0:
                pct = int(count * 100 / total)
                out_lines.append(f'tellraw @s {{"text":"进度: {pct}% ({count}/{total})","color":"aqua"}}')
        out_lines.append(line)
    out_lines.append(f'tellraw @s {{"text":"完成! 共 {total} 个方块","color":"green"}}')

    if not out_path:
        out_path = default_output_path(input_path or "input.txt", "_加进度", ".txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    return out_path


def fall_protection(lines, out_path=None, input_path=None):
    """掉落方块保护: 为重力方块下方添加 barrier / fall protection."""
    blocks = parse_txt(lines)
    if not blocks:
        return out_path or default_output_path(input_path or "input.txt", "_防掉落", ".txt")

    # 找出所有重力方块位置
    gravity_positions = set()
    for b in blocks:
        name = b[3].lower()
        # 去除 minecraft: 前缀
        short = name.split(":")[-1]
        if short in GRAVITY_BLOCKS or any(g in short for g in GRAVITY_BLOCKS):
            gravity_positions.add((b[0], b[1], b[2]))

    # 找出已有方块位置
    existing = {(b[0], b[1], b[2]) for b in blocks}

    # 为重力方块下方添加 barrier (如果下方没有方块)
    barriers = set()
    for (x, y, z) in gravity_positions:
        below = (x, y - 1, z)
        if below not in existing:
            barriers.add(below)

    out_lines = list(lines)
    if barriers:
        out_lines.append("# 掉落方块保护 barriers")
        for (x, y, z) in sorted(barriers):
            out_lines.append(f"setblock ~{x} ~{y} ~{z} barrier")

    if not out_path:
        out_path = default_output_path(input_path or "input.txt", "_防掉落", ".txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    return out_path


def generate_protection(lines, out_path=None, input_path=None, border=True, deny=True):
    """生成保护: border_block + deny 区域 / generate protection.

    自动识别建筑范围, 生成两层 border_block 和/或 deny 保护区域。
    """
    blocks = parse_txt(lines)
    if not blocks:
        return out_path or default_output_path(input_path or "input.txt", "_保护", ".txt")

    xs = [b[0] for b in blocks]
    ys = [b[1] for b in blocks]
    zs = [b[2] for b in blocks]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)

    out_lines = list(lines)

    if border:
        out_lines.append("# border_block 保护")
        # 两层 border_block
        for layer in range(2):
            ox = min_x - 1 - layer
            oy = min_y - 1 - layer
            oz = min_z - 1 - layer
            tx = max_x + 1 + layer
            ty = max_y + 1 + layer
            tz = max_z + 1 + layer
            out_lines.append(
                f"fill ~{ox} ~{oy} ~{oz} ~{tx} ~{ty} ~{tz} border_block"
            )

    if deny:
        out_lines.append("# deny 区域")
        out_lines.append(
            f"fill ~{min_x} ~{min_y} ~{min_z} ~{max_x} ~{max_y} ~{max_z} deny"
        )

    if not out_path:
        out_path = default_output_path(input_path or "input.txt", "_保护", ".txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    return out_path
