> 🎵 音乐直链获取工具 — tkinter 图形界面版

获取网易云音乐、咪咕音乐、波点音乐等平台的 **VIP 歌曲播放直链**，支持一键复制。

> **v2 架构**：从 Kivy 迁移到 Python 标准库 tkinter，零外部依赖，即装即用。见 [技术栈](#技术栈)。

---

## 特点

- 🖥️ **纯标准库 GUI** — 基于 tkinter（Python 内置），Windows / macOS / Linux 开箱即用，**原生中文输入法**
- 🎨 **深色主题** — 自定义配色 + ttk 深色滚动条（clam 主题），风格统一
- 📐 **固定窗口** — 500×700 禁止缩放，布局稳定
- 🎯 **多屏架构** — Welcome → Search → Result → History → Settings，Screen 基类 + 滚轮隔离
- 📋 **一键复制** — 获取链接后点击「复制」直接到剪贴板
- 📜 **历史记录** — 自动缓存（上限可配），超长文本自动截断，滚动条内容不足时自动隐藏
- 📌 **GUI 设置** — 搜索数量、超时、重试、DEBUG 开关均可可视化配置
- ⚠️ **平台标注** — 选择咪咕/波点时橙色提示成功率较低

---

## 平台支持

| 平台 | 搜索 | 直链接 | 建议 |
|------|:--:|:--:|------|
| 网易云音乐 | ✅ | ✅ | **首选**，直链获取最稳定 |
| 咪咕音乐 | ✅ | ⚠️ | 直链成功率较低，GUI 有橙色提示 |
| 波点音乐 | ✅ | ⚠️ | 可能只返回试听片段，GUI 有橙色提示 |

---

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

> tkinter 为 Python 标准库，Windows / macOS 已内置。
> Linux 若缺失：`sudo apt install python3-tk`

### 运行

```bash
cd getmusic
python main.py
```

### 操作

1. 欢迎页 → 点击「开始搜索」
2. 搜索页 → 选择平台 → 输入歌名/关键词 → 搜索
3. 结果页 → 浏览卡片 → 点击「获取链接」→ 链接展开显示前 30 字 → 点「复制」
4. 右上角可进入「历史记录」/「设置」

---

## 文件结构

```
getmusic/
├── core.py           # 核心：API 请求（含重试）、搜索、链接获取、缓存读写
├── gui.py            # tkinter UI：Welcome/Search/Result/History/Settings + 公用组件
├── main.py           # 入口：Tk 根窗口初始化
├── setting.json      # 用户配置（首次运行自动生成，.gitignore）
├── cache.json        # 获取历史（最多 max_cache 条，.gitignore）
├── requirements.txt  # 零外部依赖（纯 Python 标准库）
└── README.md
```

---

## 技术栈

| 组件 | 技术 |
|------|------|
| GUI | [tkinter](https://docs.python.org/3/library/tkinter.html)（Python 标准库） |
| 主题 | 纯手写 CSS-in-Python 深色主题 + ttk.Style(claw) 自定义滚动条 |
| 网络 | `urllib.request`（标准库） |
| 数据 | `json`（标准库） |
| 多线程 | `threading`（标准库，搜索不阻塞 UI） |
| Python | 3.8+（仅依赖标准库） |

> **为什么从 Kivy 切到 tkinter？**
> Kivy 在 Windows 下 IME 输入法兼容性差（中文无法输入），且需要额外安装 30MB+ 依赖。
> tkinter 随 Python 自带，原生支持系统输入法，零安装成本。

---

## 版本对比

| 功能 | `min-cmd` | `max-cmd` | **`max-gui`** |
|------|:--:|:--:|:--:|
| 搜索 + 获取直链 | ✅ | ✅ | ✅ |
| 多平台 | ✅ | ✅ | ✅ |
| 重试机制 | ❌ | ✅ | ✅ |
| DEBUG 模式 | `--debug` | 设置菜单 | **GUI 开关** |
| 历史/缓存 | ❌ | ✅ 自动保存 | ✅ 自动保存 |
| 设置界面 | ❌ | 交互式 CLI | **GUI 配置** |
| 配置文件 | ❌ | `setting.json` | `setting.json` |
| 图形界面 | ❌ | ❌ | **tkinter** |
| 一键复制 | ❌ | ❌ | ✅ |
| 深色主题 | ❌ | ❌ | ✅ |
| Toast 提示 | ❌ | ❌ | ✅ |
| 平台成功率标注 | ❌ | ❌ | ✅ |
| 固定窗口 | ❌ | ❌ | ✅ |
| 外部依赖 | 无 | 无 | **无** |
| 适合 | 脚本/学习 | 日常命令行 | **不喜欢终端** |

- [`min-cmd`](https://github.com/VZService/getmusic/tree/min-cmd)
- [`max-cmd`](https://github.com/VZService/getmusic/tree/max-cmd)
- **max-gui** ← 你在这里

```bash
git checkout min-cmd   # 精简命令行
git checkout max-cmd   # 完整命令行
git checkout max-gui   # 图形界面
```

---

## 设置项

| 配置项 | 默认值 | 说明 |
|--------|:--:|------|
| `default_num` | 10 | 单次搜索返回条数 |
| `timeout` | 10s | API 请求超时 |
| `max_retries` | 3 | 失败重试次数 |
| `retry_delay` | 1s | 重试间隔 |
| `max_cache` | 20 | 历史记录保留上限 |
| `debug_mode` | false | 开启后控制台输出完整 API 返回 JSON |

---

## 注意事项

- 仅供**学习交流**，音乐链接**有时效性**，失效后重新搜索即可
- 网易云音乐直链获取最稳定，**建议优先使用**
- 咪咕/波点 API 不稳定，GUI 选择时会有橙色提示
- 配置/缓存文件已加入 `.gitignore`，不会误提交
- **禁止商业用途**

---

## 许可

✅ 允许个人学习、研究、非商业用途下的使用、修改、复制、分发
❌ 禁止任何形式的商业用途
📜 修改后的衍生版本必须开源，并保留原始版权声明和作者信息

**GitHub**: [VZService/getmusic](https://github.com/VZService/getmusic)
