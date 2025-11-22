from re import T
import win32gui
import win32con
import win32api
import win32process
import ctypes
import time
import psutil
from typing import Tuple, Optional, Union, List, Dict, Literal


class Controller:
    def __init__(self):
        self._foreground_window_cache = None
        self._window_list_cache = None
        self._cache_time = 0
        self._cache_ttl = 2  # 缓存有效期（秒）
        self.screen_size = (win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1))

    def boost_priority(self, pid=None):
        """提高当前进程或目标进程的优先级（增强版）"""
        try:
            if pid is None:
                pid = win32process.GetCurrentProcessId()
            
            process_handle = ctypes.windll.kernel32.OpenProcess(
                win32con.PROCESS_ALL_ACCESS, False, pid
            )
            
            # 设置为高优先级（谨慎使用）
            ctypes.windll.kernel32.SetPriorityClass(
                process_handle, win32con.HIGH_PRIORITY_CLASS
            )
            
            # 设置线程优先级为最高
            # 使用正确的线程访问权限常量
            THREAD_ALL_ACCESS = 0x1F03FF  # 标准线程所有访问权限
            thread_handle = ctypes.windll.kernel32.OpenThread(
                THREAD_ALL_ACCESS, False, win32api.GetCurrentThreadId()
            )
            ctypes.windll.kernel32.SetThreadPriority(
                thread_handle, win32con.THREAD_PRIORITY_HIGHEST
            )
            
            ctypes.windll.kernel32.CloseHandle(thread_handle)
            ctypes.windll.kernel32.CloseHandle(process_handle)
            
            print(f"成功提高进程 {pid} 的优先级（进程: HIGH_PRIORITY_CLASS, 线程: THREAD_PRIORITY_HIGHEST）")
            return True
        except Exception as e:
            print(f"提高优先级失败: {e}")
            return False
    
    def optimize_for_background(self):
        """优化后台运行性能"""
        try:
            # 设置进程为后台模式
            process_handle = ctypes.windll.kernel32.OpenProcess(
                win32con.PROCESS_ALL_ACCESS, False, win32process.GetCurrentProcessId()
            )
            
            # 使用标准的高优先级类，而不是不存在的后台模式常量
            ctypes.windll.kernel32.SetPriorityClass(
                process_handle, win32con.HIGH_PRIORITY_CLASS
            )
            
            ctypes.windll.kernel32.CloseHandle(process_handle)
            print("已优化为后台运行模式（使用高优先级）")
            return True
        except Exception as e:
            print(f"后台优化失败: {e}")
            return False

    def get_foreground_hwnd(self) -> Optional[int]:
        """
        获取当前前台窗口句柄
        
        :return: 当前前台窗口句柄，未找到返回None
        """
        hwnd = win32gui.GetForegroundWindow()
        if hwnd and win32gui.IsWindowVisible(hwnd):
            return hwnd
        return None

    def get_window_info(self, hwnd: int) -> Dict[str, any]:
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
                window_info = self.get_window_info(hwnd)
                if window_info:
                    windows.append(window_info)
            return True
        
        win32gui.EnumWindows(enum_windows_proc, None)
        
        # 更新缓存
        self._window_list_cache = windows
        self._cache_time = current_time
        
        return windows
    
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

    def get_cursor_position(self) -> Tuple[int, int]:
        """
        获取当前鼠标位置（屏幕坐标）
        
        :return: (x, y) 坐标元组
        """
        return win32api.GetCursorPos()

    def get_cursor_position_relative(self, hwnd: int) -> Tuple[int, int]:
        """
        获取当前鼠标相对于指定窗口的位置
        
        :param hwnd: 窗口句柄
        :return: (x, y) 窗口内相对坐标，如果不在窗口内返回(-1, -1)
        """
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

    def mouse_button(self):
        pass

    def mouse_move(self):
        pass

    def key(self):
        pass

    def type_keys(self):
        pass


class MessageController(Controller):
    def __init__(self) -> None:
        super().__init__()

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

    def mouse_button(self, hwnd: int, x: int, y: int, down: bool, button: str = 'left', relative_to_window: bool = True) -> bool:
        """
        使用窗口消息方法发送鼠标点击
        
        :param hwnd: 窗口句柄
        :param x: 点击位置的x坐标
        :param y: 点击位置的y坐标
        :param down: 是否按下鼠标按钮
        :param button: 鼠标按钮 'left', 'right', 'middle'
        :param relative_to_window: 坐标是否相对于窗口
        :return: 是否成功
        """
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
        
        message = win32con.WM_LBUTTONDOWN if down else win32con.WM_LBUTTONUP

        # 发送鼠标消息
        if button == 'left':
            win32gui.SendMessage(hwnd, message, win32con.MK_LBUTTON, point)
        elif button == 'right':
            win32gui.SendMessage(hwnd, message, win32con.MK_RBUTTON, point)
        elif button == 'middle':
            win32gui.SendMessage(hwnd, message, win32con.MK_MBUTTON, point)
        else:
            return False
        
        return True

    def mouse_move(self, hwnd: int, x: int, y: int, relative_to_window: bool = True) -> bool:
        """
        使用窗口消息方法移动鼠标（不实际移动物理鼠标）
        
        :param hwnd: 窗口句柄
        :param x: 目标位置的x坐标
        :param y: 目标位置的y坐标
        :param relative_to_window: 坐标是否相对于窗口
        :return: 是否成功
        """
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

    def key(self, hwnd: int, down: bool, virtual_key: int) -> bool:
        """
        发送按键
        
        :param hwnd: 窗口句柄
        :param down: 是否按下按键
        :param virtual_key: 虚拟键码（如win32con.VK_RETURN）
        :return: 是否成功
        """
        if not hwnd or not self.ensure_window_ready(hwnd):
            return False
        
        # 发送按键按下和释放消息
        if down:
            win32gui.SendMessage(hwnd, win32con.WM_KEYDOWN, virtual_key, 0)
        else:
            win32gui.SendMessage(hwnd, win32con.WM_KEYUP, virtual_key, 0)
        return True

    def type_keys(self, hwnd: int, text: str, delay: float = 0.01) -> bool:
        """
        向窗口发送按键（窗口消息方法）
        
        :param hwnd: 窗口句柄
        :param text: 要发送的文本
        :param delay: 按键间延迟（秒）
        :return: 是否成功
        """
        if not hwnd or not self.ensure_window_ready(hwnd):
            return False
        
        for char in text:
            win32gui.SendMessage(hwnd, win32con.WM_CHAR, ord(char), 0)
            time.sleep(delay)
        
        return True


class HardwareController(Controller):
    def __init__(self) -> None:
        super().__init__()
        self.user32 = ctypes.windll.user32

    def mouse_button(self, down: bool, button: str = 'left') -> bool:
        """
        在当前鼠标位置按下鼠标按钮
        
        :param down: 是否按下鼠标按钮
        :param button: 鼠标按钮 'left', 'right', 'middle'
        :return: 是否成功
        """
        try:
            if button == 'left':
                if down:
                    self.user32.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                else:
                    self.user32.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            elif button == 'right':
                if down:
                    self.user32.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                else:
                    self.user32.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            elif button == 'middle':
                if down:
                    self.user32.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
                else:
                    self.user32.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
            else:
                return False
            return True
        except Exception as e:
            print(f"鼠标按下操作失败: {e}")
            return False

    def mouse_move(self, x: int, y: int, duration: float = 0) -> bool:
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

    def key(self, down: bool, virtual_key: int) -> bool:
        """
        使用硬件模拟方法发送特殊按键
        
        :param down: 是否按下按键
        :param virtual_key: 虚拟键码
        :return: 是否成功
        """
        # 按下键
        if down:
            self.user32.keybd_event(virtual_key, 0, 0, 0)
        else:
            self.user32.keybd_event(virtual_key, 0, 2, 0)
        
        return True

    def type_keys(self, text: str, delay: float = 0.01) -> bool:
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

# 使用示例和测试代码
if __name__ == "__main__":
    # 创建控制器实例
    controller = BackgroundController()