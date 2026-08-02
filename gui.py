# coding: utf-8
"""getmusic GUI -- 基于 tkinter（原生 IME 支持，中文输入正常）

相比 Kivy 版，本版本改用标准库 tkinter，彻底解决 Windows 下无法用
输入法输入中文的问题。core.py 业务逻辑保持不变。
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont

import core
from core import (
    PLATFORMS, search_songs, fetch_music_by_song,
    load_config, save_config, load_cache, add_to_cache
)

# 配色（深色主题）
BG     = "#1e1e22"
CARD   = "#242429"
CARD2  = "#2c2c33"
BLUE   = "#3399ff"
GREEN  = "#2eae4d"
ORANGE = "#d9811a"
RED    = "#b8342e"
WHITE  = "#f2f2f7"
GRAY   = "#8c8c93"
MUTED  = "#59595f"
LINK   = "#33a6ff"

# 跨平台中文字体回退：Windows -> 微软雅黑，macOS -> 苹方，Linux -> 文泉驿/系统
FONT_FAMILY = ("Microsoft YaHei", "PingFang SC", "WenQuanYi Micro Hei", "SimHei", "sans-serif")


def font(size=11, bold=False):
    return (FONT_FAMILY, size, "bold" if bold else "normal")


def _truncate(text, size, bold, max_px):
    """超长文本按像素宽度截断并追加省略号，保证单行显示"""
    f = tkfont.Font(font=font(size, bold))
    if f.measure(text) <= max_px:
        return text
    cut = text
    while cut and f.measure(cut + "…") > max_px:
        cut = cut[:-1]
    return cut + "…"


def _shade(hex_color, factor):
    """按比例调亮/调暗颜色：factor>1 变亮，<1 变暗（用于按钮 hover/press 反馈）"""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return f'#{r:02x}{g:02x}{b:02x}'


def btn(master, text, bg, fg=WHITE, command=None, size=12, height=None, width=None, padx=0, pady=0):
    b = tk.Button(
        master, text=text, bg=bg, fg=fg,
        activebackground=_shade(bg, 1.12), activeforeground=fg,
        font=font(size), relief="flat", bd=0,
        command=command, cursor="hand2", highlightthickness=0,
    )
    # 记录“静止态”颜色，供 hover/press 与运行时换色（选中/完成态）统一使用
    b._rest_bg = bg
    b._rest_fg = fg

    def _enter(e):
        if str(b["state"]) != "disabled":
            b.configure(bg=_shade(b._rest_bg, 1.16), fg=b._rest_fg)

    def _leave(e):
        if str(b["state"]) != "disabled":
            b.configure(bg=b._rest_bg, fg=b._rest_fg)

    def _down(e):
        if str(b["state"]) != "disabled":
            b.configure(bg=_shade(b._rest_bg, 0.86))

    def _up(e):
        if str(b["state"]) != "disabled":
            b.configure(bg=_shade(b._rest_bg, 1.16))

    b.bind("<Enter>", _enter)
    b.bind("<Leave>", _leave)
    b.bind("<ButtonPress-1>", _down)
    b.bind("<ButtonRelease-1>", _up)

    if width:
        b.config(width=width)
    if height:
        b.config(height=height)
    if padx or pady:
        b.config(padx=padx, pady=pady)
    return b


def style_btn(b, bg, fg=None):
    """运行时更新按钮静止态颜色（如选中/完成态），并同步 hover 基线"""
    b._rest_bg = bg
    if fg is not None:
        b._rest_fg = fg
    b.configure(bg=bg, **({} if fg is None else {"fg": fg}))


class Toast:
    """轻量提示条（底部状态栏样式），自动消失。"""
    _win = None

    @classmethod
    def show(cls, root, msg, color=ORANGE, ms=2200):
        if cls._win and cls._win.winfo_exists():
            cls._win.destroy()
        w = tk.Toplevel(root)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        w.configure(bg=CARD2)
        lbl = tk.Label(w, text=msg, bg=CARD2, fg=WHITE, font=font(11),
                       padx=14, pady=8)
        lbl.pack()
        # 居中显示在父窗口下方
        root.update_idletasks()
        x = root.winfo_x() + (root.winfo_width() - w.winfo_reqwidth()) // 2
        y = root.winfo_y() + root.winfo_height() - 70
        w.geometry(f"+{x}+{y}")
        w.after(ms, lambda: w.destroy() if w.winfo_exists() else None)
        cls._win = w


class Screen:
    """屏幕基类：每个屏幕是一块 Frame，由 App 切换显示。"""
    def __init__(self, parent, app):
        self.app = app
        self.frame = tk.Frame(parent, bg=BG)

    def on_show(self):
        pass

    def on_hide(self):
        pass


class Welcome(Screen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        f = self.frame
        f.columnconfigure(0, weight=1)

        tk.Label(f, text="music", bg=BG, fg=WHITE, font=font(64, bold=True)).pack(pady=(70, 0))
        tk.Label(f, text="getmusic", bg=BG, fg=BLUE, font=font(28, bold=True)).pack(pady=(4, 0))
        tk.Frame(f, bg=MUTED, height=1, width=160).pack(pady=(20, 16))
        tk.Label(f, text="音乐获取工具", bg=BG, fg=WHITE, font=font(15, bold=True)).pack()
        tk.Label(f, text="支持 网易云音乐 · 咪咕音乐 · 波点音乐\n获取 VIP 歌曲播放直链",
                 bg=BG, fg=GRAY, font=font(12), justify="center").pack(pady=(10, 36))

        b = btn(f, "开始搜索", BLUE, size=15, height=1, width=18)
        b.configure(command=lambda: app.show("Search"))
        b.pack()

        tk.Label(f, text="GitHub 开源  |  禁止商用",
                 bg=BG, fg=MUTED, font=font(10)).pack(side="bottom", pady=16)


class Search(Screen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.platform = None
        self.config = load_config()
        f = self.frame

        # 标题栏
        hdr = tk.Frame(f, bg=BG)
        hdr.pack(fill="x", padx=16, pady=12)
        tk.Label(hdr, text="搜索音乐", bg=BG, fg=WHITE, font=font(16, bold=True)).pack(side="left")
        hbtn = tk.Frame(hdr, bg=BG)
        hbtn.pack(side="right")
        btn(hbtn, "历史记录", CARD2, size=11, width=9, command=lambda: app.show("History")).pack(side="left", padx=4)
        btn(hbtn, "设置", CARD2, size=11, width=7, command=lambda: app.show("Settings")).pack(side="left")

        # 主体卡片
        body = tk.Frame(f, bg=CARD, highlightbackground="#33333b", highlightthickness=1)
        body.pack(fill="both", expand=True, padx=16, pady=8)

        tk.Label(body, text="选择平台", bg=CARD, fg=GRAY, font=font(12), anchor="w").pack(fill="x", padx=14, pady=(14, 6))
        self.plat_btns = {}
        prow = tk.Frame(body, bg=CARD)
        prow.pack(fill="x", padx=14, pady=(0, 8))
        for i, (key, info) in enumerate(PLATFORMS.items()):
            b = btn(prow, info["name"], "#1a1a1f", fg=GRAY, size=12, width=12, command=lambda k=key: self._on_toggle(k))
            b.pack(side="left", padx=4, fill="x", expand=True)
            self.plat_btns[key] = b

        tk.Label(body, text="歌名 / 关键词", bg=CARD, fg=GRAY, font=font(12), anchor="w").pack(fill="x", padx=14, pady=(10, 4))
        self.kw = tk.Entry(body, bg="#1a1a1f", fg=WHITE, insertbackground=WHITE,
                           font=font(13), relief="flat", bd=2, highlightthickness=1,
                           highlightcolor=BLUE, highlightbackground="#3a3a42")
        self.kw.pack(fill="x", padx=14, pady=(0, 8))
        self.kw.bind("<Return>", lambda e: self.do_search())

        tk.Label(body, text="搜索数量", bg=CARD, fg=GRAY, font=font(12), anchor="w").pack(fill="x", padx=14, pady=(6, 4))
        self.num = tk.Entry(body, bg="#1a1a1f", fg=WHITE, insertbackground=WHITE,
                            font=font(13), relief="flat", bd=2, highlightthickness=1,
                            highlightcolor=BLUE, highlightbackground="#3a3a42")
        self.num.insert(0, str(self.config.get("default_num", 10)))
        self.num.pack(fill="x", padx=14, pady=(0, 12))
        self.num.bind("<Return>", lambda e: self.do_search())

        self.sbtn = btn(body, "搜 索", BLUE, size=14, height=1)
        self.sbtn.configure(command=self.do_search)
        self.sbtn.pack(fill="x", padx=14, pady=(4, 6))

        self.status = tk.Label(body, text="", bg=CARD, fg=MUTED, font=font(11))
        self.status.pack(fill="x", padx=14, pady=(2, 14))

    def _on_toggle(self, key):
        name = PLATFORMS[key]["name"]
        if self.platform == key:
            # 再次点击 = 取消选中
            style_btn(self.plat_btns[key], "#1a1a1f", GRAY)
            self.plat_btns[key].configure(text=name)
            self.platform = None
            self.status.configure(text="", fg=MUTED)
        else:
            # 先清空所有按钮的选中样式
            for k, b in self.plat_btns.items():
                style_btn(b, "#1a1a1f", GRAY)
                b.configure(text=PLATFORMS[k]["name"])
            # 再高亮当前选中：蓝底白字 + ✓ 勾标，状态一目了然
            style_btn(self.plat_btns[key], BLUE, WHITE)
            self.plat_btns[key].configure(text=f"✓ {name}")
            self.platform = key
            if key == "3":
                self.status.configure(text="[!] 波点音乐可能只返回试听片段", fg=ORANGE)
            elif key == "2":
                self.status.configure(text="[!] 咪咕音乐直链获取成功率较低", fg=ORANGE)
            else:
                self.status.configure(text=f"已选择：{name}")

    def do_search(self):
        if not self.platform:
            Toast.show(self.app.root, "请先选择音乐平台", ORANGE)
            return
        kw = self.kw.get().strip()
        if not kw:
            Toast.show(self.app.root, "请输入搜索关键词", ORANGE)
            return
        num_str = self.num.get().strip()
        num = int(num_str) if num_str.isdigit() else self.config.get("default_num", 10)
        if num < 1:
            num = 10

        plat = PLATFORMS[self.platform]
        self.sbtn.configure(text="搜索中...", state="disabled")
        self.status.configure(text=f'正在搜索 "{kw}"...', fg=BLUE)
        threading.Thread(target=self._worker, args=(plat, kw, num), daemon=True).start()

    def _worker(self, plat, kw, num):
        cfg = self.config.copy()
        cfg["default_num"] = num
        try:
            songs = search_songs(plat["url"], kw, cfg)
            err = None
        except Exception as e:
            songs, err = None, str(e)
        self.app.root.after(0, lambda: self._done(songs, plat, kw, err))

    def _done(self, songs, plat, kw, err):
        self.sbtn.configure(text="搜 索", state="normal")
        if err:
            Toast.show(self.app.root, f"出错：{err}", RED)
            self.status.configure(text=f"搜索失败：{err}", fg=RED)
            return
        if not songs:
            Toast.show(self.app.root, f'未找到 "{kw}" 相关歌曲', ORANGE)
            self.status.configure(text="未找到结果", fg=MUTED)
            return
        result = self.app.frames["Result"]
        result.show_results(songs, plat, kw)
        self.app.show("Result")

    def _on_config(self, cfg):
        self.config = cfg
        self.num.delete(0, "end")
        self.num.insert(0, str(cfg.get("default_num", 10)))

    def on_show(self):
        # 回到搜索页时清空上次的状态提示（"正在搜索..."、"搜索失败"等），避免残留
        self.status.configure(text="", fg=MUTED)


class Result(Screen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.songs = []
        self.platform = None
        self.config = load_config()
        self.bars = []
        f = self.frame

        hdr = tk.Frame(f, bg=BG)
        hdr.pack(fill="x", padx=16, pady=12)
        self.ttl = tk.Label(hdr, text="搜索结果", bg=BG, fg=WHITE, font=font(16, bold=True))
        self.ttl.pack(side="left")
        bb = btn(hdr, "<- 返回", CARD2, size=11, width=9, command=lambda: app.show("Search"))
        bb.pack(side="right")

        # 可滚动结果区（画布 + 滚动条放入一个填充容器，避免与底部状态栏位置冲突）
        list_frame = tk.Frame(f, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=16, pady=8)
        self.canvas = tk.Canvas(list_frame, bg=BG, highlightthickness=0)
        self.scroll = ttk.Scrollbar(list_frame, orient="vertical",
                                     command=self.canvas.yview, style="Dark.Vertical.TScrollbar")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scroll.set)

        self.inner = tk.Frame(self.canvas, bg=BG)
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        # 让内部框架宽度跟随画布宽度，卡片才能铺满整行
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self._win, width=e.width))

        # 底部状态栏（独立一行，放在列表区下方）
        self.info = tk.Label(f, text="", bg=BG, fg=MUTED, font=font(11))
        self.info.pack(fill="x", padx=16, pady=(0, 10))

    def _on_wheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_show(self):
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)

    def on_hide(self):
        self.canvas.unbind_all("<MouseWheel>")

    def show_results(self, songs, platform, keyword):
        self.songs = songs
        self.platform = platform
        for w in list(self.inner.children.values()):
            w.destroy()
        self.bars = []
        self.canvas.yview_moveto(0)
        if not songs:
            self.info.configure(text=f'未找到 "{keyword}" 的相关歌曲', fg=MUTED)
            self.ttl.configure(text="搜索结果 (0 首)")
            return
        self.ttl.configure(text=f"搜索结果 ({len(songs)} 首)")
        self.info.configure(text="", fg=GREEN)
        for i, s in enumerate(songs):
            self._card(i, s)

    def _card(self, idx, s):
        name = _truncate(s.get("song", "未知"), 13, True, 300)
        singer = _truncate(s.get("singer", "未知"), 11, False, 260)

        # 卡片：细边框 + 左侧平台色强调条，层次更清晰
        accent = self.platform.get("accent", BLUE)
        card = tk.Frame(self.inner, bg=CARD, highlightbackground="#33333b", highlightthickness=1)
        card.pack(fill="x", padx=2, pady=5)
        tk.Frame(card, bg=accent, width=4).pack(side="left", fill="y")

        body = tk.Frame(card, bg=CARD)
        body.pack(side="left", fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)  # 信息区自适应
        body.grid_columnconfigure(1, weight=0)  # 按钮区固定

        left = tk.Frame(body, bg=CARD)
        left.grid(row=0, column=0, sticky="nsew", padx=10, pady=8)
        tk.Label(left, text=str(idx + 1), bg=CARD, fg=accent,
                 font=font(14, bold=True), width=3).pack(side="left")

        info = tk.Frame(left, bg=CARD)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=name, bg=CARD, fg=WHITE, font=font(13, bold=True), anchor="w").pack(fill="x")
        tk.Label(info, text=singer, bg=CARD, fg=MUTED, font=font(11), anchor="w").pack(fill="x")

        fbtn = btn(body, "获取链接", BLUE, size=11, padx=12, pady=4)
        fbtn.configure(command=lambda i=idx + 1: self._fetch(i, fbtn))
        fbtn.grid(row=0, column=1, sticky="e", padx=(0, 10), pady=8)

        area = tk.Frame(body, bg="#1a1a1f")
        area.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        area.grid_columnconfigure(0, weight=1)  # 链接区扩展，复制按钮才贴右
        area.grid_remove()  # 默认隐藏，获取后显示
        lbl = tk.Label(area, text="", bg="#1a1a1f", fg=LINK, font=font(10),
                       anchor="w", justify="left")
        lbl.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        cbtn = btn(area, "复制", GREEN, size=10, width=7)
        cbtn.grid(row=0, column=1, sticky="e", padx=6, pady=6)

        self.bars.append((area, lbl, cbtn, fbtn))

    def _fetch(self, index, fbtn):
        s = self.songs[index - 1]
        name, singer = s.get("song", "未知"), s.get("singer", "未知")
        fbtn.configure(text="获取中...", state="disabled")
        self.info.configure(text=f"正在获取《{name}》播放链接...", fg=BLUE)
        threading.Thread(target=self._worker, args=(name, singer, index, fbtn), daemon=True).start()

    def _worker(self, name, singer, index, fbtn):
        cfg = load_config()
        try:
            result = fetch_music_by_song(self.platform["url"], name, singer, cfg, index)
            err = None
        except Exception as e:
            result, err = None, str(e)
        self.app.root.after(0, lambda: self._got(result, name, singer, index, err, fbtn))

    def _got(self, result, name, singer, index, err, fbtn):
        area, lbl, cbtn, _ = self.bars[index - 1]
        if err or not result:
            Toast.show(self.app.root, f"获取失败：{err or '可能无版权或 API 限制'}", RED)
            fbtn.configure(text="重试", state="normal")
            self.info.configure(text=f"获取《{name}》失败", fg=RED)
            return

        url = result["music_url"]
        add_to_cache(result.get("song", name), result.get("singer", singer),
                     url, self.platform["name"], self.config.get("max_cache", 20))

        fbtn.configure(text="[v] 已获取", state="disabled")
        style_btn(fbtn, GREEN, WHITE)
        # 链接只显示前 30 个字，完整链接仍保留在内存供复制
        lbl.configure(text=(url[:30] + "…") if len(url) > 30 else url)
        cbtn.configure(command=lambda: (self.app.root.clipboard_clear(),
                                         self.app.root.clipboard_append(url),
                                         Toast.show(self.app.root, "已复制", GREEN)))
        area.grid()
        self.info.configure(text=f'[OK]   {result.get("song", name)} - {result.get("singer", singer)}', fg=GREEN)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


class Settings(Screen):
    FIELDS = [
        ("默认搜索数量", "default_num", 10),
        ("请求超时秒数", "timeout", 10),
        ("最大重试次数", "max_retries", 3),
        ("重试间隔秒数", "retry_delay", 1),
        ("最大缓存条目数", "max_cache", 20),
    ]

    def __init__(self, parent, app):
        super().__init__(parent, app)
        f = self.frame
        self.config = load_config()
        self.inputs = {}

        hdr = tk.Frame(f, bg=BG)
        hdr.pack(fill="x", padx=16, pady=12)
        tk.Label(hdr, text="设置", bg=BG, fg=WHITE, font=font(16, bold=True)).pack(side="left")
        btn(hdr, "<- 返回", CARD2, size=11, width=9, command=lambda: app.show("Search")).pack(side="right")

        box = tk.Frame(f, bg=CARD, highlightbackground="#33333b", highlightthickness=1)
        box.pack(fill="x", padx=16, pady=4)
        # 标签贴卡片左边、输入框/按钮贴卡片右边：标签列 weight=1 吃掉中间空白。
        box.grid_columnconfigure(0, weight=1)
        for i, (label, key, default) in enumerate(self.FIELDS):
            tk.Label(box, text=label, bg=CARD, fg=GRAY, font=font(11), anchor="w").grid(
                row=i, column=0, sticky="w", padx=(12, 10), pady=7)
            ti = tk.Entry(box, bg="#1a1a1f", fg=WHITE, insertbackground=WHITE,
                          font=font(11), relief="flat", width=10,
                          highlightthickness=1, highlightcolor=BLUE, highlightbackground="#3a3a42")
            ti.insert(0, str(self.config.get(key, default)))
            ti.grid(row=i, column=1, sticky="e", padx=(0, 12), pady=7)
            self.inputs[key] = ti

        # DEBUG 开关（自定义开关按钮，避免原生勾选框蓝色边框歧义）
        di = len(self.FIELDS)
        tk.Label(box, text="DEBUG 模式", bg=CARD, fg=GRAY, font=font(11), anchor="w").grid(
            row=di, column=0, sticky="w", padx=(12, 10), pady=7)
        self.debug_on = bool(self.config.get("debug_mode", False))
        self.debug_btn = btn(box, "", CARD2, size=11, width=11, command=self._toggle_debug)
        self.debug_btn.grid(row=di, column=1, sticky="e", padx=(0, 12), pady=7)
        self._render_debug()

        save = btn(f, "保存", BLUE, size=13)
        save.configure(command=self.save)
        save.pack(fill="x", padx=16, pady=14)

    def on_show(self):
        # 重新打开时从磁盘同步最新配置（防止在其他界面改过）
        self.config = load_config()
        for label, key, default in self.FIELDS:
            self.inputs[key].delete(0, "end")
            self.inputs[key].insert(0, str(self.config.get(key, default)))
        self.debug_on = bool(self.config.get("debug_mode", False))
        self._render_debug()

    def _render_debug(self):
        """根据当前开关状态刷新按钮外观：开启=绿底，关闭=灰底"""
        if self.debug_on:
            style_btn(self.debug_btn, GREEN, WHITE)
            self.debug_btn.configure(text="● 已开启")
        else:
            style_btn(self.debug_btn, CARD2, GRAY)
            self.debug_btn.configure(text="○ 已关闭")

    def _toggle_debug(self):
        self.debug_on = not self.debug_on
        self._render_debug()

    def save(self):
        errors = []
        for key, ti in self.inputs.items():
            try:
                v = int(ti.get().strip())
                if v < 0:
                    errors.append(key)
                else:
                    self.config[key] = v
            except ValueError:
                errors.append(key)
        self.config["debug_mode"] = self.debug_on
        if errors:
            Toast.show(self.app.root, f"无效输入：{', '.join(errors)}", RED)
            return
        save_config(self.config)
        self.app.config = self.config
        self.app.frames["Search"]._on_config(self.config)
        Toast.show(self.app.root, "设置已保存", GREEN)
        self.app.show("Search")


class History(Screen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        f = self.frame

        hdr = tk.Frame(f, bg=BG)
        hdr.pack(fill="x", padx=16, pady=12)
        tk.Label(hdr, text="历史记录", bg=BG, fg=WHITE, font=font(16, bold=True)).pack(side="left")
        btn(hdr, "<- 返回", CARD2, size=11, width=9, command=lambda: app.show("Search")).pack(side="right")

        self.canvas = tk.Canvas(f, bg=BG, highlightthickness=0)
        self.scroll = ttk.Scrollbar(f, orient="vertical",
                                     command=self.canvas.yview, style="Dark.Vertical.TScrollbar")
        self.inner = tk.Frame(self.canvas, bg=BG)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self._win, width=e.width))
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True, padx=(16, 0))
        self.scroll.pack(side="right", fill="y")

    def on_show(self):
        self._refresh()
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)
        self.canvas.yview_moveto(0)  # 进入页面重置滚动位置，确保记录贴顶

    def on_hide(self):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_wheel(self, event):
        # 内容不满一屏时不响应滚轮，避免 yview 被改变导致 inner 在视口里偏移
        self.inner.update_idletasks()
        if self.inner.winfo_reqheight() <= self.canvas.winfo_height():
            self.canvas.yview_moveto(0)
            return
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _check_scroll(self):
        """内容不满一屏时隐藏滚动条并重置位置，满一屏时显示"""
        self.inner.update_idletasks()
        ch = self.canvas.winfo_height()
        ih = self.inner.winfo_reqheight()
        if ih <= ch:
            self.scroll.pack_forget()
            self.canvas.yview_moveto(0)
        else:
            self.scroll.pack(side="right", fill="y")

    def _refresh(self):
        for w in list(self.inner.children.values()):
            w.destroy()
        cache = load_cache()
        n = self.app.config.get("max_cache", 20)
        if not cache:
            tk.Label(self.inner, text="暂无历史记录", bg=BG, fg=MUTED, font=font(13)).pack(pady=30)
            self._check_scroll()
            return
        for e in reversed(cache[-n:]):
            row = tk.Frame(self.inner, bg=CARD, highlightbackground="#33333b", highlightthickness=1)
            row.pack(fill="x", padx=2, pady=1)
            tk.Label(row, text=e["time"], bg=CARD, fg=MUTED, font=font(9), width=16, anchor="w").pack(side="left", padx=8)
            info_txt = _truncate(f"{e['song']} - {e['singer']}", 11, False, 380)
            tk.Label(row, text=info_txt, bg=CARD, fg=WHITE,
                     font=font(10), anchor="w").pack(side="left", fill="x", expand=True, padx=4)
        self._check_scroll()


class GetMusicApp:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.root.title("getmusic -- 音乐获取工具")
        self.root.geometry("500x700")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)  # 禁止放大缩小，保持默认尺寸

        # 深色滚动条样式（Windows 默认主题无法自定义颜色，必须切到 clam）
        try:
            _style = ttk.Style()
            _style.theme_use("clam")
            # darkcolor/lightcolor 设成与滑块同色，避免 thumb 上的 grip 抓握线显示成黑色
            _style.configure("Dark.Vertical.TScrollbar",
                             background=MUTED, troughcolor=BG,
                             bordercolor=BG, darkcolor=MUTED, lightcolor=MUTED,
                             arrowcolor=GRAY, arrowsize=13, gripcount=0)
            _style.map("Dark.Vertical.TScrollbar",
                       background=[("active", GRAY)],
                       arrowcolor=[("active", WHITE)])
        except tk.TclError:
            pass

        container = tk.Frame(root, bg=BG)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (Welcome, Search, Result, History, Settings):
            f = F(container, self)
            self.frames[F.__name__] = f
            f.frame.grid(row=0, column=0, sticky="nsew")

        self.current = None
        self.show("Welcome")

    def show(self, name):
        cur = getattr(self, "current", None)
        if cur is not None and cur in self.frames:
            self.frames[cur].on_hide()
        self.frames[name].frame.tkraise()
        self.frames[name].on_show()
        self.current = name
