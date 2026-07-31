# -*- coding: utf-8 -*-
"""getmusic max-gui — 图形界面版，基于 Kivy"""

import os
import threading

from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.metrics import dp

from core import (
    PLATFORMS, search_songs, fetch_music_by_song,
    load_config, save_config, load_cache, add_to_cache
)

# 配色
CARD = (0.14, 0.14, 0.16, 1)
BLUE = (0.20, 0.55, 1.00, 1)
GREEN = (0.18, 0.68, 0.30, 1)
ORANGE = (0.85, 0.50, 0.10, 1)
RED = (0.72, 0.20, 0.18, 1)
WHITE = (0.95, 0.95, 0.97, 1)
GRAY = (0.55, 0.55, 0.60, 1)
MUTED = (0.35, 0.35, 0.38, 1)
LINK = (0.20, 0.65, 1.00, 1)

# 字体
_font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'chinesefont.ttf')
if os.path.exists(_font_path):
    LabelBase.register(name='ChineseFont', fn_regular=_font_path)
    CF = 'ChineseFont'
else:
    CF = 'Roboto'


def toast(msg, color=ORANGE):
    icons = {GREEN: '✅', ORANGE: '⚠️', RED: '❌'}
    t = Toast(msg, icons.get(color, 'ℹ️'), color)
    t.open()


class Toast(Popup):
    def __init__(self, msg, icon, color, **kw):
        super().__init__(**kw)
        self.title = ''
        self.size_hint = (0.6, 0.16)
        Clock.schedule_once(lambda dt: self.dismiss(), 2.0)
        self.content = BoxLayout(
            spacing=8, padding=12,
            children=[Label(
                text=f'{icon}  {msg}', font_name=CF, font_size='14sp',
                size_hint_x=1, color=WHITE, halign='center', valign='middle'
            )]
        )


class Welcome(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        v = BoxLayout(orientation='vertical', padding=30, spacing=0)
        v.add_widget(Widget(size_hint_y=None, height=dp(60)))
        v.add_widget(Label(text='🎵', font_name=CF, font_size='80sp',
                           size_hint_y=None, height=dp(120), halign='center'))
        v.add_widget(Label(text='getmusic', font_name=CF, font_size='32sp', bold=True,
                           size_hint_y=None, height=dp(60), halign='center', color=BLUE))
        v.add_widget(Label(text='音乐获取工具', font_name=CF, font_size='18sp',
                           size_hint_y=None, height=dp(40), halign='center', color=GRAY))
        v.add_widget(Label(
            text='支持网易云音乐 · 咪咕音乐 · 波点音乐\n获取 VIP 歌曲播放链接',
            font_name=CF, font_size='14sp',
            size_hint_y=None, height=dp(60),
            halign='center', valign='middle', color=MUTED))
        v.add_widget(Widget())

        btn = Button(text='开始搜索', font_name=CF, font_size='20sp',
                     size_hint=(None, None), size=(dp(220), dp(55)),
                     background_color=BLUE, color=WHITE)
        btn.bind(on_press=lambda x: setattr(self, '_go', True))
        v.add_widget(btn)
        v.add_widget(Widget(size_hint_y=None, height=dp(20)))
        v.add_widget(Label(
            text='作者 QQ 535595887  |  GitHub 开源  |  禁止商用',
            font_name=CF, font_size='12sp',
            size_hint_y=None, height=dp(30), halign='center', color=MUTED))
        v.add_widget(Widget())
        self.add_widget(v)
        Clock.schedule_interval(self._check_go, 0.2)

    def _check_go(self, dt):
        if getattr(self, '_go', False):
            self._go = False
            self.manager.current = 'search'


class Search(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.platform = None
        self.config = load_config()
        self.btns = {}
        self.searching = False

        main = BoxLayout(orientation='vertical', padding=15, spacing=8)

        # 标题栏
        hdr = BoxLayout(size_hint_y=None, height=dp(45), spacing=8)
        hdr.add_widget(Label(text='🎶  搜索音乐', font_name=CF, font_size='18sp', bold=True,
                             size_hint_x=1, color=WHITE, halign='left'))
        hist = Button(text='📋 历史', font_name=CF, font_size='13sp',
                      size_hint=(None, None), size=(dp(80), dp(35)),
                      background_color=CARD, color=WHITE)
        sett = Button(text='⚙️ 设置', font_name=CF, font_size='13sp',
                      size_hint=(None, None), size=(dp(80), dp(35)),
                      background_color=CARD, color=WHITE)
        hist.bind(on_press=self.show_history)
        sett.bind(on_press=self.open_settings)
        hdr.add_widget(hist)
        hdr.add_widget(sett)
        main.add_widget(hdr)

        # 主体
        scroll = ScrollView(do_scroll_x=False)
        body = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None, padding=[10, 10])
        body.bind(minimum_height=body.setter('height'))

        # 平台选择
        body.add_widget(Label(text='选择平台', font_name=CF, font_size='15sp',
                              size_hint_y=None, height=dp(28), halign='left', color=GRAY))
        plat_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=8)
        for key, info in PLATFORMS.items():
            btn = ToggleButton(text=info['name'], font_name=CF, font_size='14sp',
                               size_hint=(1, 1),
                               background_color=(0.12, 0.12, 0.14, 1),
                               background_color_down=BLUE,
                               color=WHITE, down_color=WHITE)
            btn.bind(state=self._on_toggle)
            self.btns[key] = btn
            plat_row.add_widget(btn)
        body.add_widget(plat_row)

        # 关键词
        body.add_widget(Label(text='歌名 / 关键词', font_name=CF, font_size='15sp',
                              size_hint_y=None, height=dp(28), halign='left', color=GRAY))
        self.kw = TextInput(hint_text='例如：晴天 周杰伦', multiline=False,
                            font_name=CF, font_size='16sp',
                            background_color=CARD, foreground_color=WHITE,
                            size_hint_y=None, height=dp(50))
        body.add_widget(self.kw)

        # 数量
        body.add_widget(Label(text='搜索数量', font_name=CF, font_size='15sp',
                              size_hint_y=None, height=dp(28), halign='left', color=GRAY))
        self.num = TextInput(text=str(self.config.get('default_num', 10)),
                             hint_text='默认 10', multiline=False,
                             font_name=CF, font_size='16sp',
                             background_color=CARD, foreground_color=WHITE,
                             size_hint_y=None, height=dp(50))
        body.add_widget(self.num)

        # 搜索按钮
        self.sbtn = Button(text='🔍  搜 索', font_name=CF, font_size='20sp',
                           size_hint_y=None, height=dp(55),
                           background_color=BLUE, color=WHITE)
        self.sbtn.bind(on_press=self.do_search)
        body.add_widget(self.sbtn)

        self.status = Label(text='', font_name=CF, font_size='13sp',
                            size_hint_y=None, height=dp(35),
                            halign='center', valign='middle', color=MUTED)
        body.add_widget(self.status)

        scroll.add_widget(body)
        main.add_widget(scroll)
        self.add_widget(main)

    def _on_toggle(self, instance, state):
        if state == 'down':
            for k, b in self.btns.items():
                if b is not instance:
                    b.state = 'normal'
            self.platform = instance
            self.status.text = f'已选择: {PLATFORMS[self.platform]["name"]}'
            self.status.color = GRAY
            if self.platform == '3':
                self.status.text = '⚠️  波点音乐可能只返回试听片段'
                self.status.color = ORANGE
        else:
            self.platform = None
            self.status.text = ''
            self.status.color = MUTED

    def do_search(self, instance):
        if not self.platform:
            toast('请先选择音乐平台', ORANGE)
            return
        kw = self.kw.text.strip()
        if not kw:
            toast('请输入搜索关键词', ORANGE)
            return
        num_str = self.num.text.strip()
        num = int(num_str) if num_str.isdigit() else self.config['default_num']
        if num < 1:
            num = 10

        plat = PLATFORMS[self.platform]
        self.sbtn.disabled = True
        self.sbtn.text = '⏳  搜索中...'
        self.sbtn.color = MUTED
        self.status.text = f'正在搜索 "{kw}"...'
        self.status.color = BLUE
        self.searching = True

        threading.Thread(target=self._worker, args=(plat, kw, num), daemon=True).start()

    def _worker(self, plat, kw, num):
        cfg = self.config.copy()
        cfg['default_num'] = num
        try:
            songs = search_songs(plat['url'], kw, cfg)
            err = None
        except Exception as e:
            songs, err = None, str(e)
        Clock.schedule_once(lambda dt: self._done(songs, plat, kw, err))

    def _done(self, songs, plat, kw, err):
        self.searching = False
        self.sbtn.disabled = False
        self.sbtn.text = '🔍  搜 索'
        self.sbtn.color = WHITE

        if err:
            toast(f'网络错误: {err}', RED)
            self.status.text = '搜索失败'
            self.status.color = RED
            return
        if not songs:
            toast(f'未找到 "{kw}" 相关歌曲', ORANGE)
            self.status.text = '未找到结果'
            self.status.color = MUTED
            return

        self.manager.get_screen('result').show_results(songs, plat, kw)
        self.manager.current = 'result'

    def open_settings(self, instance):
        Settings(self.config, self._on_config).open()

    def _on_config(self, cfg):
        self.config = cfg
        self.num.text = str(cfg.get('default_num', 10))

    def show_history(self, instance):
        History(self.config).open()


class Result(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.songs = []
        self.platform = None
        self.config = load_config()
        self.bars = []

        outer = BoxLayout(orientation='vertical', padding=15, spacing=8)

        hdr = BoxLayout(size_hint_y=None, height=dp(45), spacing=8)
        self.ttl = Label(text='搜索结果', font_name=CF, font_size='18sp', bold=True,
                         size_hint_x=1, halign='left', color=WHITE)
        back = Button(text='←  返回', font_name=CF, font_size='14sp',
                      size_hint=(None, None), size=(dp(80), dp(35)),
                      background_color=CARD, color=WHITE)
        back.bind(on_press=lambda x: setattr(self.manager, 'current', 'search'))
        hdr.add_widget(self.ttl)
        hdr.add_widget(back)
        outer.add_widget(hdr)

        scroll = ScrollView(do_scroll_x=False)
        self.grid = GridLayout(cols=1, spacing=6, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)
        outer.add_widget(scroll)

        self.info = Label(text='', font_name=CF, font_size='12sp',
                          size_hint_y=None, height=dp(25),
                          halign='center', color=MUTED)
        outer.add_widget(self.info)
        self.add_widget(outer)

    def show_results(self, songs, platform, keyword):
        self.songs = songs
        self.platform = platform
        self.grid.clear_widgets()
        self.bars = []
        if not songs:
            self.info.text = f'未找到 "{keyword}" 的相关歌曲'
            self.ttl.text = '搜索结果 (0 首)'
            return
        self.ttl.text = f'搜索结果 ({len(songs)} 首)'
        self.info.text = ''
        for i, s in enumerate(songs):
            self._card(i, s)

    def _card(self, idx, s):
        name = s.get('song', '未知')
        singer = s.get('singer', '未知')

        card = BoxLayout(orientation='vertical', spacing=4,
                         size_hint_y=None, height=dp(75),
                         padding=[10, 5], background_color=CARD)

        top = BoxLayout(size_hint_y=None, height=dp(42), spacing=8)
        top.add_widget(Label(
            text=str(idx + 1), font_name=CF, font_size='16sp', bold=True,
            size_hint_x=None, width=dp(35),
            halign='center', valign='middle', color=MUTED))

        info = BoxLayout(orientation='vertical', spacing=1, size_hint_x=1)
        info.add_widget(Label(
            text=name, font_name=CF, font_size='15sp', bold=True,
            halign='left', size_hint_y=None, height=dp(26)))
        info.add_widget(Label(
            text=singer, font_name=CF, font_size='12sp',
            halign='left', size_hint_y=None, height=dp(18), color=MUTED))
        top.add_widget(info)

        btn = Button(text='获取链接', font_name=CF, font_size='12sp',
                     size_hint=(None, None), size=(dp(90), dp(34)),
                     background_color=BLUE, color=WHITE)
        btn.bind(on_press=lambda x, i=idx + 1: self._fetch(i))
        top.add_widget(btn)
        card.add_widget(top)

        area = BoxLayout(size_hint_y=None, height=dp(30), spacing=6,
                         padding=[10, 3], opacity=0,
                         background_color=(0.10, 0.10, 0.12, 1))
        bar = BoxLayout(spacing=6)
        lbl = Label(text='', font_name=CF, font_size='11sp',
                    size_hint_x=1, halign='left', valign='middle', color=LINK)
        copy = Button(text='📋 复制', font_name=CF, font_size='11sp',
                      size_hint=(None, None), size=(dp(70), dp(26)),
                      background_color=GREEN, color=WHITE)
        copy.opacity = 0
        bar.add_widget(lbl)
        bar.add_widget(copy)
        area.add_widget(bar)
        card.add_widget(area)
        self.bars.append((area, lbl, copy, btn))
        self.grid.add_widget(card)

    def _fetch(self, index):
        s = self.songs[index - 1]
        name, singer = s.get('song', '未知'), s.get('singer', '未知')
        _, _, _, btn = self.bars[index - 1]
        btn.text = '⏳ 获取中...'
        btn.disabled = True
        btn.color = MUTED
        self.info.text = f'正在获取《{name}》播放链接...'
        threading.Thread(target=self._worker, args=(name, singer, index), daemon=True).start()

    def _worker(self, name, singer, index):
        cfg = load_config()
        try:
            result = fetch_music_by_song(self.platform['url'], name, singer, cfg, index)
            err = None
        except Exception as e:
            result, err = None, str(e)
        Clock.schedule_once(lambda dt: self._got(result, name, singer, index, err))

    def _got(self, result, name, singer, index, err):
        area, lbl, copy, btn = self.bars[index - 1]
        if err or not result:
            toast(f'获取失败：{err or "可能无版权或 API 限制"}', RED)
            btn.text = '重试'
            btn.disabled = False
            btn.color = WHITE
            btn.unbind(on_press)
            btn.bind(on_press=lambda x, i=index: self._fetch(i))
            self.info.text = f'获取《{name}》失败'
            return

        url = result['music_url']
        add_to_cache(result.get('song', name), result.get('singer', singer),
                     url, self.platform['name'], self.config.get('max_cache', 20))

        btn.text = '✓ 已获取'
        btn.background_color = GREEN
        btn.disabled = True

        lbl.text = url
        copy.opacity = 1
        area.opacity = 1
        self.info.text = f'✅  {result.get("song", name)} - {result.get("singer", singer)}'
        self.info.color = GREEN

        copy.bind(on_press=lambda x: (Clipboard.copy(url), toast('已复制', GREEN)))


class Settings(Popup):
    def __init__(self, config, cb, **kw):
        super().__init__(**kw)
        self.title = ''
        self.size_hint = (0.75, 0.75)
        self.config = config
        self.cb = cb
        self.inputs = {}

        main = BoxLayout(orientation='vertical', spacing=6, padding=12)
        main.add_widget(BoxLayout(
            size_hint_y=None, height=dp(38), spacing=8,
            children=[
                Label(text='⚙️  设置', font_name=CF, font_size='18sp', bold=True,
                      size_hint_x=1, halign='left', color=WHITE),
                Button(text='✕', font_name=CF, font_size='14sp',
                       size_hint=(None, None), size=(dp(36), dp(36)),
                       background_color=RED, color=WHITE)
            ]))

        scroll = ScrollView()
        body = BoxLayout(orientation='vertical', spacing=10, padding=8, size_hint_y=None)
        body.bind(minimum_height=body.setter('height'))

        for label, key, default in [
            ('默认搜索数量', 'default_num', 10),
            ('请求超时秒数', 'timeout', 10),
            ('最大重试次数', 'max_retries', 3),
            ('重试间隔秒数', 'retry_delay', 1),
            ('最大缓存条目数', 'max_cache', 20),
        ]:
            row = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=None, height=dp(50))
            row.add_widget(Label(
                text=label, font_name=CF, font_size='14sp',
                size_hint_x=None, width=dp(140), halign='right', valign='middle',
                color=GRAY))
            ti = TextInput(
                text=str(config.get(key, default)), multiline=False,
                font_name=CF, font_size='14sp',
                background_color=CARD, foreground_color=WHITE,
                input_filter='int')
            row.add_widget(ti)
            self.inputs[key] = ti
            body.add_widget(row)

        # DEBUG 开关
        self.debug_tb = ToggleButton(
            text='ON' if config.get('debug_mode', False) else 'OFF',
            font_name=CF, font_size='13sp',
            size_hint=(None, None), size=(dp(80), dp(38)),
            background_color=CARD if not config.get('debug_mode', False) else GREEN,
            color=WHITE)
        self.debug_tb.state = 'down' if config.get('debug_mode', False) else 'normal'
        body.add_widget(BoxLayout(
            orientation='horizontal', spacing=8, size_hint_y=None, height=dp(42),
            children=[
                Label(text='DEBUG 模式', font_name=CF, font_size='14sp',
                      size_hint_x=None, width=dp(140), halign='right', valign='middle',
                      color=GRAY),
                self.debug_tb
            ]))

        body.add_widget(Button(
            text='保存', font_name=CF, font_size='16sp',
            size_hint_y=None, height=dp(45),
            background_color=BLUE, color=WHITE))
        body.children[-1].bind(on_press=self.save)

        scroll.add_widget(body)
        main.add_widget(scroll)
        self.content = main

    def save(self, instance):
        errors = []
        for key, ti in self.inputs.items():
            try:
                self.config[key] = int(ti.text)
            except (ValueError, AttributeError):
                errors.append(key)
        self.config['debug_mode'] = self.debug_tb.state == 'down'
        if errors:
            toast(f'无效输入: {", ".join(errors)}', RED)
            return
        save_config(self.config)
        self.cb(self.config)
        toast('设置已保存', GREEN)
        self.dismiss()


class History(Popup):
    def __init__(self, config=None, **kw):
        super().__init__(**kw)
        self.title = ''
        self.size_hint = (0.7, 0.65)
        self.config = config or {}

        main = BoxLayout(orientation='vertical', spacing=6, padding=12)
        main.add_widget(BoxLayout(
            size_hint_y=None, height=dp(38), spacing=8,
            children=[
                Label(text='📋  历史记录', font_name=CF, font_size='18sp', bold=True,
                      size_hint_x=1, halign='left', color=WHITE),
                Button(text='✕', font_name=CF, font_size='14sp',
                       size_hint=(None, None), size=(dp(36), dp(36)),
                       background_color=RED, color=WHITE)
            ]))

        scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=4, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)
        main.add_widget(scroll)
        self.content = main
        Clock.schedule_once(lambda dt: self._refresh())

    def _refresh(self):
        self.grid.clear_widgets()
        cache = load_cache()
        n = self.config.get('max_cache', 20)
        if not cache:
            self.grid.add_widget(Label(
                text='暂无历史记录', font_name=CF, font_size='15sp',
                halign='center', size_hint_y=None, height=dp(60), color=MUTED))
            return
        for e in reversed(cache[-n:]):
            self.grid.add_widget(BoxLayout(
                orientation='horizontal', spacing=8,
                size_hint_y=None, height=dp(44), padding=[8, 2],
                children=[
                    Label(text=e['time'], font_name=CF, font_size='11sp',
                          size_hint_x=None, width=dp(100), valign='middle',
                          color=MUTED),
                    Label(text=f"{e['song']} - {e['singer']}",
                          font_name=CF, font_size='13sp',
                          size_hint_x=1, valign='middle', halign='left',
                          color=WHITE)
                ]))


class GetMusicApp(App):
    title = 'getmusic — 音乐获取工具'

    def build(self):
        from kivy.uix.screenmanager import ScreenManager, SlideTransition
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(Welcome(name='welcome'))
        sm.add_widget(Search(name='search'))
        sm.add_widget(Result(name='result'))
        return sm


if __name__ == '__main__':
    GetMusicApp().run()
