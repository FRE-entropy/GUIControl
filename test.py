from utils.hgr_utils import HGRUtils

hgr_utils = HGRUtils("./data")

while True:
    hand_landmarks = hgr_utils.get_all_hand_landmarks()
    if hand_landmarks:
        print(hand_landmarks[0])
        hgr_utils.replace_save_hand_landmarks(0, hand_landmarks[0])
        break
# hand_landmarks_list = hgr_utils.read_all_hand_landmarks()
# print(hand_landmarks_list)
