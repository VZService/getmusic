#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
getmusic max-gui
图形界面版 — 基于 Kivy 框架

依赖安装:
    pip install kivy

运行:
    python main.py
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition, SlideTransition
from kivy.config import Config

# 窗口设置：禁止调整大小，设置初始尺寸
Config.set('graphics', 'width', '500')
Config.set('graphics', 'height', '700')
Config.set('graphics', 'resizable', '0')

# 禁止多触控（桌面端不需要）
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from gui import WelcomeScreen, SearchScreen, ResultScreen


class GetMusicApp(App):
    """音乐获取工具 - 图形界面版"""

    title = 'getmusic — 音乐获取工具'

    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(SearchScreen(name='search'))
        sm.add_widget(ResultScreen(name='result'))
        return sm


if __name__ == '__main__':
    GetMusicApp().run()
