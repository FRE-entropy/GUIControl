import win32gui
import win32con
import win32api
import win32process
import ctypes
import time
import psutil
import pynput
from typing import Tuple, Optional, Union, List, Dict, Literal
from .logger import logger


class GUIController:
    def __init__(self):
        logger.debug("初始化GUIController")
        self.screen_size = (win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1))
        self.VK_const = win32con
        logger.info(f"屏幕尺寸: {self.screen_size}")

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
            
            logger.info(f"成功提高进程 {pid} 的优先级（进程: HIGH_PRIORITY_CLASS, 线程: THREAD_PRIORITY_HIGHEST）")
            return True
        except Exception as e:
            logger.error(f"提高优先级失败: {e}")
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
            logger.info("已优化为后台运行模式（使用高优先级）")
            return True
        except Exception as e:
            logger.error(f"后台优化失败: {e}")
            return False

    def get_foreground_hwnd(self) -> Optional[int]:
        """
        获取当前前台窗口句柄
        
        :return: 当前前台窗口句柄，未找到返回None
        """
        logger.debug("获取前台窗口句柄")
        hwnd = win32gui.GetForegroundWindow()
        if hwnd and win32gui.IsWindowVisible(hwnd):
            logger.debug(f"找到前台窗口句柄: {hwnd}")
            return hwnd
        logger.debug("未找到可见的前台窗口")
        return None

    def get_window_info(self, hwnd: int) -> Dict[str, any]:
        """
        通过窗口句柄获取窗口详细信息
        
        :param hwnd: 窗口句柄
        :return: 窗口信息字典
        """
        logger.debug(f"获取窗口信息，句柄: {hwnd}")
        if not hwnd or not win32gui.IsWindow(hwnd):
            logger.warning(f"无效的窗口句柄: {hwnd}")
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
            logger.error(f"获取窗口信息失败: {e}")
            return None
  
    def find_window(self, window_title: str, exact_match: bool = False) -> Optional[int]:
        """
        查找窗口句柄
        
        :param window_title: 窗口标题（支持部分匹配）
        :param exact_match: 是否精确匹配标题
        :return: 窗口句柄，未找到返回None
        """
        logger.debug(f"查找窗口，标题: '{window_title}', 精确匹配: {exact_match}")
        # 精确匹配
        if exact_match:
            hwnd = win32gui.FindWindow(None, window_title)
            if hwnd:
                logger.debug(f"精确匹配找到窗口句柄: {hwnd}")
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
        
        if enum_windows_proc.found_hwnd:
            logger.debug(f"部分匹配找到窗口句柄: {enum_windows_proc.found_hwnd}")
        else:
            logger.debug(f"未找到匹配标题 '{window_title}' 的窗口")
        
        return enum_windows_proc.found_hwnd

    def find_windows_by_process(self, process_name: str) -> List[Dict[str, any]]:
        """
        根据进程名查找所有相关窗口
        
        :param process_name: 进程名（如notepad.exe）
        :return: 窗口信息列表
        """
        logger.debug(f"根据进程名查找窗口: {process_name}")
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
        logger.debug(f"找到 {len(windows)} 个与进程 '{process_name}' 相关的窗口")
        return windows
    
    def get_all_windows(self, force_refresh: bool = False) -> List[Dict[str, any]]:
        """
        获取所有可见窗口的详细信息
        
        :param force_refresh: 是否强制刷新缓存
        :return: 窗口信息列表
        """
        logger.debug(f"获取所有可见窗口，强制刷新: {force_refresh}")
        current_time = time.time()
        
        # 使用缓存提高性能
        if not force_refresh and self._window_list_cache and current_time - self._cache_time < self._cache_ttl:
            logger.debug(f"使用缓存，返回 {len(self._window_list_cache)} 个窗口")
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
        
        logger.debug(f"枚举完成，找到 {len(windows)} 个可见窗口")
        return windows
    
    def ensure_window_ready(self, hwnd: int) -> bool:
        """
        确保窗口就绪（可见且未最小化）
        
        :param hwnd: 窗口句柄
        :return: 是否成功
        """
        logger.debug(f"确保窗口就绪，句柄: {hwnd}")
        if not hwnd:
            logger.warning("无效的窗口句柄")
            return False
        
        # 确保窗口可见
        if not win32gui.IsWindowVisible(hwnd):
            logger.debug("窗口不可见，显示窗口")
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        
        # 确保窗口未最小化
        if win32gui.IsIconic(hwnd):
            logger.debug("窗口最小化，恢复窗口")
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        
        logger.debug("窗口已就绪")
        return True

    def get_cursor_position(self) -> Tuple[int, int]:
        """
        获取当前鼠标位置（屏幕坐标）
        
        :return: (x, y) 坐标元组
        """
        pos = win32api.GetCursorPos()
        logger.debug(f"获取鼠标位置: {pos}")
        return pos

    def get_cursor_position_relative(self, hwnd: int) -> Tuple[int, int]:
        """
        获取当前鼠标相对于指定窗口的位置
        
        :param hwnd: 窗口句柄
        :return: (x, y) 窗口内相对坐标，如果不在窗口内返回(-1, -1)
        """
        logger.debug(f"获取鼠标相对于窗口 {hwnd} 的相对位置")
        if not hwnd:
            logger.warning("无效的窗口句柄")
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
            logger.debug(f"鼠标在窗口内，相对位置: ({relative_x}, {relative_y})")
            return relative_x, relative_y
        else:
            logger.debug(f"鼠标不在窗口内，相对位置: ({relative_x}, {relative_y})")
            return -1, -1

    def click(self, x: int, y: int, button: str = 'left', delay: float = 0.1) -> bool:
        """
        点击鼠标
        
        :param x: 点击位置的x坐标
        :param y: 点击位置的y坐标
        :param button: 鼠标按钮 'left', 'right', 'middle'
        :param delay: 点击间隔时间（秒）
        :return: 是否成功
        """
        logger.debug(f"执行鼠标点击，位置: ({x}, {y}), 按钮: {button}, 延迟: {delay}")
        self.mouse_button(x, y, True, button)
        time.sleep(delay)
        self.mouse_button(x, y, False, button)
        logger.debug("鼠标点击完成")
        return True

    # --------------------------------------------------------------------------------------
    def mouse_button(self, x: int, y: int, down: bool, button: Literal['left', 'right', 'middle'] = 'left') -> bool:
        """
        使用窗口消息方法发送鼠标点击
        
        :param x: 点击位置的x坐标
        :param y: 点击位置的y坐标
        :param down: 是否按下鼠标按钮
        :param button: 鼠标按钮 'left', 'right', 'middle'
        :return: 是否成功
        """
        pass

    def mouse_scroll(self, x: int, y: int, scroll_amount: int) -> bool:
        """
        鼠标滚动
        
        :param x: 滚动位置的x坐标
        :param y: 滚动位置的y坐标
        :param scroll_amount: 滚动量（正值向上滚动，负值向下滚动）
        :return: 是否成功
        """
        pass

    def mouse_move(self, x: int, y: int) -> bool:
        """
        使用窗口消息方法移动鼠标
        
        :param x: 目标位置的x坐标
        :param y: 目标位置的y坐标
        :return: 是否成功
        """
        pass

    def key(self, virtual_key: int, down: bool = True) -> bool:
        """
        使用窗口消息方法发送键盘事件
        
        :param down: 是否按下按键
        :param virtual_key: 虚拟按键码（如 win32con.VK_A, win32con.VK_F1, win32con.VK_LEFT）
        :return: 是否成功
        """
        pass

    def type_keys(self, text: str, delay: float = 0.1) -> bool:
        """
        模拟输入文本
        
        :param text: 要输入的文本
        :param delay: 每个字符之间的延迟时间（秒）
        :return: 是否成功
        """
        pass


class MessageController(GUIController):
    def __init__(self) -> None:
        super().__init__()
        self.hwnd = self.get_foreground_hwnd()
        logger.debug(f"MessageController初始化完成，当前窗口句柄: {self.hwnd}")

    def set_hwnd(self, hwnd: int) -> bool:
        """
        设置当前操作的窗口句柄
        
        :param hwnd: 窗口句柄
        :return: 是否成功
        """
        logger.debug(f"设置窗口句柄: {hwnd}")
        if not hwnd or not self.ensure_window_ready(hwnd):
            logger.warning(f"无法设置窗口句柄: {hwnd}")
            return False
        self.hwnd = hwnd
        logger.debug(f"窗口句柄设置成功: {hwnd}")
        return True

    def set_hwnd_foreground(self) -> bool:
        """
        设置当前操作的窗口句柄为前台窗口
        
        :return: 是否成功
        """
        logger.debug("设置当前窗口句柄为前台窗口")
        foreground_hwnd = self.get_foreground_hwnd()
        if not self.set_hwnd(foreground_hwnd):
            logger.warning("无法设置前台窗口句柄")
            return False
        logger.debug(f"前台窗口句柄设置成功: {foreground_hwnd}")
        return True

    def mouse_button(self, x: int, y: int, down: bool, button: Literal['left', 'right', 'middle'] = 'left') -> bool:
        """
        使用窗口消息方法发送鼠标点击
        
        :param x: 点击位置的x坐标
        :param y: 点击位置的y坐标
        :param down: 是否按下鼠标按钮
        :param button: 鼠标按钮 'left', 'right', 'middle'
        :return: 是否成功
        """
        logger.debug(f"发送鼠标按钮事件，位置: ({x}, {y}), 按钮: {button}, 按下: {down}")
        if not self.hwnd or not self.ensure_window_ready(self.hwnd):
            logger.warning("窗口未就绪，无法发送鼠标按钮事件")
            return False
        
        # 获取窗口位置和大小
        rect = win32gui.GetWindowRect(self.hwnd)
        window_x, window_y = rect[0], rect[1]
        
        # 确保坐标在窗口内
        if not (window_x <= x <= rect[2] and window_y <= y <= rect[3]):
            logger.warning(f"坐标({x}, {y})不在窗口区域内")
            return False
        
        # 将屏幕坐标转换为窗口客户区坐标
        point = win32api.MAKELONG(x - window_x, y - window_y)
        
        message = win32con.WM_LBUTTONDOWN if down else win32con.WM_LBUTTONUP

        # 发送鼠标消息
        if button == 'left':
            win32gui.SendMessage(self.hwnd, message, win32con.MK_LBUTTON, point)
            logger.debug("发送左键鼠标消息")
        elif button == 'right':
            win32gui.SendMessage(self.hwnd, message, win32con.MK_RBUTTON, point)
            logger.debug("发送右键鼠标消息")
        elif button == 'middle':
            win32gui.SendMessage(self.hwnd, message, win32con.MK_MBUTTON, point)
            logger.debug("发送中键鼠标消息")
        else:
            logger.warning(f"不支持的鼠标按钮: {button}")
            return False
        
        logger.debug("鼠标按钮事件发送成功")
        return True

    def mouse_move(self, x: int, y: int) -> bool:
        """
        使用窗口消息方法移动鼠标（不实际移动物理鼠标）
        
        :param x: 目标位置的x坐标
        :param y: 目标位置的y坐标
        :return: 是否成功
        """
        logger.debug(f"发送鼠标移动事件，目标位置: ({x}, {y})")
        if not self.hwnd or not self.ensure_window_ready(self.hwnd):
            logger.warning("窗口未就绪，无法发送鼠标移动事件")
            return False
        
        # 获取窗口位置和大小
        rect = win32gui.GetWindowRect(self.hwnd)
        window_x, window_y = rect[0], rect[1]
        
        # 确保坐标在窗口内
        if not (window_x <= x <= rect[2] and window_y <= y <= rect[3]):
            logger.warning(f"坐标({x}, {y})不在窗口区域内")  
            return False
        
        # 将屏幕坐标转换为窗口客户区坐标
        point = win32api.MAKELONG(screen_x - window_x, screen_y - window_y)
        
        # 发送鼠标移动消息
        win32gui.SendMessage(self.hwnd, win32con.WM_MOUSEMOVE, 0, point)
        logger.debug("鼠标移动事件发送成功")
        return True

    def key(self, virtual_key: int, down: bool = True) -> bool:
        """
        发送按键
        
        :param virtual_key: 虚拟键码（如win32con.VK_RETURN）
        :param down: 是否按下按键
        :return: 是否成功
        """
        logger.debug(f"发送按键事件，虚拟键码: {virtual_key}, 按下: {down}")
        if not self.hwnd or not self.ensure_window_ready(self.hwnd):
            logger.warning("窗口未就绪，无法发送按键事件")
            return False
        
        # 发送按键按下和释放消息
        if down:
            win32gui.SendMessage(self.hwnd, win32con.WM_KEYDOWN, virtual_key, 0)
            logger.debug("发送按键按下消息")
        else:
            win32gui.SendMessage(self.hwnd, win32con.WM_KEYUP, virtual_key, 0)
            logger.debug("发送按键释放消息")
        logger.debug("按键事件发送成功")
        return True

    def type_keys(self, text: str, delay: float = 0.01) -> bool:
        """
        向窗口发送按键（窗口消息方法）
        
        :param text: 要发送的文本
        :param delay: 按键间延迟（秒）
        :return: 是否成功
        """
        logger.debug(f"发送文本输入，文本: '{text}', 延迟: {delay}")
        if not self.hwnd or not self.ensure_window_ready(self.hwnd):
            logger.warning("窗口未就绪，无法发送文本输入")
            return False
        
        for char in text:
            win32gui.SendMessage(self.hwnd, win32con.WM_CHAR, ord(char), 0)
            time.sleep(delay)
        
        logger.debug(f"文本输入完成，共发送 {len(text)} 个字符")
        return True


class HardwareController(GUIController):
    def __init__(self) -> None:
        super().__init__()
        self.user32 = ctypes.windll.user32
        logger.debug("HardwareController初始化完成")

    def mouse_button(self, x: int, y: int, down: bool, button: Literal['left', 'right', 'middle'] = 'left') -> bool:
        """
        在当前鼠标位置按下鼠标按钮
        
        :param down: 是否按下鼠标按钮
        :param button: 鼠标按钮 'left', 'right', 'middle'
        :return: 是否成功
        """
        logger.debug(f"执行硬件鼠标按钮事件，位置: ({x}, {y}), 按钮: {button}, 按下: {down}")
        if x > 0 and y > 0:
            logger.debug("移动鼠标到指定位置")
            self.mouse_move(x, y)

        try:
            if button == 'left':
                if down:
                    self.user32.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    logger.debug("发送左键按下事件")
                else:
                    self.user32.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    logger.debug("发送左键释放事件")
            elif button == 'right':
                if down:
                    self.user32.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                    logger.debug("发送右键按下事件")
                else:
                    self.user32.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
                    logger.debug("发送右键释放事件")
            elif button == 'middle':
                if down:
                    self.user32.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
                    logger.debug("发送中键按下事件")
                else:
                    self.user32.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
                    logger.debug("发送中键释放事件")
            else:
                logger.warning(f"不支持的鼠标按钮: {button}")
                return False
            logger.debug("硬件鼠标按钮事件执行成功")
            return True
        except Exception as e:
            logger.error(f"鼠标按下操作失败: {e}")
            return False

    def mouse_move(self, x: int, y: int) -> bool:
        """
        使用硬件模拟方法移动鼠标（实际移动物理鼠标指针）
        
        :param x: 目标x坐标（屏幕绝对坐标）
        :param y: 目标y坐标（屏幕绝对坐标）
        :return: 是否成功
        """

        self.user32.SetCursorPos(x, y)
        return True

    def key(self, virtual_key: int, down: bool = True) -> bool:
        """
        使用硬件模拟方法发送特殊按键
        
        :param virtual_key: 虚拟键码
        :param down: 是否按下按键
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

    def wait_key_press(self, *virtual_keys: int, timeout: float = 1.0) -> bool:
        """
        等待指定按键或组合键按下（支持快捷键检测）
        例如：wait_key_press(VK_LCONTROL, ord('C')) 可检测 Ctrl+C
        
        :param virtual_keys: 虚拟键码列表，可以是单个键或多个键（组合键）
        :param timeout: 超时时间（秒）
        :return: 是否成功
        """
        start_time = time.time()
        # 使用更小的睡眠间隔以提高响应灵敏度
        small_sleep = 0.01  # 10ms的小睡眠间隔
        
        # 如果没有提供按键，则返回False
        if not virtual_keys:
            return False
            
        while True:
            # 检查所有键是否同时被按下
            all_keys_pressed = True
            for vk in virtual_keys:
                if self.user32.GetKeyState(vk) & 0x8000 == 0:
                    all_keys_pressed = False
                    break
                    
            if all_keys_pressed:
                return True
            
            # 检查是否超时
            elapsed_time = time.time() - start_time
            if elapsed_time >= timeout:
                return False
            
            # 计算剩余时间并确保只睡眠必要的时间
            remaining_time = timeout - elapsed_time
            # 只睡眠较小的时间间隔或者剩余时间（取较小值）
            time.sleep(min(small_sleep, remaining_time))
    
# 使用示例和测试代码
if __name__ == "__main__":
    # 创建控制器实例
    controller = BackgroundController()