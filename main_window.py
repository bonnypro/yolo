import os
import sys
import cv2
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QFileDialog, QFrame, QSlider)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QTimer
from video_processor import VideoProcessor


class YOLOVideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.processor = VideoProcessor()
        self.timer = QTimer(self)

        self.initUI()
        self.timer.timeout.connect(self.update_frame)
        self.load_default_model()

    def load_default_model(self):
        """尝试加载默认模型(best.pt)"""
        if os.path.exists("best.pt"):
            success, message = self.processor.load_model("best.pt")
            self.statusBar().showMessage(message, 3000)
            self.check_ready_state()

    def initUI(self):
        """初始化用户界面"""
        self.setWindowTitle("AI蒙皮铝屑观察助手")
        self.setGeometry(100, 100, 1000, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        self.create_sidebar(main_layout)
        self.create_video_area(main_layout)

    def create_sidebar(self, main_layout):
        """创建侧边栏"""
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar.setFixedWidth(220)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar.setLayout(sidebar_layout)

        title_label = QLabel("功能面板")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title_label)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        sidebar_layout.addWidget(separator)

        self.load_model_btn = QPushButton("加载YOLO模型")
        self.load_model_btn.clicked.connect(self.load_model)
        sidebar_layout.addWidget(self.load_model_btn)

        self.open_video_btn = QPushButton("打开视频文件")
        self.open_video_btn.clicked.connect(self.open_video)
        sidebar_layout.addWidget(self.open_video_btn)

        self.start_stop_btn = QPushButton("开始检测")
        self.start_stop_btn.clicked.connect(self.toggle_video)
        self.start_stop_btn.setEnabled(False)
        sidebar_layout.addWidget(self.start_stop_btn)

        self.add_confidence_slider(sidebar_layout)
        sidebar_layout.addStretch()

        separator_bottom = QFrame()
        separator_bottom.setFrameShape(QFrame.Shape.HLine)
        sidebar_layout.addWidget(separator_bottom)

        self.fps_label = QLabel("FPS: --")
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fps_label.setStyleSheet(
            "font-weight: bold; font-size: 16px; color: #333; padding: 5px; background-color: #f0f0f0; border-radius: 4px;")
        sidebar_layout.addWidget(self.fps_label)

        main_layout.addWidget(sidebar)

    def add_confidence_slider(self, layout):
        """添加置信度调节滑块"""
        confidence_label = QLabel("置信度阈值: 0.5")
        confidence_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        confidence_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(confidence_label)

        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setRange(10, 100)
        self.confidence_slider.setValue(50)
        self.confidence_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.confidence_slider.valueChanged.connect(
            lambda: self.update_confidence(confidence_label))
        layout.addWidget(self.confidence_slider)

    def update_confidence(self, label):
        """更新置信度阈值"""
        confidence = self.confidence_slider.value() / 100.0
        self.processor.set_confidence(confidence)
        label.setText(f"置信度阈值: {confidence:.2f}")

    def create_video_area(self, main_layout):
        """创建视频显示区域"""
        video_container = QWidget()
        video_layout = QVBoxLayout()
        video_container.setLayout(video_layout)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        video_layout.addWidget(self.video_label)

        main_layout.addWidget(video_container, stretch=1)

    def load_model(self):
        """加载YOLO模型"""
        model_path, _ = QFileDialog.getOpenFileName(
            self, "选择YOLO模型文件", "", "模型文件 (*.pt)")
        if model_path:
            success, message = self.processor.load_model(model_path)
            self.statusBar().showMessage(message, 3000)
            self.check_ready_state()

    def open_video(self):
        """打开视频文件"""
        video_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", "视频文件 (*.mp4 *.avi *.mov)")
        if video_path and self.processor.open_video(video_path):
            self.statusBar().showMessage(f"视频加载成功: {video_path}", 3000)
            self.check_ready_state()
            frame, ret = self.processor.get_frame()
            if ret:
                self.display_frame(frame)
                self.processor.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def check_ready_state(self):
        """检查是否准备好开始检测"""
        self.start_stop_btn.setEnabled(self.processor.model is not None and
                                       self.processor.cap is not None and
                                       self.processor.cap.isOpened())

    def toggle_video(self):
        """开始/停止视频检测"""
        if self.timer.isActive():
            self.timer.stop()
            self.start_stop_btn.setText("开始检测")
            self.statusBar().showMessage("检测已停止", 2000)
            self.fps_label.setText("FPS: --")
        else:
            self.processor.frame_count = 0
            self.processor.last_time = time.time()
            self.timer.start(30)
            self.start_stop_btn.setText("停止检测")
            self.statusBar().showMessage("检测已开始", 2000)

    def update_frame(self):
        """更新视频帧"""
        frame, ret = self.processor.get_frame()
        if ret:
            fps = self.processor.update_fps_counter()
            if fps is not None:
                self.fps_label.setText(f"FPS: {fps:.1f}")
            self.display_frame(frame)

    def display_frame(self, frame):
        """在QLabel中显示帧"""
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        qt_image = QImage(rgb_image.data, w, h, ch * w,
                          QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image).scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.video_label.setPixmap(pixmap)

    def closeEvent(self, event):
        """窗口关闭时释放资源"""
        self.processor.release()
        if self.timer.isActive():
            self.timer.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = YOLOVideoPlayer()
    player.show()
    sys.exit(app.exec())
