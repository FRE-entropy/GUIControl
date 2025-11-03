import cv2
import mediapipe as mp
import time
import os
import numpy as np


class HGRUtils:
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

        # 打开摄像头
        self.cap = cv2.VideoCapture(0)

        # 用于计算FPS
        self.p_time = 0
        self.c_time = 0

        self.save_dir = save_dir
        self.save_file = os.path.join(self.save_dir, "hand_landmarks.npy")

        # 确保目录存在
        os.makedirs(self.save_dir, exist_ok=True)

    def get_camera_frame(self):
        """获取摄像头画面"""
        success, image = self.cap.read()
        if not success:
            print("无法读取摄像头画面，退出程序...")
            return None
        return image

    def get_result(self, image):
        """获取手势识别结果"""
        # 为了提高性能，可以选择将图像标记为不可写
        image.flags.writeable = False
        # 将图像从BGR格式转换为RGB格式
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # 处理图像，获取手势检测结果
        results = self.hands.process(image_rgb)
        # 恢复图像的可写状态
        image.flags.writeable = True

        hand_landmarks = []

        if results.multi_hand_landmarks:
            for hand_landmark in results.multi_hand_landmarks:
                hand_landmarks.append(hand_landmark)

        return hand_landmarks

    def get_hand_landmarks(self):
        image = self.get_camera_frame()
        results = self.get_result(image)
        return results

    def add_save_hand_landmark(self, hand_landmark):
        """保存手部关键点"""
        existing_landmarks = self.read_hand_landmarks()
        existing_landmarks.append(hand_landmark)
        self.save_hand_landmarks(existing_landmarks)

    def replace_save_hand_landmark(self, index, hand_landmark):
        """替换手部关键点"""
        if index < 0 or index >= len(self.read_hand_landmarks()):
            print("索引超出范围，无法替换手部关键点")
            return
        existing_landmarks = self.read_hand_landmarks()
        existing_landmarks[index] = hand_landmark
        self.save_hand_landmarks(existing_landmarks)

    def save_hand_landmarks(self, hand_landmarks):
        """保存手部关键点"""
        np.save(self.save_file, hand_landmarks)
        print(f"手部关键点已保存到 {self.save_file}")

    def read_hand_landmarks(self):
        """读取手部关键点"""
        try:
            hand_landmarks = np.load(self.save_file, allow_pickle=True)
        except FileNotFoundError:
            hand_landmarks = []
        return hand_landmarks

    def get_hand_landmark_distance(self, hand_landmark1, hand_landmark2):
        """计算两点之间的距离"""
        return ((hand_landmark1.x - hand_landmark2.x) ** 2 + (hand_landmark1.y - hand_landmark2.y) ** 2) ** 0.5

    #-------------------------------------------------------------------------------------------------------------
    def recognize_gestures(self):
        """实时手势识别主循环"""
        print("手势识别已启动！按ESC键退出...")

        while self.cap.isOpened():
            image = self.get_camera_frame()
            if image is None:
                break

            results = self.get_result(image)

            # 如果检测到手部
            if results:
                for hand_landmarks in results:
                    # 绘制手部关键点和连接线
                    self.mp_drawing.draw_landmarks(
                        image,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing_styles.get_default_hand_landmarks_style(),
                        self.mp_drawing_styles.get_default_hand_connections_style(),
                    )

                    # 获取并显示手部关键点坐标
                    self._process_hand_landmarks(image, hand_landmarks)

            # 计算并显示FPS
            self._calculate_fps(image)

            # 显示结果图像
            cv2.imshow("MediaPipe手势识别", image)

            # 按ESC键退出
            if cv2.waitKey(5) & 0xFF == 27:
                break

    def _process_hand_landmarks(self, image, hand_landmarks):
        """处理手部关键点，这里可以添加自定义手势识别逻辑"""
        h, w, c = image.shape

        # 获取食指指尖坐标
        index_finger_tip = hand_landmarks.landmark[
            self.mp_hands.HandLandmark.INDEX_FINGER_TIP
        ]
        x, y = int(index_finger_tip.x * w), int(index_finger_tip.y * h)

        # 在食指指尖显示坐标
        cv2.putText(
            image,
            f"({x}, {y})",
            (x + 10, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )

        # 这里可以添加手势识别逻辑，例如检测手指的屈伸状态
        # 简单示例：检测食指是否伸直（可以扩展为更复杂的手势识别）
        index_finger_mcp = hand_landmarks.landmark[
            self.mp_hands.HandLandmark.INDEX_FINGER_MCP
        ]
        index_finger_pip = hand_landmarks.landmark[
            self.mp_hands.HandLandmark.INDEX_FINGER_PIP
        ]
        index_finger_dip = hand_landmarks.landmark[
            self.mp_hands.HandLandmark.INDEX_FINGER_DIP
        ]

        # 简单判断食指是否伸直（通过比较各关节的y坐标）
        if (
            index_finger_mcp.y
            > index_finger_pip.y
            > index_finger_dip.y
            > index_finger_tip.y
        ):
            # 使用OpenCV的putText绘制中文
            cv2.putText(
                image, "食指伸直", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
            )

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
    try:
        hand_gesture = HGRUtils()
        hand_gesture.recognize_gestures()
    except Exception as e:
        print(f"程序运行出错: {e}")
    finally:
        # 确保资源被释放
        cv2.destroyAllWindows()
