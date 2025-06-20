import cv2
import time
from ultralytics import YOLO


class VideoProcessor:
    def __init__(self):
        self.cap = None
        self.model = None
        self.frame_count = 0
        self.fps = 0
        self.last_time = time.time()
        self.confidence_threshold = 0.5
        self.camera_index = None

    def load_model(self, model_path):
        try:
            self.model = YOLO(model_path)
            return True, f"模型加载成功: {model_path}"
        except Exception as e:
            return False, f"模型加载失败: {str(e)}"

    def open_video(self, video_path):
        self.release()
        self.camera_index = None
        self.cap = cv2.VideoCapture(video_path)
        return self.cap.isOpened()

    def open_camera(self, camera_index=0):
        self.release()
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(camera_index)
        return self.cap.isOpened()

    def get_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return None, False

        ret, frame = self.cap.read()
        if not ret:
            if self.camera_index is None:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                return frame, ret
            else:
                return None, False

        return frame, ret

    def update_fps_counter(self):
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_time >= 1.0:
            self.fps = self.frame_count / (current_time - self.last_time)
            self.frame_count = 0
            self.last_time = current_time
            return self.fps
        return None

    def set_confidence(self, confidence):
        self.confidence_threshold = confidence

    def release(self):
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        self.cap = None
