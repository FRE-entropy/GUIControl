import time
import traceback
import numpy as np
from collections import deque
from utils.hgr_utils import HGRUtils, HandLandmark
from utils.gui_utils import GUIController, HardwareController
from utils.logger import logger

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
        
        # 初始化组件
        self._initialize_components()
        
        # 计算帧时间
        self.frame_time = 1.0 / self.TARGET_FPS
        
        # 初始化功能模块
        self.function_list = [
            GestureMouse(self.gui_controller)
        ]
        
        logger.info(f"手势控制系统初始化完成 - 数据目录: {self.data_dir}, 控制方法: {self.control_method}")
    
    def _initialize_components(self):
        """初始化核心组件"""
        try:
            self.hgr_utils = HGRUtils(self.data_dir)
            self.gui_controller = HardwareController()
            
            # 优化后台运行性能
            self.gui_controller.boost_priority()
            self.gui_controller.optimize_for_background()
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
            raise

    def test(self):
        """测试手势识别功能"""
        try:
            hand_landmarks = self.hgr_utils.get_hand_landmarks()
            if hand_landmarks is None or len(hand_landmarks) == 0:
                logger.info("未检测到手部")
                return
            logger.debug(f"手部关键点: {hand_landmarks}")
            logger.debug(f"食指指尖坐标: {hand_landmarks[0].landmark[
                self.hgr_utils.mp_hands.HandLandmark.INDEX_FINGER_TIP
            ]}")
        except Exception as e:
            logger.error(f"测试过程中发生错误: {e}")

    def start(self):
        """启动手势控制主循环"""
        logger.info("手势控制已启动，按Ctrl+C退出...")
        self.is_running = True
        
        try:
            self._run_main_loop()
        except KeyboardInterrupt:
            logger.info("手势控制已停止")
        except Exception as e:
            logger.error(f"发生错误: {e}")
            logger.error(traceback.format_exc())
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
                
                # 控制帧率
                self._control_frame_rate(frame_start_time)
                
                # 重置错误计数（成功执行一轮）
                self.error_count = 0
                
            except Exception as e:
                self._handle_error(e)
                
                # 如果错误次数过多，停止运行
                if self.error_count >= self.MAX_ERROR_COUNT:
                    logger.error(f"错误次数过多({self.error_count}次)，停止运行")
                    self.is_running = False
                    break
    
    def _process_gesture_data(self):
        """处理手势数据并更新功能模块"""
        try:
            # 获取手势数据（添加超时保护）
            hand_landmarks_list, image = self.hgr_utils.get_all_hand_landmarks()
            # self.hgr_utils.display_results(image)
            if len(hand_landmarks_list) == 0:
                if not self.is_paused:
                    for function in self.function_list:
                        function.pause()
                        self.is_paused = True
                return False
            else:
                self.is_paused = False

            # 更新所有功能模块
            for function in self.function_list:
                function.update(hand_landmarks_list)
            
            return True
                
        except Exception as e:
            logger.error(f"处理手势数据时发生错误: {e}")
            # 错误计数增加
            self.error_count += 1
            # 如果错误次数过多，停止运行
            if self.error_count >= self.MAX_ERROR_COUNT:
                logger.error(f"错误次数过多({self.error_count}次)，停止运行")
                self.is_running = False
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
            logger.error(f"帧率控制时发生错误: {e}")

    def _handle_error(self, error):
        """
        处理错误
        
        Args:
            error (Exception): 发生的错误对象
        """
        self.error_count += 1
        logger.error(f"发生错误 (第{self.error_count}次): {error}")
        
        # 短暂延迟，避免错误循环过快
        time.sleep(0.1)
    
    def _cleanup(self):
        """清理资源"""
        logger.info("正在清理资源...")
        self.is_running = False
        
        try:
            if hasattr(self, 'hgr_utils'):
                if hasattr(self.hgr_utils, 'cleanup'):
                    self.hgr_utils.cleanup()
            
            logger.info("资源清理完成")
        except Exception as e:
            logger.error(f"清理资源时发生错误: {e}")


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
    CLICK_DISTANCE_THRESHOLD = 8  # 降低点击阈值，提高灵敏度
    SMOOTHING_WINDOW_SIZE = 5  # 增加平滑窗口大小，减少抖动
    MIN_MOVEMENT_THRESHOLD = 1  # 降低移动阈值，提高灵敏度
    SENSITIVITY = 1500.0
    SCALE = 1.3
    
    def __init__(self, gui_controller: GUIController):
        """初始化手势鼠标控制（优化版本）"""
        self.gui_controller = gui_controller
        self.is_click = False
        self.is_dragging = False
        self.start_move_tip = None
        self.start_move_pos = None
        
        # 位置平滑 - 使用相对坐标初始化（0-1范围）
        initial_pos = [0.5, 0.5, 1.0]  # 屏幕中心对应的相对坐标
      
        self.thumb_location_list = np.tile([initial_pos], (self.SMOOTHING_WINDOW_SIZE, 1))
        self.index_location_list = np.tile([initial_pos], (self.SMOOTHING_WINDOW_SIZE, 1))
        self.middle_location_list = np.tile([initial_pos], (self.SMOOTHING_WINDOW_SIZE, 1))
        

        self.thumb_middle_finger_distance = 0.0
        self.thumb_index_finger_distance = 0.0
        
        # 性能优化 - 使用指数衰减权重，让最近的数据权重更大
        # 权重分布：最近的数据权重最大，逐渐衰减
        decay_factor = 0.7  # 衰减因子，越小衰减越快
        self._weights = np.array([decay_factor ** (self.SMOOTHING_WINDOW_SIZE - i - 1) 
                                 for i in range(self.SMOOTHING_WINDOW_SIZE)], dtype=np.float32)
        self._total_weight = np.sum(self._weights)
        
        # 缓存
        self._last_mouse_pos = None
        self._last_distance = 0.0
        
        # 点击状态跟踪
        self.click_start_time = 0
        self.last_click_state = False
        
        # 帧计数器，用于控制移动频率
        self._frame_counter = 0

    def update(self, hand_landmarks_list):
        """
        更新鼠标控制状态（优化版本）
        """
        try:
            if len(hand_landmarks_list) == 0:
                return

            current_hand_landmarks = hand_landmarks_list[0]
            
            # 计算拇指和食指位置
            self._update_location_list(current_hand_landmarks)
            thumb_tip = self._calculate_weighted_average(self.thumb_location_list)
            index_finger_tip = self._calculate_weighted_average(self.index_location_list)
            middle_finger_tip = self._calculate_weighted_average(self.middle_location_list)
            
            # 计算鼠标位置（食指位置）
            # mouse_x, mouse_y = self._calculate_mouse_position(index_finger_tip)
            
            # 计算手指距离
            self.thumb_middle_finger_distance = self._calculate_finger_distance(thumb_tip, middle_finger_tip)
            self.thumb_index_finger_distance = self._calculate_finger_distance(thumb_tip, index_finger_tip)
            
            # 更新帧计数器
            self._frame_counter += 1
            
            # 更新鼠标位置
            self._update_mouse_position(index_finger_tip)
            
            # 处理点击事件
            self._handle_click_event()

            self._display_status()
                
        except Exception as e:
            logger.error(f"鼠标控制更新时发生错误: {e}")

    def pause(self):
        """暂停手势鼠标控制"""
        self.is_click = False
        self.is_dragging = False
        self.gui_controller.mouse_button(-1, -1, False, "left")

    def _calculate_mouse_position(self, tip):
        """
        计算鼠标屏幕位置（优化版本）
        """
        x = (1 - tip[0]) * self.gui_controller.screen_size[0]
        y = tip[1] * self.gui_controller.screen_size[1]
        
        # 应用缩放
        center_x = self.gui_controller.screen_size[0] / 2
        center_y = self.gui_controller.screen_size[1] / 2
        
        x = center_x + (x - center_x) * self.SCALE
        y = center_y + (y - center_y) * self.SCALE
        
        # 限制在屏幕范围内
        x = max(0, min(x, self.gui_controller.screen_size[0] - 1))
        y = max(0, min(y, self.gui_controller.screen_size[1] - 1))
        
        return x, y
    
    def _calculate_finger_distance(self, tip1, tip2):
        """
        计算两指之间的距离
        """
        dx = tip1[0] - tip2[0]
        dy = tip1[1] - tip2[1]
        # 直接使用欧几里得距离，不缩放
        distance = (dx**2 + dy**2)**0.5

        distance = distance / tip1[2] * -10
        
        return distance

    def _update_mouse_position(self, tip):
        """
        更新鼠标位置（相对移动）- 优化版本
        """
        try:
            if self.thumb_middle_finger_distance < self.CLICK_DISTANCE_THRESHOLD:
                if self.start_move_tip is None:
                    self.start_move_tip = tip
                    self.start_move_pos = self.gui_controller.get_cursor_position()
                    return
                
                # 计算移动距离，添加移动阈值
                delta_x = (tip[0] - self.start_move_tip[0]) * -self.SENSITIVITY
                delta_y = (tip[1] - self.start_move_tip[1]) * self.SENSITIVITY
                
                # 添加移动阈值，减少微小移动
                if abs(delta_x) < 2 and abs(delta_y) < 2:
                    return
                
                mouse_x = self.start_move_pos[0] + delta_x
                mouse_y = self.start_move_pos[1] + delta_y

                # 添加移动频率控制，每2帧移动一次
                if self._frame_counter % 2 == 0:
                    self.gui_controller.mouse_move(int(mouse_x), int(mouse_y))

            else:
                self.start_move_tip = None
        
        except Exception as e:
            logger.error(f"更新鼠标位置（相对移动）时发生错误: {e}")

    def _should_move_mouse(self, x, y):
        """
        检查是否需要移动鼠标
        """
        dx = abs(x - self.start_move_pos[0])
        dy = abs(y - self.start_move_pos[1])
        return (dx > self.MIN_MOVEMENT_THRESHOLD or dy > self.MIN_MOVEMENT_THRESHOLD) and self.thumb_middle_finger_distance < self.CLICK_DISTANCE_THRESHOLD
    
    def _update_location_list(self, current_hand_landmarks):
        """
        更新位置列表（优化版本）
        """
        thumb_tip = current_hand_landmarks[HandLandmark.THUMB_TIP]
        index_finger_tip = current_hand_landmarks[HandLandmark.INDEX_FINGER_TIP]
        middle_finger_tip = current_hand_landmarks[HandLandmark.MIDDLE_FINGER_TIP]
        
        self.thumb_location_list = np.roll(self.thumb_location_list, -1, axis=0)
        self.thumb_location_list[-1] = [thumb_tip[0], thumb_tip[1], thumb_tip[2]]
        
        self.index_location_list = np.roll(self.index_location_list, -1, axis=0)
        self.index_location_list[-1] = [index_finger_tip[0], index_finger_tip[1], index_finger_tip[2]]
        
        self.middle_location_list = np.roll(self.middle_location_list, -1, axis=0)
        self.middle_location_list[-1] = [middle_finger_tip[0], middle_finger_tip[1], middle_finger_tip[2]]
        
    def _calculate_weighted_average(self, location_list):
        """
        计算加权平均位置（优化版本）
        """
        try:
            # 检查数据有效性
            if np.any(np.isnan(location_list)) or np.any(np.isinf(location_list)):
                # 如果数据无效，返回最近的有效位置
                return location_list[-1][0], location_list[-1][1], location_list[-1][2]
            
            # 计算加权平均
            weighted_x = np.sum(location_list[:, 0] * self._weights)
            weighted_y = np.sum(location_list[:, 1] * self._weights)
            weighted_z = np.sum(location_list[:, 2] * self._weights)
            
            avg_x = weighted_x / self._total_weight
            avg_y = weighted_y / self._total_weight
            avg_z = weighted_z / self._total_weight
            
            # 确保结果在有效范围内（0-1）
            avg_x = max(0.0, min(1.0, avg_x))
            avg_y = max(0.0, min(1.0, avg_y))
            
            return avg_x, avg_y, avg_z
            
        except Exception as e:
            logger.error(f"加权平均计算错误: {e}")
            # 出错时返回最近的有效位置
            return location_list[-1][0], location_list[-1][1]
    
    def _handle_click_event(self):
        """
        处理鼠标点击事件（优化版本）
        
        主要改进：
        1. 简化状态机逻辑
        2. 改进点击检测算法
        3. 增强响应性
        """
        try:
            is_index = self.thumb_index_finger_distance < self.CLICK_DISTANCE_THRESHOLD
            is_middle = self.thumb_middle_finger_distance < self.CLICK_DISTANCE_THRESHOLD
            if is_index and is_middle:
                if not self.is_dragging:
                    self.gui_controller.mouse_button(-1, -1, True, "left")
                    self.is_dragging = True
                    self.is_click = True
                    logger.info("拖拽开始")
            else:
                if self.is_dragging:
                    self.gui_controller.mouse_button(-1, -1, False, "left")
                    self.is_dragging = False
                    logger.info("拖拽释放")
            if is_index:
                if not self.is_click and not self.is_dragging:
                    self.gui_controller.click(-1, -1, "left")
                    self.is_click = True
                    logger.info("点击")
            else:
                self.is_click = False

        except Exception as e:
            logger.error(f"处理点击事件时发生错误: {e}")
    
    def _display_status(self):
        """显示状态信息"""
        status_text = "未点击"
        if self.is_dragging:
            status_text = "拖拽中"
        
        # 使用print在一行显示状态信息，不记录到日志文件
        print(f"食指距离: {self.thumb_index_finger_distance:.3f} | 中指距离: {self.thumb_middle_finger_distance:.3f} | 状态: {status_text}", end='\r')


if __name__ == "__main__":
    """
    主程序入口
    """
    try:
        gesture_control = GestureControl()
        gesture_control.start()
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        logger.error(traceback.format_exc())