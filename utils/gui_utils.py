import time
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController
import pyautogui
from typing import Tuple, Optional, Union, List, Dict, Literal
from .logger import logger
import time


class GUIController:
    def __init__(self):
        logger.debug("初始化GUIController")
        self.screen_size = pyautogui.size()
        logger.info(f"屏幕尺寸: {self.screen_size}")
        self.mouse = MouseController()
        self.keyboard = KeyboardController()

    def get_cursor_position(self) -> Tuple[int, int]:
        """
        获取当前鼠标位置（屏幕坐标）
        
        :return: (x, y) 坐标元组
        """
        pos = self.mouse.position
        logger.debug(f"获取鼠标位置: {pos}")
        return pos

    def click(self, button: str = 'left', delay: float = 0.1) -> bool:
        """
        点击鼠标
        
        :param button: 鼠标按钮 'left', 'right', 'middle'
        :param delay: 点击间隔时间（秒）
        :return: 是否成功
        """
        logger.debug(f"执行鼠标点击，按钮: {button}, 延迟: {delay}")
        self.mouse_button(button, True)
        time.sleep(delay)
        self.mouse_button(button, False)
        logger.debug("鼠标点击完成")
        return True

    def mouse_button(self, button: Literal['left', 'right', 'middle'] = 'left', down: bool = True) -> bool:
        """
        使用窗口消息方法发送鼠标点击
        
        :param down: 是否按下鼠标按钮
        :param button: 鼠标按钮 'left', 'right', 'middle'
        :return: 是否成功
        """
        logger.debug(f"执行鼠标{'按下' if down else '释放'}，按钮: {button}")
        if down:
            self.mouse.press(Button[button])
        else:
            self.mouse.release(Button[button])
        return True

    def mouse_scroll(self, scroll_amount: int) -> bool:
        """
        鼠标滚动
        
        :param scroll_amount: 滚动量（正值向上滚动，负值向下滚动）
        :return: 是否成功
        """
        logger.debug(f"执行鼠标滚动，位置: ({x}, {y}), 滚动量: {scroll_amount}")
        pynput.mouse.scroll(0, scroll_amount)
        return True

    def mouse_move(self, x: int, y: int) -> bool:
        """
        使用窗口消息方法移动鼠标
        
        :param x: 目标位置的x坐标
        :param y: 目标位置的y坐标
        :return: 是否成功
        """
        logger.debug(f"执行鼠标移动，位置: ({x}, {y})")
        self.mouse.position = (x, y)
        return True

    def key(self, key: int, down: bool = True) -> bool:
        """
        使用窗口消息方法发送键盘事件
        
        :param down: 是否按下按键
        :param key: 按键
        :return: 是否成功
        """
        logger.debug(f"执行键盘{'按下' if down else '释放'}，按键码: {key}")
        if down:
            self.keyboard.press(key)
        else:
            self.keyboard.release(key)
        return True

    def type_keys(self, text: str, delay: float = 0.1) -> bool:
        """
        模拟输入文本
        
        :param text: 要输入的文本
        :param delay: 每个字符之间的延迟时间（秒）
        :return: 是否成功
        """
        logger.debug(f"执行模拟输入文本，文本: {text}, 延迟: {delay}")
        for char in text:
            self.key(ord(char), True)
            time.sleep(delay)
            self.key(ord(char), False)
        return True

# 使用示例和测试代码
if __name__ == "__main__":
    # 创建控制器实例
    controller = BackgroundController()