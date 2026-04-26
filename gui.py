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
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.metrics import dp

from core import (
    PLATFORMS, search_songs, fetch_music_by_song,
    load_config, save_config, load_cache
)

_base = os.path.dirname(os.path.abspath(__file__))
LabelBase.register(name='ChineseFont', fn_regular=os.path.join(_base, 'data', 'chinesefont.ttf'))
CF = 'ChineseFont'


class SettingsPopup(Popup):
    def __init__(self, config, save_callback, **kwargs):
        super().__init__(**kwargs)
        self.title = "设置"
        self.size_hint = (0.8, 0.7)
        self.config = config
        self.save_callback = save_callback

        layout = BoxLayout(orientation='vertical', spacing=12, padding=20)

        layout.add_widget(Label(text='默认搜索数量', font_name=CF, size_hint_y=None, height=dp(30)))
        self.num_input = TextInput(text=str(config.get('default_num', 10)), multiline=False, font_name=CF,
                                   size_hint_y=None, height=dp(40))
        layout.add_widget(self.num_input)

        layout.add_widget(Label(text='请求超时秒数', font_name=CF, size_hint_y=None, height=dp(30)))
        self.timeout_input = TextInput(text=str(config.get('timeout', 10)), multiline=False, font_name=CF,
                                       size_hint_y=None, height=dp(40))
        layout.add_widget(self.timeout_input)

        layout.add_widget(Label(text='最大重试次数', font_name=CF, size_hint_y=None, height=dp(30)))
        self.retries_input = TextInput(text=str(config.get('max_retries', 3)), multiline=False, font_name=CF,
                                       size_hint_y=None, height=dp(40))
        layout.add_widget(self.retries_input)

        layout.add_widget(Label(text='重试间隔秒数', font_name=CF, size_hint_y=None, height=dp(30)))
        self.delay_input = TextInput(text=str(config.get('retry_delay', 1)), multiline=False, font_name=CF,
                                     size_hint_y=None, height=dp(40))
        layout.add_widget(self.delay_input)

        layout.add_widget(Label(text='最大缓存条目数', font_name=CF, size_hint_y=None, height=dp(30)))
        self.cache_input = TextInput(text=str(config.get('max_cache', 20)), multiline=False, font_name=CF,
                                     size_hint_y=None, height=dp(40))
        layout.add_widget(self.cache_input)

        save_btn = Button(text='保存并关闭', font_name=CF, size_hint_y=None, height=dp(50))
        save_btn.bind(on_press=self.save_and_close)
        layout.add_widget(save_btn)

        self.content = layout

    def save_and_close(self, instance):
        try:
            self.config['default_num'] = int(self.num_input.text)
            self.config['timeout'] = float(self.timeout_input.text)
            self.config['max_retries'] = int(self.retries_input.text)
            self.config['retry_delay'] = float(self.delay_input.text)
            self.config['max_cache'] = int(self.cache_input.text)
            save_config(self.config)
            self.save_callback(self.config)
            self.dismiss()
        except ValueError:
            pass


class HistoryPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "历史记录"
        self.size_hint = (0.8, 0.6)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=15)
        scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=6, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)
        layout.add_widget(scroll)
        close_btn = Button(text='关闭', font_name=CF, size_hint_y=None, height=dp(45))
        close_btn.bind(on_press=self.dismiss)
        layout.add_widget(close_btn)
        self.content = layout
        self.refresh()

    def refresh(self):
        self.grid.clear_widgets()
        cache = load_cache()
        if not cache:
            self.grid.add_widget(Label(text='暂无历史记录', font_name=CF, size_hint_y=None, height=dp(40)))
            return
        for entry in reversed(cache[-20:]):
            line = f"{entry['time']}  {entry['song']} - {entry['singer']}"
            lbl = Label(text=line, font_name=CF, size_hint_y=None, height=dp(35), halign='left',
                        text_size=(self.width - dp(30), None))
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

        outer = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # 平台选择
        plat_box = BoxLayout(size_hint_y=None, height=dp(140), spacing=10)
        plat_label = Label(text='选择平台：', font_name=CF, font_size='16sp', size_hint_x=0.3)
        plat_btns = BoxLayout(orientation='vertical', size_hint_x=0.7, spacing=5)
        self.plat_buttons = {}
        for key, info in PLATFORMS.items():
            btn = Button(text=info['name'], font_name=CF, font_size='14sp',
                         background_color=(0.2, 0.2, 0.2, 1), color=(1,1,1,1))
            btn.bind(on_press=self.on_platform_select)
            self.plat_buttons[key] = btn
            plat_btns.add_widget(btn)
        plat_box.add_widget(plat_label)
        plat_box.add_widget(plat_btns)
        outer.add_widget(plat_box)

        # 歌名输入
        input_row = BoxLayout(size_hint_y=None, height=dp(45), spacing=10)
        input_row.add_widget(Label(text='歌名/关键词：', font_name=CF, font_size='15sp',
                                   size_hint_x=None, width=dp(140)))
        self.keyword_input = TextInput(hint_text='请输入...', multiline=False, font_name=CF, font_size='15sp')
        input_row.add_widget(self.keyword_input)
        outer.add_widget(input_row)

        # 数量输入
        num_row = BoxLayout(size_hint_y=None, height=dp(45), spacing=10)
        num_row.add_widget(Label(text='搜索数量：', font_name=CF, font_size='15sp',
                                 size_hint_x=None, width=dp(140)))
        self.num_input = TextInput(text=str(self.config.get('default_num', 10)), hint_text='默认10',
                                   multiline=False, font_name=CF, font_size='15sp')
        num_row.add_widget(self.num_input)
        outer.add_widget(num_row)

        # 搜索按钮
        self.search_btn = Button(text='搜索', font_name=CF, font_size='18sp', size_hint_y=None, height=dp(55),
                                 background_color=(0.2, 0.6, 1, 1))
        self.search_btn.bind(on_press=self.do_search)
        outer.add_widget(self.search_btn)

        # 状态标签
        self.status_label = Label(text='', font_name=CF, font_size='13sp', size_hint_y=None, height=dp(25),
                                  color=(0.5, 0.5, 0.5, 1))
        outer.add_widget(self.status_label)

        # 底部按钮行：右对齐
        bottom_row = BoxLayout(size_hint_y=None, height=dp(50))
        bottom_row.add_widget(Label())  # 占位，将按钮推到右侧
        history_btn = Button(text='历史记录', font_name=CF, font_size='14sp',
                             size_hint=(None, None), size=(dp(100), dp(40)))
        history_btn.bind(on_press=self.show_history)
        bottom_row.add_widget(history_btn)
        settings_btn = Button(text='设置', font_name=CF, font_size='14sp',
                              size_hint=(None, None), size=(dp(100), dp(40)))
        settings_btn.bind(on_press=self.open_settings)
        bottom_row.add_widget(settings_btn)
        outer.add_widget(bottom_row)

        self.add_widget(outer)

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
        popup = HistoryPopup()
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

            # 卡片容器，固定高度
            card = BoxLayout(orientation='vertical', spacing=2, size_hint_y=None, height=dp(100))

            # 主行
            row = BoxLayout(size_hint_y=None, height=dp(60), spacing=8, padding=[5, 3])
            idx_lbl = Label(text=f'{idx+1}.', font_name=CF, font_size='14sp', bold=True,
                            size_hint_x=None, width=dp(35))

            info_col = BoxLayout(orientation='vertical', spacing=2, size_hint_x=1)
            name_lbl = Label(text=name, font_name=CF, font_size='15sp', bold=True, halign='left',
                             size_hint_y=None, height=dp(30), text_size=(None, None))
            singer_lbl = Label(text=singer, font_name=CF, font_size='12sp',
                               color=(0.4,0.4,0.4,1), halign='left',
                               size_hint_y=None, height=dp(20), text_size=(None, None))
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

            # 链接展示区
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

        link_area, link_lbl, copy_btn, get_btn = self._link_bars[index-1]
        link_lbl.text = url
        copy_btn.opacity = 1
        link_area.opacity = 1

        def copy_clipboard(x):
            Clipboard.copy(url)
            copy_btn.text = '已复制!'
            Clock.schedule_once(lambda t: setattr(copy_btn, 'text', '复制链接'), 1.5)
        copy_btn.bind(on_press=copy_clipboard)