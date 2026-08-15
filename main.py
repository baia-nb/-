# -*- coding: utf-8 -*-
"""我的世界格式转换器 - 程序入口 / Minecraft Format Converter - entry point.

支持两种模式:
- 交互式菜单 GUI (默认): 双击运行
- 命令行模式: 我的世界格式转换器.exe --plugin "插件名" --args "参数1" "参数2"
"""
import os
import sys


def _import_plugins():
    """导入所有插件模块以触发注册 / import all plugins."""
    try:
        from plugins import converters, music, optimizers, batch, tools, crypto_service
    except Exception as e:
        print(f"插件导入警告: {e}", file=sys.stderr)


def cli_mode(argv):
    """命令行模式 / CLI mode.

    格式: --plugin "插件名" --args "参数1" "参数2" ...
    或:   --list  (列出所有插件)
    """
    _import_plugins()
    from plugins.registry import list_plugins, get_plugin

    if not argv or argv[0] in ("--list", "-list", "-l"):
        # 重定向 stdout 为 UTF-8 以支持 emoji / force utf-8 stdout
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
        cats = list_plugins()
        cat_names = {
            "转换": "[转换] 转换类",
            "指令txt": "[指令txt] 指令txt类",
            "音乐": "[音乐] 音乐类",
            "优化": "[优化] 优化类",
            "批量": "[批量] 批量类",
            "加密服务": "[加密] 加密服务",
            "其它": "[其它] 其它类",
        }
        for cat, plugins in cats.items():
            print(f"\n{cat_names.get(cat, cat)}")
            for p in plugins:
                print(f"  {p['name']}: {p['desc']}")
        return 0

    if argv[0] in ("--plugin", "-plugin", "-p"):
        if len(argv) < 2:
            print("用法: --plugin \"插件名\" --args \"参数1\" \"参数2\" ...")
            return 1
        plugin_name = argv[1]
        args = []
        if len(argv) > 2:
            if argv[2] in ("--args", "-args", "-a"):
                args = argv[3:]
            else:
                args = argv[2:]
        plugin = get_plugin(plugin_name)
        if not plugin:
            print(f"未找到插件: {plugin_name}")
            print("使用 --list 查看可用插件")
            return 1
        try:
            result = plugin["run"](args)
            print(f"[OK] 输出: {result}")
            return 0
        except Exception as e:
            import traceback
            print(f"[ERR] {e}")
            traceback.print_exc()
            return 2

    print(f"未知参数: {argv[0]}")
    print("使用 --list 查看可用插件")
    return 1


def main():
    argv = sys.argv[1:]
    # CLI 模式
    if argv and (argv[0].startswith("--") or argv[0].startswith("-")):
        sys.exit(cli_mode(argv))
    # GUI 模式
    _import_plugins()
    from ui.app import launch
    launch()


if __name__ == "__main__":
    main()
