import time
import traceback
import numpy as np
from collections import deque
import psutil
from utils.hgr_utils import HGRUtils, HandLandmark
from utils.gui_utils import BackgroundController


class PerformanceMonitor:
    """
    性能监控类
    
    实时监控系统性能指标，包括CPU使用率、内存使用、帧率等。
    """
    
    def __init__(self):
        self.process = psutil.Process()
        self.start_time = time.time()
        self.frame_count = 0
        self.cpu_usage = deque(maxlen=60)
        self.memory_usage = deque(maxlen=60)
        self.fps_history = deque(maxlen=60)
        
    def update(self):
        """更新性能指标"""
        try:
            # CPU使用率
            cpu_percent = self.process.cpu_percent()
            self.cpu_usage.append(cpu_percent)
            
            # 内存使用
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024  # 转换为MB
            self.memory_usage.append(memory_mb)
            
            # 帧率计算
            self.frame_count += 1
            elapsed_time = time.time() - self.start_time
            current_fps = self.frame_count / elapsed_time
            self.fps_history.append(current_fps)
            
        except Exception as e:
            print(f"性能监控更新失败: {e}")
    
    def get_stats(self):
        """获取性能统计"""
        try:
            avg_cpu = np.mean(self.cpu_usage) if self.cpu_usage else 0
            avg_memory = np.mean(self.memory_usage) if self.memory_usage else 0
            avg_fps = np.mean(self.fps_history) if self.fps_history else 0
            
            return {
                'cpu_usage': avg_cpu,
                'memory_usage_mb': avg_memory,
                'fps': avg_fps,
                'total_frames': self.frame_count,
                'uptime_seconds': time.time() - self.start_time
            }
        except Exception as e:
            print(f"获取性能统计失败: {e}")
            return {}
    
    def display_stats(self):
        """显示性能统计信息"""
        stats = self.get_stats()
        if stats:
            print(f"CPU: {stats['cpu_usage']:.1f}% | 内存: {stats['memory_usage_mb']:.1f}MB | FPS: {stats['fps']:.1f}", end="\r")


class GestureControl:
    """
    手势控制主类
    
    负责管理手势识别和鼠标控制功能，提供完整的基于手势的鼠标控制解决方案。
    该类整合了手势识别、鼠标控制、错误处理和资源管理等功能。
    
    Attributes:
        TARGET_FPS (int): 目标帧率，默认30FPS
        DEFAULT_DATA_DIR (str): 默认数据目录路径
        DEFAULT_CONTROL_METHOD (str): 默认控制方法
        MAX_ERROR_COUNT (int): 最大错误次数限制
    """
    
    # 常量定义
    TARGET_FPS = 30
    DEFAULT_DATA_DIR = "./data"
    DEFAULT_CONTROL_METHOD = "hardware"
    MAX_ERROR_COUNT = 5  # 最大错误次数
    
    def __init__(self, data_dir=None, control_method=None):
        """
        初始化手势控制系统
        
        Args:
            data_dir (str, optional): 数据目录路径，默认为"./data"
            control_method (str, optional): 控制方法，默认为"hardware"
            
        Raises:
            Exception: 组件初始化失败时抛出异常
        """
        # 使用默认值或传入的参数
        self.data_dir = data_dir or self.DEFAULT_DATA_DIR
        self.control_method = control_method or self.DEFAULT_CONTROL_METHOD

        self.is_paused = False
        
        # 错误处理相关
        self.error_count = 0
        self.is_running = False
        
        # 性能监控相关
        self.frame_count = 0
        self.start_time = time.time()
        self.frame_times = deque(maxlen=60)  # 存储最近60帧的时间
        self.performance_stats = {
            'fps': 0,
            'avg_frame_time': 0,
            'min_frame_time': float('inf'),
            'max_frame_time': 0
        }
        
        # 集成性能监控器
        self.performance_monitor = PerformanceMonitor()
        
        # 初始化组件
        self._initialize_components()
        
        # 计算帧时间
        self.frame_time = 1.0 / self.TARGET_FPS
        
        # 初始化功能模块
        self.function_list = [
            GestureMouse(self.bc)
        ]
        
        print(f"手势控制系统初始化完成 - 数据目录: {self.data_dir}, 控制方法: {self.control_method}")
    
    def _initialize_components(self):
        """
        初始化核心组件
        
        负责初始化手势识别工具和后台控制器，设置控制方法。
        
        Raises:
            Exception: 组件初始化失败时抛出异常
        """
        try:
            self.hgr_utils = HGRUtils(self.data_dir)
            self.bc = BackgroundController()
            self.bc.set_control_method(self.control_method)
            
            # 优化后台运行性能
            self.bc.boost_priority()
            self.bc.optimize_for_background()
        except Exception as e:
            print(f"组件初始化失败: {e}")
            raise

    def test(self):
        """
        测试手势识别功能
        
        用于调试和验证手势识别功能是否正常工作。
        输出检测到的手部关键点信息。
        """
        try:
            hand_landmarks = self.hgr_utils.get_hand_landmarks()
            if not hand_landmarks:
                print("未检测到手部")
                return
            print(hand_landmarks)
            print(hand_landmarks[0].landmark[
                self.hgr_utils.mp_hands.HandLandmark.INDEX_FINGER_TIP
            ])
        except Exception as e:
            print(f"测试过程中发生错误: {e}")

    def start(self):
        """
        启动手势控制主循环
        
        开始手势识别和鼠标控制的主循环，支持优雅退出和错误处理。
        按Ctrl+C可以安全退出程序。
        """
        print("手势控制已启动，按Ctrl+C退出...")
        self.is_running = True
        
        try:
            self._run_main_loop()
        except KeyboardInterrupt:
            print("\n手势控制已停止")
        except Exception as e:
            print(f"发生错误: {e}")
            traceback.print_exc()
        finally:
            self._cleanup()
    
    def _run_main_loop(self):
        """
        运行主循环逻辑
        
        持续处理手势数据并更新鼠标控制状态，包含错误计数和自动停止机制。
        """
        last_frame_time = time.time()
        
        while self.is_running:
            try:
                frame_start_time = time.time()
                
                # 处理手势数据
                if not self._process_gesture_data():
                    # 即使没有手势数据，也要控制帧率
                    self._control_frame_rate(frame_start_time)
                    continue
                
                # 更新性能统计
                self._update_performance_stats(frame_start_time)
                
                # 控制帧率
                self._control_frame_rate(frame_start_time)
                
                # 重置错误计数（成功执行一轮）
                self.error_count = 0
                
            except Exception as e:
                self._handle_error(e)
                
                # 如果错误次数过多，停止运行
                if self.error_count >= self.MAX_ERROR_COUNT:
                    print(f"错误次数过多({self.error_count}次)，停止运行")
                    self.is_running = False
                    break
    
    def _process_gesture_data(self):
        """
        处理手势数据并更新功能模块
        
        Returns:
            bool: 是否成功处理了手势数据
        """
        try:
            # 获取手势数据
            hand_landmarks_list = self.hgr_utils.get_all_hand_landmarks()
            if len(hand_landmarks_list) == 0:
                if not self.is_paused:
                    for function in self.function_list:
                        function.pause()
                return False
            
            self.is_paused = False

            # 更新所有功能模块
            for function in self.function_list:
                function.update(hand_landmarks_list)
            
            return True
            
        except Exception as e:
            print(f"处理手势数据时发生错误: {e}")
            return False
    
    def _control_frame_rate(self, start_time):
        """
        控制帧率，确保稳定的运行频率（后台优化版）
        
        Args:
            start_time (float): 当前循环开始的时间戳
        """
        try:
            elapsed_time = time.time() - start_time
            if elapsed_time < self.frame_time:
                wait_time = self.frame_time - elapsed_time
                
                # 后台运行时使用更智能的睡眠策略
                if wait_time > 0.005:  # 对于较长的等待时间
                    # 后台模式下使用更长的睡眠时间，减少CPU占用
                    time.sleep(wait_time * 0.95)
                    # 使用短时间的忙等待进行最终调整
                    end_time = start_time + self.frame_time
                    while time.time() < end_time:
                        pass
                else:
                    # 短时间等待直接使用忙等待，提高精度
                    end_time = start_time + self.frame_time
                    while time.time() < end_time:
                        pass
                        
        except Exception as e:
            print(f"帧率控制时发生错误: {e}")
    
    def _update_performance_stats(self, frame_start_time):
        """
        更新性能统计信息
        
        Args:
            frame_start_time (float): 当前帧开始的时间戳
        """
        try:
            frame_time = time.time() - frame_start_time
            self.frame_times.append(frame_time)
            self.frame_count += 1
            
            # 更新性能监控器
            self.performance_monitor.update()
            
            # 每10帧更新一次性能统计
            if self.frame_count % 10 == 0:
                total_time = time.time() - self.start_time
                self.performance_stats['fps'] = self.frame_count / total_time
                self.performance_stats['avg_frame_time'] = np.mean(self.frame_times) * 1000  # 转换为毫秒
                self.performance_stats['min_frame_time'] = min(self.frame_times) * 1000
                self.performance_stats['max_frame_time'] = max(self.frame_times) * 1000
                
                # 显示性能信息
                self._display_performance_info()
        except Exception as e:
            print(f"更新性能统计时发生错误: {e}")
    
    def _display_performance_info(self):
        """显示性能信息"""
        stats = self.performance_stats
        monitor_stats = self.performance_monitor.get_stats()
        
        if monitor_stats:
            print(f"FPS: {stats['fps']:.1f} | 帧时间: {stats['avg_frame_time']:.1f}ms | CPU: {monitor_stats['cpu_usage']:.1f}% | 内存: {monitor_stats['memory_usage_mb']:.1f}MB", end="\r")
        else:
            print(f"FPS: {stats['fps']:.1f} | 帧时间: {stats['avg_frame_time']:.1f}ms (min: {stats['min_frame_time']:.1f}ms, max: {stats['max_frame_time']:.1f}ms)", end="\r")
    
    def _handle_error(self, error):
        """
        处理错误
        
        Args:
            error (Exception): 发生的错误对象
        """
        self.error_count += 1
        print(f"发生错误 (第{self.error_count}次): {error}")
        
        # 短暂延迟，避免错误循环过快
        time.sleep(0.1)
    
    def _cleanup(self):
        """
        清理资源
        
        在程序退出时执行资源清理操作，确保系统资源被正确释放。
        """
        print("正在清理资源...")
        self.is_running = False
        
        try:
            # 这里可以添加资源清理逻辑
            if hasattr(self, 'hgr_utils'):
                # 如果有清理方法，调用它
                if hasattr(self.hgr_utils, 'cleanup'):
                    self.hgr_utils.cleanup()
            
            print("资源清理完成")
        except Exception as e:
            print(f"清理资源时发生错误: {e}")


class GestureMouse:
    """
    手势鼠标控制类（优化版本）
    
    负责将手势转换为鼠标操作，提供平滑的鼠标移动和可靠的点击检测。
    包含移动阈值检测、位置平滑、点击迟滞等高级功能。
    
    Attributes:
        CLICK_DISTANCE_THRESHOLD (float): 点击距离阈值
        SMOOTHING_WINDOW_SIZE (int): 平滑窗口大小
        MIN_MOVEMENT_THRESHOLD (int): 最小移动阈值（像素）
    """
    
    # 常量定义
    CLICK_DISTANCE_THRESHOLD = 0.5 # 点击距离阈值
    CLICK_HYSTERESIS = 0.1  # 点击迟滞阈值，防止抖动
    SMOOTHING_WINDOW_SIZE = 5  # 平滑窗口大小
    MIN_MOVEMENT_THRESHOLD = 2  # 最小移动阈值（像素）
    CLICK_COOLDOWN = 5  # 点击冷却时间（帧），减少以提高响应速度
    CLICK_MIN_DURATION = 3  # 点击最小持续时间（帧），确保点击被识别
    DRAG_THRESHOLD_DURATION = 15  # 拖拽阈值持续时间（帧），超过此时间触发拖拽
    SCALE = 1.3
    
    def __init__(self, bc: BackgroundController):
        """初始化手势鼠标控制（优化版本）"""
        self.bc = bc
        self.is_click = False
        self.is_dragging = False  # 拖拽状态标志
        self.click_cooldown = 0
        self.click_duration = 0  # 点击持续时间计数器
        
        # 优化：使用numpy数组代替列表，提高计算效率
        initial_pos = self.bc.get_cursor_position()
        self.location_list = np.tile([initial_pos], (self.SMOOTHING_WINDOW_SIZE, 1))
        self.current_distance = 0.0
        self.last_position = initial_pos
        
        # 性能优化：预计算权重
        self._weights = np.arange(1, self.SMOOTHING_WINDOW_SIZE + 1, dtype=np.float32)
        self._total_weight = np.sum(self._weights)
        
        # 缓存上次计算的结果
        self._last_mouse_pos = None
        self._last_distance = 0.0

    def update(self, hand_landmarks_list):
        """
        更新鼠标控制状态
        
        Args:
            hand_landmarks_list: 手部关键点列表
        """
        try:
            if len(hand_landmarks_list) == 0:
                return
                
            current_hand_landmarks = hand_landmarks_list[0]
            
            # 计算拇指和食指位置
            thumb_tip = current_hand_landmarks[HandLandmark.THUMB_TIP]
            index_finger_tip = current_hand_landmarks[HandLandmark.INDEX_FINGER_TIP]
            
            # 计算鼠标位置
            mouse_x, mouse_y = self._calculate_mouse_position(thumb_tip, index_finger_tip)
            
            # 计算手指距离（用于判断点击）
            self.current_distance = self._calculate_finger_distance(thumb_tip, index_finger_tip)
            
            # 更新鼠标位置（带平滑和阈值检测）
            self._update_mouse_position(mouse_x, mouse_y)
            
            # 处理点击事件
            self._handle_click_event()
                
        except Exception as e:
            print(f"鼠标控制更新时发生错误: {e}")

    def pause(self):
        """暂停手势鼠标控制"""
        self.is_click = False
        self.bc.mouse_up_current_hardware()

    
    def _calculate_mouse_position(self, thumb_tip, index_finger_tip):
        """
        计算鼠标屏幕位置（优化版本）
        
        Args:
            thumb_tip: 拇指指尖坐标
            index_finger_tip: 食指指尖坐标
            
        Returns:
            tuple: 鼠标在屏幕上的坐标 (x, y)
        """
        # 缓存计算结果，避免重复计算
        if self._last_mouse_pos is not None:
            # 检查手指位置是否显著变化
            dx = abs(thumb_tip[0] - self._last_mouse_pos[0]) + abs(index_finger_tip[0] - self._last_mouse_pos[2])
            dy = abs(thumb_tip[1] - self._last_mouse_pos[1]) + abs(index_finger_tip[1] - self._last_mouse_pos[3])
            if dx < 0.01 and dy < 0.01:  # 微小变化，使用缓存
                return self._last_mouse_pos[4], self._last_mouse_pos[5]
        
        # 优化计算：减少重复计算
        avg_x = (index_finger_tip[0] + thumb_tip[0]) / 2
        avg_y = (index_finger_tip[1] + thumb_tip[1]) / 2
        
        x = ((1 - avg_x) * self.SCALE - (self.SCALE - 1) / 2) * self.bc.screen_size[0]
        y = (avg_y * self.SCALE - (self.SCALE - 1) / 2) * self.bc.screen_size[1]
        
        # 缓存计算结果
        self._last_mouse_pos = (thumb_tip[0], thumb_tip[1], index_finger_tip[0], index_finger_tip[1], x, y)
        
        return x, y
    
    def _calculate_finger_distance(self, thumb_tip, index_finger_tip):
        """
        计算拇指和食指之间的距离（优化版本）
        
        Args:
            thumb_tip: 拇指指尖坐标
            index_finger_tip: 食指指尖坐标
            
        Returns:
            float: 手指之间的距离（缩放后的值）
        """
        # 使用缓存避免重复计算
        if abs(thumb_tip[0] - self._last_mouse_pos[0]) < 0.001 and abs(index_finger_tip[0] - self._last_mouse_pos[2]) < 0.001:
            return self._last_distance
        
        dx = index_finger_tip[0] - thumb_tip[0]
        dy = index_finger_tip[1] - thumb_tip[1]
        distance = (dx**2 + dy**2)**0.5 * 10
        
        # 缓存结果
        self._last_distance = distance
        return distance
    
    def _update_mouse_position(self, x, y):
        """
        更新鼠标位置（带平滑处理和移动阈值检测）
        
        Args:
            x (float): 鼠标X坐标
            y (float): 鼠标Y坐标
        """
        try:
            # 检查移动距离是否超过阈值
            # 在拖拽模式下，即使有冷却时间也允许移动
            can_move = self._should_move_mouse(x, y) and (self.click_cooldown <= 0 or self.is_dragging)
            
            if can_move:
                # 使用numpy数组的滚动操作替代append和pop
                self.location_list = np.roll(self.location_list, -1, axis=0)
                self.location_list[-1] = [x, y]
                
                # 计算加权平均位置（最近的位置权重更高）
                avg_x, avg_y = self._calculate_weighted_average()
                
                # 移动鼠标
                self.bc.move_foreground(int(avg_x), int(avg_y), relative=False)
                
                # 更新最后位置
                self.last_position = (avg_x, avg_y)
            
            # 显示距离和状态信息
            status_text = "未点击"
            if self.is_dragging:
                status_text = "拖拽中"
            elif self.is_click:
                status_text = "点击中"
            
            print(f"手指距离: {self.current_distance:.2f} | 状态: {status_text} | 持续时间: {self.click_duration}帧       ", end="\r")
            
        except Exception as e:
            print(f"更新鼠标位置时发生错误: {e}")
    
    def _should_move_mouse(self, x, y):
        """
        检查是否需要移动鼠标（基于移动阈值）
        
        Args:
            x (float): 新位置X坐标
            y (float): 新位置Y坐标
            
        Returns:
            bool: 是否需要移动鼠标
        """
        dx = abs(x - self.last_position[0])
        dy = abs(y - self.last_position[1])
        return dx > self.MIN_MOVEMENT_THRESHOLD or dy > self.MIN_MOVEMENT_THRESHOLD
    
    def _calculate_weighted_average(self):
        """
        计算加权平均位置（优化版本）
        
        使用加权平均算法对鼠标位置进行平滑处理，最近的位置权重更高。
        使用numpy向量化操作提高计算效率。
        
        Returns:
            tuple: 平滑后的鼠标坐标 (x, y)
        """
        # 使用预计算的权重和numpy向量化操作
        weighted_x = np.sum(self.location_list[:, 0] * self._weights)
        weighted_y = np.sum(self.location_list[:, 1] * self._weights)
        
        return weighted_x / self._total_weight, weighted_y / self._total_weight
    
    def _handle_click_event(self):
        """
        处理鼠标点击和拖拽事件（增强版：支持点击/拖拽区分）
        
        优化点：
        1. 短时间点击：普通点击
        2. 长时间点击：拖拽操作
        3. 添加点击迟滞防止抖动
        4. 改进状态机逻辑
        """
        try:
            # 更新冷却时间
            if self.click_cooldown > 0:
                self.click_cooldown -= 1
                return
            
            # 检查是否处于点击状态
            if self.is_click:
                # 增加点击持续时间
                self.click_duration += 1
                
                # 检查是否达到拖拽阈值
                if not self.is_dragging and self.click_duration >= self.DRAG_THRESHOLD_DURATION:
                    # 进入拖拽模式
                    self.is_dragging = True
                    print("\n进入拖拽模式")
                
                # 如果手指距离超过阈值+迟滞，结束点击/拖拽
                if self.current_distance > self.CLICK_DISTANCE_THRESHOLD + self.CLICK_HYSTERESIS:
                    # 确保点击持续时间足够长
                    if self.click_duration >= self.CLICK_MIN_DURATION:
                        if self.is_dragging:
                            self.bc.mouse_up_current_hardware()
                            print(f"\n拖拽结束（持续时间: {self.click_duration}帧）")
                        else:
                            self.bc.mouse_up_current_hardware()
                            print(f"\n点击结束（持续时间: {self.click_duration}帧）")
                    
                    self.is_click = False
                    self.is_dragging = False
                    self.click_duration = 0
                    # 只有在拖拽模式下才设置冷却时间，普通点击不设置冷却时间
                    if self.is_dragging:
                        self.click_cooldown = self.CLICK_COOLDOWN
            else:
                # 如果手指距离小于阈值-迟滞，开始点击
                if self.current_distance < self.CLICK_DISTANCE_THRESHOLD - self.CLICK_HYSTERESIS:
                    # 开始点击
                    self.is_click = True
                    self.is_dragging = False
                    self.click_duration = 1
                    self.bc.mouse_down_current_hardware()
                    print("\n点击开始")
                
        except Exception as e:
            print(f"处理点击事件时发生错误: {e}")


if __name__ == "__main__":
    """
    主程序入口
    
    创建GestureControl实例并启动手势控制系统。
    包含完整的异常处理机制。
    """
    try:
        gesture_control = GestureControl()
        gesture_control.start()
    except Exception as e:
        print(f"程序启动失败: {e}")
        traceback.print_exc()
