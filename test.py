from pynput.keyboard import Key, Controller as KeyController
from pynput.mouse import Button, Controller as MouseController
import time

keyboard = KeyController()
mouse = MouseController()
tqqtt
def press_key(key, duration=0.1):
    keyboard.press(key)
    time.sleep(duration)
    keyboard.release(key)

def click_at(x, y):
    # 移动鼠标并点击
    mouse.position = (x, y)
    time.sleep(0.1)
    mouse.click(Button.left)

# 使用示例
press_key('w', 2.0)  # 向前移动2秒
press_key(Key.space)  # 跳跃