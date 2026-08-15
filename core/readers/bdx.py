# -*- coding: utf-8 -*-
"""BDX 格式读取器 / BDX format reader.

BDX 是 Minecraft 基岩版建筑指令格式 (BD@ 魔数)。
使用 BDXConverter 库解析二进制 BD@ 文件, 回退到明文解析。

BDX 操作类型:
- CreateConstantString: 定义方块名常量 (如 "bedrock")
- PlaceBlock: 放置方块 (用 blockConstantStringID 引用常量)
- PlaceBlockWithBlockStates: 放置带状态的方块 (如 facing_direction)
- PlaceBlockWithNBTData: 放置带 NBT 的方块 (如箱子内容)
- PlaceBlockWithCommandBlockData: 放置命令方块
- PlaceRuntimeBlock: 用运行时 ID 放置方块 (需版本映射表)
- AddX/Y/ZValue: 游标移动 (+1)
- SubtractX/Y/ZValue: 游标移动 (-1)
- AddInt8/16/32X/Y/ZValue: 游标移动 (带值)
- UseRuntimeIDPool: 指定运行时 ID 池版本
"""
import os
import re
from ..model import Structure, Block

BDX_MAGIC = b"BD@"

_RUNTIME_ID_TABLE = None


def _load_runtime_id_table():
    """加载运行时 ID 映射表 / load runtime ID mapping table."""
    global _RUNTIME_ID_TABLE
    if _RUNTIME_ID_TABLE is not None:
        return _RUNTIME_ID_TABLE
    import json
    import sys
    candidates = [
        os.path.join(os.path.dirname(__file__), "block_runtime_ids.json"),
        os.path.join(getattr(sys, "_MEIPASS", ""), "core", "block_runtime_ids.json"),
    ]
    for table_path in candidates:
        try:
            with open(table_path, "r", encoding="utf-8") as f:
                _RUNTIME_ID_TABLE = json.load(f)
            return _RUNTIME_ID_TABLE
        except (OSError, json.JSONDecodeError):
            continue
    _RUNTIME_ID_TABLE = []
    return _RUNTIME_ID_TABLE


def _runtime_id_to_name(runtime_id: int, pool_id: int = 117) -> tuple:
    """运行时 ID 转方块名 / convert runtime ID to block name.

    Returns:
        (block_name, block_data)
    """
    table = _load_runtime_id_table()
    if runtime_id < len(table):
        entry = table[runtime_id]
        name = entry[0].replace("tile.", "")
        data = entry[1] if len(entry) > 1 else 0
        return name, data
    return f"unknown_{runtime_id}", 0


def _convert_states_string(states_str: str) -> dict:
    """将 BDX 状态字符串转为字典 / convert BDX states string to dict.

    BDX 格式: ["facing_direction":1,"open_bit":false]
    输出: {"facing_direction": 1, "open_bit": False}
    """
    if not states_str or states_str == "[]":
        return {}
    inner = states_str.strip().lstrip("[").rstrip("]")
    if not inner:
        return {}
    states = {}
    for pair in inner.split(","):
        pair = pair.strip()
        if ":" in pair:
            k, v = pair.split(":", 1)
            k = k.strip().strip('"')
            v = v.strip().strip('"')
            if v.lower() in ("true", "false"):
                states[k] = v.lower() == "true"
            else:
                try:
                    states[k] = int(v)
                except ValueError:
                    states[k] = v
    return states


def _nbt_to_dict(nbt_obj):
    """递归将 NBT 对象转为可序列化字典 / convert NBT object to dict."""
    if nbt_obj is None:
        return None
    try:
        from nbtlib import Compound, List, Byte, Int, Short, Long, Float, Double, String
    except ImportError:
        return str(nbt_obj)
    if isinstance(nbt_obj, Compound):
        return {k: _nbt_to_dict(v) for k, v in nbt_obj.items()}
    if isinstance(nbt_obj, List):
        return [_nbt_to_dict(v) for v in nbt_obj]
    if isinstance(nbt_obj, (Byte, Int, Short, Long)):
        return int(nbt_obj)
    if isinstance(nbt_obj, (Float, Double)):
        return float(nbt_obj)
    if isinstance(nbt_obj, String):
        return str(nbt_obj)
    return str(nbt_obj)


def _is_text(data: bytes) -> bool:
    """判断字节流是否主要为可打印文本 / check if bytes are mostly printable text."""
    if not data:
        return False
    sample = data[:512]
    ok = 0
    for b in sample:
        if b in (9, 10, 13) or 32 <= b < 127:
            ok += 1
    return ok / len(sample) > 0.85


def _split_fields(line: str):
    line = line.strip()
    if "," in line:
        return [p.strip() for p in line.split(",") if p.strip() != ""]
    return [p for p in re.split(r"\s+", line) if p]


def _to_int(s, default=0):
    if s is None:
        return default
    try:
        return int(s)
    except (ValueError, TypeError):
        try:
            return int(float(s))
        except (ValueError, TypeError):
            return default


def _parse_plain(text: str) -> Structure:
    """解析明文 BDX: 头部(author/size/offset) + (x,y,z,name,data) 行。"""
    st = Structure(format="bdx")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    header_keys = ("author", "size", "offset", "origin", "尺寸", "作者", "偏移")
    body_start = 0
    for i, ln in enumerate(lines[:8]):
        low = ln.lower().lstrip("#").strip()
        if low.startswith("size") or low.startswith("尺寸"):
            nums = [p for p in re.split(r"[,\s]+", low) if re.match(r"^-?\d+$", p)]
            if len(nums) >= 3:
                st.size = (int(nums[0]), int(nums[1]), int(nums[2]))
                body_start = max(body_start, i + 1)
        elif low.startswith("offset") or low.startswith("origin") or low.startswith("偏移"):
            nums = [p for p in re.split(r"[,\s]+", low) if re.match(r"^-?\d+$", p)]
            if len(nums) >= 3:
                st.origin = (int(nums[0]), int(nums[1]), int(nums[2]))
                body_start = max(body_start, i + 1)
        elif low.startswith("author") or low.startswith("作者"):
            body_start = max(body_start, i + 1)
    for ln in lines[body_start:]:
        s = ln.strip()
        if s.startswith("#"):
            continue
        low = s.lower()
        if any(low.startswith(k) for k in header_keys):
            continue
        fields = _split_fields(s)
        if len(fields) < 4:
            continue
        x = _to_int(fields[0], None)
        y = _to_int(fields[1], None)
        z = _to_int(fields[2], None)
        if x is None or y is None or z is None:
            continue
        name = fields[3]
        data = _to_int(fields[4]) if len(fields) >= 5 else 0
        if name == "air":
            continue
        st.add(Block(name=name, data=data, nbt_data={"pos": (x, y, z)}))
    return st


def _parse_bd_binary(path: str) -> Structure:
    """用 BDXConverter 库解析 BD@ 二进制文件 / parse BD@ with BDXConverter."""
    from BDXConverter import ReadBDXFile

    bdx = ReadBDXFile(path)
    st = Structure(format="bdx")

    strings = []
    x = y = z = 0
    current_pool_id = 117

    for item in bdx.BDXContents:
        t = type(item).__name__
        op_num = getattr(item, "operationNumber", 0)

        if t == "CreateConstantString":
            strings.append(item.constantString)

        elif t == "PlaceBlock":
            name = strings[item.blockConstantStringID] if item.blockConstantStringID < len(strings) else "unknown"
            if name != "air":
                st.add(Block(name=name, data=item.blockData, nbt_data={"pos": (x, y, z)}))

        elif t == "PlaceBlockWithBlockStates":
            name = strings[item.blockConstantStringID] if item.blockConstantStringID < len(strings) else "unknown"
            sid = item.blockStatesConstantStringID
            states_str = strings[sid] if sid < len(strings) else "[]"
            states = _convert_states_string(states_str)
            if name != "air":
                st.add(Block(name=name, states=states, nbt_data={"pos": (x, y, z)}))

        elif t == "PlaceBlockWithNBTData":
            name = strings[item.blockConstantStringID] if item.blockConstantStringID < len(strings) else "unknown"
            sid = item.blockStatesConstantStringID
            states_str = strings[sid] if sid < len(strings) else "[]"
            states = _convert_states_string(states_str)
            nbt = _nbt_to_dict(getattr(item, "blockNBT", None))
            if name != "air":
                st.add(Block(name=name, states=states, nbt_data={"pos": (x, y, z), "nbt": nbt}))

        elif t == "PlaceBlockWithCommandBlockData":
            name = strings[item.blockConstantStringID] if item.blockConstantStringID < len(strings) else "unknown"
            nbt = {
                "pos": (x, y, z),
                "command": getattr(item, "command", ""),
                "mode": getattr(item, "mode", 0),
                "conditional": getattr(item, "conditional", False),
                "needsRedstone": getattr(item, "needsRedstone", False),
                "tickDelay": getattr(item, "tickDelay", 0),
                "customName": getattr(item, "customName", ""),
                "trackOutput": getattr(item, "trackOutput", True),
            }
            st.add(Block(name=name, data=item.blockData, nbt_data=nbt))

        elif t == "PlaceRuntimeBlock":
            rid = getattr(item, "runtimeId", 0)
            name, rdata = _runtime_id_to_name(rid, current_pool_id)
            if name != "air":
                st.add(Block(name=name, data=rdata, nbt_data={"pos": (x, y, z)}))

        elif t == "PlaceRuntimeBlockWithCommandBlockData":
            rid = getattr(item, "runtimeId", 0)
            name, rdata = _runtime_id_to_name(rid, current_pool_id)
            nbt = {
                "pos": (x, y, z),
                "command": getattr(item, "command", ""),
                "mode": getattr(item, "mode", 0),
                "conditional": getattr(item, "conditional", False),
                "needsRedstone": getattr(item, "needsRedstone", False),
                "tickDelay": getattr(item, "tickDelay", 0),
                "customName": getattr(item, "customName", ""),
                "trackOutput": getattr(item, "trackOutput", True),
            }
            st.add(Block(name=name, data=rdata, nbt_data=nbt))

        elif t == "UseRuntimeIDPool":
            current_pool_id = getattr(item, "poolId", 117)

        elif t == "NOP":
            pass

        # 游标移动: 单步
        elif t in ("AddXValue",):
            x += 1
        elif t in ("AddYValue",):
            y += 1
        elif t in ("AddZValue",):
            z += 1
        elif t in ("SubtractXValue",):
            x -= 1
        elif t in ("SubtractYValue",):
            y -= 1
        elif t in ("SubtractZValue",):
            z -= 1

        # 游标移动: 带值
        elif hasattr(item, "value") and "Add" in t:
            val = item.value
            if "X" in t:
                x += val
            elif "Y" in t:
                y += val
            elif "Z" in t:
                z += val
        elif hasattr(item, "value") and "Subtract" in t:
            val = item.value
            if "X" in t:
                x -= val
            elif "Y" in t:
                y -= val
            elif "Z" in t:
                z -= val

    st.origin = (0, 0, 0)
    if st.blocks:
        xs = [b.nbt_data["pos"][0] for b in st.blocks]
        ys = [b.nbt_data["pos"][1] for b in st.blocks]
        zs = [b.nbt_data["pos"][2] for b in st.blocks]
        st.size = (max(xs) + 1, max(ys) + 1, max(zs) + 1)
    return st


def read_bdx(path) -> Structure:
    """读取 BDX 建筑文件 / read BDX structure file."""
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return Structure(format="bdx")

    # BD@ 二进制格式: 用 BDXConverter 解析
    if data.startswith(BDX_MAGIC):
        try:
            return _parse_bd_binary(path)
        except Exception as e:
            # BDXConverter 解析失败, 记录错误并尝试明文回退
            import traceback
            err_msg = f"{type(e).__name__}: {e}"
            tb = traceback.format_exc()
            rest = data[len(BDX_MAGIC):]
            if rest:
                for enc in ("utf-8", "gbk", "gb2312", "gb18030", "utf-16", "latin-1"):
                    try:
                        text = rest.decode(enc)
                        if text and _is_text(text.encode("utf-8", errors="ignore")):
                            parsed = _parse_plain(text)
                            if len(parsed.blocks) > 0:
                                parsed.format = "bdx"
                                return parsed
                    except (UnicodeDecodeError, LookupError):
                        continue
            st_err = Structure(format="bdx_error")
            st_err.origin = (0, 0, 0)
            st_err.size = (0, 0, 0)
            st_err._error = err_msg
            st_err._traceback = tb
            return st_err

    # 明文 BDX (无 BD@ 头)
    if _is_text(data):
        for enc in ("utf-8", "gbk", "gb2312", "gb18030"):
            try:
                text = data.decode(enc)
                parsed = _parse_plain(text)
                if len(parsed.blocks) > 0:
                    parsed.format = "bdx"
                    return parsed
            except (UnicodeDecodeError, LookupError):
                continue
        try:
            return _parse_plain(data.decode("utf-8", errors="ignore"))
        except Exception:
            return Structure(format="bdx")

    return Structure(format="bdx")
