import cv2
import mediapipe as mp
from mediapipe.python.solutions.hands import HandLandmark
import time
import os
import numpy as np
from collections import deque


class HGRUtils:
    """
    手势识别工具类
    """
    def __init__(self, save_dir=""):
        # 初始化MediaPipe手势识别模型
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,  # 连续视频模式
            max_num_hands=2,  # 最多检测2只手
            min_detection_confidence=0.7,  # 检测置信度阈值
            min_tracking_confidence=0.5,  # 跟踪置信度阈值
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

    def get_camera_frame(self):
        """获取摄像头画面"""
        success, image = self.cap.read()
        if not success:
            print("无法读取摄像头画面，退出程序...")
            return None
        return image

    def get_result(self, image, array=True):
        """获取手势识别结果（优化版本）"""
        if image is None:
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
            for hand_landmarks in results.multi_hand_landmarks:
                if array:
                    # 预分配数组，避免重复内存分配
                    landmarks_array = np.empty((21, 3), dtype=np.float32)
                    for i, landmark in enumerate(hand_landmarks.landmark):
                        landmarks_array[i] = [landmark.x, landmark.y, landmark.z]
                    hand_landmarks_list.append(landmarks_array)
                else:
                    hand_landmarks_list.append(hand_landmarks)

        return hand_landmarks_list

    def get_all_hand_landmarks(self):
        """获取所有手部关键点（优化版本）"""
        # 跳帧处理：每2帧处理一次，提高性能
        self._frame_counter += 1
        if self._frame_counter % 2 != 0 and self._last_results is not None:
            return self._last_results
        
        image = self.get_camera_frame()
        if image is None:
            return []
            
        results = self.get_result(image)
        self._last_results = results  # 缓存结果
        return results

    def add_save_hand_landmarks(self, hand_landmarks):
        """保存手部关键点"""
        if self.hand_landmarks_list.size == 0:
            self.hand_landmarks_list = np.array([hand_landmarks])
        else:
            self.hand_landmarks_list = np.append(self.hand_landmarks_list, [hand_landmarks], axis=0)
        self.save_all_hand_landmarks(self.hand_landmarks_list)

    def replace_save_hand_landmarks(self, index, hand_landmarks):
        """替换手部关键点"""
        if index < 0 or index >= len(self.read_all_hand_landmarks()):
            print("索引超出范围，无法替换手部关键点")
            return
        existing_landmarks = self.read_all_hand_landmarks()
        existing_landmarks[index] = hand_landmarks
        self.save_all_hand_landmarks(existing_landmarks)

    def save_all_hand_landmarks(self, hand_landmarks_list):
        """保存手部关键点"""
        np.save(self.save_file, hand_landmarks_list)
        print(f"手部关键点已保存到 {self.save_file}")

    def read_all_hand_landmarks(self):
        """读取手部关键点"""
        try:
            hand_landmarks_list = np.load(self.save_file, allow_pickle=True)
            print(f"手部关键点已从 {self.save_file} 加载")
        except FileNotFoundError:
            hand_landmarks_list = np.array([])
        return hand_landmarks_list

    def get_hand_landmark_distance(self, hand_landmark1, hand_landmark2):
        hand_landmark1 = self.to_relative(hand_landmark1)
        hand_landmark2 = self.to_relative(hand_landmark2)

        if hand_landmark1 is None or hand_landmark2 is None:
            return 0.0
            
        # 计算欧几里得距离
        distance = np.linalg.norm(hand_landmark1 - hand_landmark2)
        
        return distance

    def to_relative(self, hand_landmarks):
        """将手部关键点转换为相对坐标"""
        # 添加错误处理和类型检查
        if hand_landmarks is None or len(hand_landmarks) == 0:
            print("错误：输入的手部关键点为空")
            return hand_landmarks
        
        # 确保输入是numpy数组
        if not isinstance(hand_landmarks, np.ndarray):
            hand_landmarks = np.array(hand_landmarks)
        
        relative_landmarks = [[0, 0, 0]]
        
        # 计算其他点相对于手腕点的坐标
        for i in range(1, len(hand_landmarks)):
            relative_landmarks.append(hand_landmarks[i] - hand_landmarks[0])
        
        return np.array(relative_landmarks)

    def show_hand_landmarks(self, image, hand_landmarks: np.ndarray):
        """显示手部关键点"""
        # 绘制手部关键点和连接线
        self.mp_drawing.draw_landmarks(
            image,
            hand_landmarks,
            self.mp_hands.HAND_CONNECTIONS,
            self.mp_drawing_styles.get_default_hand_landmarks_style(),
            self.mp_drawing_styles.get_default_hand_connections_style(),
        )

    #-------------------------------------------------------------------------------------------------------------
    def recognize_gestures(self):
        """实时手势识别主循环"""
        print("手势识别已启动！按ESC键退出...")

        while self.cap.isOpened():
            image = self.get_camera_frame()
            if image is None:
                break

            results = self.get_result(image, array=False)

            # 如果检测到手部
            if results:
                for hand_landmarks in results:
                    # 绘制手部关键点和连接线
                    self.show_hand_landmarks(image, hand_landmarks)

            # 计算并显示FPS
            self._calculate_fps(image)

            # 显示结果图像
            cv2.imshow("MediaPipe手势识别", image)

            # 按ESC键退出
            if cv2.waitKey(5) & 0xFF == 27:
                break

    def _calculate_fps(self, image):
        """计算并显示FPS"""
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

    def __del__(self):
        """清理资源"""
        if hasattr(self, "cap"):
            self.cap.release()
        cv2.destroyAllWindows()
        print("程序已退出，资源已释放")


if __name__ == "__main__":
    hand_gesture = HGRUtils("../data")
    hand_gesture.recognize_gestures()
