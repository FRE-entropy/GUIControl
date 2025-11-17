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


import win32gui
import win32con
import win32api
import win32process
import ctypes
import time
import psutil
from typing import Tuple, Optional, Union, List, Dict

class BackgroundController:
    """
    Windows后台控制工具类 - 增强版
    支持自动获取当前聚焦窗口和进程信息
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
        self._foreground_window_cache = None
        self._window_list_cache = None
        self._cache_time = 0
        self._cache_ttl = 2  # 缓存有效期（秒）
    
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
    
    def get_foreground_window(self) -> Dict[str, any]:
        """
        获取当前聚焦窗口的详细信息
        
        :return: 窗口信息字典，包含句柄、标题、进程等信息
        """
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None
        
        return self.get_window_info_by_handle(hwnd)
    
    def get_window_info_by_handle(self, hwnd: int) -> Dict[str, any]:
        """
        通过窗口句柄获取窗口详细信息
        
        :param hwnd: 窗口句柄
        :return: 窗口信息字典
        """
        if not hwnd or not win32gui.IsWindow(hwnd):
            return None
        
        # 获取窗口标题
        title = win32gui.GetWindowText(hwnd)
        
        # 获取窗口位置和大小
        try:
            rect = win32gui.GetWindowRect(hwnd)
            client_rect = win32gui.GetClientRect(hwnd)
            
            # 获取窗口类名
            class_name = win32gui.GetClassName(hwnd)
            
            # 获取进程ID和进程名
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process_name = ""
            try:
                process = psutil.Process(pid)
                process_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                process_name = "Unknown"
            
            return {
                'handle': hwnd,
                'title': title,
                'class_name': class_name,
                'position': (rect[0], rect[1]),
                'size': (rect[2] - rect[0], rect[3] - rect[1]),
                'client_size': (client_rect[2], client_rect[3]),
                'is_visible': win32gui.IsWindowVisible(hwnd),
                'is_minimized': win32gui.IsIconic(hwnd),
                'is_foreground': hwnd == win32gui.GetForegroundWindow(),
                'process_id': pid,
                'process_name': process_name
            }
        except Exception as e:
            print(f"获取窗口信息失败: {e}")
            return None
    
    def find_window(self, window_title: str, exact_match: bool = False) -> Optional[int]:
        """
        查找窗口句柄
        
        :param window_title: 窗口标题（支持部分匹配）
        :param exact_match: 是否精确匹配标题
        :return: 窗口句柄，未找到返回None
        """
        # 精确匹配
        if exact_match:
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
    
    def find_windows_by_process(self, process_name: str) -> List[Dict[str, any]]:
        """
        根据进程名查找所有相关窗口
        
        :param process_name: 进程名（如notepad.exe）
        :return: 窗口信息列表
        """
        windows = []
        
        def enum_windows_proc(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    process = psutil.Process(pid)
                    if process.name().lower() == process_name.lower():
                        window_info = self.get_window_info_by_handle(hwnd)
                        if window_info:
                            windows.append(window_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return True
        
        win32gui.EnumWindows(enum_windows_proc, None)
        return windows
    
    def get_all_windows(self, force_refresh: bool = False) -> List[Dict[str, any]]:
        """
        获取所有可见窗口的详细信息
        
        :param force_refresh: 是否强制刷新缓存
        :return: 窗口信息列表
        """
        current_time = time.time()
        
        # 使用缓存提高性能
        if not force_refresh and self._window_list_cache and current_time - self._cache_time < self._cache_ttl:
            return self._window_list_cache
        
        windows = []
        
        def enum_windows_proc(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                window_info = self.get_window_info_by_handle(hwnd)
                if window_info:
                    windows.append(window_info)
            return True
        
        win32gui.EnumWindows(enum_windows_proc, None)
        
        # 更新缓存
        self._window_list_cache = windows
        self._cache_time = current_time
        
        return windows
    
    def get_window_info(self, window_title: str, exact_match: bool = False) -> Optional[dict]:
        """
        获取窗口详细信息
        
        :param window_title: 窗口标题
        :param exact_match: 是否精确匹配标题
        :return: 窗口信息字典，未找到返回None
        """
        hwnd = self.find_window(window_title, exact_match)
        if not hwnd:
            return None
        
        return self.get_window_info_by_handle(hwnd)
    
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

    def mouse_down_current_hardware(self, button: str = 'left'):
        """
        在当前鼠标位置按下鼠标按钮
        
        :param button: 鼠标按钮 'left', 'right', 'middle'
        :return: 是否成功
        """
        try:
            if button == 'left':
                self.user32.mouse_event(self.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            elif button == 'right':
                self.user32.mouse_event(self.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            elif button == 'middle':
                self.user32.mouse_event(self.MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
            else:
                return False
            return True
        except Exception as e:
            print(f"鼠标按下操作失败: {e}")
            return False

    def mouse_up_current_hardware(self, button: str = 'left'):
        """
        在当前鼠标位置抬起鼠标按钮
        
        :param button: 鼠标按钮 'left', 'right', 'middle'
        :return: 是否成功
        """
        try:
            if button == 'left':
                self.user32.mouse_event(self.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            elif button == 'right':
                self.user32.mouse_event(self.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            elif button == 'middle':
                self.user32.mouse_event(self.MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
            else:
                return False
            return True
        except Exception as e:
            print(f"鼠标抬起操作失败: {e}")
            return False

    def mouse_click_current_hardware(self, button: str = 'left', 
                           double_click: bool = False):
        """
        在当前鼠标位置执行鼠标点击
        
        :param button: 鼠标按钮 'left', 'right', 'middle'
        :param double_click: 是否双击
        :return: 是否成功
        """
        try:
            # 使用单独的按下和抬起方法
            if not self.mouse_down_current_hardware(button):
                return False
            
            time.sleep(0.05)  # 短暂延迟确保点击生效
            
            if not self.mouse_up_current_hardware(button):
                return False
            
            # 如果是双击，再执行一次点击
            if double_click:
                time.sleep(0.1)
                if not self.mouse_down_current_hardware(button):
                    return False
                time.sleep(0.05)
                if not self.mouse_up_current_hardware(button):
                    return False
            
            return True
        except Exception as e:
            print(f"鼠标点击操作失败: {e}")
            return False
    
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
        
        self.mouse_click_current_hardware(button, double_click)
        
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
        try:
            # 移动到起点
            self.user32.SetCursorPos(start_x, start_y)
            time.sleep(0.1)
            
            # 按下鼠标左键（使用新方法）
            if not self.mouse_down_current_hardware('left'):
                return False
            time.sleep(0.1)
            
            # 平滑移动到终点
            steps = max(1, int(duration * 10))  # 每0.1秒一步
            for i in range(steps + 1):
                t = i / steps
                current_x = int(start_x + (end_x - start_x) * t)
                current_y = int(start_y + (end_y - start_y) * t)
                self.user32.SetCursorPos(current_x, current_y)
                time.sleep(duration / steps)
            
            # 释放鼠标左键（使用新方法）
            if not self.mouse_up_current_hardware('left'):
                return False
            return True
        except Exception as e:
            print(f"鼠标拖拽操作失败: {e}")
            return False
    
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
    
    # 新增方法：自动控制当前聚焦窗口
    def click_foreground(self, x: int, y: int, button: str = 'left', 
                         double_click: bool = False, relative: bool = True) -> bool:
        """
        在当前聚焦窗口上点击
        
        :param x: x坐标
        :param y: y坐标
        :param button: 鼠标按钮
        :param double_click: 是否双击
        :param relative: 坐标是否相对于窗口
        :return: 是否成功
        """
        foreground_info = self.get_foreground_window()
        if not foreground_info:
            return False
        
        return self.click(foreground_info['title'], x, y, button, double_click, relative)
    
    def type_text_foreground(self, text: str, delay: float = 0.01) -> bool:
        """
        在当前聚焦窗口输入文本
        
        :param text: 要输入的文本
        :param delay: 按键间延迟
        :return: 是否成功
        """
        foreground_info = self.get_foreground_window()
        if not foreground_info:
            return False
        
        return self.type_text(foreground_info['title'], text, delay)
    
    def press_key_foreground(self, virtual_key: int) -> bool:
        """
        在当前聚焦窗口按特殊键
        
        :param virtual_key: 虚拟键码
        :return: 是否成功
        """
        foreground_info = self.get_foreground_window()
        if not foreground_info:
            return False
        
        return self.press_key(foreground_info['title'], virtual_key)
    
    def drag_foreground(self, start_x: int, start_y: int, 
                        end_x: int, end_y: int, duration: float = 1.0, relative: bool = True) -> bool:
        """
        在当前聚焦窗口进行拖拽操作
        
        :param start_x: 起点x坐标
        :param start_y: 起点y坐标
        :param end_x: 终点x坐标
        :param end_y: 终点y坐标
        :param duration: 拖拽持续时间
        :param relative: 坐标是否相对于窗口
        :return: 是否成功
        """
        foreground_info = self.get_foreground_window()
        if not foreground_info:
            return False
        
        return self.drag(foreground_info['title'], start_x, start_y, end_x, end_y, duration, relative)
    
    def send_mouse_move_message(self, window_title: str, x: int, y: int, 
                          relative_to_window: bool = True) -> bool:
        """
        使用窗口消息方法移动鼠标（不实际移动物理鼠标）
        
        :param window_title: 窗口标题
        :param x: 目标位置的x坐标
        :param y: 目标位置的y坐标
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
        
        # 发送鼠标移动消息
        win32gui.SendMessage(hwnd, win32con.WM_MOUSEMOVE, 0, point)
        return True

    def mouse_move_hardware(self, x: int, y: int, duration: float = 0) -> bool:
        """
        使用硬件模拟方法移动鼠标（实际移动物理鼠标指针）
        
        :param x: 目标x坐标（屏幕绝对坐标）
        :param y: 目标y坐标（屏幕绝对坐标）
        :param duration: 移动持续时间（秒），0表示立即移动
        :return: 是否成功
        """
        if duration <= 0:
            # 立即移动
            self.user32.SetCursorPos(x, y)
            return True
        
        # 平滑移动
        current_x, current_y = win32api.GetCursorPos()
        steps = max(1, int(duration * 60))  # 每秒60帧
        
        for i in range(steps + 1):
            t = i / steps
            # 使用缓动函数使移动更自然
            # ease_out_quad: t*(2-t)
            eased_t = t * (2 - t)
            current_step_x = int(current_x + (x - current_x) * eased_t)
            current_step_y = int(current_y + (y - current_y) * eased_t)
            
            self.user32.SetCursorPos(current_step_x, current_step_y)
            time.sleep(duration / steps)
        
        return True

    def mouse_move_hardware_relative(self, window_title: str, x: int, y: int, 
                                duration: float = 0) -> bool:
        """
        使用硬件模拟方法移动鼠标到窗口内相对位置
        
        :param window_title: 窗口标题
        :param x: 窗口内x坐标
        :param y: 窗口内y坐标
        :param duration: 移动持续时间（秒）
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
        
        return self.mouse_move_hardware(screen_x, screen_y, duration)

    def mouse_move_relative(self, delta_x: int, delta_y: int, duration: float = 0) -> bool:
        """
        相对于当前位置移动鼠标
        
        :param delta_x: x方向移动距离
        :param delta_y: y方向移动距离
        :param duration: 移动持续时间（秒）
        :return: 是否成功
        """
        current_x, current_y = win32api.GetCursorPos()
        target_x = current_x + delta_x
        target_y = current_y + delta_y
        
        return self.mouse_move_hardware(target_x, target_y, duration)

    def get_cursor_position(self) -> Tuple[int, int]:
        """
        获取当前鼠标位置（屏幕坐标）
        
        :return: (x, y) 坐标元组
        """
        return win32api.GetCursorPos()

    def get_cursor_position_relative(self, window_title: str) -> Tuple[int, int]:
        """
        获取当前鼠标相对于指定窗口的位置
        
        :param window_title: 窗口标题
        :return: (x, y) 窗口内相对坐标，如果不在窗口内返回(-1, -1)
        """
        hwnd = self.find_window(window_title)
        if not hwnd:
            return -1, -1
        
        # 获取窗口位置
        rect = win32gui.GetWindowRect(hwnd)
        window_x, window_y = rect[0], rect[1]
        
        # 获取当前鼠标位置
        screen_x, screen_y = self.get_cursor_position()
        
        # 计算相对坐标
        relative_x = screen_x - window_x
        relative_y = screen_y - window_y
        
        # 检查是否在窗口内
        if (0 <= relative_x <= rect[2] - rect[0] and 
            0 <= relative_y <= rect[3] - rect[1]):
            return relative_x, relative_y
        else:
            return -1, -1

    # 添加到统一接口方法
    def move(self, window_title: str, x: int, y: int, 
            duration: float = 0, relative: bool = True) -> bool:
        """
        统一鼠标移动方法，根据当前设置的方法调用对应实现
        
        :param window_title: 窗口标题
        :param x: x坐标
        :param y: y坐标
        :param duration: 移动持续时间（仅硬件方法有效）
        :param relative: 坐标是否相对于窗口
        :return: 是否成功
        """
        if self.current_method == "message":
            return self.send_mouse_move_message(window_title, x, y, relative)
        else:  # hardware
            if relative:
                return self.mouse_move_hardware_relative(window_title, x, y, duration)
            else:
                return self.mouse_move_hardware(x, y, duration)

    def move_foreground(self, x: int, y: int, 
                    duration: float = 0, relative: bool = True) -> bool:
        """
        在当前聚焦窗口移动鼠标
        
        :param x: x坐标
        :param y: y坐标
        :param duration: 移动持续时间（仅硬件方法有效）
        :param relative: 坐标是否相对于窗口
        :return: 是否成功
        """
        foreground_info = self.get_foreground_window()
        if not foreground_info:
            return False
        
        return self.move(foreground_info['title'], x, y, duration, relative)

    # 添加鼠标悬停方法
    def hover(self, window_title: str, x: int, y: int, 
            hover_time: float = 1.0, relative: bool = True) -> bool:
        """
        鼠标悬停在指定位置
        
        :param window_title: 窗口标题
        :param x: x坐标
        :param y: y坐标
        :param hover_time: 悬停时间（秒）
        :param relative: 坐标是否相对于窗口
        :return: 是否成功
        """
        # 先移动鼠标
        if not self.move(window_title, x, y, 0.5, relative):
            return False
        
        # 悬停指定时间
        time.sleep(hover_time)
        return True

    def hover_foreground(self, x: int, y: int, 
                        hover_time: float = 1.0, relative: bool = True) -> bool:
        """
        在当前聚焦窗口悬停鼠标
        
        :param x: x坐标
        :param y: y坐标
        :param hover_time: 悬停时间（秒）
        :param relative: 坐标是否相对于窗口
        :return: 是否成功
        """
        foreground_info = self.get_foreground_window()
        if not foreground_info:
            return False
        
        return self.hover(foreground_info['title'], x, y, hover_time, relative)

    # 添加鼠标移动轨迹方法
    def move_along_path(self, points: List[Tuple[int, int]], 
                    duration: float = 1.0, relative_to_window: bool = False,
                    window_title: str = None) -> bool:
        """
        沿着路径移动鼠标
        
        :param points: 路径点列表，每个点是(x, y)元组
        :param duration: 总移动时间（秒）
        :param relative_to_window: 点坐标是否相对于窗口
        :param window_title: 窗口标题（如果使用相对坐标）
        :return: 是否成功
        """
        if not points:
            return False
        
        # 如果使用窗口相对坐标，需要转换为屏幕坐标
        if relative_to_window and window_title:
            hwnd = self.find_window(window_title)
            if not hwnd:
                return False
            
            rect = win32gui.GetWindowRect(hwnd)
            window_x, window_y = rect[0], rect[1]
            
            screen_points = []
            for x, y in points:
                screen_x = window_x + x
                screen_y = window_y + y
                screen_points.append((screen_x, screen_y))
            
            points = screen_points
        
        # 计算每段路径的时间
        segment_duration = duration / len(points)
        
        # 移动到第一个点
        self.mouse_move_hardware(points[0][0], points[0][1], segment_duration)
        
        # 移动到后续点
        for i in range(1, len(points)):
            self.mouse_move_hardware(points[i][0], points[i][1], segment_duration)
        
        return True

    # 添加鼠标移动和点击的组合方法
    def move_and_click(self, window_title: str, x: int, y: int, 
                    button: str = 'left', move_duration: float = 0.5,
                    click_delay: float = 0.1, relative: bool = True) -> bool:
        """
        移动鼠标到指定位置并点击
        
        :param window_title: 窗口标题
        :param x: x坐标
        :param y: y坐标
        :param button: 鼠标按钮
        :param move_duration: 移动持续时间
        :param click_delay: 点击前延迟
        :param relative: 坐标是否相对于窗口
        :return: 是否成功
        """
        # 移动鼠标
        if not self.move(window_title, x, y, move_duration, relative):
            return False
        
        # 点击前短暂延迟
        time.sleep(click_delay)
        
        # 执行点击
        return self.click(window_title, x, y, button, False, relative)

    def move_and_click_foreground(self, x: int, y: int, 
                                button: str = 'left', move_duration: float = 0.5,
                                click_delay: float = 0.1, relative: bool = True) -> bool:
        """
        在当前聚焦窗口移动鼠标到指定位置并点击
        
        :param x: x坐标
        :param y: y坐标
        :param button: 鼠标按钮
        :param move_duration: 移动持续时间
        :param click_delay: 点击前延迟
        :param relative: 坐标是否相对于窗口
        :return: 是否成功
        """
        foreground_info = self.get_foreground_window()
        if not foreground_info:
            return False
        
        return self.move_and_click(foreground_info['title'], x, y, button, 
                                move_duration, click_delay, relative)


# 使用示例和测试代码
if __name__ == "__main__":
    # 创建控制器实例
    controller = BackgroundController()
    
    # 设置控制方法
    controller.set_control_method("message")  # 使用窗口消息方法（真正的后台控制）
    
    # 1. 获取当前聚焦窗口信息
    foreground = controller.get_foreground_window()
    if foreground:
        print("当前聚焦窗口:")
        for key, value in foreground.items():
            print(f"  {key}: {value}")
        print()
    
    # 2. 获取所有可见窗口
    all_windows = controller.get_all_windows()
    print(f"发现 {len(all_windows)} 个可见窗口:")
    for i, window in enumerate(all_windows[:5]):  # 只显示前5个
        print(f"  {i+1}. {window['title']} (PID: {window['process_id']})")
    if len(all_windows) > 5:
        print("  ...")
    print()
    
    # 3. 根据进程名查找窗口
    notepad_windows = controller.find_windows_by_process("notepad.exe")
    print(f"找到 {len(notepad_windows)} 个记事本窗口:")
    for window in notepad_windows:
        print(f"  - {window['title']}")
    print()
    
    # 4. 在当前聚焦窗口执行操作（如果找到记事本窗口）
    if notepad_windows:
        # 使用第一个记事本窗口
        notepad_window = notepad_windows[0]
        print(f"将对记事本窗口执行操作: {notepad_window['title']}")
        
        # 点击窗口中心
        center_x = notepad_window['size'][0] // 2
        center_y = notepad_window['size'][1] // 2
        controller.click(notepad_window['title'], center_x, center_y)
        
        # 输入文本
        controller.type_text(notepad_window['title'], "这是通过后台控制输入的文本")
        
        # 按回车键
        controller.press_key(notepad_window['title'], win32con.VK_RETURN)
        
        print("操作完成!")
    
    # 5. 自动控制当前聚焦窗口
    print("等待5秒，请切换到目标窗口...")
    time.sleep(5)
    
    foreground = controller.get_foreground_window()
    if foreground:
        print(f"当前聚焦窗口: {foreground['title']}")
        
        # 在当前聚焦窗口中心点击
        center_x = foreground['size'][0] // 2
        center_y = foreground['size'][1] // 2
        controller.click_foreground(center_x, center_y)
        
        # 输入文本
        controller.type_text_foreground("这是在当前窗口输入的文本")
        
        print("当前窗口操作完成!")