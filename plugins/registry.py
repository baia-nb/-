# -*- coding: utf-8 -*-
"""插件注册表 / Plugin Registry.

参考 Exchange Tool v13.0 的插件化架构, 每个插件有:
- name: 插件名称(中文)
- category: 分类(转换/指令txt/优化/批量/其它)
- desc: 描述
- run: 执行函数(args) -> output_path
"""
import os

_PLUGINS = {}


def register(name, category, desc, aliases=None):
    """装饰器: 注册插件 / decorator to register a plugin."""
    def deco(func):
        _PLUGINS[name] = {
            "name": name,
            "category": category,
            "desc": desc,
            "run": func,
            "aliases": aliases or [],
        }
        for a in (aliases or []):
            _PLUGINS[a] = _PLUGINS[name]
        return func
    return deco


def get_plugin(name):
    """获取插件 / get plugin by name."""
    return _PLUGINS.get(name)


def list_plugins():
    """列出所有插件(按分类) / list all plugins by category."""
    cats = {}
    seen = set()
    for name, p in _PLUGINS.items():
        if name in seen:
            continue
        seen.add(name)
        cat = p["category"]
        cats.setdefault(cat, []).append(p)
    return cats


def get_desktop_dir():
    """桌面/建筑txt 目录 / desktop output directory."""
    return os.path.join(os.path.expanduser("~"), "Desktop", "建筑txt")


def ensure_dir(path):
    """确保目录存在 / ensure directory exists."""
    os.makedirs(path, exist_ok=True)
    return path
