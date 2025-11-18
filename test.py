from utils.hgr_utils import HGRUtils

hgr_utils = HGRUtils("./data")

while True:
    hand_landmarks = hgr_utils.get_all_hand_landmarks()
    if hand_landmarks is not None and len(hand_landmarks) > 0:
        print(hand_landmarks)
        print(hand_landmarks[0].landmark[hgr_utils.mp_hands.HandLandmark.INDEX_FINGER_TIP])
        break
# hand_landmarks_list = hgr_utils.read_all_hand_landmarks()
# print(hand_landmarks_list)
