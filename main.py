#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from core import load_config, save_config, add_to_cache
from core import search_songs, fetch_music_by_song, PLATFORMS
from ui import (
    print_welcome, main_menu, choose_platform, show_cache,
    config_menu, colorize, Colors
)

def main():
    config = load_config()
    print_welcome(config)

    while True:
        choice = main_menu(config)
        if choice == "0":
            print(colorize("👋 再见！", Colors.CYAN, config["color_enabled"]))
            break

        elif choice == "1":   # 搜索音乐
            platform = choose_platform(config)
            print(colorize(f"\n🎶已选择：{platform['name']}", Colors.GREEN, config["color_enabled"]))

            keyword = input(colorize("🎶请输入歌名/关键词：", Colors.CYAN, config["color_enabled"])).strip()
            if not keyword:
                print(colorize("666你想播放空气？没关系，已经播放了awa", Colors.YELLOW, config["color_enabled"]))
                continue

            # 临时覆盖搜索数量
            num_str = input(colorize(f"🔢搜索数量（默认{config['default_num']}，直接回车使用默认）: ", Colors.CYAN, config["color_enabled"])).strip()
            if num_str.isdigit():
                config["default_num"] = int(num_str)
            elif num_str:
                print(colorize("输入无效，使用默认值", Colors.YELLOW, config["color_enabled"]))
            # 未输入时保持默认值不变

            print(colorize(f"🔍正在搜索“{keyword}”（最多{config['default_num']}首），请稍候...", Colors.BLUE, config["color_enabled"]))
            songs = search_songs(platform['url'], keyword, config)
            if not songs:
                print(colorize("❎没有找到相关歌曲，请尝试其他关键词", Colors.RED, config["color_enabled"]))
                continue

            print(colorize(f"\n📋 找到 {len(songs)} 首歌曲：", Colors.BOLD, config["color_enabled"]))
            for idx, s in enumerate(songs, start=1):
                song_name = s.get("song", "未知")
                singer = s.get("singer", "未知")
                print(f"{idx}. {song_name} - {singer}")

            # 用户选择序号
            if len(songs) == 1:
                print(colorize("\n🎯 只有一首歌曲，自动选中。", Colors.GREEN, config["color_enabled"]))
                selected = songs[0]
                sel = 1
            else:
                while True:
                    try:
                        choice_idx = input(colorize(f"\n⌨️请选择序号(1-{len(songs)}): ", Colors.CYAN, config["color_enabled"])).strip()
                        sel = int(choice_idx)
                        if 1 <= sel <= len(songs):
                            selected = songs[sel-1]
                            break
                        else:
                            print(colorize(f"请输入 1~{len(songs)} 之间的数字", Colors.RED, config["color_enabled"]))
                    except ValueError:
                        print(colorize("请输入有效数字", Colors.RED, config["color_enabled"]))

            song_name = selected.get("song", "未知")
            singer = selected.get("singer", "未知")
            print(colorize(f"\n🎵 正在获取《{song_name}》的播放链接...", Colors.BLUE, config["color_enabled"]))
            # 传入序号 sel（波点平台需要，其他平台忽略）
            result = fetch_music_by_song(platform['url'], song_name, singer, config, sel)
            if result:
                print(colorize(f"\n✅ 获取成功辣awa!", Colors.GREEN, config["color_enabled"]))
                print(colorize(f"🎤 歌曲：{result['song']} - {result['singer']}", Colors.MAGENTA, config["color_enabled"]))
                print(colorize(f"🔗 播放链接：{result['music_url']}", Colors.CYAN, config["color_enabled"]))
                print(colorize("用浏览器打开即可收听!", Colors.GREEN, config["color_enabled"]))
                add_to_cache(result['song'], result['singer'], result['music_url'], platform['name'], config["max_cache"])
            else:
                print(colorize("❎获取播放链接失败惹，可能是该歌曲无法获取或API限制。", Colors.RED, config["color_enabled"]))

            input(colorize("\n按回车键继续...", Colors.CYAN, config["color_enabled"]))

        elif choice == "2":   # 查看历史记录
            show_cache(config)

        elif choice == "3":   # 设置
            config = config_menu(config)

        else:
            print(colorize("无效选项，请重新输入", Colors.RED, config["color_enabled"]))

if __name__ == "__main__":
    main()