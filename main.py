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
        self.frame_times = deque(maxlen=60)
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
        """初始化核心组件"""
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
        """测试手势识别功能"""
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
        """启动手势控制主循环"""
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
        """运行主循环逻辑"""
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
        """处理手势数据并更新功能模块"""
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
        控制帧率，确保稳定的运行频率
        
        Args:
            start_time (float): 当前循环开始的时间戳
        """
        try:
            elapsed_time = time.time() - start_time
            sleep_time = self.frame_time - elapsed_time
            
            if sleep_time > 0:
                time.sleep(sleep_time)
                        
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
                self.performance_stats['avg_frame_time'] = np.mean(self.frame_times) * 1000
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
        """清理资源"""
        print("正在清理资源...")
        self.is_running = False
        
        try:
            if hasattr(self, 'hgr_utils'):
                if hasattr(self.hgr_utils, 'cleanup'):
                    self.hgr_utils.cleanup()
            
            print("资源清理完成")
        except Exception as e:
            print(f"清理资源时发生错误: {e}")


class GestureMouse:
    """
    手势鼠标控制类（优化版本）
    
    主要优化点：
    1. 改进点击检测算法，提高灵敏度
    2. 优化距离计算和阈值设置
    3. 简化状态机逻辑
    4. 增强错误处理
    """
    
    # 优化后的常量定义
    CLICK_DISTANCE_THRESHOLD = 0.3  # 降低点击阈值，提高灵敏度
    CLICK_HYSTERESIS = 0.05  # 减少迟滞，提高响应速度
    SMOOTHING_WINDOW_SIZE = 5
    MIN_MOVEMENT_THRESHOLD = 1  # 降低移动阈值，提高灵敏度
    CLICK_COOLDOWN = 3  # 减少冷却时间
    CLICK_MIN_DURATION = 2  # 减少最小持续时间
    DRAG_THRESHOLD_DURATION = 10  # 减少拖拽阈值
    SCALE = 1.3
    
    def __init__(self, bc: BackgroundController):
        """初始化手势鼠标控制（优化版本）"""
        self.bc = bc
        self.is_click = False
        self.is_dragging = False
        self.click_cooldown = 0
        self.click_duration = 0
        
        # 位置平滑
        initial_pos = self.bc.get_cursor_position()
        self.location_list = np.tile([initial_pos], (self.SMOOTHING_WINDOW_SIZE, 1))
        self.current_distance = 0.0
        self.last_position = initial_pos
        
        # 性能优化
        self._weights = np.arange(1, self.SMOOTHING_WINDOW_SIZE + 1, dtype=np.float32)
        self._total_weight = np.sum(self._weights)
        
        # 缓存
        self._last_mouse_pos = None
        self._last_distance = 0.0
        
        # 点击状态跟踪
        self.click_start_time = 0
        self.last_click_state = False

    def update(self, hand_landmarks_list):
        """
        更新鼠标控制状态（优化版本）
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
            
            # 计算手指距离
            self.current_distance = self._calculate_finger_distance(thumb_tip, index_finger_tip)
            
            # 更新鼠标位置
            self._update_mouse_position(mouse_x, mouse_y)
            
            # 处理点击事件
            self._handle_click_event()
                
        except Exception as e:
            print(f"鼠标控制更新时发生错误: {e}")

    def pause(self):
        """暂停手势鼠标控制"""
        self.is_click = False
        self.is_dragging = False
        self.bc.mouse_up_current_hardware()

    def _calculate_mouse_position(self, thumb_tip, index_finger_tip):
        """
        计算鼠标屏幕位置（优化版本）
        """
        # 使用食指指尖作为主要控制点，更自然
        x = (1 - index_finger_tip[0]) * self.bc.screen_size[0]
        y = index_finger_tip[1] * self.bc.screen_size[1]
        
        # 应用缩放
        center_x = self.bc.screen_size[0] / 2
        center_y = self.bc.screen_size[1] / 2
        
        x = center_x + (x - center_x) * self.SCALE
        y = center_y + (y - center_y) * self.SCALE
        
        # 限制在屏幕范围内
        x = max(0, min(x, self.bc.screen_size[0] - 1))
        y = max(0, min(y, self.bc.screen_size[1] - 1))
        
        return x, y
    
    def _calculate_finger_distance(self, thumb_tip, index_finger_tip):
        """
        计算拇指和食指之间的距离（优化版本）
        """
        dx = index_finger_tip[0] - thumb_tip[0]
        dy = index_finger_tip[1] - thumb_tip[1]
        # 直接使用欧几里得距离，不缩放
        distance = (dx**2 + dy**2)**0.5
        
        return distance
    
    def _update_mouse_position(self, x, y):
        """
        更新鼠标位置（优化版本）
        """
        try:
            # 检查移动距离是否超过阈值
            can_move = self._should_move_mouse(x, y)
            
            if can_move:
                # 更新位置列表
                self.location_list = np.roll(self.location_list, -1, axis=0)
                self.location_list[-1] = [x, y]
                
                # 计算平滑位置
                avg_x, avg_y = self._calculate_weighted_average()
                
                # 移动鼠标（在拖拽模式下也允许移动）
                if not self.is_click or self.is_dragging:
                    self.bc.move_foreground(int(avg_x), int(avg_y), relative=False)
                
                # 更新最后位置
                self.last_position = (avg_x, avg_y)
            
            # 显示状态信息
            self._display_status()
            
        except Exception as e:
            print(f"更新鼠标位置时发生错误: {e}")
    
    def _should_move_mouse(self, x, y):
        """
        检查是否需要移动鼠标
        """
        dx = abs(x - self.last_position[0])
        dy = abs(y - self.last_position[1])
        return dx > self.MIN_MOVEMENT_THRESHOLD or dy > self.MIN_MOVEMENT_THRESHOLD
    
    def _calculate_weighted_average(self):
        """
        计算加权平均位置
        """
        weighted_x = np.sum(self.location_list[:, 0] * self._weights)
        weighted_y = np.sum(self.location_list[:, 1] * self._weights)
        
        return weighted_x / self._total_weight, weighted_y / self._total_weight
    
    def _handle_click_event(self):
        """
        处理鼠标点击事件（优化版本）
        
        主要改进：
        1. 简化状态机逻辑
        2. 改进点击检测算法
        3. 增强响应性
        """
        try:
            # 更新冷却时间
            if self.click_cooldown > 0:
                self.click_cooldown -= 1
                return
            
            current_time = time.time()
            current_click_state = self.current_distance < self.CLICK_DISTANCE_THRESHOLD
            
            # 状态变化检测
            if current_click_state != self.last_click_state:
                if current_click_state:  # 开始点击
                    self._start_click()
                else:  # 结束点击
                    self._end_click()
                
                self.last_click_state = current_click_state
            
            # 处理持续点击状态
            if self.is_click:
                self.click_duration += 1
                
                # 检查是否进入拖拽模式
                if not self.is_dragging and self.click_duration >= self.DRAG_THRESHOLD_DURATION:
                    self.is_dragging = True
                    print("\n进入拖拽模式")
                
        except Exception as e:
            print(f"处理点击事件时发生错误: {e}")
    
    def _start_click(self):
        """开始点击"""
        self.is_click = True
        self.is_dragging = False
        self.click_duration = 1
        self.click_start_time = time.time()
        self.bc.mouse_down_current_hardware()
        print("\n点击开始")
    
    def _end_click(self):
        """结束点击"""
        if self.is_click:
            # 确保点击持续时间足够长
            if self.click_duration >= self.CLICK_MIN_DURATION:
                if self.is_dragging:
                    self.bc.mouse_up_current_hardware()
                    print(f"\n拖拽结束（持续时间: {self.click_duration}帧）")
                    self.click_cooldown = self.CLICK_COOLDOWN  # 拖拽后设置冷却
                else:
                    self.bc.mouse_up_current_hardware()
                    print(f"\n点击结束（持续时间: {self.click_duration}帧）")
                    # 普通点击不设置冷却时间，提高响应性
            
            self.is_click = False
            self.is_dragging = False
            self.click_duration = 0
    
    def _display_status(self):
        """显示状态信息"""
        status_text = "未点击"
        if self.is_dragging:
            status_text = "拖拽中"
        elif self.is_click:
            status_text = "点击中"
        
        print(f"手指距离: {self.current_distance:.3f} | 状态: {status_text} | 持续时间: {self.click_duration}帧       ", end="\r")


if __name__ == "__main__":
    """
    主程序入口
    """
    try:
        gesture_control = GestureControl()
        gesture_control.start()
    except Exception as e:
        print(f"程序启动失败: {e}")
        traceback.print_exc()