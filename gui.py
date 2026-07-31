# -*- coding: utf-8 -*-

import os
import threading
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.metrics import dp

from core import (
    PLATFORMS, search_songs, fetch_music_by_song,
    load_config, save_config, load_cache, add_to_cache
)

_base = os.path.dirname(os.path.abspath(__file__))
_font_path = os.path.join(_base, 'data', 'chinesefont.ttf')
if os.path.exists(_font_path):
    LabelBase.register(name='ChineseFont', fn_regular=_font_path)
    CF = 'ChineseFont'
else:
    CF = 'Roboto'


class SettingsPopup(Popup):
    def __init__(self, config, save_callback, **kwargs):
        super().__init__(**kwargs)
        self.title = ''
        self.size_hint = (0.8, 0.85)
        self.config = config
        self.save_callback = save_callback

        main_layout = BoxLayout(orientation='vertical', spacing=5, padding=10)

        title_bar = BoxLayout(size_hint_y=None, height=dp(40), spacing=10)
        title_label = Label(text='设置', font_name=CF, font_size='18sp', bold=True, size_hint_x=1)
        close_btn = Button(text='X', font_name=CF, size_hint=(None, None), size=(dp(40), dp(40)))
        close_btn.bind(on_press=self.dismiss)
        title_bar.add_widget(title_label)
        title_bar.add_widget(close_btn)
        main_layout.add_widget(title_bar)

        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=12, padding=10, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        content.add_widget(Label(text='默认搜索数量', font_name=CF, size_hint_y=None, height=dp(30)))
        self.num_input = TextInput(text=str(config.get('default_num', 10)), multiline=False, font_name=CF,
                                   size_hint_y=None, height=dp(40))
        content.add_widget(self.num_input)

        content.add_widget(Label(text='请求超时秒数', font_name=CF, size_hint_y=None, height=dp(30)))
        self.timeout_input = TextInput(text=str(config.get('timeout', 10)), multiline=False, font_name=CF,
                                       size_hint_y=None, height=dp(40))
        content.add_widget(self.timeout_input)

        content.add_widget(Label(text='最大重试次数', font_name=CF, size_hint_y=None, height=dp(30)))
        self.retries_input = TextInput(text=str(config.get('max_retries', 3)), multiline=False, font_name=CF,
                                       size_hint_y=None, height=dp(40))
        content.add_widget(self.retries_input)

        content.add_widget(Label(text='重试间隔秒数', font_name=CF, size_hint_y=None, height=dp(30)))
        self.delay_input = TextInput(text=str(config.get('retry_delay', 1)), multiline=False, font_name=CF,
                                     size_hint_y=None, height=dp(40))
        content.add_widget(self.delay_input)

        content.add_widget(Label(text='最大缓存条目数', font_name=CF, size_hint_y=None, height=dp(30)))
        self.cache_input = TextInput(text=str(config.get('max_cache', 20)), multiline=False, font_name=CF,
                                     size_hint_y=None, height=dp(40))
        content.add_widget(self.cache_input)

        save_btn = Button(text='保存并关闭', font_name=CF, size_hint_y=None, height=dp(50))
        save_btn.bind(on_press=self.save_and_close)
        content.add_widget(save_btn)

        scroll.add_widget(content)
        main_layout.add_widget(scroll)

        self.content = main_layout

    def save_and_close(self, instance):
        try:
            default_num = int(self.num_input.text)
            timeout_val = float(self.timeout_input.text)
            max_retries = int(self.retries_input.text)
            retry_delay = float(self.delay_input.text)
            max_cache = int(self.cache_input.text)

            if default_num <= 0:
                raise ValueError("默认搜索数量必须大于0")
            if timeout_val <= 0:
                raise ValueError("超时时间必须大于0")
            if max_retries <= 0:
                raise ValueError("重试次数必须大于0")
            if retry_delay < 0:
                raise ValueError("重试间隔不能为负数")
            if max_cache <= 0:
                raise ValueError("缓存条目数必须大于0")

            self.config['default_num'] = default_num
            self.config['timeout'] = timeout_val
            self.config['max_retries'] = max_retries
            self.config['retry_delay'] = retry_delay
            self.config['max_cache'] = max_cache
            save_config(self.config)
            self.save_callback(self.config)
            self.dismiss()
        except ValueError as e:
            if str(e) != "":
                print(f"[设置错误] {e}")
            else:
                print("[设置错误] 请输入有效数字")


class HistoryPopup(Popup):
    def __init__(self, config=None, **kwargs):
        super().__init__(**kwargs)
        self.title = ''
        self.size_hint = (0.8, 0.6)
        self.config = config or {}

        main_layout = BoxLayout(orientation='vertical', spacing=5, padding=10)

        title_bar = BoxLayout(size_hint_y=None, height=dp(40), spacing=10)
        title_label = Label(text='历史记录', font_name=CF, font_size='18sp', bold=True, size_hint_x=1)
        close_btn = Button(text='X', font_name=CF, size_hint=(None, None), size=(dp(40), dp(40)))
        close_btn.bind(on_press=self.dismiss)
        title_bar.add_widget(title_label)
        title_bar.add_widget(close_btn)
        main_layout.add_widget(title_bar)

        scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=6, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)
        main_layout.add_widget(scroll)

        self.content = main_layout
        self.bind(size=self._refresh)
        Clock.schedule_once(lambda dt: self._refresh(), 0.1)

    def _refresh(self, *args):
        self.grid.clear_widgets()
        cache = load_cache()
        max_display = self.config.get('max_cache', 20)
        if not cache:
            self.grid.add_widget(Label(text='暂无历史记录', font_name=CF, size_hint_y=None, height=dp(40)))
            return

        avail_width = self.width - dp(80)
        if avail_width < 200:
            Clock.schedule_once(lambda dt: self._refresh(), 0.1)
            return

        for entry in reversed(cache[-max_display:]):
            line = f"{entry['time']}  {entry['song']} - {entry['singer']}"
            lbl = Label(
                text=line,
                font_name=CF,
                size_hint_y=None,
                halign='left',
                valign='top',
                text_size=(avail_width, None),
                padding=(5, 5)
            )
            lbl.texture_update()
            lbl.height = lbl.texture_size[1] + dp(10)
            self.grid.add_widget(lbl)


class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        layout.add_widget(Label(text='--- 欢迎使用音乐获取工具 ---', font_name=CF, font_size='22sp', bold=True,
                                size_hint_y=None, height=dp(50)))
        layout.add_widget(Label(text='提示：', font_name=CF, font_size='14sp', size_hint_y=None, height=dp(30)))
        layout.add_widget(Label(text='1. 作者QQ 535595887', font_name=CF, font_size='14sp', size_hint_y=None, height=dp(30)))
        layout.add_widget(Label(text='2. 本工具在GitHub开源，禁止商业用途', font_name=CF, font_size='14sp', size_hint_y=None, height=dp(30)))
        layout.add_widget(Label(text='3. 可以获取VIP音乐', font_name=CF, font_size='14sp', size_hint_y=None, height=dp(30)))
        layout.add_widget(BoxLayout())
        btn = Button(text='开始使用 ->', font_name=CF, font_size='18sp',
                     size_hint=(None, None), size=(dp(200), dp(50)),
                     pos_hint={'center_x': 0.5})
        btn.bind(on_press=self.go_search)
        layout.add_widget(btn)
        self.add_widget(layout)

    def go_search(self, instance):
        self.manager.current = 'search'


class SearchScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_platform = None
        self.config = load_config()

        # 主布局：垂直方向
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # ---------- 可滚动区域：所有主要控件 ----------
        scroll = ScrollView(do_scroll_x=False)
        top_area = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        top_area.bind(minimum_height=top_area.setter('height'))

        # 平台选择（去掉固定高度，自适应）
        plat_box = BoxLayout(orientation='vertical', spacing=10)  # 改为垂直布局，让按钮纵向排列
        plat_label = Label(text='选择平台：', font_name=CF, font_size='16sp', size_hint_y=None, height=dp(30), halign='left')
        plat_box.add_widget(plat_label)
        self.plat_buttons = {}
        # 将平台按钮放在一个水平布局里，避免挤在一起
        btns_row = BoxLayout(spacing=10, size_hint_y=None, height=dp(50))
        for key, info in PLATFORMS.items():
            btn = Button(text=info['name'], font_name=CF, font_size='14sp',
                         background_color=(0.2, 0.2, 0.2, 1), color=(1,1,1,1))
            btn.bind(on_press=self.on_platform_select)
            self.plat_buttons[key] = btn
            btns_row.add_widget(btn)
        plat_box.add_widget(btns_row)
        top_area.add_widget(plat_box)

        # 歌名输入
        input_row = BoxLayout(size_hint_y=None, height=dp(45), spacing=10)
        input_row.add_widget(Label(text='歌名/关键词：', font_name=CF, font_size='15sp',
                                   size_hint_x=None, width=dp(140)))
        self.keyword_input = TextInput(hint_text='请输入...', multiline=False, font_name=CF, font_size='15sp')
        input_row.add_widget(self.keyword_input)
        top_area.add_widget(input_row)

        # 数量输入
        num_row = BoxLayout(size_hint_y=None, height=dp(45), spacing=10)
        num_row.add_widget(Label(text='搜索数量：', font_name=CF, font_size='15sp',
                                 size_hint_x=None, width=dp(140)))
        self.num_input = TextInput(text=str(self.config.get('default_num', 10)), hint_text='默认10',
                                   multiline=False, font_name=CF, font_size='15sp')
        num_row.add_widget(self.num_input)
        top_area.add_widget(num_row)

        # 搜索按钮
        self.search_btn = Button(text='搜索', font_name=CF, font_size='18sp', size_hint_y=None, height=dp(55),
                                 background_color=(0.2, 0.6, 1, 1))
        self.search_btn.bind(on_press=self.do_search)
        top_area.add_widget(self.search_btn)

        # 状态提示
        self.status_label = Label(text='', font_name=CF, font_size='13sp', size_hint_y=None, height=dp(25),
                                  color=(0.5, 0.5, 0.5, 1))
        top_area.add_widget(self.status_label)

        scroll.add_widget(top_area)
        main_layout.add_widget(scroll)

        # ---------- 底部按钮行：左历史记录，右设置 ----------
        bottom_row = BoxLayout(size_hint_y=None, height=dp(50))
        history_btn = Button(text='历史记录', font_name=CF, font_size='14sp',
                             size_hint=(None, None), size=(dp(100), dp(40)))
        history_btn.bind(on_press=self.show_history)
        bottom_row.add_widget(history_btn)
        bottom_row.add_widget(Widget())  # 弹性空白
        settings_btn = Button(text='设置', font_name=CF, font_size='14sp',
                              size_hint=(None, None), size=(dp(100), dp(40)))
        settings_btn.bind(on_press=self.open_settings)
        bottom_row.add_widget(settings_btn)

        main_layout.add_widget(bottom_row)

        self.add_widget(main_layout)

    # 以下方法保持不变（on_platform_select, open_settings, on_config_updated, show_history, do_search 等）
    # 注意：do_search 和 _search_worker 等函数不做修改，直接复制之前的代码。
    # 为了完整，我将它们一并列在下面（从之前版本复制即可）。

    def on_platform_select(self, instance):
        for key, btn in self.plat_buttons.items():
            if btn is instance:
                btn.background_color = (0.2, 0.7, 0.3, 1)
                self.selected_platform = key
            else:
                btn.background_color = (0.2, 0.2, 0.2, 1)
        self.status_label.text = f'已选择: {PLATFORMS[self.selected_platform]["name"]}'
        if self.selected_platform == "3":
            self.status_label.text = "警告: 波点音乐可能只返回11秒试听片段，建议使用其他平台。"

    def open_settings(self, instance):
        popup = SettingsPopup(self.config, self.on_config_updated)
        popup.open()

    def on_config_updated(self, new_config):
        self.config = new_config
        self.num_input.text = str(self.config.get('default_num', 10))
        self.status_label.text = "设置已保存"

    def show_history(self, instance):
        popup = HistoryPopup(self.config)
        popup.open()

    def do_search(self, instance):
        if not self.selected_platform:
            self.status_label.text = '请先选择一个平台!'
            return
        keyword = self.keyword_input.text.strip()
        if not keyword:
            self.status_label.text = '请输入搜索关键词!'
            return
        num_str = self.num_input.text.strip()
        num = int(num_str) if num_str.isdigit() else self.config['default_num']

        platform = PLATFORMS[self.selected_platform]
        self.search_btn.disabled = True
        self.search_btn.text = '搜索中...'
        self.status_label.text = f'正在搜索 "{keyword}"...'

        threading.Thread(target=self._search_worker, args=(platform, keyword, num), daemon=True).start()

    def _search_worker(self, platform, keyword, num):
        cfg = self.config.copy()
        cfg['default_num'] = num
        try:
            songs = search_songs(platform['url'], keyword, cfg)
        except Exception as e:
            songs = None
            error_msg = str(e)
        else:
            error_msg = None
        Clock.schedule_once(lambda dt: self._on_search_done(songs, platform, keyword, error_msg))

    def _on_search_done(self, songs, platform, keyword, error_msg):
        self.search_btn.disabled = False
        self.search_btn.text = '搜索'
        if error_msg:
            self.status_label.text = f'网络错误: {error_msg}'
            return
        if not songs:
            self.status_label.text = f'未找到 "{keyword}" 相关歌曲'
            return
        result_screen = self.manager.get_screen('result')
        result_screen.show_results(songs, platform, keyword)
        self.manager.current = 'result'


class ResultScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.songs = []
        self.platform = None
        self.keyword = ''
        self.config = load_config()

        outer = BoxLayout(orientation='vertical', padding=15, spacing=8)

        header = BoxLayout(size_hint_y=None, height=dp(48), spacing=10)
        self.title_label = Label(text='搜索结果', font_name=CF, font_size='18sp', bold=True,
                                 halign='left', size_hint_x=1)
        back_btn = Button(text='<- 返回', font_name=CF, font_size='14sp',
                          size_hint=(None, None), size=(dp(100), dp(40)))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'search'))
        header.add_widget(self.title_label)
        header.add_widget(back_btn)
        outer.add_widget(header)

        scroll = ScrollView(do_scroll_x=False)
        self.result_grid = GridLayout(cols=1, spacing=8, size_hint_y=None)
        self.result_grid.bind(minimum_height=self.result_grid.setter('height'))
        scroll.add_widget(self.result_grid)
        outer.add_widget(scroll)

        self.info_label = Label(text='', font_name=CF, font_size='13sp', size_hint_y=None, height=dp(30),
                                color=(0.3, 0.3, 0.3, 1))
        outer.add_widget(self.info_label)

        self.add_widget(outer)
        self._link_bars = []

    def show_results(self, songs, platform, keyword):
        self.songs = songs
        self.platform = platform
        self.keyword = keyword
        self.result_grid.clear_widgets()
        self._link_bars = []

        if not songs:
            self.info_label.text = f'未找到 "{keyword}" 的相关歌曲'
            self.title_label.text = '搜索结果 (0 首)'
            return

        self.title_label.text = f'搜索结果 ({len(songs)} 首)'
        self.info_label.text = ''

        for idx, s in enumerate(songs):
            name = s.get('song', '未知')
            singer = s.get('singer', '未知')

            card = BoxLayout(orientation='vertical', spacing=2, size_hint_y=None, height=dp(100))

            row = BoxLayout(size_hint_y=None, height=dp(60), spacing=8, padding=[5, 3])
            idx_lbl = Label(text=f'{idx+1}.', font_name=CF, font_size='14sp', bold=True,
                            size_hint_x=None, width=dp(35))

            info_col = BoxLayout(orientation='vertical', spacing=2, size_hint_x=1)
            name_lbl = Label(text=name, font_name=CF, font_size='15sp', bold=True, halign='left',
                             size_hint_y=None, height=dp(30))
            singer_lbl = Label(text=singer, font_name=CF, font_size='12sp',
                               color=(0.4,0.4,0.4,1), halign='left',
                               size_hint_y=None, height=dp(20))
            info_col.add_widget(name_lbl)
            info_col.add_widget(singer_lbl)

            get_btn = Button(text='获取链接', font_name=CF, font_size='12sp',
                             size_hint=(None, None), size=(dp(100), dp(38)),
                             background_color=(0.18,0.55,0.95,1))
            get_idx = idx+1
            get_btn.bind(on_press=lambda x, i=get_idx: self._get_link(i))

            row.add_widget(idx_lbl)
            row.add_widget(info_col)
            row.add_widget(get_btn)
            card.add_widget(row)

            link_area = BoxLayout(size_hint_y=None, height=dp(30), spacing=6, padding=[5,3], opacity=0)
            link_bar = BoxLayout(spacing=6)
            link_lbl = Label(text='', font_name=CF, font_size='11sp', halign='left',
                             size_hint_x=1, color=(0.1,0.1,0.8,1))
            copy_btn = Button(text='复制链接', font_name=CF, font_size='11sp',
                              size_hint=(None, None), size=(dp(80), dp(28)),
                              background_color=(0.15,0.65,0.25,1))
            copy_btn.opacity = 0
            link_bar.add_widget(link_lbl)
            link_bar.add_widget(copy_btn)
            link_area.add_widget(link_bar)
            card.add_widget(link_area)

            self._link_bars.append((link_area, link_lbl, copy_btn, get_btn))
            self.result_grid.add_widget(card)

    def _get_link(self, index):
        selected = self.songs[index-1]
        name = selected.get('song', '未知')
        singer = selected.get('singer', '未知')
        self.info_label.text = f'正在获取《{name}》播放链接...'
        threading.Thread(target=self._fetch_worker, args=(name, singer, index), daemon=True).start()

    def _fetch_worker(self, name, singer, index):
        cfg = load_config()
        try:
            result = fetch_music_by_song(self.platform['url'], name, singer, cfg, index)
        except Exception as e:
            result = None
            error = str(e)
        else:
            error = None
        Clock.schedule_once(lambda dt: self._on_link_fetched(result, name, singer, index, error))

    def _on_link_fetched(self, result, name, singer, index, error):
        if error or not result:
            self.info_label.text = f'获取失败：{error or "可能无版权或API限制"}'
            return
        url = result['music_url']
        display_name = result.get('song', name)
        display_singer = result.get('singer', singer)
        self.info_label.text = f'获取成功：{display_name} - {display_singer}'

        add_to_cache(display_name, display_singer, url, self.platform['name'], self.config.get('max_cache', 20))

        link_area, link_lbl, copy_btn, get_btn = self._link_bars[index-1]
        link_lbl.text = url
        copy_btn.opacity = 1
        link_area.opacity = 1

        def copy_clipboard(x):
            Clipboard.copy(url)
            copy_btn.text = '已复制!'
            Clock.schedule_once(lambda t: setattr(copy_btn, 'text', '复制链接'), 1.5)
        copy_btn.bind(on_press=copy_clipboard)