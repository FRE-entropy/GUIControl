import time
from ast import main
from utils.hgr_utils import HGRUtils, HandLandmark
from utils.gui_utils import screen_size, scroll_down, move_mouse, wait_key
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
        self.target_fps = 60
        self.frame_time = 1.0 / self.target_fps
        self.function_list = [
            GestureMouse()
        ]


    def test(self):
        hand_landmarks = self.hgr_utils.get_hand_landmarks()
        if not hand_landmarks:
            return
        print(hand_landmarks)
        print(hand_landmarks[0].landmark[
            self.hgr_utils.mp_hands.HandLandmark.INDEX_FINGER_TIP
        ])

    def start(self):
        while True:
            start_time = time.time()
            hand_landmarks_list = self.hgr_utils.get_all_hand_landmarks()
            if len(hand_landmarks_list) == 0:
                continue

            for function in self.function_list:
                function.update(hand_landmarks_list)
            
            # current_hand_landmarks_list = self.hgr_utils.get_all_hand_landmarks()
            # if len(current_hand_landmarks_list) == 0:
            #     continue

            # current_hand_landmarks = current_hand_landmarks_list[0]

            # self.GestureQueue.put(current_hand_landmarks)

            # if self.GestureQueue.qsize() >= 10:
            #     hand_landmarks_p = self.GestureQueue.get()
            #     if self.find_gesture(current_hand_landmarks) == 1 and\
            #         self.find_gesture(hand_landmarks_p) == 0:
            #         print(" gesture 1 -> 0", end="\r")
            #         # 翻页
            #         if not self.signs["scroll_down"]:
            #             scroll_down()
            #         self.signs["scroll_down"] = True
            #     else:
            #         print("                     ", end="\r")
            #         self.signs["scroll_down"] = False

            # 等待到下一个帧的时间
            elapsed_time = time.time() - start_time
            if elapsed_time < self.frame_time:
                wait_time = self.frame_time - elapsed_time
                time.sleep(wait_time)
        
    def find_gesture(self, current_hand_landmarks):
        for i, hand_landmarks in enumerate(self.hand_landmarks_list):
            distance = self.hgr_utils.get_hand_landmark_distance(current_hand_landmarks, hand_landmarks)
            if distance < 1:
                return i
        return None


class GestureMouse:
    def __init__(self):
        self.is_click = False
        self.location_list = [[0, 0]] * 3
        self.scale = 1.2

    def update(self, hand_landmarks_list):
        if len(hand_landmarks_list) == 0:
            return
        current_hand_landmarks = hand_landmarks_list[0]

        thumb_tip = current_hand_landmarks[HandLandmark.THUMB_TIP]
        index_finger_tip = current_hand_landmarks[HandLandmark.INDEX_FINGER_TIP]

        dx = index_finger_tip[0] - thumb_tip[0]
        dy = index_finger_tip[1] - thumb_tip[1]

        x = (1 - (index_finger_tip[0] + thumb_tip[0]) / 2) * screen_size[0]
        y = (index_finger_tip[1] + thumb_tip[1]) / 2 * screen_size[1]
        # scale_x = x * self.scale
        # scale_y = y * self.scale
        # x = scale_x - (scale_x - x) / 2
        # y = scale_y - (scale_y - y) / 2

        distance = (dx**2 + dy**2)**0.5 * 10
        self.location_list.append([x, y])
        self.location_list.pop(0)
        print(distance, "       ", end="\r")

        average_location = [sum([location[i] for location in self.location_list]) / len(self.location_list) for i in range(2)]

        move_mouse(*average_location)

        if distance < 1:
            if not self.is_click:
                print("click")
                self.is_click = True
        else:
            self.is_click = False



if __name__ == "__main__":
    gesture_control = GestureControl()
    gesture_control.start()
