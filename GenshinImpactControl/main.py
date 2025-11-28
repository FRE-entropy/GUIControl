import sys
import os
import time
import mido

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.logger import logger
from utils.gui_utils import GUIController


class GenshinImpactMusicPlayer:
    def __init__(self):
        self.controller = GUIController()
        self.music_score_text = ""
        self.music_score = []
        self.duration = 0.1
        self.pressed_keys = []
        self.map = {
            48: "z",
            50: "x",
            52: "c",
            53: "v",
            55: "b",
            57: "n",
            59: "m",
            60: "a",
            62: "s",
            64: "d",
            65: "f",
            67: "g",
            69: "h",
            71: "j",
            72: "q",
            74: "w",
            76: "e",
            77: "r",
            79: "t",
            81: "y",
            83: "u",
        }
        self.min_time = 0.03
        self.bpm = 240
        self.tempo = 60 / self.bpm


    def read_midi(self, file_path):
        if not os.path.exists(file_path):
            logger.error(f"file {file_path} not exists")
            return None
        return mido.MidiFile(file_path)

    def mode_recognition(self, midi):
        if midi is None:
            return None

        # 获取midi中所有音组成的音阶
        
    def play_midi(self, file_path):
        # 检测文件是否存在
        mid = self.read_midi(file_path)
        if mid is None:
            return

        for track in mid.tracks:
            for i in range(len(track)):
                msg = track[i].dict()
                print(msg)
                if "note" not in msg.keys():
                    continue
                
                for j in range(i + 1, len(track)):
                    next_msg_time = track[j + 1].dict()["time"]
                    if next_msg_time > 0:
                        break
                
                delete_time = msg["time"] / mid.ticks_per_beat * self.tempo
                if self.min_time < delete_time:
                    time.sleep(delete_time - (self.min_time if next_msg_time / mid.ticks_per_beat * self.tempo < self.min_time else 0))
                elif 0 < msg["time"]:
                    time.sleep(delete_time + self.min_time)

                if msg["note"] not in self.map.keys():
                    logger.error(f"note {msg['note']} not in map")
                    continue
                if msg["type"] == "note_on" and msg["velocity"] > 0:
                    logger.info(f"press {self.map[msg['note']]}")
                    self.controller.key(self.map[msg["note"]], True)
                elif msg["type"] == "note_off" or msg["velocity"] == 0:
                    logger.info(f"release {self.map[msg['note']]}")
                    self.controller.key(self.map[msg["note"]], False)


    def read(self, file_path):
        with open(file_path, "r") as f:
            music_score_text = f.read()

        messages, music_score_text = music_score_text.split("\n", 1)

        self.duration = float(messages)

        music_score_list = music_score_text.split(",")
        self.music_score = []
        for note in music_score_list:
            if ":" in note:
                downs, continues = note.strip(":")
                continues = [i for i in continues.strip()]
            else:
                downs = note.strip()
                continues = []
            downs = [i for i in downs.strip()]
            self.music_score.append((downs, continues))

    def __del__(self):
        for key in self.map.values():
            self.controller.key(key, False)
            
if __name__ == "__main__":
    # 检测按下某快捷键开始播放
    time.sleep(1)

    music_player = GenshinImpactMusicPlayer()
    # music_player.play_midi("./data/music/2.mid")
    music_player.play_midi("./data/music/离月_music.midi")
    # music_player.play_music_score()
