# -*- coding: utf-8 -*-

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

# ---------- 配置常量 ----------
DEFAULT_CONFIG = {
    "debug_mode": False,
    "default_num": 10,
    "timeout": 10,
    "max_retries": 3,
    "retry_delay": 1,
    "max_cache": 20,
    "color_enabled": True
}

CONFIG_FILE = "setting.json"
CACHE_FILE = "cache.json"

# ---------- 彩色输出 ----------
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"

def colorize(text, color, enable=True):
    if enable:
        return f"{color}{text}{Colors.RESET}"
    return text

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

# ---------- 缓存管理 ----------
def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_cache(cache, max_cache):
    if len(cache) > max_cache:
        cache = cache[-max_cache:]
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

def add_to_cache(song_name, singer, music_url, platform, max_cache):
    cache = load_cache()
    entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "song": song_name,
        "singer": singer,
        "url": music_url,
        "platform": platform
    }
    cache.append(entry)
    save_cache(cache, max_cache)

# ---------- 平台配置 ----------
PLATFORMS = {
    "1": {"name": "网易云音乐", "url": "https://a.aa.cab/wy.music", "accent": "#d33a3a"},
    "2": {"name": "咪咕音乐",   "url": "https://a.aa.cab/mg.music", "accent": "#1f9e8f"},
    "3": {"name": "波点音乐",   "url": "https://a.aa.cab/bd.music", "accent": "#d9811a"}
}

# ---------- API请求（带重试） ----------
def api_request_with_retry(platform_url, params, config):
    url = platform_url + "?" + urllib.parse.urlencode(params)
    retries = config["max_retries"]
    delay = config["retry_delay"]
    timeout = config["timeout"]
    
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            if config["debug_mode"]:
                print(colorize("\n[DEBUG] API返回:", Colors.MAGENTA, config["color_enabled"]))
                print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        except urllib.error.URLError as e:
            last_err = e
            if config["debug_mode"]:
                print(colorize(f"🌐❎ 网络错误 (尝试 {attempt}/{retries}): {e.reason}", Colors.RED, config["color_enabled"]))
            if attempt < retries:
                time.sleep(delay)
        except json.JSONDecodeError as e:
            last_err = e
            if config["debug_mode"]:
                print(colorize("❎ API返回解析失败", Colors.RED, config["color_enabled"]))
            if attempt < retries:
                time.sleep(delay)
        except Exception as e:
            last_err = e
            if config["debug_mode"]:
                print(colorize(f"❓ 未知错误: {e}", Colors.RED, config["color_enabled"]))
            if attempt < retries:
                time.sleep(delay)
    # 所有重试均失败：抛出异常，让上层区分"网络错误"与"无结果"
    if last_err is not None:
        raise last_err
    raise RuntimeError("请求失败（未知原因）")


def _safe_fetch(platform_url, params, config):
    """安全调用 API，异常时返回 None（兼容旧 fetch 逻辑）"""
    try:
        return api_request_with_retry(platform_url, params, config)
    except Exception:
        return None


def search_songs(platform_url, keyword, config):
    """搜索歌曲，统一使用 num 参数获取列表（所有平台均支持）

    网络故障或 API 返回错误时抛出异常，便于上层区分"网络错误"与"无结果"。
    """
    params = {"msg": keyword, "num": config["default_num"]}
    data = api_request_with_retry(platform_url, params, config)
    if not isinstance(data, dict) or data.get("code") != 0:
        msg = data.get("msg", "未知错误") if isinstance(data, dict) else "未知错误"
        raise RuntimeError(f"获取失败: {msg}")
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
    # 波点音乐：尝试多种参数获取单首链接
    if "bd.music" in platform_url:
        # 策略1：使用 n=index
        params = {"msg": song_name, "n": index}
        data = _safe_fetch(platform_url, params, config)
        if data and data.get("code") == 0:
            info = data.get("data")
            if isinstance(info, dict):
                music_url = info.get("music")
                if music_url:
                    return {
                        "music_url": music_url,
                        "song": info.get("song", song_name),
                        "singer": info.get("singer", singer)
                    }
            elif isinstance(info, list) and len(info) > 0:
                first = info[0]
                music_url = first.get("music")
                if music_url:
                    return {
                        "music_url": music_url,
                        "song": first.get("song", song_name),
                        "singer": first.get("singer", singer)
                    }
        
        # 策略2：如果 index 不是1，尝试 n=1（第一首）
        if index != 1:
            params2 = {"msg": song_name, "n": 1}
            data2 = _safe_fetch(platform_url, params2, config)
            if data2 and data2.get("code") == 0:
                info = data2.get("data")
                if isinstance(info, dict):
                    music_url = info.get("music")
                    if music_url:
                        return {
                            "music_url": music_url,
                            "song": info.get("song", song_name),
                            "singer": info.get("singer", singer)
                        }
        
        # 策略3：尝试使用 num=1（返回列表，但可能包含music字段？）
        params3 = {"msg": song_name, "num": 1}
        data3 = _safe_fetch(platform_url, params3, config)
        if data3 and data3.get("code") == 0:
            result = data3.get("data")
            if isinstance(result, list) and len(result) > 0:
                first = result[0]
                music_url = first.get("music")
                if music_url:
                    return {
                        "music_url": music_url,
                        "song": first.get("song", song_name),
                        "singer": first.get("singer", singer)
                    }
        
        # 所有策略失败
        if config["debug_mode"]:
            print(colorize(f"[DEBUG] 波点音乐获取链接失败，已尝试所有策略", Colors.YELLOW, config["color_enabled"]))
        return None

    # 网易云、咪咕：使用 n=1，查询时拼接歌手名
    query = song_name
    if singer and singer != "未知":
        query = f"{song_name} {singer}"
    params = {"msg": query, "n": 1}
    data = _safe_fetch(platform_url, params, config)
    if not data or data.get("code") != 0:
        return None
    info = data.get("data", {})
    music_url = info.get("music")
    if not music_url:
        return None
    return {
        "music_url": music_url,
        "song": info.get("song", song_name),
        "singer": info.get("singer", singer)
    }