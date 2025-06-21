import os
import sys
import cv2
import time
import colorsys
import math
import platform
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QFileDialog, QFrame, QSlider)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QTimer

from config import (APP_VERSION, APP_TITLE, DEFAULT_SETTINGS, STYLES, 
                   FUNCTION_BUTTONS, FILE_FILTERS, VIDEO_CODECS)
from core.model_handler import ModelHandler
from core.video_handler import VideoHandler


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化处理器
        self.model_handler = ModelHandler()
        self.video_handler = VideoHandler()
        
        # 初始化UI状态
        self.timer = QTimer(self)
        self.pulse_timer = QTimer(self)
        self.record_timer = QTimer(self)
        self.pulse_phase = 0
        self.recording_mode = False
        
        self.init_ui()
        self.setup_timers()
        self.load_default_model()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle(APP_TITLE)
        self.setGeometry(*DEFAULT_SETTINGS["window_position"], *DEFAULT_SETTINGS["window_size"])
        self.setStyleSheet(STYLES["BACKGROUND"])

        central_widget = QWidget()
        central_widget.setStyleSheet(STYLES["BACKGROUND"])
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        self.create_sidebar(main_layout)
        self.create_video_area(main_layout)
        self.setup_status_bar()

    def setup_timers(self):
        """设置定时器"""
        self.timer.timeout.connect(self.update_frame)
        self.pulse_timer.timeout.connect(self.update_pulse_effect)
        self.record_timer.timeout.connect(self.update_record_button)

    def create_styled_frame(self, shape=QFrame.Shape.StyledPanel):
        """创建样式化框架"""
        frame = QFrame()
        frame.setFrameShape(shape)
        frame.setStyleSheet(f"{STYLES['BACKGROUND']} border: 1px solid #75715E;")
        return frame

    def create_sidebar(self, main_layout):
        """创建侧边栏"""
        sidebar = self.create_styled_frame()
        sidebar.setFixedWidth(DEFAULT_SETTINGS["sidebar_width"])
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar.setLayout(sidebar_layout)

        self.add_title(sidebar_layout, "功能面板")
        self.add_separator(sidebar_layout, Qt.Orientation.Horizontal)

        # 创建功能按钮
        for text, method_name in FUNCTION_BUTTONS:
            btn = QPushButton(text)
            btn.setStyleSheet(STYLES["BUTTON"])
            btn.clicked.connect(getattr(self, method_name))
            sidebar_layout.addWidget(btn)

        self.add_confidence_slider(sidebar_layout)
        sidebar_layout.addStretch()
        self.add_separator(sidebar_layout, Qt.Orientation.Horizontal)

        # 开始/停止检测按钮
        self.start_stop_btn = QPushButton("开始检测")
        self.start_stop_btn.setStyleSheet(STYLES["START_BUTTON"])
        self.start_stop_btn.clicked.connect(self.toggle_video)
        self.start_stop_btn.setEnabled(False)
        sidebar_layout.addWidget(self.start_stop_btn)

        self.add_separator(sidebar_layout, Qt.Orientation.Horizontal)

        # FPS显示
        self.fps_label = QLabel("FPS: --")
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fps_label.setStyleSheet(STYLES["FPS_LABEL"])
        sidebar_layout.addWidget(self.fps_label)

        main_layout.addWidget(sidebar)

    def create_video_area(self, main_layout):
        """创建视频显示区域"""
        video_container = QWidget()
        video_container.setStyleSheet(STYLES["BACKGROUND"])
        video_layout = QVBoxLayout()
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.setSpacing(10)
        video_container.setLayout(video_layout)

        # 视频显示标签
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(*DEFAULT_SETTINGS["video_min_size"])
        self.video_label.setStyleSheet(STYLES["BACKGROUND"])
        video_layout.addWidget(self.video_label, stretch=1)

        # 录制面板
        self.record_panel = QWidget()
        self.record_panel.setVisible(False)
        record_panel_layout = QHBoxLayout()
        record_panel_layout.setContentsMargins(0, 0, 0, 0)
        record_panel_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.record_panel.setLayout(record_panel_layout)

        record_panel_layout.addStretch()
        
        self.select_path_btn = QPushButton("选择保存路径")
        self.select_path_btn.setStyleSheet(STYLES["LARGE_BUTTON"])
        self.select_path_btn.setMinimumSize(150, 40)
        self.select_path_btn.clicked.connect(self.select_record_path)

        self.record_btn = QPushButton("开始录制")
        self.record_btn.setStyleSheet(STYLES["LARGE_BUTTON"])
        self.record_btn.setMinimumSize(150, 40)
        self.record_btn.clicked.connect(self.toggle_recording)

        record_panel_layout.addWidget(self.select_path_btn)
        record_panel_layout.addWidget(self.record_btn)
        record_panel_layout.addStretch()

        video_layout.addWidget(self.record_panel)

        # 录制状态标签
        self.recording_label = QLabel("未录制")
        self.recording_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recording_label.setStyleSheet(STYLES["RECORDING_LABEL"])
        self.recording_label.setVisible(False)
        video_layout.addWidget(self.recording_label)

        main_layout.addWidget(video_container, stretch=1)

    def setup_status_bar(self):
        """设置状态栏"""
        self.statusBar().setStyleSheet(STYLES["STATUS_BAR"])
        
        self.model_info_label = QLabel("<b>模型:</b> 未加载")
        self.model_info_label.setStyleSheet("font-weight: bold;")
        self.statusBar().addPermanentWidget(self.model_info_label)
        
        self.add_separator_to_status_bar()
        
        self.version_label = QLabel(f"<b>版本:</b> {APP_VERSION}")
        self.version_label.setStyleSheet("font-weight: bold;")
        self.statusBar().addPermanentWidget(self.version_label)

    def add_title(self, layout, text):
        """添加标题"""
        label = QLabel(text)
        label.setStyleSheet(STYLES["TITLE"])
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

    def add_separator(self, layout, orientation):
        """添加分隔符"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine if orientation ==
                                Qt.Orientation.Horizontal else QFrame.Shape.VLine)
        separator.setStyleSheet("color: #75715E;")
        layout.addWidget(separator)

    def add_separator_to_status_bar(self):
        """添加状态栏分隔符"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("color: #75715E;")
        self.statusBar().addPermanentWidget(separator)

    def add_confidence_slider(self, layout):
        """添加置信度滑块"""
        confidence_label = QLabel("置信度阈值: 0.5")
        confidence_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        confidence_label.setStyleSheet(STYLES["CONFIDENCE_LABEL"])
        layout.addWidget(confidence_label)

        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setRange(10, 100)
        self.confidence_slider.setValue(50)
        self.confidence_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.confidence_slider.setTickInterval(10)
        self.confidence_slider.setSingleStep(1)

        self.update_slider_style(50, confidence_label)
        self.confidence_slider.valueChanged.connect(
            lambda value: self.update_slider_style(value, confidence_label))
        layout.addWidget(self.confidence_slider)

    def hsv_to_hex(self, h, s, v):
        """HSV转十六进制颜色"""
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return "#{:02X}{:02X}{:02X}".format(int(r*255), int(g*255), int(b*255))

    def update_slider_style(self, value, label):
        """更新滑块样式"""
        confidence = value / 100.0
        label.setText(f"置信度阈值: {confidence:.2f}")
        self.model_handler.set_confidence(confidence)
        
        hue = (1.0 - confidence) * 240 / 360
        color_hex = self.hsv_to_hex(hue, 0.9, 0.9)

        tick_style = f"""
            QSlider::sub-page:horizontal {{
                background: {color_hex};
                height: 8px;
                border-radius: 4px;
            }}
            QSlider::groove:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0000FF,
                    stop:0.5 #00FF00,
                    stop:1 #FF0000);
                height: 8px;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: #F8F8F2;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }}
            QSlider::add-page:horizontal {{
                background: #75715E;
                height: 8px;
                border-radius: 4px;
            }}
            QSlider::sub-control:bottom {{
                margin-top: 10px;
            }}
            QSlider::tick:below {{
                height: 4px;
                width: 1px;
                background: #F8F8F2;
            }}
        """
        self.confidence_slider.setStyleSheet(tick_style)

    def load_model(self):
        """加载AI模型"""
        self.exit_recording_mode()
        model_path, _ = QFileDialog.getOpenFileName(
            self, "选择YOLO模型文件", "", FILE_FILTERS["model"])
        if model_path:
            success, message = self.model_handler.load_model(model_path)
            self.update_model_info()
            self.statusBar().showMessage(message, 3000)
            self.check_ready_state()

    def load_default_model(self):
        """加载默认模型"""
        success, message = self.model_handler.load_default_model()
        if success:
            self.update_model_info()
        self.statusBar().showMessage(message, 3000)
        self.check_ready_state()

    def update_model_info(self):
        """更新模型信息显示"""
        model_info = self.model_handler.get_model_info()
        self.model_info_label.setText(f"<b>模型:</b> {model_info}")

    def open_camera(self):
        """打开USB摄像头"""
        self.exit_recording_mode()
        if self.video_handler.open_camera(0):
            self.statusBar().showMessage("摄像头已打开", 3000)
            self.check_ready_state()
            if not self.timer.isActive():
                self.toggle_video()
        else:
            self.statusBar().showMessage("无法打开摄像头", 3000)

    def open_video(self):
        """打开视频文件"""
        self.exit_recording_mode()
        video_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", FILE_FILTERS["video"])
        if video_path and self.video_handler.open_video(video_path):
            self.statusBar().showMessage(f"视频加载成功: {video_path}", 3000)
            self.check_ready_state()
            frame, ret = self.video_handler.get_frame()
            if ret:
                self.display_frame(frame)
                self.video_handler.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def check_ready_state(self):
        """检查就绪状态"""
        if self.recording_mode:
            self.start_stop_btn.setEnabled(False)
        else:
            self.start_stop_btn.setEnabled(
                self.model_handler.is_model_loaded() and 
                self.video_handler.is_video_ready()
            )

    def toggle_video(self):
        """切换视频检测状态"""
        if self.recording_mode:
            return
            
        if self.timer.isActive():
            self.timer.stop()
            self.pulse_timer.stop()
            self.start_stop_btn.setText("开始检测")
            self.start_stop_btn.setStyleSheet(STYLES["START_BUTTON"])
            self.statusBar().showMessage("检测已停止", 2000)
            self.fps_label.setText("FPS: --")
        else:
            self.video_handler.frame_count = 0
            self.video_handler.last_time = time.time()
            self.timer.start(DEFAULT_SETTINGS["fps_update_interval"])
            self.pulse_timer.start(50)
            self.start_stop_btn.setText("停止检测")
            self.start_stop_btn.setStyleSheet(STYLES["STOP_BUTTON"])
            self.statusBar().showMessage("检测已开始", 2000)

    def update_frame(self):
        """更新帧显示"""
        frame, ret = self.video_handler.get_frame()
        if ret:
            fps = self.video_handler.update_fps_counter()
            if fps is not None:
                self.fps_label.setText(f"FPS: {fps:.1f}")

            # 录制帧
            self.video_handler.write_frame(frame)

            # 推理处理
            display_frame = self.model_handler.predict(frame)
            self.display_frame(display_frame)

    def display_frame(self, frame):
        """显示帧"""
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image).scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.video_label.setPixmap(pixmap)

    def update_pulse_effect(self):
        """更新脉冲效果"""
        if not self.timer.isActive():
            self.pulse_timer.stop()
            self.start_stop_btn.setStyleSheet(STYLES["START_BUTTON"])
            return

        self.pulse_phase += DEFAULT_SETTINGS["pulse_speed"]
        if self.pulse_phase > 1:
            self.pulse_phase = 0
        
        alpha = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(self.pulse_phase * 2 * math.pi))
        color = f"rgba(244, 67, 54, {alpha})"

        self.start_stop_btn.setStyleSheet(f"""
            background-color: {color};
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            padding: 12px 24px;
            font-weight: bold;
        """)

    def setup_recording_mode(self):
        """设置录制模式"""
        self.recording_mode = True
        if self.video_handler.open_camera(0):
            self.statusBar().showMessage("准备录制训练数据", 3000)
            self.record_panel.setVisible(True)
            self.recording_label.setVisible(True)

            if self.timer.isActive():
                self.toggle_video()

            self.timer.start(DEFAULT_SETTINGS["fps_update_interval"])
            self.start_stop_btn.setEnabled(False)
            self.fps_label.setText("FPS: --")
        else:
            self.statusBar().showMessage("无法打开摄像头", 3000)
            self.recording_mode = False
            self.record_panel.setVisible(False)
            self.recording_label.setVisible(False)
            self.start_stop_btn.setEnabled(True)

    def exit_recording_mode(self):
        """退出录制模式"""
        if self.recording_mode:
            if self.video_handler.is_recording():
                self.stop_recording()

            if self.timer.isActive():
                self.timer.stop()
                if self.pulse_timer.isActive():
                    self.pulse_timer.stop()
            
            self.record_panel.setVisible(False)
            self.recording_label.setVisible(False)
            self.recording_mode = False
            self.start_stop_btn.setEnabled(True)
            self.start_stop_btn.setStyleSheet(STYLES["START_BUTTON"])
            self.fps_label.setText("FPS: --")

    def select_record_path(self):
        """选择录制保存路径"""
        default_path = os.path.join(os.getcwd(), DEFAULT_SETTINGS["training_data_dir"])
        if not os.path.exists(default_path):
            os.makedirs(default_path)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if platform.system() == "Windows":
            default_file = os.path.join(default_path, f"training_{timestamp}.mp4")
            file_filter = FILE_FILTERS["save_video_windows"]
        else:
            default_file = os.path.join(default_path, f"training_{timestamp}.avi")
            file_filter = FILE_FILTERS["save_video_linux"]

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存训练视频", default_file, file_filter)

        if file_path:
            if platform.system() == "Windows":
                if not file_path.lower().endswith('.mp4'):
                    file_path += '.mp4'
            else:
                if not file_path.lower().endswith('.avi'):
                    file_path += '.avi'
            self.video_handler.record_path = file_path
            self.statusBar().showMessage(f"视频将保存到: {file_path}", 3000)

    def toggle_recording(self):
        """切换录制状态"""
        if self.video_handler.is_recording():
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        """开始录制"""
        if not self.video_handler.record_path:
            self.statusBar().showMessage("请先选择保存路径", 3000)
            return

        success, message = self.video_handler.start_recording(self.video_handler.record_path)
        if success:
            self.record_btn.setText("停止录制")
            self.record_btn.setStyleSheet(STYLES["RECORD_BUTTON"])
            self.recording_label.setText("录制中...")
            self.recording_label.setStyleSheet(STYLES["RECORDING_ACTIVE"])
            self.record_timer.start(DEFAULT_SETTINGS["record_timer_interval"])
            self.statusBar().showMessage("开始录制训练数据", 3000)
        else:
            self.statusBar().showMessage(message, 3000)

    def stop_recording(self):
        """停止录制"""
        success, message = self.video_handler.stop_recording()
        self.record_btn.setText("开始录制")
        self.record_btn.setStyleSheet(STYLES["LARGE_BUTTON"])
        self.recording_label.setText("未录制")
        self.recording_label.setStyleSheet(STYLES["RECORDING_LABEL"])
        self.record_timer.stop()
        self.statusBar().showMessage(message, 5000)

    def update_record_button(self):
        """更新录制按钮样式"""
        if self.record_btn.styleSheet() == STYLES["RECORD_BUTTON"]:
            self.record_btn.setStyleSheet(
                "background-color: #880000; color: #FFFFFF; border: none; border-radius: 4px; font-size: 16px; padding: 8px 16px;")
        else:
            self.record_btn.setStyleSheet(STYLES["RECORD_BUTTON"])

    def closeEvent(self, event):
        """关闭事件处理"""
        # 停止所有定时器
        if self.timer.isActive():
            self.timer.stop()
        if self.pulse_timer.isActive():
            self.pulse_timer.stop()
        if self.record_timer.isActive():
            self.record_timer.stop()
        
        # 退出录制模式
        if self.recording_mode:
            self.exit_recording_mode()

        # 释放资源
        self.video_handler.release()
        
        event.accept() 