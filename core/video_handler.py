import cv2
import time
import platform
import os
from datetime import datetime


class VideoHandler:
    def __init__(self):
        self.cap = None
        self.video_writer = None
        self.recording = False
        self.record_path = ""
        self.camera_index = None
        
        # FPS计算相关
        self.frame_count = 0
        self.fps = 0
        self.last_time = time.time()

    def open_camera(self, camera_index=0):
        """打开摄像头"""
        self.release()
        self.camera_index = camera_index
        
        api_preference = None
        if platform.system() == "Windows":
            api_preference = cv2.CAP_DSHOW
        elif platform.system() == "Linux":
            api_preference = cv2.CAP_V4L2
        
        if api_preference is not None:
            self.cap = cv2.VideoCapture(camera_index, api_preference)
        else:
            self.cap = cv2.VideoCapture(camera_index)

        # 如果首选API失败，则尝试使用默认API
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(camera_index)
            
        return self.cap.isOpened()

    def open_video(self, video_path):
        """打开视频文件"""
        self.release()
        self.camera_index = None
        self.cap = cv2.VideoCapture(video_path)
        return self.cap.isOpened()

    def get_frame(self):
        """获取当前帧"""
        if self.cap is None or not self.cap.isOpened():
            return None, False

        ret, frame = self.cap.read()
        if not ret:
            if self.camera_index is None:
                # 视频文件结束，重新开始播放
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret:
                    return None, False
                return frame, ret
            else:
                # 摄像头读取失败
                return None, False

        return frame, ret

    def update_fps_counter(self):
        """更新FPS计数器"""
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_time >= 1.0:
            self.fps = self.frame_count / (current_time - self.last_time)
            self.frame_count = 0
            self.last_time = current_time
            return self.fps
        return None

    def start_recording(self, record_path):
        """开始录制（仅支持Linux下mp4）"""
        if not self.cap or not self.cap.isOpened():
            return False, "没有可用的视频源"

        os.makedirs(os.path.dirname(record_path), exist_ok=True)
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        if fps <= 0:
            fps = 30

        # 只允许mp4
        if not record_path.lower().endswith('.mp4'):
            record_path += '.mp4'
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        self.video_writer = cv2.VideoWriter(
            record_path, fourcc, fps, (width, height))

        if not self.video_writer.isOpened():
            return False, "无法创建视频文件"

        self.recording = True
        self.record_path = record_path
        return True, "录制已开始"

    def stop_recording(self):
        """停止录制"""
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None

        self.recording = False
        return True, f"录制完成，视频已保存到: {self.record_path}"

    def write_frame(self, frame):
        """写入帧到录制文件"""
        if self.recording and self.video_writer is not None:
            self.video_writer.write(frame)

    def is_recording(self):
        """检查是否正在录制"""
        return self.recording

    def is_video_ready(self):
        """检查视频源是否就绪"""
        return self.cap is not None and self.cap.isOpened()

    def is_running(self):
        """检查视频流是否正在运行"""
        return self.cap is not None and self.cap.isOpened()

    def release(self):
        """释放资源"""
        if self.recording:
            self.stop_recording()
        
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        self.cap = None
        self.camera_index = None 