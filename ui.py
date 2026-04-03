# -*- coding: utf-8 -*-

import sys
from core import load_cache, save_config, PLATFORMS, colorize, Colors

def print_welcome(config):
    """打印欢迎信息"""
    print(colorize("---*欢迎使用音乐🎵获取工具*---", Colors.BOLD, config["color_enabled"]))
    print(colorize("提示：   +++++++++++", Colors.YELLOW, config["color_enabled"]))
    print(colorize("1.#️⃣  作者QQ535595887", Colors.CYAN, config["color_enabled"]))
    print(colorize("2.⚠️  本工具在GitHub开源，禁止商业用途", Colors.YELLOW, config["color_enabled"]))
    print(colorize("3.🔆  可以获取VIP音乐", Colors.GREEN, config["color_enabled"]))
    print(colorize("+++++++++++++++++++++", Colors.YELLOW, config["color_enabled"]))

def show_cache(config):
    """显示历史缓存"""
    cache = load_cache()
    if not cache:
        print(colorize("📭 暂无历史记录口牙，搜索个音乐吧", Colors.YELLOW, config["color_enabled"]))
        return
    print(colorize(f"\n📜 最近 {len(cache)} 条历史记录：", Colors.BOLD, config["color_enabled"]))
    for idx, entry in enumerate(reversed(cache[-10:]), 1):
        print(f"{idx}. {entry['time']} | {entry['song']} - {entry['singer']} | {entry['platform']}")
        print(f"   🔗 {entry['url'][:80]}...")
    input(colorize("\n按回车键继续...", Colors.CYAN, config["color_enabled"]))

def config_menu(config):
    """设置界面"""
    print(colorize("\n⚙️ 设置脚本", Colors.BOLD, config["color_enabled"]))
    print("可调整项：")
    print("1. 默认搜索数量 (当前: {})".format(config["default_num"]))
    print("2. 请求超时秒数 (当前: {})".format(config["timeout"]))
    print("3. 最大重试次数 (当前: {})".format(config["max_retries"]))
    print("4. 重试间隔秒数 (当前: {})".format(config["retry_delay"]))
    print("5. 最大缓存条目数 (当前: {})".format(config["max_cache"]))
    print("6. 彩色输出开关 (当前: {})".format("开" if config["color_enabled"] else "关"))
    print("7. DEBUG模式开关 (当前: {})".format("开" if config["debug_mode"] else "关"))
    print("0. 返回主菜单")
    
    while True:
        choice = input(colorize("请选择要修改的序号(0-7): ", Colors.CYAN, config["color_enabled"])).strip()
        if choice == "0":
            break
        elif choice == "1":
            val = input("请输入新的默认搜索数量: ")
            if val.isdigit():
                config["default_num"] = int(val)
            else:
                print(colorize("输入无效，必须是数字", Colors.RED, config["color_enabled"]))
        elif choice == "2":
            val = input("请输入新的超时秒数: ")
            if val.replace('.', '').isdigit():
                config["timeout"] = float(val)
            else:
                print(colorize("输入无效，必须是数字", Colors.RED, config["color_enabled"]))
        elif choice == "3":
            val = input("请输入新的最大重试次数: ")
            if val.isdigit():
                config["max_retries"] = int(val)
            else:
                print(colorize("输入无效，必须是整数", Colors.RED, config["color_enabled"]))
        elif choice == "4":
            val = input("请输入新的重试间隔秒数: ")
            if val.replace('.', '').isdigit():
                config["retry_delay"] = float(val)
            else:
                print(colorize("输入无效，必须是数字", Colors.RED, config["color_enabled"]))
        elif choice == "5":
            val = input("请输入新的最大缓存条目数: ")
            if val.isdigit():
                config["max_cache"] = int(val)
            else:
                print(colorize("输入无效，必须是整数", Colors.RED, config["color_enabled"]))
        elif choice == "6":
            config["color_enabled"] = not config["color_enabled"]
            print("彩色输出已" + ("开启" if config["color_enabled"] else "关闭"))
        elif choice == "7":
            config["debug_mode"] = not config["debug_mode"]
            print("DEBUG模式已" + ("开启" if config["debug_mode"] else "关闭"))
        else:
            print(colorize("无效输入，请重试", Colors.RED, config["color_enabled"]))
            continue
        save_config(config)
        print(colorize("✅ 配置已保存", Colors.GREEN, config["color_enabled"]))
    return config

def choose_platform(config):
    """平台选择菜单，对波点音乐给出警告"""
    print(colorize("\n请选择音乐平台：", Colors.BOLD, config["color_enabled"]))
    for key, plat in PLATFORMS.items():
        print(f"{key}. {plat['name']}")
    while True:
        choice = input(colorize("⌨️ 请输入序号(1-3): ", Colors.CYAN, config["color_enabled"])).strip()
        if choice not in PLATFORMS:
            print(colorize("❔你可能输入错了？请重新选择 1-3", Colors.RED, config["color_enabled"]))
            continue
        
        # 如果选择波点音乐（序号3），给出警告
        if choice == "3":
            print(colorize("⚠️  警告：波点音乐接口可能只返回11秒试听片段，建议使用其他平台获取完整歌曲。", Colors.YELLOW, config["color_enabled"]))
            confirm = input(colorize("是否继续使用波点音乐？(y/N): ", Colors.CYAN, config["color_enabled"])).strip().lower()
            if confirm == 'y':
                return PLATFORMS[choice]
            else:
                print(colorize("已取消，请重新选择平台。", Colors.YELLOW, config["color_enabled"]))
                continue
        else:
            return PLATFORMS[choice]

def main_menu(config):
    """主菜单"""
    print(colorize("\n🎵 主菜单", Colors.BOLD, config["color_enabled"]))
    print("1. 搜索音乐")
    print("2. 查看历史记录")
    print("3. 设置")
    print("0. 退出")
    return input(colorize("请选择: ", Colors.CYAN, config["color_enabled"])).strip()