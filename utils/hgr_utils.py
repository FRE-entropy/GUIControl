import cv2
import mediapipe as mp
from mediapipe.python.solutions.hands import HandLandmark
import time
import os
import numpy as np
from collections import deque
from typing import List, Tuple, Optional, Dict, Any
from .logger import logger


class HGRUtils:
    """
    手势识别工具类
    """
    def __init__(self, save_dir=""):
        logger.debug(f"初始化HGRUtils，保存目录: {save_dir}")
        # 初始化MediaPipe手势识别模型
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,  # 连续视频模式
            max_num_hands=1,  # 最多检测1只手，提高性能
            min_detection_confidence=0.7,  # 降低检测置信度阈值，提高响应性
            min_tracking_confidence=0.5,  # 降低跟踪置信度阈值，提高性能
        )

        # 用于绘制手部关键点的工具
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        # 打开摄像头并优化设置
        self.cap = cv2.VideoCapture(0)
        # 设置较低的摄像头分辨率以提高性能
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        # 用于计算FPS
        self.p_time = 0
        self.c_time = 0

        self.save_dir = save_dir
        self.save_file = os.path.join(self.save_dir, "hand_landmarks.npy")

        # 确保目录存在
        os.makedirs(self.save_dir, exist_ok=True)

        self.hand_landmarks_list = self.read_all_hand_landmarks()
        
        # 性能优化：预分配内存和缓存
        self._frame_cache = None
        self._last_results = None
        self._frame_counter = 0
        self._skip_frames = 0  # 跳帧计数器，用于降低处理频率
        
        logger.debug("HGRUtils初始化完成")

    def get_camera_frame(self):
        """获取摄像头画面"""
        logger.debug("开始获取摄像头画面")
        success, image = self.cap.read()
        if not success:
            logger.error("无法读取摄像头画面，退出程序...")
            return None
        logger.debug("摄像头画面获取成功")
        return image

    def get_result(self, image, array=True):
        """获取手势识别结果（优化版本）"""
        logger.debug(f"开始获取手势识别结果，array模式: {array}")
        if image is None:
            logger.warning("输入图像为空，返回空列表")
            return []
            
        # 为了提高性能，可以选择将图像标记为不可写
        image.flags.writeable = False
        # 将图像从BGR格式转换为RGB格式
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # 处理图像，获取手势检测结果
        results = self.hands.process(image_rgb)
        # 恢复图像的可写状态
        image.flags.writeable = True

        hand_landmarks_list = []

        if results.multi_hand_landmarks:
            logger.debug(f"检测到 {len(results.multi_hand_landmarks)} 只手")
            for hand_landmarks in results.multi_hand_landmarks:
                if array:
                    # 预分配数组，避免重复内存分配
                    landmarks_array = np.empty((21, 3), dtype=np.float32)
                    for i, landmark in enumerate(hand_landmarks.landmark):
                        landmarks_array[i] = [landmark.x, landmark.y, landmark.z]
                    hand_landmarks_list.append(landmarks_array)
                else:
                    hand_landmarks_list.append(hand_landmarks)
        else:
            logger.debug("未检测到手部")

        logger.debug(f"手势识别完成，返回 {len(hand_landmarks_list)} 个手部关键点")
        return hand_landmarks_list

    def get_all_hand_landmarks(self):
        """获取所有手部关键点（优化版本）"""
        logger.debug("开始获取所有手部关键点")
        
        image = self.get_camera_frame()
        if image is None:
            return [], None
            
        results = self.get_result(image)
        logger.debug(f"获取到 {len(results)} 个手部关键点")
        return results, image

    def add_save_hand_landmarks(self, hand_landmarks):
        """保存手部关键点"""
        logger.debug("开始添加并保存手部关键点")
        if len(self.hand_landmarks_list) == 0:
            logger.debug("手部关键点列表为空，创建新列表")
            self.hand_landmarks_list = np.array([hand_landmarks])
        else:
            logger.debug("手部关键点列表已存在，追加新关键点")
            self.hand_landmarks_list = np.append(self.hand_landmarks_list, [hand_landmarks], axis=0)
        self.save_all_hand_landmarks(self.hand_landmarks_list)
        logger.debug("手部关键点添加并保存完成")

    def replace_save_hand_landmarks(self, index, hand_landmarks):
        """替换手部关键点"""
        logger.debug(f"开始替换手部关键点，索引: {index}")
        if index < 0 or index >= len(self.read_all_hand_landmarks()):
            logger.error("索引超出范围，无法替换手部关键点")
            return
        existing_landmarks = self.read_all_hand_landmarks()
        existing_landmarks[index] = hand_landmarks
        self.save_all_hand_landmarks(existing_landmarks)
        logger.debug("手部关键点替换完成")

    def save_all_hand_landmarks(self, hand_landmarks_list):
        """保存手部关键点"""
        logger.debug(f"开始保存手部关键点，数量: {len(hand_landmarks_list)}")
        np.save(self.save_file, hand_landmarks_list)
        logger.info(f"手部关键点已保存到 {self.save_file}")
        logger.debug("手部关键点保存完成")

    def read_all_hand_landmarks(self):
        """读取手部关键点"""
        logger.debug("开始读取手部关键点")
        try:
            hand_landmarks_list = np.load(self.save_file, allow_pickle=True)
            logger.info(f"手部关键点已从 {self.save_file} 加载")
            logger.debug(f"读取到 {len(hand_landmarks_list)} 个手部关键点")
        except FileNotFoundError:
            logger.warning(f"手部关键点文件 {self.save_file} 不存在，返回空数组")
            hand_landmarks_list = np.array([])
        logger.debug("手部关键点读取完成")
        return hand_landmarks_list

    def get_hand_landmark_distance(self, hand_landmark1, hand_landmark2):
        logger.debug("开始计算手部关键点距离")
        hand_landmark1 = self.to_relative(hand_landmark1)
        hand_landmark2 = self.to_relative(hand_landmark2)

        if hand_landmark1 is None or hand_landmark2 is None:
            logger.warning("手部关键点为空，返回距离0.0")
            return 0.0
            
        # 计算欧几里得距离
        distance = np.linalg.norm(hand_landmark1 - hand_landmark2)
        logger.debug(f"手部关键点距离计算完成: {distance}")
        
        return distance

    def to_relative(self, hand_landmarks):
        """将手部关键点转换为相对坐标"""
        logger.debug("开始转换手部关键点为相对坐标")
        # 添加错误处理和类型检查
        if hand_landmarks is None or len(hand_landmarks) == 0:
            logger.error("错误：输入的手部关键点为空")
            return hand_landmarks
        
        # 确保输入是numpy数组
        if not isinstance(hand_landmarks, np.ndarray):
            logger.debug("输入不是numpy数组，转换为numpy数组")
            hand_landmarks = np.array(hand_landmarks)
        
        relative_landmarks = [[0, 0, 0]]
        
        # 计算其他点相对于手腕点的坐标
        for i in range(1, len(hand_landmarks)):
            relative_landmarks.append(hand_landmarks[i] - hand_landmarks[0])
        
        logger.debug("手部关键点相对坐标转换完成")
        return np.array(relative_landmarks)

    def show_hand_landmarks(self, image, hand_landmarks: np.ndarray):
        """显示手部关键点"""
        logger.debug("开始绘制手部关键点")
        # 绘制手部关键点和连接线
        self.mp_drawing.draw_landmarks(
            image,
            hand_landmarks,
            self.mp_hands.HAND_CONNECTIONS,
            self.mp_drawing_styles.get_default_hand_landmarks_style(),
            self.mp_drawing_styles.get_default_hand_connections_style(),
        )
        logger.debug("手部关键点绘制完成")

    def recognize_gestures(self):
        """实时手势识别主循环"""
        logger.info("手势识别已启动！按ESC键退出...")

        while self.cap.isOpened():
            logger.debug("开始处理摄像头帧")
            image = self.get_camera_frame()
            if image is None:
                logger.warning("无法获取摄像头画面，退出循环")
                break

            # 如果检测到手部
            self.display_results(image)

            # 计算并显示FPS
            self._calculate_fps(image)

            # 按ESC键退出
            if cv2.waitKey(5) & 0xFF == 27:
                logger.info("检测到ESC键，退出手势识别")
                break
            logger.debug("摄像头帧处理完成")
    
    def display_results(self, image):
        """显示图像"""
        logger.debug("开始显示手势识别结果")
        results = self.get_result(image, array=False)
        if results is not None and len(results) > 0 and image is not None:
            logger.debug(f"检测到 {len(results)} 只手，开始绘制关键点")
            for hand_landmarks in results:
                # 绘制手部关键点和连接线
                self.show_hand_landmarks(image, hand_landmarks)
            # 显示结果图像
        cv2.imshow("MediaPipe手势识别", image)
        # 使用非阻塞的waitKey，避免程序阻塞
        cv2.waitKey(1)
        logger.debug("手势识别结果显示完成")

    def _calculate_fps(self, image):
        """计算并显示FPS"""
        logger.debug("开始计算FPS")
        self.c_time = time.time()
        fps = 1 / (self.c_time - self.p_time)
        self.p_time = self.c_time

        cv2.putText(
            image,
            f"FPS: {int(fps)}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 0, 0),
            2,
        )
        logger.debug(f"FPS计算完成: {int(fps)}")

    def __del__(self):
        """清理资源"""
        logger.debug("开始清理HGRUtils资源")
        if hasattr(self, "cap"):
            logger.debug("释放摄像头资源")
            self.cap.release()
        cv2.destroyAllWindows()
        logger.info("程序已退出，资源已释放")
        logger.debug("HGRUtils资源清理完成")


if __name__ == "__main__":
    hand_gesture = HGRUtils("../data")
    hand_gesture.recognize_gestures()
