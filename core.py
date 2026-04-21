# -*- coding: utf-8 -*-

import json
import os
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

# ---------- 配置常量 ----------
DEFAULT_CONFIG = {
    "debug_mode": False,
    "default_num": 10,
    "timeout": 10,
    "max_retries": 3,
    "retry_delay": 1,
}

CONFIG_FILE = "setting.json"

# ---------- 配置管理 ----------
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in config:
                        config[k] = v
                return config
        except:
            return DEFAULT_CONFIG.copy()
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

# ---------- 平台配置 ----------
PLATFORMS = {
    "1": {"name": "网易云音乐", "url": "https://a.aa.cab/wy.music"},
    "2": {"name": "咪咕音乐",   "url": "https://a.aa.cab/mg.music"},
    "3": {"name": "波点音乐",   "url": "https://a.aa.cab/bd.music"}
}

# ---------- API请求（带重试） ----------
def api_request_with_retry(platform_url, params, config):
    url = platform_url + "?" + urllib.parse.urlencode(params)
    retries = config["max_retries"]
    delay = config["retry_delay"]
    timeout = config["timeout"]

    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            if config["debug_mode"]:
                print("\n[DEBUG] API返回:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        except urllib.error.URLError as e:
            print(f"[!] 网络错误 (尝试 {attempt}/{retries}): {e.reason}")
            if attempt < retries:
                import time
                time.sleep(delay)
            else:
                return None
        except json.JSONDecodeError:
            print("[!] API返回解析失败")
            return None
        except Exception as e:
            print(f"[!] 未知错误: {e}")
            return None
    return None

def search_songs(platform_url, keyword, config):
    """搜索歌曲"""
    params = {"msg": keyword, "num": config["default_num"]}
    data = api_request_with_retry(platform_url, params, config)
    if not data or data.get("code") != 0:
        if data:
            print(f"[!] 获取失败: {data.get('msg', '未知错误')}")
        return []
    result = data.get("data")
    if isinstance(result, dict):
        return [result] if result.get("music") else []
    elif isinstance(result, list):
        return result
    else:
        return []

def fetch_music_by_song(platform_url, song_name, singer, config, index=1):
    """
    根据精确歌名和歌手获取播放链接
    index: 对于波点平台，表示选择列表中的第几首（从1开始）
    """
    # 波点音乐
    if "bd.music" in platform_url:
        params = {"msg": song_name, "n": index}
        data = api_request_with_retry(platform_url, params, config)
        if data and data.get("code") == 0:
            info = data.get("data")
            if isinstance(info, dict):
                music_url = info.get("music")
                if music_url:
                    return {"music_url": music_url, "song": info.get("song", song_name), "singer": info.get("singer", singer)}
            elif isinstance(info, list) and len(info) > 0:
                first = info[0]
                music_url = first.get("music")
                if music_url:
                    return {"music_url": music_url, "song": first.get("song", song_name), "singer": first.get("singer", singer)}

        if index != 1:
            params2 = {"msg": song_name, "n": 1}
            data2 = api_request_with_retry(platform_url, params2, config)
            if data2 and data2.get("code") == 0:
                info = data2.get("data")
                if isinstance(info, dict):
                    music_url = info.get("music")
                    if music_url:
                        return {"music_url": music_url, "song": info.get("song", song_name), "singer": info.get("singer", singer)}

        params3 = {"msg": song_name, "num": 1}
        data3 = api_request_with_retry(platform_url, params3, config)
        if data3 and data3.get("code") == 0:
            result = data3.get("data")
            if isinstance(result, list) and len(result) > 0:
                first = result[0]
                music_url = first.get("music")
                if music_url:
                    return {"music_url": music_url, "song": first.get("song", song_name), "singer": first.get("singer", singer)}

        if config["debug_mode"]:
            print("[DEBUG] 波点音乐获取链接失败，已尝试所有策略")
        return None

    # 网易云、咪咕
    query = song_name
    if singer and singer != "未知":
        query = f"{song_name} {singer}"
    params = {"msg": query, "n": 1}
    data = api_request_with_retry(platform_url, params, config)
    if not data or data.get("code") != 0:
        return None
    info = data.get("data", {})
    music_url = info.get("music")
    if not music_url:
        return None
    return {"music_url": music_url, "song": info.get("song", song_name), "singer": info.get("singer", singer)}
