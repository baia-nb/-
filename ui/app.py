# -*- coding: utf-8 -*-
"""交互式菜单 GUI / interactive menu GUI.

参考 Exchange Tool v13.0 的双模式设计:
- 交互式菜单 (GUI 风格, 显示 Banner 和编号选择)
- 命令行模式 (适合自动化)
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext


def _import_plugins():
    """导入所有插件模块以触发注册 / import all plugins to trigger registration."""
    try:
        from plugins import converters, music, optimizers, batch, tools, crypto_service
    except Exception as e:
        print(f"插件导入警告: {e}")


def launch():
    """启动 GUI / launch GUI."""
    _import_plugins()
    from plugins.registry import list_plugins

    root = tk.Tk()
    root.title("我的世界格式转换器")
    root.geometry("800x600")
    root.configure(bg="#2b2b2b")

    # Banner
    banner = tk.Label(root, text="我的世界格式转换器",
                      font=("微软雅黑", 18, "bold"), fg="#00ff88", bg="#2b2b2b")
    banner.pack(pady=10)

    # 主容器
    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=10, pady=5)

    # 左侧: 插件列表
    left_frame = ttk.LabelFrame(main_frame, text="功能列表")
    left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

    tree = ttk.Treeview(left_frame, columns=("desc",), show="tree")
    tree.heading("#0", text="插件")
    tree.heading("desc", text="说明")
    tree.pack(fill="both", expand=True)

    cats = list_plugins()
    cat_names = {
        "转换": "🔄 转换类",
        "指令txt": "📜 指令txt类",
        "音乐": "🎵 音乐类",
        "优化": "⚡ 优化类",
        "批量": "📦 批量类",
        "加密服务": "🔐 加密服务",
        "其它": "🛠️ 其它类",
    }
    for cat, plugins in cats.items():
        cat_label = cat_names.get(cat, cat)
        node = tree.insert("", "end", text=cat_label, open=True)
        for p in plugins:
            tree.insert(node, "end", text=p["name"], values=(p["desc"],),
                        tags=(p["name"],))

    # 右侧: 参数和执行
    right_frame = ttk.LabelFrame(main_frame, text="参数")
    right_frame.pack(side="right", fill="y", padx=(5, 0))

    ttk.Label(right_frame, text="输入文件/文件夹:").pack(anchor="w", pady=(10, 0))
    path_entry = ttk.Entry(right_frame, width=40)
    path_entry.pack(fill="x", pady=2)
    ttk.Button(right_frame, text="浏览...",
               command=lambda: _browse(path_entry)).pack(pady=2)

    ttk.Label(right_frame, text="输出文件(可选):").pack(anchor="w", pady=(10, 0))
    out_entry = ttk.Entry(right_frame, width=40)
    out_entry.pack(fill="x", pady=2)

    ttk.Label(right_frame, text="附加参数(可选):").pack(anchor="w", pady=(10, 0))
    args_entry = ttk.Entry(right_frame, width=40)
    args_entry.pack(fill="x", pady=2)

    run_btn = ttk.Button(right_frame, text="执行",
                         command=lambda: _run(tree, path_entry, out_entry, args_entry, log))
    run_btn.pack(pady=10)

    # 底部: 日志
    log_frame = ttk.LabelFrame(main_frame, text="日志")
    log_frame.pack(side="bottom", fill="x", pady=(5, 0))
    log = scrolledtext.ScrolledText(log_frame, height=8, bg="#1e1e1e", fg="#d4d4d4")
    log.pack(fill="both", expand=True)

    root.mainloop()


def _browse(entry):
    """浏览文件或文件夹 / browse for file or folder."""
    path = filedialog.askopenfilename()
    if not path:
        path = filedialog.askdirectory()
    if path:
        entry.delete(0, "end")
        entry.insert(0, path)


def _run(tree, path_entry, out_entry, args_entry, log):
    """执行选中的插件 / run selected plugin."""
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("提示", "请先选择一个插件")
        return
    item = tree.item(sel[0])
    name = item.get("text")
    tags = item.get("tags")
    if not tags:
        return  # 选中了分类节点
    plugin_name = tags[0]
    from plugins.registry import get_plugin
    plugin = get_plugin(plugin_name)
    if not plugin:
        log.insert("end", f"未找到插件: {plugin_name}\n")
        return
    input_path = path_entry.get()
    out_path = out_entry.get() or None
    extra = args_entry.get()
    args = [a for a in [input_path, out_path, extra] if a]
    log.insert("end", f"执行: {plugin_name}\n参数: {args}\n")
    log.see("end")
    try:
        result = plugin["run"](args)
        log.insert("end", f"完成: {result}\n\n")
        log.see("end")
        messagebox.showinfo("完成", f"输出: {result}")
    except Exception as e:
        import traceback
        log.insert("end", f"错误: {e}\n{traceback.format_exc()}\n\n")
        log.see("end")
        messagebox.showerror("错误", str(e))
