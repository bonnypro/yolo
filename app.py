from ultralytics import YOLO
import cv2
import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout,
                             QWidget, QPushButton, QFileDialog)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QTimer

# 获取当前 Conda 环境的根目录
conda_env_path = Path(os.environ["CONDA_PREFIX"])

# 设置 QT_QPA_PLATFORM_PLUGIN_PATH 以适配当前环境
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(
    conda_env_path / "plugins" / "platforms")


class YOLOVideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        # 初始化UI
        self.initUI()

        # 初始化YOLO模型
        self.model = None
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        # 设置QT插件路径
        self.set_qt_plugin_path()

    def initUI(self):
        """初始化用户界面"""
        self.setWindowTitle("YOLO视频检测器")
        self.setGeometry(100, 100, 800, 600)

        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 布局
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # 视频显示标签
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        layout.addWidget(self.video_label)

        # 按钮区域
        button_layout = QVBoxLayout()

        # 加载模型按钮
        self.load_model_btn = QPushButton("加载YOLO模型")
        self.load_model_btn.clicked.connect(self.load_model)
        button_layout.addWidget(self.load_model_btn)

        # 打开视频按钮
        self.open_video_btn = QPushButton("打开视频文件")
        self.open_video_btn.clicked.connect(self.open_video)
        button_layout.addWidget(self.open_video_btn)

        # 开始/停止按钮
        self.start_stop_btn = QPushButton("开始检测")
        self.start_stop_btn.clicked.connect(self.toggle_video)
        self.start_stop_btn.setEnabled(False)
        button_layout.addWidget(self.start_stop_btn)

        layout.addLayout(button_layout)

    def set_qt_plugin_path(self):
        """设置QT插件路径"""
        conda_env_path = Path(os.environ["CONDA_PREFIX"])
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(
            conda_env_path / "plugins" / "platforms")

    def load_model(self):
        """加载YOLO模型"""
        model_path, _ = QFileDialog.getOpenFileName(
            self, "选择YOLO模型文件", "", "模型文件 (*.pt)")

        if model_path:
            try:
                self.model = YOLO(model_path)
                self.statusBar().showMessage(f"模型加载成功: {model_path}", 3000)
                self.check_ready_state()
            except Exception as e:
                self.statusBar().showMessage(f"模型加载失败: {str(e)}", 5000)

    def open_video(self):
        """打开视频文件"""
        video_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", "视频文件 (*.mp4 *.avi *.mov)")

        if video_path:
            self.cap = cv2.VideoCapture(video_path)
            if self.cap.isOpened():
                self.statusBar().showMessage(f"视频加载成功: {video_path}", 3000)
                self.check_ready_state()

                # 显示第一帧
                ret, frame = self.cap.read()
                if ret:
                    self.display_frame(frame)
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            else:
                self.statusBar().showMessage("无法打开视频文件", 5000)

    def check_ready_state(self):
        """检查是否准备好开始检测"""
        if self.model is not None and self.cap is not None and self.cap.isOpened():
            self.start_stop_btn.setEnabled(True)

    def toggle_video(self):
        """开始/停止视频检测"""
        if self.timer.isActive():
            self.timer.stop()
            self.start_stop_btn.setText("开始检测")
            self.statusBar().showMessage("检测已停止", 2000)
        else:
            self.timer.start(30)  # 约30fps
            self.start_stop_btn.setText("停止检测")
            self.statusBar().showMessage("检测已开始", 2000)

    def update_frame(self):
        """更新视频帧并进行YOLO检测"""
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # 运行YOLO推理
                results = self.model(frame)
                annotated_frame = results[0].plot()

                # 显示处理后的帧
                self.display_frame(annotated_frame)
            else:
                # 视频结束，重置到开头
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def display_frame(self, frame):
        """在QLabel中显示帧"""
        # 将OpenCV BGR格式转换为RGB
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w

        # 创建QImage并显示
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line,
                          QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)

        # 缩放以适应标签大小，同时保持宽高比
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        """窗口关闭时释放资源"""
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        if self.timer.isActive():
            self.timer.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = YOLOVideoPlayer()
    player.show()
    sys.exit(app.exec())
