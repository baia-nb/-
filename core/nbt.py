# -*- coding: utf-8 -*-
"""NBT (Named Binary Tag) 解析器 / NBT parser.

支持 Java (big-endian) 与 Bedrock (little-endian) 格式, 支持 gzip 压缩。
参考 Minecraft 数据格式规范。
"""
import gzip
import io
import struct


TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12


class Tag:
    """通用 Tag 容器 / generic tag container."""
    __slots__ = ("type", "name", "value")

    def __init__(self, type_, name="", value=None):
        self.type = type_
        self.name = name
        self.value = value

    def __repr__(self):
        return f"Tag(type={self.type}, name={self.name!r}, value={self.value!r})"


def _read_string(f, little_endian=False):
    fmt = "<H" if little_endian else ">H"
    (length,) = struct.unpack(fmt, f.read(2))
    if length == 0:
        return ""
    data = f.read(length)
    return data.decode("utf-8", errors="replace")


def _read_payload(f, tag_type, little_endian=False):
    """读取 tag 载荷 / read tag payload."""
    le = little_endian
    if tag_type == TAG_BYTE:
        return struct.unpack("<b" if le else ">b", f.read(1))[0]
    if tag_type == TAG_SHORT:
        return struct.unpack("<h" if le else ">h", f.read(2))[0]
    if tag_type == TAG_INT:
        return struct.unpack("<i" if le else ">i", f.read(4))[0]
    if tag_type == TAG_LONG:
        return struct.unpack("<q" if le else ">q", f.read(8))[0]
    if tag_type == TAG_FLOAT:
        return struct.unpack("<f" if le else ">f", f.read(4))[0]
    if tag_type == TAG_DOUBLE:
        return struct.unpack("<d" if le else ">d", f.read(8))[0]
    if tag_type == TAG_BYTE_ARRAY:
        n = struct.unpack("<i" if le else ">i", f.read(4))[0]
        return list(struct.unpack(f"{'<' if le else '>'}{n}b", f.read(n))) if n > 0 else []
    if tag_type == TAG_STRING:
        return _read_string(f, le)
    if tag_type == TAG_LIST:
        child_type = struct.unpack("<B" if le else ">B", f.read(1))[0]
        n = struct.unpack("<i" if le else ">i", f.read(4))[0]
        items = []
        for _ in range(n):
            items.append(_read_payload(f, child_type, le))
        return items
    if tag_type == TAG_COMPOUND:
        d = {}
        while True:
            t = struct.unpack("<B" if le else ">B", f.read(1))[0]
            if t == TAG_END:
                break
            name = _read_string(f, le)
            val = _read_payload(f, t, le)
            d[name] = Tag(t, name, val)
        return d
    if tag_type == TAG_INT_ARRAY:
        n = struct.unpack("<i" if le else ">i", f.read(4))[0]
        return list(struct.unpack(f"{'<' if le else '>'}{n}i", f.read(4 * n))) if n > 0 else []
    if tag_type == TAG_LONG_ARRAY:
        n = struct.unpack("<i" if le else ">i", f.read(4))[0]
        return list(struct.unpack(f"{'<' if le else '>'}{n}q", f.read(8 * n))) if n > 0 else []
    raise ValueError(f"未知 tag 类型: {tag_type}")


def parse(data, little_endian=False, compressed=False):
    """解析 NBT 数据 / parse NBT bytes."""
    if compressed:
        data = gzip.decompress(data)
    f = io.BytesIO(data)
    root_type = struct.unpack("<B" if little_endian else ">B", f.read(1))[0]
    if root_type == TAG_END:
        return Tag(TAG_END, "", {})
    root_name = _read_string(f, little_endian)
    root_val = _read_payload(f, root_type, little_endian)
    return Tag(root_type, root_name, root_val)


def to_plain(tag):
    """递归将 Tag 转为纯 Python 值 / recursively convert Tag to plain value."""
    if isinstance(tag, Tag):
        return to_plain(tag.value)
    if isinstance(tag, dict):
        return {k: to_plain(v) for k, v in tag.items()}
    if isinstance(tag, list):
        return [to_plain(v) for v in tag]
    return tag


def make_compound(d, name=""):
    """从字典构造 compound Tag / build compound Tag from dict."""
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            t = TAG_COMPOUND
        elif isinstance(v, list) and v and isinstance(v[0], int):
            t = TAG_INT_ARRAY if len(v) > 0 else TAG_LIST
        elif isinstance(v, int):
            t = TAG_INT
        elif isinstance(v, float):
            t = TAG_DOUBLE
        elif isinstance(v, str):
            t = TAG_STRING
        else:
            t = TAG_COMPOUND
        out[k] = Tag(t, k, v)
    return Tag(TAG_COMPOUND, name, out)
