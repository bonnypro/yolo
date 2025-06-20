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
        self.camera_index = None  # 存储摄像头索引

    def load_model(self, model_path):
        """加载YOLO模型"""
        try:
            self.model = YOLO(model_path)
            return True, f"模型加载成功: {model_path}"
        except Exception as e:
            return False, f"模型加载失败: {str(e)}"

    def open_video(self, video_path):
        """打开视频文件"""
        self.release()  # 先释放之前的资源
        self.camera_index = None  # 重置摄像头索引
        self.cap = cv2.VideoCapture(video_path)
        return self.cap.isOpened()

    def open_camera(self, camera_index=0):
        """打开USB摄像头"""
        self.release()  # 先释放之前的资源
        self.camera_index = camera_index  # 存储摄像头索引
        self.cap = cv2.VideoCapture(camera_index)
        return self.cap.isOpened()

    def get_frame(self):
        """获取下一帧并进行YOLO检测"""
        if self.cap is None or not self.cap.isOpened():
            return None, False

        ret, frame = self.cap.read()
        if not ret:
            # 如果是视频文件，循环播放
            if self.camera_index is None:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                return frame, ret
            else:
                # 如果是摄像头，返回空帧
                return None, False

        if self.model is not None:
            results = self.model(frame, conf=self.confidence_threshold)
            frame = results[0].plot()

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

    def set_confidence(self, confidence):
        """设置置信度阈值"""
        self.confidence_threshold = confidence

    def release(self):
        """释放视频资源"""
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        self.cap = None
