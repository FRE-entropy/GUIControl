from utils.hgr_utils import HGRUtils

hgr_utils = HGRUtils("./data")

hand_landmarks = hgr_utils.get_hand_landmarks()
hgr_utils.add_save_hand_landmark(hand_landmarks)
