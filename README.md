# GUIControl - 游戏与手势交互控制工具集合

这是一个包含多个GUI交互控制工具的项目集合，旨在提供游戏辅助和手势控制等功能。

## 项目目录

### 1. [原神弹琴器](GenshinImpactControl/README.md)

一个用于在原神游戏中自动弹奏音乐的工具，可以播放MIDI文件，让你在游戏中轻松演奏美妙的音乐。

**主要功能：**
- MIDI文件播放
- 键盘映射控制
- 可调节播放速度
- 热键中断控制

### 2. [手势鼠标控制](GestureMouseControl/README.md)

通过手势识别来控制鼠标操作的工具，支持多种手势识别和鼠标控制功能。

**主要功能：**
- 手势识别
- 鼠标移动控制
- 点击和拖拽操作
- 手势自定义配置

## 项目结构

```
GUIControl/
├── GenshinImpactControl/  # 原神弹琴器
├── GestureMouseControl/   # 手势鼠标控制
├── utils/                 # 共享工具函数
├── pyproject.toml         # 项目配置文件
├── uv.lock                # 依赖版本锁定文件
├── .gitignore             # Git忽略文件
├── .python-version        # Python版本指定
├── test.py                # 测试文件
└── README.md              # 主项目文档（当前文件）
```

## 安装说明

### 前置条件

- Python 3.7+
- 依赖管理：支持pip或uv包管理器

### 全局安装

```bash
# 使用pip安装
pip install -e .

# 或使用uv安装
uv sync
```

## 工具说明

### 共享工具模块

项目中的`utils`目录包含了所有子项目共享的工具函数：

- **gui_utils.py**: GUI交互控制工具，提供键盘和鼠标操作
- **hgr_utils.py**: 手势识别相关工具函数
- **logger.py**: 日志管理工具

## 使用指南

请点击上方的链接查看各个子项目的详细使用说明：

1. [原神弹琴器详细说明](GenshinImpactControl/README.md)
2. [手势鼠标控制详细说明](GestureMouseControl/README.md)

## 注意事项

1. 本项目中的工具仅供学习和研究使用
2. 使用游戏相关工具时，请遵守游戏的用户协议
3. 手势控制功能可能需要摄像头或其他输入设备

## 更新日志

### v1.0
- 初始版本
- 包含原神弹琴器和手势鼠标控制两个主要工具
- 实现基础功能和共享工具模块

## 联系方式

如有问题或建议，请通过项目Issue页面提交反馈。
QQ: 2655998023