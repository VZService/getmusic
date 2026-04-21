# -*- coding: utf-8 -*-

from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard

from core import PLATFORMS, search_songs, fetch_music_by_song


# ==================== 欢迎页（水印） ====================
class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)

        layout.add_widget(Label(
            text='---*欢迎使用音乐获取工具*---',
            font_size='22sp', bold=True,
            size_hint_y=None, height='50dp'
        ))
        layout.add_widget(Label(text='提示：   +++++++++++', font_size='14sp',
                               size_hint_y=None, height='30dp'))
        layout.add_widget(Label(text='1.  作者QQ 535595887', font_size='14sp',
                               size_hint_y=None, height='30dp'))
        layout.add_widget(Label(text='2.  本工具在GitHub开源，禁止商业用途', font_size='14sp',
                               size_hint_y=None, height='30dp'))
        layout.add_widget(Label(text='3.  可以获取VIP音乐', font_size='14sp',
                               size_hint_y=None, height='30dp'))
        layout.add_widget(Label(text='+++++++++++++++++++++', font_size='14sp',
                               size_hint_y=None, height='30dp'))

        layout.add_widget(BoxLayout())  # spacer

        btn = Button(text='开始使用 →', font_size='18sp',
                     size_hint=(None, None), size=('200dp', '50dp'),
                     pos_hint={'center_x': 0.5})
        btn.bind(on_press=self.go_search)
        layout.add_widget(btn)

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
        plat_label = Label(text='选择平台：', font_size='16sp', size_hint_x=0.3)
        plat_btns = BoxLayout(orientation='vertical', size_hint_x=0.7, spacing=5)
        self.plat_buttons = {}
        for key, info in PLATFORMS.items():
            btn = Button(text=info['name'], font_size='14sp')
            btn.bind(on_press=self.on_platform_select)
            self.plat_buttons[key] = btn
            plat_btns.add_widget(btn)
        plat_box.add_widget(plat_label)
        plat_box.add_widget(plat_btns)
        outer.add_widget(plat_box)

        # 关键词输入
        input_row = BoxLayout(size_hint_y=None, height='45dp', spacing=10)
        input_row.add_widget(Label(text='歌名/关键词：', font_size='15sp', size_hint_x=None, width='140dp'))
        self.keyword_input = TextInput(hint_text='请输入...', multiline=False,
                                       font_size='15sp')
        input_row.add_widget(self.keyword_input)
        outer.add_widget(input_row)

        # 数量输入
        num_row = BoxLayout(size_hint_y=None, height='45dp', spacing=10)
        num_row.add_widget(Label(text='搜索数量：', font_size='15sp', size_hint_x=None, width='140dp'))
        self.num_input = TextInput(text='10', hint_text='默认10', multiline=False,
                                   font_size='15sp')
        num_row.add_widget(self.num_input)
        outer.add_widget(num_row)

        # 搜索按钮
        self.search_btn = Button(text='🔍 搜索', font_size='18sp',
                                 size_hint_y=None, height='55dp',
                                 background_color=(0.2, 0.6, 1, 1))
        self.search_btn.bind(on_press=self.do_search)
        outer.add_widget(self.search_btn)

        # 状态提示
        self.status_label = Label(text='', font_size='13sp', size_hint_y=None, height='25dp',
                                  color=(0.5, 0.5, 0.5, 1))
        outer.add_widget(self.status_label)

        outer.add_widget(BoxLayout())
        self.add_widget(outer)

    def on_platform_select(self, instance):
        """高亮选中平台"""
        for key, btn in self.plat_buttons.items():
            if btn is instance:
                btn.background_color = (0.2, 0.7, 0.3, 1)  # 绿色选中
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
        num = int(num_str) if num_str.isdigit() else 10

        platform = PLATFORMS[self.selected_platform]
        self.search_btn.disabled = True
        self.search_btn.text = '搜索中...'
        self.status_label.text = f'正在搜索 "{keyword}"...'

        # 异步搜索避免卡 UI
        Clock.schedule_once(lambda dt: self._run_search(platform, keyword, num), 0.1)

    def _run_search(self, platform, keyword, num):
        songs = search_songs(platform['url'], keyword, num)
        result_screen = self.manager.get_screen('result')
        result_screen.show_results(songs, platform, keyword)
        self.manager.current = 'result'

        self.search_btn.disabled = False
        self.search_btn.text = '🔍 搜索'


# ==================== 结果页 ====================
class SongButton(Button):
    """可点击的歌曲条目"""
    pass


class ResultScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.songs = []
        self.platform = None
        self.keyword = ''

        outer = BoxLayout(orientation='vertical', padding=15, spacing=8)

        # 标题栏
        header = BoxLayout(size_hint_y=None, height='48dp', spacing=10)
        self.title_label = Label(text='搜索结果', font_size='18sp', bold=True, halign='left',
                                 text_size=(None, None))
        back_btn = Button(text='← 返回', font_size='14sp',
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

        # 底部信息区
        self.info_label = Label(text='', font_size='13sp', size_hint_y=None, height='40dp',
                                color=(0.3, 0.3, 0.3, 1))
        outer.add_widget(self.info_label)

        self.add_widget(outer)

    def show_results(self, songs, platform, keyword):
        self.songs = songs
        self.platform = platform
        self.keyword = keyword
        self.result_grid.clear_widgets()

        if not songs:
            self.info_label.text = f'未找到 "{keyword}" 的相关歌曲，换个关键词试试吧~'
            self.title_label.text = '搜索结果 (0 首)'
            return

        self.title_label.text = f'搜索结果 ({len(songs)} 首)'
        self.info_label.text = ''

        for idx, s in enumerate(songs):
            name = s.get('song', '未知')
            singer = s.get('singer', '未知')

            row = BoxLayout(size_hint_y=None, height='50dp', spacing=8, padding=[5, 3])

            idx_lbl = Label(text=f'{idx + 1}.', font_size='14sp', bold=True,
                            size_hint_x=None, width='35dp')
            info_col = BoxLayout(orientation='vertical', spacing=2)
            name_lbl = Label(text=name, font_size='15sp', bold=True, halign='left',
                             text_size=(self.width - 150, None))
            singer_lbl = Label(text=singer, font_size='12sp', color=(0.4, 0.4, 0.4, 1),
                               halign='left', text_size=(self.width - 150, None))
            info_col.add_widget(name_lbl)
            info_col.add_widget(singer_lbl)

            get_btn = Button(text='获取链接', font_size='12sp',
                             size_hint=(None, None), size=('100dp', '38dp'),
                             background_color=(0.18, 0.55, 0.95, 1))
            get_idx = idx + 1
            get_btn.bind(on_press=lambda x, i=get_idx: self._get_link(i))

            row.add_widget(idx_lbl)
            row.add_widget(info_col)
            row.add_widget(get_btn)
            self.result_grid.add_widget(row)

    def _get_link(self, index):
        """获取某首歌的直链"""
        selected = self.songs[index - 1]
        name = selected.get('song', '未知')
        singer = selected.get('singer', '未知')

        self.info_label.text = f'正在获取《{name}》的播放链接...'
        Clock.schedule_once(lambda dt: self._do_get(name, singer, index), 0.1)

    def _do_get(self, name, singer, index):
        result = fetch_music_by_song(self.platform['url'], name, singer, index)

        if result:
            url = result['music_url']
            display_name = result.get('song', name)
            display_singer = result.get('singer', singer)
            self.info_label.text = f'✅ {display_name} - {display_singer}\n点击下方复制链接 👇'

            # 显示复制按钮和完整链接
            link_bar = BoxLayout(size_hint_y=None, height='45dp', spacing=8, padding=[0, 5])
            link_lbl = Label(text=url[:60] + ('...' if len(url) > 60 else ''),
                             font_size='12sp', halign='left', text_size=(None, None),
                             color=(0.1, 0.1, 0.6, 1))
            copy_btn = Button(text='复制链接', font_size='13sp',
                              size_hint=(None, None), size=('90dp', '38dp'),
                              background_color=(0.2, 0.7, 0.3, 1))

            def copy_clipboard(x):
                Clipboard.copy(url)
                copy_btn.text = '已复制! ✓'
                Clock.schedule_once(lambda t: setattr(copy_btn, text', '复制链接'), 1.5)

            copy_btn.bind(on_press=copy_clipboard)
            link_bar.add_widget(link_lbl)
            link_bar.add_widget(copy_btn)
            self.result_grid.add_widget(link_bar)
        else:
            self.info_label.text = f'❌ 获取《{name}》播放链接失败，可能无版权或API限制'
