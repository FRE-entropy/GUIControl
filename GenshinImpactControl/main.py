import sys
import os
import time
import mido
import argparse
import pygetwindow as gw
import tkinter as tk
from tkinter import filedialog, ttk
import threading

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
        self.bpm = 120
        self.tempo = 60 / self.bpm
        self.ticks_per_beat = 0
        self.min_release_time = 0.05


    def read_midi(self, file_path):
        if not os.path.exists(file_path):
            logger.error(f"file {file_path} not exists")
            return None
        return mido.MidiFile(file_path)

    def to_list(self, mid):
        track_list = []
        for track in mid.tracks:
            track_list.append([])
            for msg in track:
                track_list[-1].append(msg.dict())
        return track_list

    def mode_recognition(self, mid_list, track_num=1):
        """
        识别MIDI文件的调式，只识别大调小调，处理少量调外音
        返回值：-1表示小调，C大调为0，D大调为1，以此类推
        """
        logger.info("开始识别调式")
        
        if not mid_list:
            logger.info("mid_list为空，返回None")
            return None
        
        # 将从1开始的音轨编号转换为从0开始的索引
        actual_track_num = track_num - 1
        
        # 检查actual_track_num是否在有效范围内
        if actual_track_num < 0 or actual_track_num >= len(mid_list):
            logger.error(f"音轨编号 {track_num} 超出范围，总共有 {len(mid_list)} 条音轨")
            return None
        
        # 只使用指定音轨的音符进行统计
        all_notes = []
        if mid_list[actual_track_num]:
            first_track = mid_list[actual_track_num]
            logger.info(f"使用第{track_num}条轨道进行统计，事件数量: {len(first_track)}")
            
            for msg in first_track:
                if "note" in msg and msg["type"] == "note_on":
                    all_notes.append(msg["note"])
        
        logger.info(f"提取到的音符数量: {len(all_notes)}")
        
        if not all_notes:
            logger.info("没有提取到音符，返回None")
            return None
        
        # 统计每个音级的出现频率
        pitch_class_counts = {}
        total_notes = 0
        for note in all_notes:
            pitch_class = note % 12  # 0=C, 1=C#, ..., 11=B
            if pitch_class in pitch_class_counts:
                pitch_class_counts[pitch_class] += 1
            else:
                pitch_class_counts[pitch_class] = 1
            total_notes += 1
        
        # 大调的音级模式（全全半全全全半）
        major_scale = [0, 2, 4, 5, 7, 9, 11]
        # 小调的音级模式（全半全全半全全）
        minor_scale = [0, 2, 3, 5, 7, 8, 10]
        
        # 计算每个可能的调式的匹配度
        best_score = 0
        best_key = None
        is_minor = False
        
        # 测试所有可能的大调（12个）和小调（12个）
        for root in range(12):
            # 计算大调匹配度：只统计调内音的出现次数，忽略调外音
            major_score = 0
            for pitch_class, count in pitch_class_counts.items():
                if (pitch_class - root) % 12 in major_scale:
                    major_score += count
            
            # 计算小调匹配度：只统计调内音的出现次数，忽略调外音
            minor_score = 0
            for pitch_class, count in pitch_class_counts.items():
                if (pitch_class - root) % 12 in minor_scale:
                    minor_score += count
            
            # 增加大调的权重，因为大调通常更常见，且算法容易误判
            major_score *= 1.1
            
            # 更新最佳匹配
            if major_score > best_score:
                best_score = major_score
                best_key = root
                is_minor = False
            if minor_score > best_score:
                best_score = minor_score
                best_key = root
                is_minor = True
        
        # 返回结果：-1表示小调，大调返回对应的数值
        if is_minor:
            logger.info(f"识别到调式: 小调 (根音: {best_key})")
            return -1
        else:
            # 大调返回对应的数值，C大调为0，D大调为1，以此类推
            # 扩展支持所有12个大调，不仅仅是自然大调
            # 计算根音对应的大调名称
            major_key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            key_name = major_key_names[best_key]
            logger.info(f"识别到调式: {key_name}大调 (根音: {best_key})")
            # 返回根音值，用于后续转换
            return best_key 

    def optimize_note_timing(self, mid_list, track_num=1):
        """
        优化音符时间，解决同一个键快速松开按下导致听不出松开效果的问题
        """
        # 将从1开始的音轨编号转换为从0开始的索引
        actual_track_num = track_num - 1
        
        # 检查actual_track_num是否在有效范围内
        if actual_track_num < 0 or actual_track_num >= len(mid_list):
            logger.error(f"音轨编号 {track_num} 超出范围，总共有 {len(mid_list)} 条音轨")
            return mid_list
        
        min_release_ticks = self.min_release_time * self.ticks_per_beat / self.tempo
        track = mid_list[actual_track_num]
        
        # 遍历音轨中的所有消息，记录每个音符的状态
        i = 0
        while i < len(track):
            msg = track[i]
            # 只处理有时间间隔的note_on消息（velocity不为0）
            if msg["type"] == "note_on" and msg["velocity"] != 0:
                if msg["time"] < min_release_ticks:
                    ticks_diff = min_release_ticks - msg["time"]
                    # 查找前一个对应的note_off消息（或velocity为0的note_on）
                    # 从i-1开始向前查找，直到找到对应的note_off或到达音轨开头
                    for j in range(i - 1, -1, -1):
                        prev_msg = track[j]
                        # 检查是否是同一音符的note_off消息
                        if (prev_msg["type"] == "note_off" or (prev_msg["type"] == "note_on" and prev_msg["velocity"] == 0)) and "note" in prev_msg and prev_msg["note"] == msg["note"]:
                            # 检查前一个消息是否有时间间隔可以调整
                            if prev_msg["time"] > ticks_diff + min_release_ticks:
                                # 增加当前note_on的时间间隔
                                track[j + 1]["time"] += ticks_diff
                                # 减少前一个note_off的时间间隔，保持总时长不变
                                track[j]["time"] -= ticks_diff
                                break
            i += 1

        mid_list[actual_track_num] = track
        return mid_list
    
    def adjust_midi(self, mid_list, track_num=1):
        mode = self.mode_recognition(mid_list, track_num)
        # 使用12个大调名称列表，支持所有大调
        major_key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        logger.info(f"最终识别结果: {'小调' if mode == -1 else f'{major_key_names[mode]}大调' if mode is not None else '未知调式'}")
        
        # 如果没有识别到调式，直接返回
        if mode is None:
            return mid_list
        
        # 计算从当前调式到C大调的半音差
        if mode != -1:  # 大调
            current_root = mode  # mode现在直接返回根音值
            semitone_diff = -current_root  # 转换到C大调需要调整的半音数
        else:  # 小调
            # 小调暂时不处理，直接返回
            return mid_list
        
        logger.info(f"当前调式根音: {current_root}, 转换到C大调需要调整: {semitone_diff}个半音")
        
        # 首先收集所有音符，计算整体调整策略
        all_notes = []
        for track in mid_list:
            for msg in track:
                if "note" in msg:
                    all_notes.append(msg["note"])
        
        # 计算所有音符的平均音高
        if all_notes:
            avg_note = sum(all_notes) / len(all_notes)
            # 调整半音后，计算平均音高
            avg_adjusted_note = avg_note + semitone_diff
            
            # map包含的音符范围：48-83
            min_map_note = min(self.map.keys())
            max_map_note = max(self.map.keys())
            map_center = (min_map_note + max_map_note) / 2
            
            # 计算八度调整值，使得平均音高尽量接近map中心
            octave_diff = int((map_center - avg_adjusted_note) / 12)
            # 应用八度调整，保持相对音高不变
            total_semitone_diff = semitone_diff + (octave_diff * 12)
            
            logger.info(f"所有音符平均音高: {avg_note:.2f}, 调整半音后: {avg_adjusted_note:.2f}")
            logger.info(f"Map中心音高: {map_center:.2f}, 八度调整: {octave_diff}个八度, 总半音调整: {total_semitone_diff}个半音")
        else:
            total_semitone_diff = semitone_diff
            logger.info("没有找到音符，只进行调式半音调整")
        
        # 调整所有音符，保持相对音高不变
        adjusted_mid_list = []
        for track in mid_list:
            adjusted_track = []
            for msg in track:
                adjusted_msg = msg.copy()
                if "note" in adjusted_msg:
                    original_note = adjusted_msg["note"]
                    # 应用统一的半音调整，保持相对音高不变
                    adjusted_note = original_note + total_semitone_diff
                    adjusted_msg["note"] = adjusted_note
                    logger.debug(f"音符调整: {original_note} -> {adjusted_note}")
                adjusted_track.append(adjusted_msg)
            adjusted_mid_list.append(adjusted_track)
        
        # 优化音符时间，解决同一个键快速松开按下导致听不出松开效果的问题
        optimized_mid_list = self.optimize_note_timing(adjusted_mid_list, track_num)
        
        logger.info("MIDI调式调整和时间优化完成")
        return optimized_mid_list
        
    def play_midi(self, file_path, bpm=120, track_num=1):
        self.bpm = bpm
        self.tempo = 60 / self.bpm
        # 检测文件是否存在
        mid = self.read_midi(file_path)
        if mid is None:
            return
        self.ticks_per_beat = mid.ticks_per_beat
        mid_list = self.to_list(mid)
        mid_list = self.adjust_midi(mid_list, track_num)
        
        # 延时2秒，让用户有时间切换到目标窗口
        logger.info("程序将在2秒后开始播放，请切换到目标窗口...")
        time.sleep(2)
        
        # 获取当前聚焦窗口
        target_window = gw.getActiveWindow()
        if target_window:
            logger.info(f"当前聚焦窗口: {target_window.title}")
        else:
            logger.warning("未检测到聚焦窗口，将在当前窗口播放")
        
        # 跟踪每个音符的状态
        note_states = {}
        start_time = time.time()
        # 将从1开始的音轨编号转换为从0开始的索引
        actual_track_num = track_num - 1
        
        # 播放指定音轨
        if actual_track_num < len(mid_list):
            logger.info(f"开始播放第 {track_num} 条音轨")
            track = mid_list[actual_track_num]
            for i in range(len(track)):
                msg = track[i]
                if "note" not in msg.keys():
                    continue
                
                delete_time = msg["time"] / self.ticks_per_beat * self.tempo
                # 确保睡眠时间为非负数
                delete_time = max(delete_time, 0)
                delete_time = delete_time - (time.time() - start_time)
                time.sleep(max(delete_time, 0))
                start_time = time.time()
                
                # 检查窗口是否切换（每10个消息检查一次，减少开销）
                if i % 10 == 0:
                    current_window = gw.getActiveWindow()
                    if target_window and current_window != target_window:
                        logger.info(f"窗口已切换，从 {target_window.title} 切换到 {current_window.title}，终止播放")
                        # 释放所有按键
                        for key in self.map.values():
                            self.controller.key(key, False)
                        return

                if msg["note"] not in self.map.keys():
                    logger.error(f"note {msg['note']} not in map")
                    continue
                
                note = msg["note"]
                key = self.map[note]
                
                # 处理音符消息
                if msg["type"] == "note_on" and msg["velocity"] > 0:
                    logger.debug(f"press {key}")
                    self.controller.key(key, True)
                    note_states[note] = {"type": "on", "time": time.time()}
                elif msg["type"] == "note_off" or msg["velocity"] == 0:
                    logger.debug(f"release {key}")
                    self.controller.key(key, False)
                    note_states[note] = {"type": "off", "time": time.time()}
        else:
            logger.error(f"音轨编号 {track_num} 超出范围，总共有 {len(mid_list)} 条音轨")

    def __del__(self):
        try:
            for key in self.map.values():
                self.controller.key(key, False)
        except Exception as e:
            # 忽略在__del__方法中可能出现的异常，因为此时某些资源可能已经被释放
            pass
            
class MusicPlayerGUI:
    def __init__(self, master):
        self.master = master
        master.title("原神音乐播放器")
        master.geometry("500x300")
        master.resizable(False, False)
        
        # 创建音乐播放器实例
        self.music_player = GenshinImpactMusicPlayer()
        self.is_playing = False
        self.current_file = ""
        self.available_tracks = [1]  # 默认音轨1
        
        # 设置样式
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#ccc")
        style.configure("TLabel", padding=6, font=("Arial", 10))
        style.configure("TEntry", padding=6)
        style.configure("TCombobox", padding=6)
        
        # 创建主框架
        main_frame = ttk.Frame(master, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文件选择部分
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(file_frame, text="MIDI文件:", width=10).pack(side=tk.LEFT, padx=5)
        
        self.file_entry = ttk.Entry(file_frame)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(file_frame, text="浏览", command=self.browse_file).pack(side=tk.LEFT, padx=5)
        
        # 音轨选择部分
        track_frame = ttk.Frame(main_frame)
        track_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(track_frame, text="音轨:", width=10).pack(side=tk.LEFT, padx=5)
        
        self.track_var = tk.StringVar(value="1")
        self.track_combobox = ttk.Combobox(track_frame, textvariable=self.track_var, values=self.available_tracks, state="readonly")
        self.track_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # BPM选择部分
        bpm_frame = ttk.Frame(main_frame)
        bpm_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(bpm_frame, text="BPM:", width=10).pack(side=tk.LEFT, padx=5)
        
        self.bpm_var = tk.StringVar(value="120")
        self.bpm_entry = ttk.Entry(bpm_frame, textvariable=self.bpm_var)
        self.bpm_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 播放按钮部分
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        self.play_button = ttk.Button(button_frame, text="播放", command=self.play_music, style="TButton")
        self.play_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(button_frame, text="退出", command=master.quit).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="blue")
        status_label.pack(pady=10)
    
    def browse_file(self):
        """浏览并选择MIDI文件"""
        file_path = filedialog.askopenfilename(
            filetypes=[("MIDI文件", "*.mid *.midi")],
            initialdir=os.path.join(os.path.dirname(__file__), "data", "music")
        )
        if file_path:
            self.current_file = file_path
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)
            self.update_available_tracks(file_path)
            self.status_var.set("已选择文件")
    
    def update_available_tracks(self, file_path):
        """更新可用音轨列表"""
        try:
            mid = mido.MidiFile(file_path)
            # 音轨编号从1开始，因为代码中默认使用track_num=1
            self.available_tracks = list(range(1, len(mid.tracks) + 1))
            self.track_combobox['values'] = self.available_tracks
            self.track_var.set(str(1))  # 默认选择第一条音轨
            self.status_var.set(f"文件包含 {len(mid.tracks)} 条音轨")
        except Exception as e:
            logger.error(f"读取MIDI文件失败: {e}")
            self.status_var.set(f"读取文件失败: {e}")
    
    def play_music(self):
        """播放音乐，在新线程中执行"""
        if self.is_playing:
            return
        
        file_path = self.current_file
        if not file_path:
            self.status_var.set("请先选择MIDI文件")
            return
        
        try:
            track_num = int(self.track_var.get())
            bpm = int(self.bpm_var.get())
            
            if bpm <= 0:
                self.status_var.set("BPM必须大于0")
                return
            
            self.is_playing = True
            self.play_button.config(text="播放中...", state="disabled")
            self.status_var.set("正在准备播放...")
            
            # 在新线程中播放音乐，避免阻塞GUI
            threading.Thread(target=self._play_music_thread, args=(file_path, bpm, track_num), daemon=True).start()
        except ValueError:
            self.status_var.set("请输入有效的音轨和BPM")
    
    def _play_music_thread(self, file_path, bpm, track_num):
        """播放音乐的线程函数"""
        try:
            self.status_var.set(f"正在播放: {os.path.basename(file_path)}")
            self.music_player.play_midi(file_path, bpm, track_num)
            self.status_var.set("播放完成")
        except Exception as e:
            logger.error(f"播放失败: {e}")
            self.status_var.set(f"播放失败: {e}")
        finally:
            self.is_playing = False
            self.master.after(0, lambda: self.play_button.config(text="播放", state="normal"))


if __name__ == "__main__":
    # 如果有命令行参数，则使用命令行模式
    if len(sys.argv) > 1:
        # 创建命令行参数解析器
        parser = argparse.ArgumentParser(description="播放MIDI文件")
        # 添加文件路径参数（必填）
        parser.add_argument("file_path", help="MIDI文件路径")
        # 添加bpm参数（可选，默认120）
        parser.add_argument("--bpm", type=int, default=120, help="播放速度（默认120）")
        # 添加track参数（可选，默认0）
        parser.add_argument("--track", type=int, default=1, help="用于调式识别的音轨编号（默认0）")
        # 解析命令行参数
        args = parser.parse_args()
        # 播放MIDI文件
        music_player = GenshinImpactMusicPlayer()
        music_player.play_midi(args.file_path, args.bpm, args.track)
    else:
        # 没有参数则启动GUI模式
        root = tk.Tk()
        app = MusicPlayerGUI(root)
        root.mainloop()
