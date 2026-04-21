#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
getmusic min-cmd
精简版命令行工具 — 仅搜索功能 + 水印，无彩色输出
"""

import sys
from core import load_config, search_songs, fetch_music_by_song
from ui import print_welcome, choose_platform


def main():
    config = load_config()
    print_welcome()

    while True:
        # 选择平台
        platform = choose_platform()
        print(f"\n[>] 已选择：{platform['name']}")

        # 输入关键词
        keyword = input("请输入歌名/关键词: ").strip()
        if not keyword:
            print("[!] 关键词不能为空")
            continue

        # 搜索数量（可选）
        num_str = input(f"搜索数量（默认{config['default_num']}）: ").strip()
        if num_str.isdigit():
            config["default_num"] = int(num_str)

        print(f"[...] 正在搜索 \"{keyword}\"（最多{config['default_num']}首）...")
        songs = search_songs(platform['url'], keyword, config)
        if not songs:
            print("[!] 未找到相关歌曲")
            continue

        print(f"\n[*] 找到 {len(songs)} 首歌曲：")
        for idx, s in enumerate(songs, start=1):
            song_name = s.get("song", "未知")
            singer = s.get("singer", "未知")
            print(f"  {idx}. {song_name} - {singer}")

        # 选择歌曲
        if len(songs) == 1:
            selected = songs[0]
        else:
            while True:
                try:
                    sel = input(f"请选择序号(1-{len(songs)}): ").strip()
                    idx = int(sel)
                    if 1 <= idx <= len(songs):
                        selected = songs[idx - 1]
                        break
                    else:
                        print(f"[!] 请输入 1~{len(songs)} 之间的数字")
                except ValueError:
                    print("[!] 请输入有效数字")

        song_name = selected.get("song", "未知")
        singer = selected.get("singer", "未知")
        print(f"\n[...] 正在获取《{song_name}》的播放链接...")

        result = fetch_music_by_song(platform['url'], song_name, singer, config)
        if result:
            print("\n[OK] 获取成功!")
            print(f"     歌曲：{result['song']} - {result['singer']}")
            print(f"     链接：{result['music_url']}")
            print("     用浏览器打开即可收听")
        else:
            print("[!] 获取播放链接失败")

        again = input("\n继续搜索？(Y/n): ").strip().lower()
        if again == 'n':
            print("再见！")
            break


if __name__ == "__main__":
    main()
