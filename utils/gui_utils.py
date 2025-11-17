from re import T
from pyautogui import press, moveTo, size
import keyboard
from time import sleep


scale = 1
screen_size = size()
screen_size = (screen_size.width * scale, screen_size.height * scale)

# 向下滚动
def scroll_down():
    press("down")

def move_mouse(x, y):
    moveTo(x, y)

def wait_key(key, timeout=-1):
    start_time = time.time()
    while True:
        sleep(0.1)
        if keyboard.is_pressed(key):
            return True
        if timeout != -1 and time.time() - start_time >= timeout:
            return False


# background_controller.py
import win32gui
import win32con
import win32api
import ctypes
import time
import pyautogui
from typing import Tuple, Optional, Union

class BackgroundController:
    """
    Windows后台控制工具类
    整合了窗口消息发送和硬件级模拟两种方法
    """
    
    # 鼠标事件常量
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010
    MOUSEEVENTF_MIDDLEDOWN = 0x0020
    MOUSEEVENTF_MIDDLEUP = 0x0040
    MOUSEEVENTF_ABSOLUTE = 0x8000
    MOUSEEVENTF_MOVE = 0x0001
    
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.current_method = "message"  # 默认使用窗口消息方法
        
    def set_control_method(self, method: str):
        """
        设置控制方法
        
        :param method: "message" - 窗口消息方法（推荐，真正的后台）
                      "hardware" - 硬件模拟方法（兼容性更好）
        """
        if method in ["message", "hardware"]:
            self.current_method = method
        else:
            raise ValueError("方法必须是 'message' 或 'hardware'")
    
    def find_window(self, window_title: str) -> Optional[int]:
        """
        查找窗口句柄
        
        :param window_title: 窗口标题（支持部分匹配）
        :return: 窗口句柄，未找到返回None
        """
        # 精确匹配
        hwnd = win32gui.FindWindow(None, window_title)
        if hwnd:
            return hwnd
        
        # 部分匹配
        def enum_windows_proc(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if window_title.lower() in title.lower():
                    # 使用闭包返回结果
                    enum_windows_proc.found_hwnd = hwnd
                    return False  # 停止枚举
            return True
        
        enum_windows_proc.found_hwnd = None
        win32gui.EnumWindows(enum_windows_proc, None)
        
        return enum_windows_proc.found_hwnd
    
    def get_window_info(self, window_title: str) -> Optional[dict]:
        """
        获取窗口详细信息
        
        :param window_title: 窗口标题
        :return: 窗口信息字典，未找到返回None
        """
        hwnd = self.find_window(window_title)
        if not hwnd:
            return None
        
        rect = win32gui.GetWindowRect(hwnd)
        client_rect = win32gui.GetClientRect(hwnd)
        
        return {
            'handle': hwnd,
            'title': window_title,
            'position': (rect[0], rect[1]),
            'size': (rect[2] - rect[0], rect[3] - rect[1]),
            'client_size': (client_rect[2], client_rect[3]),
            'is_visible': win32gui.IsWindowVisible(hwnd),
            'is_minimized': win32gui.IsIconic(hwnd)
        }
    
    def ensure_window_ready(self, hwnd: int) -> bool:
        """
        确保窗口就绪（可见且未最小化）
        
        :param hwnd: 窗口句柄
        :return: 是否成功
        """
        if not hwnd:
            return False
        
        # 确保窗口可见
        if not win32gui.IsWindowVisible(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        
        # 确保窗口未最小化
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        
        return True
    
    def send_keystrokes(self, window_title: str, text: str, delay: float = 0.01) -> bool:
        """
        向窗口发送按键（窗口消息方法）
        
        :param window_title: 窗口标题
        :param text: 要发送的文本
        :param delay: 按键间延迟（秒）
        :return: 是否成功
        """
        hwnd = self.find_window(window_title)
        if not hwnd or not self.ensure_window_ready(hwnd):
            return False
        
        for char in text:
            win32gui.SendMessage(hwnd, win32con.WM_CHAR, ord(char), 0)
            time.sleep(delay)
        
        return True
    
    def send_special_key(self, window_title: str, virtual_key: int) -> bool:
        """
        发送特殊按键（如回车、Tab等）
        
        :param window_title: 窗口标题
        :param virtual_key: 虚拟键码（如win32con.VK_RETURN）
        :return: 是否成功
        """
        hwnd = self.find_window(window_title)
        if not hwnd or not self.ensure_window_ready(hwnd):
            return False
        
        # 发送按键按下和释放消息
        win32gui.SendMessage(hwnd, win32con.WM_KEYDOWN, virtual_key, 0)
        win32gui.SendMessage(hwnd, win32con.WM_KEYUP, virtual_key, 0)
        return True
    
    def send_mouse_click_message(self, window_title: str, x: int, y: int, 
                               button: str = 'left', relative_to_window: bool = True) -> bool:
        """
        使用窗口消息方法发送鼠标点击
        
        :param window_title: 窗口标题
        :param x: 点击位置的x坐标
        :param y: 点击位置的y坐标
        :param button: 鼠标按钮 'left', 'right', 'middle'
        :param relative_to_window: 坐标是否相对于窗口
        :return: 是否成功
        """
        hwnd = self.find_window(window_title)
        if not hwnd or not self.ensure_window_ready(hwnd):
            return False
        
        # 获取窗口位置和大小
        rect = win32gui.GetWindowRect(hwnd)
        window_x, window_y = rect[0], rect[1]
        
        # 转换坐标
        if relative_to_window:
            screen_x = window_x + x
            screen_y = window_y + y
        else:
            screen_x, screen_y = x, y
        
        # 确保坐标在窗口内
        if not (window_x <= screen_x <= rect[2] and window_y <= screen_y <= rect[3]):
            print(f"坐标({screen_x}, {screen_y})不在窗口区域内")
            return False
        
        # 将屏幕坐标转换为窗口客户区坐标
        point = win32api.MAKELONG(screen_x - window_x, screen_y - window_y)
        
        # 发送鼠标消息
        if button == 'left':
            win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, point)
            win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, point)
        elif button == 'right':
            win32gui.SendMessage(hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, point)
            win32gui.SendMessage(hwnd, win32con.WM_RBUTTONUP, 0, point)
        elif button == 'middle':
            win32gui.SendMessage(hwnd, win32con.WM_MBUTTONDOWN, win32con.MK_MBUTTON, point)
            win32gui.SendMessage(hwnd, win32con.WM_MBUTTONUP, 0, point)
        else:
            return False
        
        return True
    
    def send_mouse_double_click_message(self, window_title: str, x: int, y: int, 
                                      relative_to_window: bool = True) -> bool:
        """
        使用窗口消息方法发送鼠标双击
        
        :param window_title: 窗口标题
        :param x: 点击位置的x坐标
        :param y: 点击位置的y坐标
        :param relative_to_window: 坐标是否相对于窗口
        :return: 是否成功
        """
        hwnd = self.find_window(window_title)
        if not hwnd or not self.ensure_window_ready(hwnd):
            return False
        
        rect = win32gui.GetWindowRect(hwnd)
        window_x, window_y = rect[0], rect[1]
        
        if relative_to_window:
            screen_x = window_x + x
            screen_y = window_y + y
        else:
            screen_x, screen_y = x, y
        
        point = win32api.MAKELONG(screen_x - window_x, screen_y - window_y)
        
        # 发送双击消息
        win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, point)
        win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, point)
        win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, point)
        win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, point)
        win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDBLCLK, win32con.MK_LBUTTON, point)
        
        return True
    
    def mouse_click_hardware(self, x: int, y: int, button: str = 'left', 
                           double_click: bool = False, delay: float = 0.05) -> bool:
        """
        使用硬件模拟方法进行鼠标点击
        
        :param x: 屏幕x坐标
        :param y: 屏幕y坐标
        :param button: 鼠标按钮 'left', 'right', 'middle'
        :param double_click: 是否双击
        :param delay: 操作间延迟
        :return: 是否成功
        """
        # 设置鼠标位置
        self.user32.SetCursorPos(x, y)
        time.sleep(delay)
        
        # 执行点击
        if button == 'left':
            self.user32.mouse_event(self.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            self.user32.mouse_event(self.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            if double_click:
                time.sleep(0.1)
                self.user32.mouse_event(self.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                self.user32.mouse_event(self.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        elif button == 'right':
            self.user32.mouse_event(self.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            self.user32.mouse_event(self.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        elif button == 'middle':
            self.user32.mouse_event(self.MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
            self.user32.mouse_event(self.MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
        else:
            return False
        
        return True
    
    def mouse_click_hardware_relative(self, window_title: str, x: int, y: int, 
                                    button: str = 'left', double_click: bool = False) -> bool:
        """
        使用硬件模拟方法点击窗口内相对位置
        
        :param window_title: 窗口标题
        :param x: 窗口内x坐标
        :param y: 窗口内y坐标
        :param button: 鼠标按钮
        :param double_click: 是否双击
        :return: 是否成功
        """
        hwnd = self.find_window(window_title)
        if not hwnd:
            return False
        
        rect = win32gui.GetWindowRect(hwnd)
        window_x, window_y = rect[0], rect[1]
        
        # 计算屏幕绝对坐标
        screen_x = window_x + x
        screen_y = window_y + y
        
        return self.mouse_click_hardware(screen_x, screen_y, button, double_click)
    
    def mouse_drag_hardware(self, start_x: int, start_y: int, end_x: int, end_y: int, 
                          duration: float = 1.0) -> bool:
        """
        使用硬件模拟方法进行鼠标拖拽
        
        :param start_x: 起点x坐标
        :param start_y: 起点y坐标
        :param end_x: 终点x坐标
        :param end_y: 终点y坐标
        :param duration: 拖拽持续时间
        :return: 是否成功
        """
        # 移动到起点
        self.user32.SetCursorPos(start_x, start_y)
        time.sleep(0.1)
        
        # 按下鼠标左键
        self.user32.mouse_event(self.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.1)
        
        # 平滑移动到终点
        steps = max(1, int(duration * 10))  # 每0.1秒一步
        for i in range(steps + 1):
            t = i / steps
            current_x = int(start_x + (end_x - start_x) * t)
            current_y = int(start_y + (end_y - start_y) * t)
            self.user32.SetCursorPos(current_x, current_y)
            time.sleep(duration / steps)
        
        # 释放鼠标左键
        self.user32.mouse_event(self.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        return True
    
    def mouse_drag_hardware_relative(self, window_title: str, start_x: int, start_y: int, 
                                   end_x: int, end_y: int, duration: float = 1.0) -> bool:
        """
        在窗口内进行拖拽操作
        
        :param window_title: 窗口标题
        :param start_x: 起点x坐标（窗口内相对）
        :param start_y: 起点y坐标（窗口内相对）
        :param end_x: 终点x坐标（窗口内相对）
        :param end_y: 终点y坐标（窗口内相对）
        :param duration: 拖拽持续时间
        :return: 是否成功
        """
        hwnd = self.find_window(window_title)
        if not hwnd:
            return False
        
        rect = win32gui.GetWindowRect(hwnd)
        window_x, window_y = rect[0], rect[1]
        
        # 计算屏幕绝对坐标
        start_screen_x = window_x + start_x
        start_screen_y = window_y + start_y
        end_screen_x = window_x + end_x
        end_screen_y = window_y + end_y
        
        return self.mouse_drag_hardware(start_screen_x, start_screen_y, end_screen_x, end_screen_y, duration)
    
    def send_keys_hardware(self, text: str, delay: float = 0.01) -> bool:
        """
        使用硬件模拟方法发送按键
        
        :param text: 要发送的文本
        :param delay: 按键间延迟
        :return: 是否成功
        """
        for char in text:
            # 转换为虚拟键码
            vk_code = self.user32.VkKeyScanW(ord(char))
            
            # 按下键
            self.user32.keybd_event(vk_code & 0xFF, 0, 0, 0)
            time.sleep(delay)
            
            # 释放键
            self.user32.keybd_event(vk_code & 0xFF, 0, 2, 0)
            time.sleep(delay)
        
        return True
    
    def send_special_key_hardware(self, virtual_key: int) -> bool:
        """
        使用硬件模拟方法发送特殊按键
        
        :param virtual_key: 虚拟键码
        :return: 是否成功
        """
        # 按下键
        self.user32.keybd_event(virtual_key, 0, 0, 0)
        time.sleep(0.05)
        
        # 释放键
        self.user32.keybd_event(virtual_key, 0, 2, 0)
        return True
    
    # 统一接口方法
    def click(self, window_title: str, x: int, y: int, button: str = 'left', 
              double_click: bool = False, relative: bool = True) -> bool:
        """
        统一点击方法，根据当前设置的方法调用对应实现
        
        :param window_title: 窗口标题
        :param x: x坐标
        :param y: y坐标
        :param button: 鼠标按钮
        :param double_click: 是否双击
        :param relative: 坐标是否相对于窗口
        :return: 是否成功
        """
        if self.current_method == "message":
            if double_click:
                return self.send_mouse_double_click_message(window_title, x, y, relative)
            else:
                return self.send_mouse_click_message(window_title, x, y, button, relative)
        else:  # hardware
            if relative:
                return self.mouse_click_hardware_relative(window_title, x, y, button, double_click)
            else:
                return self.mouse_click_hardware(x, y, button, double_click)
    
    def type_text(self, window_title: str, text: str, delay: float = 0.01) -> bool:
        """
        统一文本输入方法
        
        :param window_title: 窗口标题
        :param text: 要输入的文本
        :param delay: 按键间延迟
        :return: 是否成功
        """
        if self.current_method == "message":
            return self.send_keystrokes(window_title, text, delay)
        else:  # hardware
            # 硬件方法需要先激活窗口
            hwnd = self.find_window(window_title)
            if hwnd:
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.1)
            return self.send_keys_hardware(text, delay)
    
    def press_key(self, window_title: str, virtual_key: int) -> bool:
        """
        统一按键方法
        
        :param window_title: 窗口标题
        :param virtual_key: 虚拟键码
        :return: 是否成功
        """
        if self.current_method == "message":
            return self.send_special_key(window_title, virtual_key)
        else:  # hardware
            # 硬件方法需要先激活窗口
            hwnd = self.find_window(window_title)
            if hwnd:
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.1)
            return self.send_special_key_hardware(virtual_key)
    
    def drag(self, window_title: str, start_x: int, start_y: int, 
             end_x: int, end_y: int, duration: float = 1.0, relative: bool = True) -> bool:
        """
        统一拖拽方法
        
        :param window_title: 窗口标题
        :param start_x: 起点x坐标
        :param start_y: 起点y坐标
        :param end_x: 终点x坐标
        :param end_y: 终点y坐标
        :param duration: 拖拽持续时间
        :param relative: 坐标是否相对于窗口
        :return: 是否成功
        """
        if self.current_method == "message":
            # 消息方法不支持拖拽，使用硬件方法
            if relative:
                return self.mouse_drag_hardware_relative(window_title, start_x, start_y, end_x, end_y, duration)
            else:
                return self.mouse_drag_hardware(start_x, start_y, end_x, end_y, duration)
        else:  # hardware
            if relative:
                return self.mouse_drag_hardware_relative(window_title, start_x, start_y, end_x, end_y, duration)
            else:
                return self.mouse_drag_hardware(start_x, start_y, end_x, end_y, duration)


# 使用示例
if __name__ == "__main__":
    # 创建控制器实例
    controller = BackgroundController()
    
    # 设置控制方法
    controller.set_control_method("message")  # 使用窗口消息方法（真正的后台控制）
    # controller.set_control_method("hardware")  # 使用硬件模拟方法
    
    # 获取窗口信息
    info = controller.get_window_info("记事本")
    if info:
        print(f"窗口信息: {info}")
        
        # 在窗口中心点击
        center_x = info['size'][0] // 2
        center_y = info['size'][1] // 2
        
        # 点击窗口中心
        controller.click("记事本", center_x, center_y, "left")
        
        # 输入文本
        controller.type_text("记事本", "这是通过后台控制输入的文本")
        
        # 按回车键
        controller.press_key("记事本", win32con.VK_RETURN)
        
        # 拖拽操作（仅在硬件模式下有效）
        controller.drag("记事本", 50, 50, 200, 200, 2.0)
    
    # 查找所有包含特定标题的窗口
    def list_windows(contains: str = ""):
        windows = []
        def enum_windows_proc(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and (not contains or contains.lower() in title.lower()):
                    windows.append((title, hwnd))
            return True
        
        win32gui.EnumWindows(enum_windows_proc, None)
        return windows
    
    # 列出所有可见窗口
    all_windows = list_windows()
    for title, hwnd in all_windows:
        print(f"窗口: {title}")