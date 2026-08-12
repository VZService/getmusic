# -*- coding: utf-8 -*-

def print_welcome():
    """打印欢迎信息（水印）"""
    print("---*欢迎使用音乐获取工具*---")
    print("提示：   +++++++++++")
    print("1.  本工具在GitHub开源，禁止商业用途")
    print("3.  可以获取VIP音乐")
    print("+++++++++++++++++++++")

def choose_platform():
    """平台选择"""
    from core import PLATFORMS
    print("\n请选择音乐平台：")
    for key, plat in PLATFORMS.items():
        print(f"{key}. {plat['name']}")
    while True:
        choice = input("请输入序号(1-3): ").strip()
        if choice not in PLATFORMS:
            print("[!] 输入错误，请重新选择 1-3")
            continue
        if choice == "3":
            print("[!] 警告：波点音乐可能只返回试听片段，建议使用其他平台。")
            confirm = input("是否继续？(y/N): ").strip().lower()
            if confirm == 'y':
                return PLATFORMS[choice]
            else:
                print("已取消，请重新选择。")
                continue
        else:
            return PLATFORMS[choice]
