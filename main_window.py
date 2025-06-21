import os
import sys
import cv2
import time
import colorsys
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QFileDialog, QFrame, QSlider)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QTimer
from video_processor import VideoProcessor
import math
import platform

APP_VERSION = "v1.0.0 by Chang"


class YOLOVideoPlayer(QMainWindow):
    BACKGROUND_STYLE = "background-color: #272822; color: #FFFFFF;"
    BUTTON_STYLE = "background-color: #3E3D32; color: #FFFFFF; border: none; border-radius: 4px;"
    TITLE_STYLE = "font-weight: bold; font-size: 14px; background-color: #272822; color: #FFFFFF;"
    STATUS_BAR_STYLE = """
        QStatusBar {
            background-color: #272822;
            color: #FFFFFF;
            border-top: 1px solid #75715E;
            font-family: Microsoft YaHei;
        }
        QLabel {
            color: #FFFFFF;
        }
    """
    FPS_LABEL_STYLE = """
        font-weight: bold; 
        font-size: 16px; 
        background-color: #3E3D32; 
        border-radius: 4px;
        color: #FFFFFF;
    """
    RECORD_BUTTON_STYLE = """
        background-color: #FF0000;
        color: #FFFFFF;
        border: none;
        border-radius: 4px;
        font-size: 16px;
        padding: 8px 16px;
    """
    LARGE_BUTTON_STYLE = """
        background-color: #3E3D32;
        color: #FFFFFF;
        border: none;
        border-radius: 4px;
        font-size: 16px;
        padding: 8px 16px;
    """

    def __init__(self):
        super().__init__()
        self.processor = VideoProcessor()
        self.timer = QTimer(self)
        self.pulse_timer = QTimer(self)
        self.record_timer = QTimer(self)
        self.pulse_phase = 0
        self.pulse_speed = 0.05
        self.current_model_path = None
        self.recording = False
        self.video_writer = None
        self.record_path = ""
        self.recording_mode = False

        self.initUI()
        self.timer.timeout.connect(self.update_frame)
        self.pulse_timer.timeout.connect(self.update_pulse_effect)
        self.record_timer.timeout.connect(self.update_record_button)
        self.load_default_model()

    def initUI(self):
        self.setWindowTitle("AI蒙皮铝屑观察助手")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(self.BACKGROUND_STYLE)

        central_widget = QWidget()
        central_widget.setStyleSheet(self.BACKGROUND_STYLE)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        self.create_sidebar(main_layout)
        self.create_video_area(main_layout)
        self.setup_status_bar()

    def create_styled_frame(self, shape=QFrame.Shape.StyledPanel):
        frame = QFrame()
        frame.setFrameShape(shape)
        frame.setStyleSheet(
            f"{self.BACKGROUND_STYLE} border: 1px solid #75715E;")
        return frame

    def create_sidebar(self, main_layout):
        sidebar = self.create_styled_frame()
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar.setLayout(sidebar_layout)

        self.add_title(sidebar_layout, "功能面板")
        self.add_separator(sidebar_layout, Qt.Orientation.Horizontal)

        buttons = [
            ("加载AI模型", self.load_model),
            ("使用USB摄像头", self.open_camera),
            ("使用视频文件", self.open_video),
            ("录制训练数据", self.setup_recording_mode),
        ]

        for text, callback in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(self.BUTTON_STYLE)
            btn.clicked.connect(callback)
            sidebar_layout.addWidget(btn)
        self.add_confidence_slider(sidebar_layout)
        sidebar_layout.addStretch()
        self.add_separator(sidebar_layout, Qt.Orientation.Horizontal)

        self.start_stop_btn = QPushButton("开始检测")
        self.start_stop_btn.setStyleSheet("""
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            padding: 12px 24px;
            font-weight: bold;
        """)
        self.start_stop_btn.clicked.connect(self.toggle_video)
        self.start_stop_btn.setEnabled(False)
        sidebar_layout.addWidget(self.start_stop_btn)

        self.add_separator(sidebar_layout, Qt.Orientation.Horizontal)

        self.fps_label = QLabel("FPS: --")
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fps_label.setStyleSheet(self.FPS_LABEL_STYLE)
        sidebar_layout.addWidget(self.fps_label)

        main_layout.addWidget(sidebar)

    def create_video_area(self, main_layout):
        video_container = QWidget()
        video_container.setStyleSheet(self.BACKGROUND_STYLE)
        video_layout = QVBoxLayout()
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.setSpacing(10)
        video_container.setLayout(video_layout)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(800, 600)
        self.video_label.setStyleSheet(self.BACKGROUND_STYLE)
        video_layout.addWidget(self.video_label, stretch=1)

        self.record_panel = QWidget()
        self.record_panel.setVisible(False)
        record_panel_layout = QHBoxLayout()
        record_panel_layout.setContentsMargins(0, 0, 0, 0)
        record_panel_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.record_panel.setLayout(record_panel_layout)

        record_panel_layout.addStretch()
        self.select_path_btn = QPushButton("选择保存路径")
        self.select_path_btn.setStyleSheet(self.LARGE_BUTTON_STYLE)
        self.select_path_btn.setMinimumSize(150, 40)
        self.select_path_btn.clicked.connect(self.select_record_path)

        self.record_btn = QPushButton("开始录制")
        self.record_btn.setStyleSheet(self.LARGE_BUTTON_STYLE)
        self.record_btn.setMinimumSize(150, 40)
        self.record_btn.clicked.connect(self.toggle_recording)

        record_panel_layout.addWidget(self.select_path_btn)
        record_panel_layout.addWidget(self.record_btn)
        record_panel_layout.addStretch()

        video_layout.addWidget(self.record_panel)

        self.recording_label = QLabel("未录制")
        self.recording_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recording_label.setStyleSheet(
            "color: #FFFFFF; font-weight: bold; font-size: 16px;")
        self.recording_label.setVisible(False)
        video_layout.addWidget(self.recording_label)

        main_layout.addWidget(video_container, stretch=1)

    def setup_status_bar(self):
        self.statusBar().setStyleSheet(self.STATUS_BAR_STYLE)
        self.model_info_label = QLabel("<b>模型:</b> 未加载")
        self.model_info_label.setStyleSheet("font-weight: bold;")
        self.statusBar().addPermanentWidget(self.model_info_label)
        self.add_separator_to_status_bar()
        self.version_label = QLabel(f"<b>版本:</b> {APP_VERSION}")
        self.version_label.setStyleSheet("font-weight: bold;")
        self.statusBar().addPermanentWidget(self.version_label)

    def add_title(self, layout, text):
        label = QLabel(text)
        label.setStyleSheet(self.TITLE_STYLE)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

    def add_separator(self, layout, orientation):
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine if orientation ==
                                Qt.Orientation.Horizontal else QFrame.Shape.VLine)
        separator.setStyleSheet("color: #75715E;")
        layout.addWidget(separator)

    def add_separator_to_status_bar(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("color: #75715E;")
        self.statusBar().addPermanentWidget(separator)

    def add_confidence_slider(self, layout):
        confidence_label = QLabel("置信度阈值: 0.5")
        confidence_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        confidence_label.setStyleSheet(
            "font-weight: bold; background-color: #272822; color: #FFFFFF;")
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
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return "#{:02X}{:02X}{:02X}".format(int(r*255), int(g*255), int(b*255))

    def update_slider_style(self, value, label):
        confidence = value / 100.0
        label.setText(f"置信度阈值: {confidence:.2f}")
        self.processor.set_confidence(confidence)
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
        self.exit_recording_mode()
        model_path, _ = QFileDialog.getOpenFileName(
            self, "选择YOLO模型文件", "", "模型文件 (*.pt)")
        if model_path:
            self.update_model_info(model_path)
            success, message = self.processor.load_model(model_path)
            self.statusBar().showMessage(message, 3000)
            self.check_ready_state()

    def load_default_model(self):
        if os.path.exists("best.pt"):
            self.update_model_info("best.pt")
            success, message = self.processor.load_model("best.pt")
            self.statusBar().showMessage(message, 3000)
            self.check_ready_state()

    def update_model_info(self, model_path):
        self.current_model_path = model_path
        model_name = os.path.basename(model_path)
        try:
            mod_time = os.path.getmtime(model_path)
            mod_time_str = datetime.fromtimestamp(
                mod_time).strftime('%Y-%m-%d %H:%M')
            info_text = f"<b>模型:</b> {model_name} <b>修改时间:</b> {mod_time_str}"
        except Exception:
            info_text = f"<b>模型:</b> {model_name}"
        self.model_info_label.setText(info_text)

    def open_camera(self):
        self.exit_recording_mode()
        if self.processor.open_camera(0):
            self.statusBar().showMessage("摄像头已打开", 3000)
            self.check_ready_state()
            if not self.timer.isActive():
                self.toggle_video()
        else:
            self.statusBar().showMessage("无法打开摄像头", 3000)

    def open_video(self):
        self.exit_recording_mode()
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
        # 在录制模式下，开始检测按钮应该被禁用
        if self.recording_mode:
            self.start_stop_btn.setEnabled(False)
        else:
            self.start_stop_btn.setEnabled(self.processor.model is not None and
                                           self.processor.cap is not None and
                                           self.processor.cap.isOpened())

    def toggle_video(self):
        # 在录制模式下，不允许切换检测状态
        if self.recording_mode:
            return
            
        if self.timer.isActive():
            self.timer.stop()
            self.pulse_timer.stop()
            self.start_stop_btn.setText("开始检测")
            self.statusBar().showMessage("检测已停止", 2000)
            self.fps_label.setText("FPS: --")
            self.reset_button_style()
        else:
            self.processor.frame_count = 0
            self.processor.last_time = time.time()
            self.timer.start(30)
            self.pulse_timer.start(50)
            self.start_stop_btn.setText("停止检测")
            self.statusBar().showMessage("检测已开始", 2000)
            # 设置"停止检测"按钮的样式
            self.start_stop_btn.setStyleSheet("""
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                padding: 12px 24px;
                font-weight: bold;
            """)

    def update_frame(self):
        frame, ret = self.processor.get_frame()
        if ret:
            fps = self.processor.update_fps_counter()
            if fps is not None:
                self.fps_label.setText(f"FPS: {fps:.1f}")

            if self.recording and self.video_writer is not None:
                self.video_writer.write(frame)

            display_frame = frame.copy()
            if not self.recording_mode and self.processor.model is not None:
                results = self.processor.model(
                    display_frame, conf=self.processor.confidence_threshold)
                display_frame = results[0].plot()

            self.display_frame(display_frame)

    def display_frame(self, frame):
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

    def update_pulse_effect(self):
        if not self.timer.isActive():
            self.pulse_timer.stop()
            self.reset_button_style()
            return

        self.pulse_phase += self.pulse_speed
        if self.pulse_phase > 1:
            self.pulse_phase = 0
        alpha = 0.3 + 0.7 * \
            (0.5 + 0.5 * math.sin(self.pulse_phase * 2 * math.pi))
        color = f"rgba(244, 67, 54, {alpha})"  # 使用红色系脉冲效果

        self.start_stop_btn.setStyleSheet(f"""
            background-color: {color};
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            padding: 12px 24px;
            font-weight: bold;
        """)

    def reset_button_style(self):
        # 重置为"开始检测"按钮的样式，但保持大尺寸
        self.start_stop_btn.setStyleSheet("""
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            padding: 12px 24px;
            font-weight: bold;
        """)

    def setup_recording_mode(self):
        self.recording_mode = True
        if self.processor.open_camera(0):
            self.statusBar().showMessage("准备录制训练数据", 3000)
            self.record_panel.setVisible(True)
            self.recording_label.setVisible(True)

            if self.timer.isActive():
                self.toggle_video()

            self.timer.start(30)
            self.start_stop_btn.setEnabled(False)
            self.fps_label.setText("FPS: --")
        else:
            self.statusBar().showMessage("无法打开摄像头", 3000)
            self.recording_mode = False
            # 重置录制相关状态
            self.record_panel.setVisible(False)
            self.recording_label.setVisible(False)
            self.start_stop_btn.setEnabled(True)

    def exit_recording_mode(self):
        if self.recording_mode:
            if self.recording:
                self.stop_recording()

            # 停止为录制模式启动的预览定时器
            if self.timer.isActive():
                self.timer.stop()
                if self.pulse_timer.isActive():
                    self.pulse_timer.stop()
            
            self.record_panel.setVisible(False)
            self.recording_label.setVisible(False)
            self.recording_mode = False
            self.start_stop_btn.setEnabled(True)
            self.reset_button_style()  # 重置按钮状态
            self.fps_label.setText("FPS: --")

    def select_record_path(self):
        default_path = os.path.join(os.getcwd(), "training_data")
        if not os.path.exists(default_path):
            os.makedirs(default_path)

        # 生成带时间戳的默认文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if platform.system() == "Windows":
            default_file = os.path.join(default_path, f"training_{timestamp}.mp4")
            file_filter = "视频文件 (*.mp4)"
        else:
            default_file = os.path.join(default_path, f"training_{timestamp}.avi")
            file_filter = "视频文件 (*.avi)"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存训练视频", default_file, file_filter)

        if file_path:
            # 确保文件以正确的扩展名结尾
            if platform.system() == "Windows":
                if not file_path.lower().endswith('.mp4'):
                    file_path += '.mp4'
            else:
                if not file_path.lower().endswith('.avi'):
                    file_path += '.avi'
            self.record_path = file_path
            self.statusBar().showMessage(f"视频将保存到: {file_path}", 3000)

    def toggle_recording(self):
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        if not self.record_path:
            self.statusBar().showMessage("请先选择保存路径", 3000)
            return

        width = int(self.processor.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.processor.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(self.processor.cap.get(cv2.CAP_PROP_FPS))
        if fps <= 0:
            fps = 30

        # 根据操作系统选择合适的编码器
        if platform.system() == "Windows":
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        else:
            # Linux系统使用更兼容的编码器
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            # 如果文件路径是mp4，改为avi格式
            if self.record_path.lower().endswith('.mp4'):
                self.record_path = self.record_path[:-4] + '.avi'
        
        self.video_writer = cv2.VideoWriter(
            self.record_path, fourcc, fps, (width, height))

        if not self.video_writer.isOpened():
            self.statusBar().showMessage("无法创建视频文件", 3000)
            return

        self.recording = True
        self.record_btn.setText("停止录制")
        self.record_btn.setStyleSheet(self.RECORD_BUTTON_STYLE)
        self.recording_label.setText("录制中...")
        self.recording_label.setStyleSheet(
            "color: #FF0000; font-weight: bold; font-size: 16px;")
        self.record_timer.start(500)
        self.statusBar().showMessage("开始录制训练数据", 3000)

    def stop_recording(self):
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None

        self.recording = False
        self.record_btn.setText("开始录制")
        self.record_btn.setStyleSheet(self.LARGE_BUTTON_STYLE)
        self.recording_label.setText("未录制")
        self.recording_label.setStyleSheet(
            "color: #FFFFFF; font-weight: bold; font-size: 16px;")
        self.record_timer.stop()
        self.statusBar().showMessage(f"录制完成，视频已保存到: {self.record_path}", 5000)

    def update_record_button(self):
        if self.record_btn.styleSheet() == self.RECORD_BUTTON_STYLE:
            self.record_btn.setStyleSheet(
                "background-color: #880000; color: #FFFFFF; border: none; border-radius: 4px; font-size: 16px; padding: 8px 16px;")
        else:
            self.record_btn.setStyleSheet(self.RECORD_BUTTON_STYLE)

    def closeEvent(self, event):
        # 停止所有定时器
        if self.timer.isActive():
            self.timer.stop()
        if self.pulse_timer.isActive():
            self.pulse_timer.stop()
        if self.record_timer.isActive():
            self.record_timer.stop()
        
        # 停止录制并释放视频写入器
        if self.recording and self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None

        # 退出录制模式
        if self.recording_mode:
            self.exit_recording_mode()

        # 释放视频处理器资源
        self.processor.release()
        
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = YOLOVideoPlayer()
    player.show()
    sys.exit(app.exec())
