import time
from ast import main
from utils.hgr_utils import HGRUtils
from queue import Queue

"""
  WRIST : 手腕
  THUMB_CMC : 拇指CMC
  THUMB_MCP : 拇指MCP
  THUMB_IP : 拇指IP
  THUMB_TIP : 拇指TIP
  INDEX_FINGER_MCP : 食指MCP
  INDEX_FINGER_PIP : 食指PIP
  INDEX_FINGER_DIP : 食指DIP
  INDEX_FINGER_TIP : 食指TIP
  MIDDLE_FINGER_MCP : 中指MCP
  MIDDLE_FINGER_PIP : 中指PIP
  MIDDLE_FINGER_DIP : 中指DIP
  MIDDLE_FINGER_TIP : 中指TIP
  RING_FINGER_MCP : 无名指MCP
  RING_FINGER_PIP : 无名指PIP
  RING_FINGER_DIP : 无名指DIP
  RING_FINGER_TIP : 无名指TIP
  PINKY_MCP : 小指MCP
  PINKY_PIP : 小指PIP
  PINKY_DIP : 小指DIP
  PINKY_TIP : 小指TIP
"""

class GestureControl:
    def __init__(self):
        self.hgr_utils = HGRUtils("./data")
        self.GestureQueue = Queue()
        self.target_fps = 30
        self.frame_time = 1.0 / self.target_fps
        self.hand_landmarks = self.hgr_utils.read_hand_landmarks()


    def test(self):
        hand_landmarks = self.hgr_utils.get_hand_landmarks()
        print(hand_landmarks)
        print(len(hand_landmarks[0].landmark[
            self.hgr_utils.mp_hands.HandLandmark.INDEX_FINGER_TIP
        ]))

    def start(self):
        while True:
            start_time = time.time()

            hand_landmarks = self.hgr_utils.get_hand_landmarks()
            if hand_landmarks:
                self.GestureQueue.put(hand_landmarks[0])

            if self.GestureQueue.qsize() >= 10:
                self.GestureQueue.get()

            # 等待到下一个帧的时间
            elapsed_time = time.time() - start_time
            if elapsed_time < self.frame_time:
                time.sleep(self.frame_time - elapsed_time)


if __name__ == "__main__":
    gesture_control = GestureControl()
    gesture_control.test()