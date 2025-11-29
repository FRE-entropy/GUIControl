import sys
from cx_Freeze import setup, Executable
import os

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 定义构建选项
build_exe_options = {
    "packages": ["mido", "pygetwindow", "tkinter", "keyboard", "loguru", "pynput"],
    "includes": ["pynput.keyboard._win32", "pynput.mouse._win32", "pynput._util.win32"],
    "excludes": [],
    "include_files": [
        (os.path.join(current_dir, "utils"), "utils"),
    ],
    "include_msvcr": True,
    "bin_includes": ["user32.dll", "kernel32.dll", "advapi32.dll"],
}

# 定义执行文件
base = "Win32GUI" if sys.platform == "win32" else None

# 要打包的主程序
executables = [
    Executable(
        script=os.path.join(current_dir, "GenshinImpactControl", "main.py"),
        base=base,
        target_name="GenshinImpactMusicPlayer.exe",
        icon=None,
    )
]

# 执行setup
setup(
    name="GenshinImpactMusicPlayer",
    version="0.1",
    description="Genshin Impact Music Player",
    options={"build_exe": build_exe_options},
    executables=executables,
)
