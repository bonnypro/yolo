from ultralytics import YOLO
import cv2
import os
import sys
import time
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QFileDialog, QFrame, QSlider)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QTimer


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

        # FPS相关变量
        self.frame_count = 0
        self.fps = 0
        self.last_time = time.time()

        # 置信度阈值 (默认0.5)
        self.confidence_threshold = 0.5

        # 设置QT插件路径
        self.set_qt_plugin_path()

        # 尝试自动加载默认模型
        self.load_default_model()

    def load_default_model(self):
        """尝试加载默认模型(best.pt)"""
        default_model = "best.pt"
        if os.path.exists(default_model):
            try:
                self.model = YOLO(default_model)
                self.statusBar().showMessage(
                    f"自动加载默认模型: {default_model}", 3000)
                self.check_ready_state()
            except Exception as e:
                self.statusBar().showMessage(f"默认模型加载失败: {str(e)}", 5000)

    def initUI(self):
        """初始化用户界面"""
        self.setWindowTitle("AI蒙皮铝屑观察助手")
        self.setGeometry(100, 100, 1000, 600)

        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局 (水平布局，包含侧边栏和视频区域)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # 创建侧边栏
        self.create_sidebar(main_layout)

        # 创建视频显示区域
        self.create_video_area(main_layout)

    def create_sidebar(self, main_layout):
        """创建侧边栏"""
        # 侧边栏框架
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar.setFixedWidth(220)  # 稍微加宽以容纳滑块

        # 侧边栏布局
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar.setLayout(sidebar_layout)

        # 添加标题
        title_label = QLabel("功能面板")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title_label)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        sidebar_layout.addWidget(separator)

        # 加载模型按钮
        self.load_model_btn = QPushButton("加载YOLO模型")
        self.load_model_btn.clicked.connect(self.load_model)
        sidebar_layout.addWidget(self.load_model_btn)

        # 打开视频按钮
        self.open_video_btn = QPushButton("打开视频文件")
        self.open_video_btn.clicked.connect(self.open_video)
        sidebar_layout.addWidget(self.open_video_btn)

        # 开始/停止按钮
        self.start_stop_btn = QPushButton("开始检测")
        self.start_stop_btn.clicked.connect(self.toggle_video)
        self.start_stop_btn.setEnabled(False)
        sidebar_layout.addWidget(self.start_stop_btn)

        # 添加置信度滑块
        self.add_confidence_slider(sidebar_layout)

        # 添加弹簧使按钮靠上
        sidebar_layout.addStretch()

        # 添加FPS显示
        separator_bottom = QFrame()
        separator_bottom.setFrameShape(QFrame.Shape.HLine)
        separator_bottom.setFrameShadow(QFrame.Shadow.Sunken)
        sidebar_layout.addWidget(separator_bottom)

        self.fps_label = QLabel("FPS: --")
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fps_label.setStyleSheet("""
            font-weight: bold;
            font-size: 16px;
            color: #333;
            padding: 5px;
            background-color: #f0f0f0;
            border-radius: 4px;
        """)
        sidebar_layout.addWidget(self.fps_label)

        # 将侧边栏添加到主布局
        main_layout.addWidget(sidebar)

    def add_confidence_slider(self, layout):
        """添加置信度调节滑块"""
        # 置信度标签
        confidence_label = QLabel("置信度阈值: 0.5")
        confidence_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        confidence_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(confidence_label)

        # 滑块容器
        slider_container = QWidget()
        slider_layout = QHBoxLayout()
        slider_container.setLayout(slider_layout)

        # 滑块
        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setRange(10, 100)  # 10%到90%
        self.confidence_slider.setValue(80)  # 默认50%
        self.confidence_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.confidence_slider.setTickInterval(10)
        self.confidence_slider.valueChanged.connect(
            lambda: self.update_confidence(confidence_label))
        slider_layout.addWidget(self.confidence_slider)

        layout.addWidget(slider_container)

    def update_confidence(self, label):
        """更新置信度阈值"""
        self.confidence_threshold = self.confidence_slider.value() / 100.0
        label.setText(f"置信度阈值: {self.confidence_threshold:.2f}")

    def create_video_area(self, main_layout):
        """创建视频显示区域"""
        # 视频区域容器
        video_container = QWidget()
        video_layout = QVBoxLayout()
        video_container.setLayout(video_layout)

        # 视频显示标签
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        video_layout.addWidget(self.video_label)

        # 将视频区域添加到主布局
        main_layout.addWidget(video_container, stretch=1)

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
            self.fps_label.setText("FPS: --")
        else:
            # 重置FPS计数器
            self.frame_count = 0
            self.last_time = time.time()

            self.timer.start(30)
            self.start_stop_btn.setText("停止检测")
            self.statusBar().showMessage("检测已开始", 2000)

    def update_frame(self):
        """更新视频帧并进行YOLO检测"""
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # 运行YOLO推理(使用当前置信度阈值)
                results = self.model(frame, conf=self.confidence_threshold)
                annotated_frame = results[0].plot()

                # 更新FPS计数
                self.frame_count += 1
                current_time = time.time()
                if current_time - self.last_time >= 1.0:
                    self.fps = self.frame_count / \
                        (current_time - self.last_time)
                    self.fps_label.setText(f"FPS: {self.fps:.1f}")
                    self.frame_count = 0
                    self.last_time = current_time

                # 显示处理后的帧
                self.display_frame(annotated_frame)
            else:
                # 视频结束，重置到开头
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def display_frame(self, frame):
        """在QLabel中显示帧"""
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w

        qt_image = QImage(rgb_image.data, w, h, bytes_per_line,
                          QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)

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
