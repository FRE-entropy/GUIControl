import sys
import os
import time
import mido
import argparse
import pygetwindow as gw

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
        self.bpm = 120
        self.tempo = 60 / self.bpm


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

    def mode_recognition(self, mid_list, track_num=0):
        """
        识别MIDI文件的调式，只识别大调小调，处理少量调外音
        返回值：-1表示小调，C大调为0，D大调为1，以此类推
        """
        logger.info("开始识别调式")
        
        if not mid_list:
            logger.info("mid_list为空，返回None")
            return None
        
        # 只使用第一条音轨的音符进行统计
        all_notes = []
        if mid_list and mid_list[track_num]:
            first_track = mid_list[track_num]
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

    def optimize_note_timing(self, mid_list):
        """
        优化音符时间，解决同一个键快速松开按下导致听不出松开效果的问题
        检测连续的note_off和note_on消息，提前处理note_off并调整后续消息时间
        """
        optimized_mid_list = []
        
        # 最小松开时间间隔（秒），小于这个值的话会被优化
        min_release_time = 0.05
        
        for track in mid_list:
            # 重写优化逻辑，直接在play_midi中处理
            # 这里返回原始轨道，实际优化在play_midi中进行
            optimized_mid_list.append(track)
        
        logger.info("音符时间优化完成")
        return optimized_mid_list
    
    def adjust_midi(self, mid_list, track_num=0):
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
        optimized_mid_list = self.optimize_note_timing(adjusted_mid_list)
        
        logger.info("MIDI调式调整和时间优化完成")
        return optimized_mid_list
        
    def play_midi(self, file_path, bpm=120, track_num=0):
        self.bpm = bpm
        self.tempo = 60 / self.bpm
        # 检测文件是否存在
        mid = self.read_midi(file_path)
        if mid is None:
            return
        mid_list = self.to_list(mid)
        mid_list = self.adjust_midi(mid_list, track_num)
        
        # 延时3秒，让用户有时间切换到目标窗口
        logger.info("程序将在1秒后开始播放，请切换到目标窗口...")
        time.sleep(1)
        
        # 获取当前聚焦窗口
        target_window = gw.getActiveWindow()
        if target_window:
            logger.info(f"当前聚焦窗口: {target_window.title}")
        else:
            logger.warning("未检测到聚焦窗口，将在当前窗口播放")
        
        # 最小松开时间间隔（秒），小于这个值的话会被优化
        min_release_time = 0.03
        
        # 跟踪每个音符的状态和时间
        note_states = {}
        
        # 播放指定音轨
        if track_num < len(mid_list):
            logger.info(f"开始播放第 {track_num} 条音轨")
            track = mid_list[track_num]
            for i in range(len(track)):
                msg = track[i]
                if "note" not in msg.keys():
                    continue
                
                delete_time = msg["time"] / mid.ticks_per_beat * self.tempo
                # 确保睡眠时间为非负数
                delete_time = max(delete_time, 0)

                time.sleep(delete_time)
                
                # 检查窗口是否切换
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
                
                if msg["type"] == "note_on" and msg["velocity"] > 0:
                    # 检查是否有最近的note_off消息
                    if note in note_states and note_states[note]["type"] == "off":
                        off_time = note_states[note]["time"]
                        current_time = time.time()
                        
                        # 计算note_off和note_on之间的时间间隔
                        time_diff = current_time - off_time
                        
                        # 如果时间间隔太短，添加一个小的延迟
                        if time_diff < min_release_time:
                            delay = min_release_time - time_diff
                            logger.debug(f"添加延迟 {delay:.3f} 秒，确保松开效果清晰")
                            time.sleep(delay)
                    
                    logger.info(f"press {key}")
                    self.controller.key(key, True)
                    note_states[note] = {"type": "on", "time": time.time()}
                elif msg["type"] == "note_off" or msg["velocity"] == 0:
                    logger.info(f"release {key}")
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
            
if __name__ == "__main__":

    # 创建音乐播放器实例
    music_player = GenshinImpactMusicPlayer()
    
    # 如果命令行有参数，则使用参数调用
    if len(sys.argv) > 1:
        # 创建命令行参数解析器
        parser = argparse.ArgumentParser(description="播放MIDI文件")
        # 添加文件路径参数（必填）
        parser.add_argument("file_path", help="MIDI文件路径")
        # 添加bpm参数（可选，默认120）
        parser.add_argument("--bpm", type=int, default=120, help="播放速度（默认120）")
        # 添加track参数（可选，默认0）
        parser.add_argument("--track", type=int, default=0, help="用于调式识别的音轨编号（默认0）")
        # 解析命令行参数
        args = parser.parse_args()
        # 播放MIDI文件
        music_player.play_midi(args.file_path, args.bpm, args.track)
    else:
        # 没有参数则直接调用默认文件和速度
        music_player.play_midi("data/music/周杰伦歌曲Midi合集/最伟大的作品.mid", 120, 1)
        # music_player.play_midi("./data/music/青花瓷(C调).mid", 120)
        # music_player.play_midi("./data/music/flower_dance.mid", 120)
        # music_player.play_midi("data/music/2.mid")
