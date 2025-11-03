import cv2
import mediapipe as mp
import time
import os
import numpy as np

class HandGestureRecognition:
    def __init__(self):
        # 初始化MediaPipe手势识别模型
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,       # 连续视频模式
            max_num_hands=2,              # 最多检测2只手
            min_detection_confidence=0.7, # 检测置信度阈值
            min_tracking_confidence=0.5   # 跟踪置信度阈值
        )
        
        # 用于绘制手部关键点的工具
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # 打开摄像头
        self.cap = cv2.VideoCapture(0)
        
        # 用于计算FPS
        self.p_time = 0
        self.c_time = 0
        
        # 设置中文字体
        self._set_chinese_font()
    
    def _set_chinese_font(self):
        """设置支持中文的字体"""
        # Windows系统下的中文字体路径
        if os.name == 'nt':  # Windows系统
            # 尝试几种常见的中文字体
            fonts_to_try = ['simhei', 'simkai', 'simsun', 'microsoftyahei']
            self.font = None
            
            for font_name in fonts_to_try:
                try:
                    # 尝试使用指定字体
                    temp_img = cv2.imread(0)
                    if temp_img is None:
                        temp_img = np.zeros((100, 100, 3), np.uint8)
                    cv2.putText(temp_img, "测试", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    self.font = cv2.FONT_HERSHEY_SIMPLEX
                    break
                except:
                    continue
        
        # 如果没有找到合适的字体，使用默认字体并做特殊处理
        if self.font is None:
            self.font = cv2.FONT_HERSHEY_SIMPLEX
            print("警告：可能无法正常显示中文，请确保系统中安装了中文字体")
            
    def recognize_gestures(self):
        """实时手势识别主循环"""
        print("手势识别已启动！按ESC键退出...")
        
        while self.cap.isOpened():
            success, image = self.cap.read()
            if not success:
                print("无法读取摄像头画面，退出程序...")
                break
            
            # 为了提高性能，可以选择将图像标记为不可写
            image.flags.writeable = False
            
            # 将图像从BGR格式转换为RGB格式
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 处理图像，获取手势检测结果
            results = self.hands.process(image_rgb)
            
            # 恢复图像的可写状态
            image.flags.writeable = True
            
            # 如果检测到手部
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # 绘制手部关键点和连接线
                    self.mp_drawing.draw_landmarks(
                        image,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing_styles.get_default_hand_landmarks_style(),
                        self.mp_drawing_styles.get_default_hand_connections_style()
                    )
                    
                    # 获取并显示手部关键点坐标
                    self._process_hand_landmarks(image, hand_landmarks)
            
            # 计算并显示FPS
            self._calculate_fps(image)
            
            # 显示结果图像
            cv2.imshow('MediaPipe手势识别', image)
            
            # 按ESC键退出
            if cv2.waitKey(5) & 0xFF == 27:
                break
    
    def _process_hand_landmarks(self, image, hand_landmarks):
        """处理手部关键点，这里可以添加自定义手势识别逻辑"""
        h, w, c = image.shape
        
        # 获取食指指尖坐标
        index_finger_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        x, y = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
        
        # 在食指指尖显示坐标
        cv2.putText(image, f'({x}, {y})', (x + 10, y - 10),
                    self.font, 0.5, (0, 255, 0), 2)
        
        # 这里可以添加手势识别逻辑，例如检测手指的屈伸状态
        # 简单示例：检测食指是否伸直（可以扩展为更复杂的手势识别）
        index_finger_mcp = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_MCP]
        index_finger_pip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_PIP]
        index_finger_dip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_DIP]
        
        # 简单判断食指是否伸直（通过比较各关节的y坐标）
        if (index_finger_mcp.y > index_finger_pip.y > index_finger_dip.y > index_finger_tip.y):
            # 使用OpenCV的putText绘制中文
            cv2.putText(image, '食指伸直', (10, 50),
                        self.font, 1, (0, 255, 0), 2)
    
    def _calculate_fps(self, image):
        """计算并显示FPS"""
        self.c_time = time.time()
        fps = 1 / (self.c_time - self.p_time)
        self.p_time = self.c_time
        
        cv2.putText(image, f'FPS: {int(fps)}', (10, 30),
                    self.font, 1, (255, 0, 0), 2)
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'cap'):
            self.cap.release()
        cv2.destroyAllWindows()
        print("程序已退出，资源已释放")

if __name__ == "__main__":
    try:
        hand_gesture = HandGestureRecognition()
        hand_gesture.recognize_gestures()
    except Exception as e:
        print(f"程序运行出错: {e}")
    finally:
        # 确保资源被释放
        cv2.destroyAllWindows()