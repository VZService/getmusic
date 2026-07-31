"""getmusic max-gui -- 基于 Kivy"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.config import Config

Config.set('graphics', 'width', '500')
Config.set('graphics', 'height', '700')
Config.set('graphics', 'resizable', '0')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from gui import Welcome, Search, Result


class GetMusicApp(App):
    title = 'getmusic -- 音乐获取工具'

    def build(self):
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(Welcome(name='welcome'))
        sm.add_widget(Search(name='search'))
        sm.add_widget(Result(name='result'))
        return sm


if __name__ == '__main__':
    GetMusicApp().run()
