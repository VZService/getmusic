#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
getmusic min-cmd
精简版 — 仅搜索 + 水印，零配置文件

用法:
  python main.py           # 正常模式
  python main.py --debug    # DEBUG模式
"""

from core import search_songs, fetch_music_by_song
from ui import print_welcome, choose_platform


def main():
    print_welcome()

    while True:
        platform = choose_platform()
        print(f"\n[>] 已选择：{platform['name']}")

        keyword = input("请输入歌名/关键词: ").strip()
        if not keyword:
            print("[!] 关键词不能为空")
            continue

        num_str = input("搜索数量（默认10）: ").strip()
        num = int(num_str) if num_str.isdigit() else 10

        print(f"[...] 正在搜索 \"{keyword}\"（最多{num}首）...")
        try:
            songs = search_songs(platform['url'], keyword, num)
        except Exception as e:
            print(f"[!] 搜索失败: {e}")
            continue
        if not songs:
            print("[!] 未找到相关歌曲")
            continue

        print(f"\n[*] 找到 {len(songs)} 首歌曲：")
        for idx, s in enumerate(songs, start=1):
            print(f"  {idx}. {s.get('song', '未知')} - {s.get('singer', '未知')}")

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
                    print(f"[!] 请输入 1~{len(songs)}")
                except ValueError:
                    print("[!] 请输入有效数字")

        song_name = selected.get("song", "未知")
        singer = selected.get("singer", "未知")
        print(f"\n[...] 获取《{song_name}》播放链接...")

        result = fetch_music_by_song(platform['url'], song_name, singer)
        if result:
            print("\n[OK] 获取成功!")
            print(f"     歌曲：{result['song']} - {result['singer']}")
            print(f"     链接：{result['music_url']}")
            print("     用浏览器打开即可收听")
        else:
            print("[!] 获取失败")

        if input("\n继续？(Y/n): ").strip().lower() == 'n':
            print("再见！")
            break


if __name__ == "__main__":
    main()
