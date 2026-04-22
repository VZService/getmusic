# -*- coding: utf-8 -*-

import os
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase

from core import PLATFORMS, DEFAULT_CONFIG, load_config, save_config, search_songs, fetch_music_by_song

# 注册中文字体
_base = os.path.dirname(os.path.abspath(__file__))
LabelBase.register(name='ChineseFont', fn_regular=os.path.join(_base, 'data', 'chinesefont.ttf'))
CF = 'ChineseFont'

# ==================== 全局配置 ====================
app_config = load_config()


def get_cfg():
    """构建传给 core 函数的配置字典"""
    return {
        "default_num": app_config.get("default_num", 10),
        "max_retries": app_config.get("max_retries", 3),
        "retry_delay": app_config.get("retry_delay", 1),
        "timeout": app_config.get("timeout", 10),
        "color_enabled": False,
        "debug_mode": app_config.get("debug_mode", False)
    }


# ==================== 欢迎页（水印） ====================
class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)

        layout.add_widget(Label(
            text='---*欢迎使用音乐获取工具*---',
            font_name=CF, font_size='22sp', bold=True,
            size_hint_y=None, height='50dp'
        ))
        layout.add_widget(Label(text='提示：', font_name=CF, font_size='14sp',
                               size_hint_y=None, height='30dp'))
        layout.add_widget(Label(text='1.  作者QQ 535595887', font_name=CF, font_size='14sp',
                               size_hint_y=None, height='30dp'))
        layout.add_widget(Label(text='2.  本工具在GitHub开源，禁止商业用途', font_name=CF, font_size='14sp',
                               size_hint_y=None, height='30dp'))
        layout.add_widget(Label(text='3.  可以获取VIP音乐', font_name=CF, font_size='14sp',
                               size_hint_y=None, height='30dp'))

        layout.add_widget(BoxLayout())  # spacer

        btn_row = BoxLayout(size_hint_y=None, height='60dp', spacing=20, padding=[20, 0])
        btn = Button(text='开始使用 →', font_name=CF, font_size='18sp',
                     size_hint=(None, None), size=('200dp', '50dp'),
                     pos_hint={'center_x': 0.5})
        btn.bind(on_press=self.go_search)
        set_btn = Button(text='⚙ 设置', font_name=CF, font_size='16sp',
                         size_hint=(None, None), size=('120dp', '45dp'),
                         background_color=(0.55, 0.55, 0.55, 1))
        set_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'settings'))
        btn_row.add_widget(BoxLayout())
        btn_row.add_widget(btn)
        btn_row.add_widget(set_btn)
        btn_row.add_widget(BoxLayout())
        layout.add_widget(btn_row)

        self.add_widget(layout)

    def go_search(self, instance):
        self.manager.current = 'search'


# ==================== 搜索页 ====================
class SearchScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_platform = None

        outer = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # 平台选择
        plat_box = BoxLayout(size_hint_y=None, height='140dp', spacing=10)
        plat_label = Label(text='选择平台：', font_name=CF, font_size='16sp', size_hint_x=0.3)
        plat_btns = BoxLayout(orientation='vertical', size_hint_x=0.7, spacing=5)
        self.plat_buttons = {}
        for key, info in PLATFORMS.items():
            btn = Button(text=info['name'], font_name=CF, font_size='14sp')
            btn.bind(on_press=self.on_platform_select)
            self.plat_buttons[key] = btn
            plat_btns.add_widget(btn)
        plat_box.add_widget(plat_label)
        plat_box.add_widget(plat_btns)
        outer.add_widget(plat_box)

        # 关键词输入
        input_row = BoxLayout(size_hint_y=None, height='45dp', spacing=10)
        input_row.add_widget(Label(text='歌名/关键词：', font_name=CF, font_size='15sp',
                                   size_hint_x=None, width='140dp'))
        self.keyword_input = TextInput(hint_text='请输入...', multiline=False,
                                       font_name=CF, font_size='15sp')
        input_row.add_widget(self.keyword_input)
        outer.add_widget(input_row)

        # 数量输入（从全局配置读默认值）
        num_row = BoxLayout(size_hint_y=None, height='45dp', spacing=10)
        num_row.add_widget(Label(text='搜索数量：', font_name=CF, font_size='15sp',
                                 size_hint_x=None, width='140dp'))
        self.num_input = TextInput(
            text=str(app_config.get('default_num', 10)),
            hint_text=f'默认{app_config.get("default_num", 10)}',
            multiline=False, font_name=CF, font_size='15sp')
        num_row.add_widget(self.num_input)
        outer.add_widget(num_row)

        # 搜索按钮
        self.search_btn = Button(text='搜索', font_name=CF, font_size='18sp',
                                 size_hint_y=None, height='55dp',
                                 background_color=(0.2, 0.6, 1, 1))
        self.search_btn.bind(on_press=self.do_search)
        outer.add_widget(self.search_btn)

        # 状态提示 + 设置入口
        top_bar = BoxLayout(size_hint_y=None, height='35dp', spacing=10)
        self.status_label = Label(text='', font_name=CF, font_size='13sp',
                                  color=(0.5, 0.5, 0.5, 1))
        set_btn2 = Button(text='⚙ 设置', font_name=CF, font_size='12sp',
                          size_hint=(None, None), size=('80dp', '32dp'),
                          background_color=(0.6, 0.6, 0.6, 1))
        set_btn2.bind(on_press=lambda x: setattr(self.manager, 'current', 'settings'))
        top_bar.add_widget(self.status_label)
        top_bar.add_widget(set_btn2)
        outer.add_widget(top_bar)

        outer.add_widget(BoxLayout())
        self.add_widget(outer)

    def on_platform_select(self, instance):
        """高亮选中平台"""
        for key, btn in self.plat_buttons.items():
            if btn is instance:
                btn.background_color = (0.2, 0.7, 0.3, 1)
                btn.background_normal = ''
                self.selected_platform = key
            else:
                btn.background_color = (0.9, 0.9, 0.9, 1)
                btn.background_normal = ''
        self.status_label.text = f'已选择: {PLATFORMS[self.selected_platform]["name"]}'

    def do_search(self, instance):
        if not self.selected_platform:
            self.status_label.text = '请先选择一个平台!'
            return
        keyword = self.keyword_input.text.strip()
        if not keyword:
            self.status_label.text = '请输入搜索关键词!'
            return
        num_str = self.num_input.text.strip()
        num = int(num_str) if num_str.isdigit() else app_config.get('default_num', 10)

        platform = PLATFORMS[self.selected_platform]
        self.search_btn.disabled = True
        self.search_btn.text = '搜索中...'
        self.status_label.text = f'正在搜索 "{keyword}"...'

        Clock.schedule_once(lambda dt: self._run_search(platform, keyword, num), 0.1)

    def _run_search(self, platform, keyword, num):
        cfg = get_cfg()
        cfg["default_num"] = num
        songs = search_songs(platform['url'], keyword, cfg)
        result_screen = self.manager.get_screen('result')
        result_screen.show_results(songs, platform, keyword)
        self.manager.current = 'result'

        self.search_btn.disabled = False
        self.search_btn.text = '搜索'


# ==================== 结果页 ====================
class ResultScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.songs = []
        self.platform = None
        self.keyword = ''

        outer = BoxLayout(orientation='vertical', padding=15, spacing=8)

        # 标题栏
        header = BoxLayout(size_hint_y=None, height='48dp', spacing=10)
        self.title_label = Label(text='搜索结果', font_name=CF, font_size='18sp', bold=True,
                                 halign='left', text_size=(None, None))
        back_btn = Button(text='← 返回', font_name=CF, font_size='14sp',
                          size_hint=(None, None), size=('100dp', '40dp'))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'search'))
        header.add_widget(self.title_label)
        header.add_widget(back_btn)
        outer.add_widget(header)

        # 结果列表（ScrollView）
        scroll = ScrollView(do_scroll_x=False)
        self.result_grid = GridLayout(cols=1, spacing=6, size_hint_y=None)
        self.result_grid.bind(minimum_height=self.result_grid.setter('height'))
        scroll.add_widget(self.result_grid)
        outer.add_widget(scroll)

        # 底部信息区 + 设置入口
        bottom_bar = BoxLayout(size_hint_y=None, height='40dp', spacing=8)
        self.info_label = Label(text='', font_name=CF, font_size='13sp',
                                color=(0.3, 0.3, 0.3, 1))
        set_btn3 = Button(text='⚙', font_name=CF, font_size='14sp',
                          size_hint=(None, None), size=('40dp', '34dp'),
                          background_color=(0.6, 0.6, 0.6, 1))
        set_btn3.bind(on_press=lambda x: setattr(self.manager, 'current', 'settings'))
        bottom_bar.add_widget(self.info_label)
        bottom_bar.add_widget(set_btn3)
        outer.add_widget(bottom_bar)

        self.add_widget(outer)

    def show_results(self, songs, platform, keyword):
        self.songs = songs
        self.platform = platform
        self.keyword = keyword
        self.result_grid.clear_widgets()
        self._link_bars = []  # 存每首歌的链接展示区

        if not songs:
            self.info_label.text = f'未找到 "{keyword}" 的相关歌曲，换个关键词试试吧~'
            self.title_label.text = '搜索结果 (0 首)'
            return

        self.title_label.text = f'搜索结果 ({len(songs)} 首)'
        self.info_label.text = ''

        for idx, s in enumerate(songs):
            name = s.get('song', '未知')
            singer = s.get('singer', '未知')

            # 每首歌一个容器
            card = BoxLayout(orientation='vertical', spacing=2)

            # 主行（序号 + 歌曲信息 + 按钮）
            row = BoxLayout(size_hint_y=None, height='50dp', spacing=8, padding=[5, 3])

            idx_lbl = Label(text=f'{idx + 1}.', font_name=CF, font_size='14sp', bold=True,
                            size_hint_x=None, width='35dp')
            info_col = BoxLayout(orientation='vertical', spacing=2)
            name_lbl = Label(text=name, font_name=CF, font_size='15sp', bold=True, halign='left',
                             size_hint_x=1)
            singer_lbl = Label(text=singer, font_name=CF, font_size='12sp',
                               color=(0.4, 0.4, 0.4, 1),
                               halign='left', size_hint_x=1)
            info_col.add_widget(name_lbl)
            info_col.add_widget(singer_lbl)

            get_btn = Button(text='获取链接', font_name=CF, font_size='12sp',
                             size_hint=(None, None), size=('100dp', '38dp'),
                             background_color=(0.18, 0.55, 0.95, 1))
            get_idx = idx + 1
            get_btn.bind(on_press=lambda x, i=get_idx: self._get_link(i))

            row.add_widget(idx_lbl)
            row.add_widget(info_col)
            row.add_widget(get_btn)
            card.add_widget(row)

            # 链接展示区（初始隐藏，获取成功后显示）
            link_area = BoxLayout(size_hint_y=None, height='40dp', spacing=6,
                                  padding=[5, 3], opacity=0)
            link_bar = BoxLayout(spacing=6)
            link_lbl = Label(text='', font_name=CF, font_size='11sp', halign='left',
                             size_hint_x=1, color=(0.1, 0.1, 0.8, 1),
                             text_size=(None, None))
            copy_btn = Button(text='复制链接', font_name=CF, font_size='11sp',
                              size_hint=(None, None), size=('80dp', '32dp'),
                              background_color=(0.15, 0.65, 0.25, 1))
            copy_btn.opacity = 0
            link_bar.add_widget(link_lbl)
            link_bar.add_widget(copy_btn)
            link_area.add_widget(link_bar)
            card.add_widget(link_area)

            self._link_bars.append((link_area, link_lbl, copy_btn, get_btn))
            self.result_grid.add_widget(card)

    def _get_link(self, index):
        """获取某首歌的直链"""
        selected = self.songs[index - 1]
        name = selected.get('song', '未知')
        singer = selected.get('singer', '未知')

        self.info_label.text = f'正在获取《{name}》的播放链接...'
        Clock.schedule_once(lambda dt: self._do_get(name, singer, index), 0.1)

    def _do_get(self, name, singer, index):
        cfg = get_cfg()
        result = fetch_music_by_song(self.platform['url'], name, singer, cfg, index)

        if result:
            url = result['music_url']
            display_name = result.get('song', name)
            display_singer = result.get('singer', singer)
            self.info_label.text = f'获取成功：{display_name} - {display_singer}'

            # 内联显示在对应歌曲下方
            link_area, link_lbl, copy_btn, get_btn = self._link_bars[index - 1]
            link_lbl.text = url
            copy_btn.opacity = 1
            link_area.opacity = 1

            def copy_clipboard(x):
                Clipboard.copy(url)
                copy_btn.text = '已复制!'
                Clock.schedule_once(lambda t: setattr(copy_btn, 'text', '复制链接'), 1.5)

            copy_btn.bind(on_press=copy_clipboard)

            # 滚动到该位置
            self.parent.children[0].scroll_y = max(0.0, 1.0 - (index * 0.15))
        else:
            self.info_label.text = f'获取《{name}》播放链接失败，可能无版权或API限制'


# ==================== 设置页 ====================
class SettingsScreen(Screen):
    """max-gui 完整版设置面板 — 与 max-cmd 同级别"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.inputs = {}  # 存储所有输入框引用

        outer = BoxLayout(orientation='vertical', padding=20, spacing=12)

        # 标题栏
        header = BoxLayout(size_hint_y=None, height='48dp', spacing=10)
        title = Label(text='⚙ 设置', font_name=CF, font_size='20sp', bold=True, size_hint_x=1)
        back_btn = Button(text='← 返回', font_name=CF, font_size='14sp',
                          size_hint=(None, None), size=('100dp', '40dp'),
                          background_color=(0.5, 0.5, 0.5, 1))
        back_btn.bind(on_press=self.go_back)
        header.add_widget(title)
        header.add_widget(back_btn)
        outer.add_widget(header)

        # 设置项滚动区
        scroll = ScrollView(do_scroll_x=False)
        form = GridLayout(cols=1, spacing=8, size_hint_y=None)
        form.bind(minimum_height=form.setter('height'))

        # ---- 搜索设置组 ----
        form.add_widget(self._section_label('🔍 搜索设置'))

        # 默认搜索数量
        form.add_widget(self._field_row(
            '默认搜索数量:', 'default_num',
            str(app_config.get('default_num', 10)),
            '每次默认返回的歌曲数量 (1-100)'))

        # ---- 网络设置组 ----
        form.add_widget(self._section_label('🌐 网络设置'))

        # 超时时间
        form.add_widget(self._field_row(
            '超时时间 (秒):', 'timeout',
            str(app_config.get('timeout', 10)),
            '网络请求超时，单位秒 (1-60)'))

        # 最大重试次数
        form.add_widget(self._field_row(
            '最大重试次数:', 'max_retries',
            str(app_config.get('max_retries', 3)),
            '失败后自动重试的次数 (0-10)'))

        # 重试间隔
        form.add_widget(self._field_row(
            '重试间隔 (秒):', 'retry_delay',
            str(app_config.get('retry_delay', 1)),
            '每次重试前的等待秒数 (1-10)'))

        # ---- 缓存设置组 ----
        form.add_widget(self._section_label('💾 存储设置'))

        # 缓存上限
        form.add_widget(self._field_row(
            '缓存上限 (条):', 'max_cache',
            str(app_config.get('max_cache', 20)),
            '历史记录最大保存条数 (0-500, 0=不保存)'))

        # ---- 高级设置组 ----
        form.add_widget(self._section_label('🔧 高级设置'))

        # DEBUG 模式开关
        debug_row = BoxLayout(size_hint_y=None, height='45dp', spacing=10, padding=[5, 0])
        debug_row.add_widget(Label(text='DEBUG 模式:', font_name=CF, font_size='15sp',
                                  size_hint_x=None, width='160dp'))
        debug_val = app_config.get('debug_mode', False)
        self.debug_toggle = Button(
            text='开启' if debug_val else '关闭',
            font_name=CF, font_size='13sp',
            size_hint=(None, None), size=('90dp', '36dp'),
            background_color=(0.2, 0.7, 0.3, 1) if debug_val else (0.7, 0.3, 0.3, 1))
        self.debug_toggle.bind(on_press=self._toggle_debug)
        debug_row.add_widget(self.debug_toggle)
        debug_row.add_widget(Label(text='显示API原始返回数据', font_name=CF, font_size='11sp',
                                  color=(0.5, 0.5, 0.5, 1)))
        form.add_widget(debug_row)

        scroll.add_widget(form)
        outer.add_widget(scroll)

        # 操作按钮
        btn_row = BoxLayout(size_hint_y=None, height='55dp', spacing=15, padding=[20, 5])
        save_btn = Button(text='✅ 保存设置', font_name=CF, font_size='16sp',
                          size_hint=(None, None), size=('150dp', '46dp'),
                          background_color=(0.18, 0.65, 0.25, 1))
        save_btn.bind(on_press=self.save_settings)
        reset_btn = Button(text='↺ 恢复默认', font_name=CF, font_size='16sp',
                           size_hint=(None, None), size=('150dp', '46dp'),
                           background_color=(0.75, 0.55, 0.15, 1))
        reset_btn.bind(on_press=self.reset_defaults)
        btn_row.add_widget(BoxLayout())
        btn_row.add_widget(save_btn)
        btn_row.add_widget(reset_btn)
        btn_row.add_widget(BoxLayout())
        outer.add_widget(btn_row)

        # 状态提示
        self.hint_label = Label(text='修改后点击「保存设置」生效', font_name=CF, font_size='13sp',
                                size_hint_y=None, height='28dp',
                                color=(0.3, 0.6, 0.3, 1))
        outer.add_widget(self.hint_label)

        outer.add_widget(BoxLayout())
        self.add_widget(outer)

    def _section_label(self, text):
        """创建分组标题"""
        lbl = Label(text=text, font_name=CF, font_size='15sp', bold=True,
                    halign='left', size_hint_y=None, height='32dp',
                    color=(0.2, 0.4, 0.7, 1))
        return lbl

    def _field_row(self, label_text, key, default_val, hint):
        """创建一行设置项: 标签 + 输入框 + 提示"""
        row = BoxLayout(size_hint_y=None, height='65dp', spacing=6, padding=[5, 2])

        left = BoxLayout(orientation='vertical', spacing=1, size_hint_x=None, width='155dp')
        left.add_widget(Label(text=label_text, font_name=CF, font_size='14sp',
                             halign='left', size_hint_y=None, height='24dp'))
        left.add_widget(Label(text=hint, font_name=CF, font_size='10sp',
                             color=(0.55, 0.55, 0.55, 1),
                             halign='left', size_hint_y=None, height='18dp'))

        inp = TextInput(text=default_val, multiline=False,
                        font_name=CF, font_size='14sp', size_hint_y=None, height='38dp')

        row.add_widget(left)
        row.add_widget(inp)
        self.inputs[key] = inp
        return row

    def _toggle_debug(self, instance):
        """切换 DEBUG 开关"""
        current = self.debug_toggle.text == '开启'
        if current:
            self.debug_toggle.text = '关闭'
            self.debug_toggle.background_color = (0.7, 0.3, 0.3, 1)
        else:
            self.debug_toggle.text = '开启'
            self.debug_toggle.background_color = (0.2, 0.7, 0.3, 1)

    def go_back(self, instance):
        self.manager.current = 'search'

    def save_settings(self, instance):
        """验证并保存所有设置到 setting.json 和全局配置"""
        errors = []

        # 验证数字字段
        validations = [
            ('default_num', 1, 100, int),
            ('timeout', 1, 60, int),
            ('max_retries', 0, 10, int),
            ('retry_delay', 1, 10, int),
            ('max_cache', 0, 500, int),
        ]

        for key, lo, hi, cast in validations:
            raw = self.inputs[key].text.strip()
            try:
                val = cast(raw)
                if val < lo or val > hi:
                    errors.append(f'{key}: 应在 {lo}-{hi} 之间')
                else:
                    app_config[key] = val
            except ValueError:
                errors.append(f'{key}: 必须是整数')

        # DEBUG 模式
        app_config['debug_mode'] = (self.debug_toggle.text == '开启')

        if errors:
            self.hint_label.text = f'❌ {errors[0]}'
            self.hint_label.color = (0.9, 0.2, 0.2, 1)
            return

        # 写入文件
        save_config(app_config)
        self.hint_label.text = '✅ 已保存！设置已写入 setting.json'
        self.hint_label.color = (0.2, 0.7, 0.2, 1)

        # 同步搜索页的数量默认值
        search_screen = self.manager.get_screen('search')
        search_screen.num_input.text = str(app_config['default_num'])

    def reset_defaults(self, instance):
        """恢复所有设置为默认值"""
        for key, val in DEFAULT_CONFIG.items():
            if key in self.inputs:
                self.inputs[key].text = str(val)
            app_config[key] = val

        # DEBUG 按钮
        self.debug_toggle.text = '关闭'
        self.debug_toggle.background_color = (0.7, 0.3, 0.3, 1)

        self.hint_label.text = '↺ 已恢复默认值，需手动点「保存」才生效'
        self.hint_label.color = (0.75, 0.55, 0.15, 1)
