import sys
import os
import time
import mido

sys.path.append("../")

from utils.logger import Logger
from utils.gui_utils import GUIController

mi_keys = {
    "C.": "Q",
    "D.": "W",
    "E.": "E",
    "F.": "R",
    "G.": "T",
    "A.": "Y",
    "B.": "U",
    "C": "A",
    "D": "S",
    "E": "D",
    "F": "F",
    "G": "G",
    "A": "H",
    "B": "J",
    "'C": "Z",
    "'D": "X",
    "'E": "C",
    "'F": "V",
    "'G": "B",
    "'A": "N",
    "'B": "M",
}

class GenshinImpactMusicPlayer:
    def __init__(self):
        self.controller = GUIController()
        self.speed = 1000
        self.music_score_text = ""
        self.music_score = []
        self.duration = 0.1
        self.pressed_keys = []
        self.map = {
            48: "Z",
            50: "X",
            52: "C",
            53: "V",
            55: "B",
            57: "N",
            59: "M",
            60: "A",
            62: "S",
            64: "D",
            65: "F",
            67: "G",
            69: "H",
            71: "J",
            72: "Q",
            74: "W",
            76: "E",
            77: "R",
            79: "T",
            81: "Y",
            83: "U",
        }

    def play_midi(self, file_path):
        mid = mido.MidiFile(file_path)
        for track in mid.tracks:
            for msg in track:
                msg = msg.dict()
                if "note" not in msg.keys():
                    continue
                if self.controller.wait_hotkey_press(
                    "ctrl", "c", 
                    timeout=msg["time"] / self.speed
                    ):
                    return
                if msg["note"] not in self.map.keys():
                    Logger.error(f"note {msg['note']} not in map")
                    continue
                if msg["type"] == "note_on":
                    self.controller.key(self.map[msg["note"]], True)
                elif msg["type"] == "note_off":
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
            
if __name__ == "__main__":
    # 检测按下某快捷键开始播放
    time.sleep(1)

    music_player = GenshinImpactMusicPlayer()
    music_player.play_midi("./data/music/2.mid")
    # music_player.play_music_score()
