import time
import traceback
from utils.hgr_utils import HGRUtils, HandLandmark
from utils.gui_utils import screen_size, BackgroundController


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
        
        # 错误处理相关
        self.error_count = 0
        self.is_running = False
        
        # 初始化组件
        self._initialize_components()
        
        # 计算帧时间
        self.frame_time = 1.0 / self.TARGET_FPS
        
        # 初始化功能模块
        self.function_list = [
            GestureMouse()
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
        while self.is_running:
            try:
                start_time = time.time()
                
                # 处理手势数据
                if not self._process_gesture_data():
                    continue
                
                # 控制帧率
                self._control_frame_rate(start_time)
                
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
                return False

            # 更新所有功能模块
            for function in self.function_list:
                function.update(hand_landmarks_list, self.bc)
            
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
            if elapsed_time < self.frame_time:
                wait_time = self.frame_time - elapsed_time
                time.sleep(wait_time)
        except Exception as e:
            print(f"帧率控制时发生错误: {e}")
    
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
    手势鼠标控制类
    
    负责将手势转换为鼠标操作，提供平滑的鼠标移动和可靠的点击检测。
    包含移动阈值检测、位置平滑、点击迟滞等高级功能。
    
    Attributes:
        CLICK_DISTANCE_THRESHOLD (float): 点击距离阈值
        SMOOTHING_WINDOW_SIZE (int): 平滑窗口大小
        MIN_MOVEMENT_THRESHOLD (int): 最小移动阈值（像素）
    """
    
    # 常量定义
    CLICK_DISTANCE_THRESHOLD = 0.5 # 点击距离阈值
    SMOOTHING_WINDOW_SIZE = 5  # 平滑窗口大小
    MIN_MOVEMENT_THRESHOLD = 2  # 最小移动阈值（像素）
    
    def __init__(self):
        """初始化手势鼠标控制"""
        self.is_click = False
        self.click_cooldown = 0
        self.location_list = [[0, 0]] * self.SMOOTHING_WINDOW_SIZE
        self.current_distance = 0.0
        self.last_position = (0, 0)

    def update(self, hand_landmarks_list, bc: BackgroundController):
        """
        更新鼠标控制状态
        
        Args:
            hand_landmarks_list: 手部关键点列表
            bc: 后台控制器实例
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
            self._update_mouse_position(mouse_x, mouse_y, bc)
            
            # 处理点击事件
            self._handle_click_event(bc)
            
            # 更新冷却时间
            if self.click_cooldown > 0:
                self.click_cooldown -= 1
                
        except Exception as e:
            print(f"鼠标控制更新时发生错误: {e}")
    
    def _calculate_mouse_position(self, thumb_tip, index_finger_tip):
        """
        计算鼠标屏幕位置
        
        Args:
            thumb_tip: 拇指指尖坐标
            index_finger_tip: 食指指尖坐标
            
        Returns:
            tuple: 鼠标在屏幕上的坐标 (x, y)
        """
        x = (1 - (index_finger_tip[0] + thumb_tip[0]) / 2) * screen_size[0]
        y = (index_finger_tip[1] + thumb_tip[1]) / 2 * screen_size[1]
        return x, y
    
    def _calculate_finger_distance(self, thumb_tip, index_finger_tip):
        """
        计算拇指和食指之间的距离
        
        Args:
            thumb_tip: 拇指指尖坐标
            index_finger_tip: 食指指尖坐标
            
        Returns:
            float: 手指之间的距离（缩放后的值）
        """
        dx = index_finger_tip[0] - thumb_tip[0]
        dy = index_finger_tip[1] - thumb_tip[1]
        distance = (dx**2 + dy**2)**0.5 * 10
        return distance
    
    def _update_mouse_position(self, x, y, bc):
        """
        更新鼠标位置（带平滑处理和移动阈值检测）
        
        Args:
            x (float): 鼠标X坐标
            y (float): 鼠标Y坐标
            bc (BackgroundController): 后台控制器实例
        """
        try:
            # 检查移动距离是否超过阈值
            if self._should_move_mouse(x, y) and self.click_cooldown <= 0:
                # 添加新位置到列表
                self.location_list.append([x, y])
                self.location_list.pop(0)
                
                # 计算加权平均位置（最近的位置权重更高）
                avg_x, avg_y = self._calculate_weighted_average()
                
                # 移动鼠标
                bc.move_foreground(int(avg_x), int(avg_y), relative=False)
                
                # 更新最后位置
                self.last_position = (avg_x, avg_y)
            
            # 显示距离信息
            print(f"手指距离: {self.current_distance:.2f} | 点击状态: {'已点击' if self.is_click else '未点击'}       ", end="\r")
            
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
        计算加权平均位置
        
        使用加权平均算法对鼠标位置进行平滑处理，最近的位置权重更高。
        
        Returns:
            tuple: 平滑后的鼠标坐标 (x, y)
        """
        total_weight = 0
        weighted_x = 0
        weighted_y = 0
        
        for i, location in enumerate(self.location_list):
            weight = i + 1  # 最近的位置权重更高
            weighted_x += location[0] * weight
            weighted_y += location[1] * weight
            total_weight += weight
        
        return weighted_x / total_weight, weighted_y / total_weight
    
    def _handle_click_event(self, bc: BackgroundController):
        """
        处理鼠标点击事件（带迟滞和冷却）
        
        Args:
            bc (BackgroundController): 后台控制器实例
        """
        try:
            if self.click_cooldown > 0:
                return
                
            if self.current_distance < self.CLICK_DISTANCE_THRESHOLD:
                if not self.is_click:
                    # 触发点击
                    self.is_click = True
                    self.click_cooldown = 10  # 设置冷却时间
                    print("\n点击事件触发")
                    # 这里可以添加实际的点击逻辑
                    bc.mouse_down_current_hardware()
            elif self.current_distance > self.CLICK_DISTANCE_THRESHOLD:
                # 只有当距离超过阈值+迟滞时才重置点击状态
                self.is_click = False
                bc.mouse_up_current_hardware()
                
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
