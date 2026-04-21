# -*- coding: utf-8 -*-

import json
import sys
import time
import urllib.request
import urllib.parse
import urllib.error

# ---------- 唯一选项：DEBUG模式 ----------
DEBUG = "--debug" in sys.argv

# ---------- 平台配置 ----------
PLATFORMS = {
    "1": {"name": "网易云音乐", "url": "https://a.aa.cab/wy.music"},
    "2": {"name": "咪咕音乐",   "url": "https://a.aa.cab/mg.music"},
    "3": {"name": "波点音乐",   "url": "https://a.aa.cab/bd.music"}
}

# ---------- API请求（带重试） ----------
def api_request(platform_url, params):
    url = platform_url + "?" + urllib.parse.urlencode(params)
    for attempt in range(1, 4):  # 最多重试3次
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            if DEBUG:
                print("\n[DEBUG] API返回:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        except Exception as e:
            print(f"[!] 请求失败 (尝试 {attempt}/3): {e}")
            if attempt < 3:
                time.sleep(1)
    return None

def search_songs(platform_url, keyword, num=10):
    """搜索歌曲"""
    data = api_request(platform_url, {"msg": keyword, "num": num})
    if not data or data.get("code") != 0:
        if data:
            print(f"[!] 获取失败: {data.get('msg', '未知错误')}")
        return []
    result = data.get("data")
    if isinstance(result, dict):
        return [result] if result.get("music") else []
    if isinstance(result, list):
        return result
    return []

def fetch_music_by_song(platform_url, song_name, singer, index=1):
    """获取播放链接"""

    # 波点音乐
    if "bd.music" in platform_url:
        for p in [{"msg": song_name, "n": index}, {"msg": song_name, "n": 1}, {"msg": song_name, "num": 1}]:
            data = api_request(platform_url, p)
            if not data or data.get("code") != 0:
                continue
            info = data.get("data")
            items = [info] if isinstance(info, dict) else info if isinstance(info, list) else []
            for item in items:
                url = item.get("music") if isinstance(item, dict) else None
                if url:
                    return {"music_url": url, "song": item.get("song", song_name), "singer": item.get("singer", singer)}
        if DEBUG:
            print("[DEBUG] 波点音乐获取失败，已尝试所有策略")
        return None

    # 网易云、咪咕
    query = f"{song_name} {singer}" if singer and singer != "未知" else song_name
    data = api_request(platform_url, {"msg": query, "n": 1})
    if not data or data.get("code") != 0:
        return None
    info = data.get("data", {})
    url = info.get("music")
    if not url:
        return None
    return {"music_url": url, "song": info.get("song", song_name), "singer": info.get("singer", singer)}
