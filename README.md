> 🎵 图形界面音乐获取工具 — 基于 Kivy，跨平台 GUI，深色主题

获取网易云音乐、咪咕音乐、波点音乐等平台的**音乐直链**。

## 特点

- 🖥️ **图形界面** — 基于 [Kivy](https://kivy.org/) 框架，Windows / macOS / Linux / Android 通用
- 🎨 **深色主题** — 卡片式布局，Toast 提示，Toggle 开关
- 🎯 **三屏流程** — 欢迎页 → 搜索页 → 结果页，清晰直观
- 📋 **一键复制** — 获取链接后直接复制到剪贴板
- 📜 **历史记录** — 自动缓存搜索记录，可回查
- 📌 **设置面板** — 搜索数量、超时、重试、DEBUG 模式均可在 GUI 中配置

## 使用方法

### 安装依赖

```
pip install -r requirements.txt
```

或直接：

```
pip install kivy>=2.3.0
```

### 运行

```
python main.py
```

### 操作流程

1. **欢迎页** — 点击「开始搜索」进入
2. **搜索页** — 选择平台（Toggle 单选） → 输入关键词 → 点击搜索
3. **结果页** — 浏览结果 → 点击「获取链接」 → 点击「📋 复制」→ 浏览器打开

## 文件结构

```
max-gui/
├── core.py              # 核心逻辑（API请求、搜索、获取链接、缓存）
├── gui.py               # Kivy UI（Welcome/Search/Result/Settings/History）
├── main.py              # Kivy App 入口
├── data/
│   └── chinesefont.ttf  # 中文字体（解决中文乱码，可选）
├── setting.json         # 用户配置（首次运行自动生成）
├── cache.json           # 历史缓存（自动保存）
├── requirements.txt     # Python 依赖清单
└── README.md            # 本文件
```

## 技术栈

| 组件     | 技术                             |
|--------|--------------------------------|
| GUI 框架 | [Kivy](https://kivy.org/) 2.3+ (最低 2.3.0) |
| Python 版本 | 3.8+ |
| 网络请求   | Python 标准库 `urllib`            |
| 数据解析   | Python 标准库 `json`              |

## 📦 各版本对比

| 功能            |   `min-cmd`    |    `max-cmd`     | **`max-gui`（本分支）** |
|---------------|:--------------:|:----------------:|:------------------:|
| **搜索 + 获取直链** |       ✅        |        ✅         |         ✅          |
| **多平台支持**     |       ✅        |        ✅         |         ✅          |
| **开源水印**      |       ✅        |        ✅         |         ✅          |
| **DEBUG 模式**  | ✅ `--debug` 参数 |     ✅ 设置菜单开关     |    ✅ GUI 开关       |
| **彩色终端输出**    |       ❌        |      ✅ 可开关       |      — (GUI)       |
| **历史记录/缓存**   |       ❌        |      ✅ 自动保存      |    ✅ 自动保存        |
| **设置界面**      |       ❌        |     ✅ 交互式配置      |    ✅ GUI 配置        |
| **配置文件**      |      ❌ 无       | ✅ `setting.json` |   ✅ `setting.json`  |
| **GUI 图形界面**  |       ❌        |        ❌         |     ✅ **Kivy**     |
| **复制链接**      |     ❌ 手动复制     |      ❌ 手动复制      |     ✅ **一键复制**     |
| **深色主题**      |       ❌        |        ❌         |     ✅               |
| **Toast 提示**   |       ❌        |        ❌         |     ✅               |
| **外部依赖**      |       无        |        无         |      **Kivy**      |
| **适合场景**      |    嵌入脚本/学习     |      日常命令行       |      不喜欢终端的用户      |

**怎么选？**
- 想要**最简单快速**的体验 → [`min-cmd`](https://github.com/VZqwq/getmusic/tree/min-cmd)
- 想要**功能完整**的命令行工具 → [`max-cmd`](https://github.com/VZqwq/getmusic/tree/max-cmd)
- 想要**图形界面** → **max-gui** ← 你在这里

```
git checkout min-cmd    # 精简版命令行
git checkout max-cmd    # 完整版命令行
git checkout max-gui    # 图形界面版
```

## ⚠️ 注意事项

- 本工具**仅供学习交流**，获取的音乐链接**有时效性**
- 音乐链接会过期，失效后重新搜索即可
- 波点音乐可能只返回试听片段，建议优先使用其他平台
- **禁止商业用途**

## 许可证

✅ 允许个人学习、研究、非商业用途下的使用、修改、复制、分发  
❌ 禁止任何形式的商业用途  
📜 修改后的衍生版本必须开源，并保留原始版权声明和作者信息

**作者 QQ**: 535595887  
**GitHub**: [VZqwq/getmusic](https://github.com/VZqwq/getmusic)
