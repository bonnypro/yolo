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

# 版本信息常量
APP_VERSION = "v1.0.0 by Chang"


class YOLOVideoPlayer(QMainWindow):
    # 样式常量
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

    def __init__(self):
        super().__init__()
        self.processor = VideoProcessor()
        self.timer = QTimer(self)
        self.pulse_animation = None
        self.pulse_timer = QTimer(self)
        self.pulse_phase = 0
        self.pulse_speed = 0.05
        self.current_model_path = None

        self.initUI()
        self.timer.timeout.connect(self.update_frame)
        self.pulse_timer.timeout.connect(self.update_pulse_effect)
        self.load_default_model()

    def initUI(self):
        """初始化用户界面"""
        self.setWindowTitle("AI蒙皮铝屑观察助手")
        self.setGeometry(100, 100, 1000, 600)
        self.setStyleSheet(self.BACKGROUND_STYLE)

        central_widget = QWidget()
        central_widget.setStyleSheet(self.BACKGROUND_STYLE)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        self.create_sidebar(main_layout)
        self.create_video_area(main_layout)
        self.setup_status_bar()

    def create_sidebar(self, main_layout):
        """创建侧边栏"""
        sidebar = self.create_styled_frame()
        sidebar.setFixedWidth(250)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar.setLayout(sidebar_layout)

        self.add_title(sidebar_layout, "功能面板")
        self.add_separator(sidebar_layout, Qt.Orientation.Horizontal)

        # 添加按钮
        buttons = [
            ("加载YOLO模型", self.load_model),
            ("打开USB摄像头", self.open_camera),
            ("打开视频文件", self.open_video),
        ]

        for text, callback in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(self.BUTTON_STYLE)
            btn.clicked.connect(callback)
            sidebar_layout.addWidget(btn)

        self.start_stop_btn = QPushButton("开始检测")
        self.start_stop_btn.setStyleSheet(self.BUTTON_STYLE)
        self.start_stop_btn.clicked.connect(self.toggle_video)
        self.start_stop_btn.setEnabled(False)
        sidebar_layout.addWidget(self.start_stop_btn)

        self.add_confidence_slider(sidebar_layout)
        sidebar_layout.addStretch()

        self.add_separator(sidebar_layout, Qt.Orientation.Horizontal)

        self.fps_label = QLabel("FPS: --")
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fps_label.setStyleSheet(self.FPS_LABEL_STYLE)
        sidebar_layout.addWidget(self.fps_label)

        main_layout.addWidget(sidebar)

    def create_video_area(self, main_layout):
        """创建视频显示区域"""
        video_container = QWidget()
        video_container.setStyleSheet(self.BACKGROUND_STYLE)
        video_layout = QVBoxLayout()
        video_container.setLayout(video_layout)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet(self.BACKGROUND_STYLE)
        video_layout.addWidget(self.video_label)

        main_layout.addWidget(video_container, stretch=1)

    def setup_status_bar(self):
        """设置状态栏"""
        self.statusBar().setStyleSheet(self.STATUS_BAR_STYLE)

        # 模型信息标签
        self.model_info_label = QLabel("<b>模型:</b> 未加载")
        self.model_info_label.setStyleSheet("font-weight: bold;")
        self.statusBar().addPermanentWidget(self.model_info_label)

        self.add_separator_to_status_bar()

        # 版本信息
        self.version_label = QLabel(f"<b>版本:</b> {APP_VERSION}")
        self.version_label.setStyleSheet("font-weight: bold;")
        self.statusBar().addPermanentWidget(self.version_label)

    def create_styled_frame(self, shape=QFrame.Shape.StyledPanel):
        """创建带有样式的框架"""
        frame = QFrame()
        frame.setFrameShape(shape)
        frame.setStyleSheet(
            f"{self.BACKGROUND_STYLE} border: 1px solid #75715E;")
        return frame

    def add_title(self, layout, text):
        """添加标题到布局"""
        label = QLabel(text)
        label.setStyleSheet(self.TITLE_STYLE)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

    def add_separator(self, layout, orientation):
        """添加分隔线到布局"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine if orientation ==
                                Qt.Orientation.Horizontal else QFrame.Shape.VLine)
        separator.setStyleSheet("color: #75715E;")
        layout.addWidget(separator)

    def add_separator_to_status_bar(self):
        """添加分隔线到状态栏"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("color: #75715E;")
        self.statusBar().addPermanentWidget(separator)

    def load_model(self):
        """加载YOLO模型"""
        model_path, _ = QFileDialog.getOpenFileName(
            self, "选择YOLO模型文件", "", "模型文件 (*.pt)")
        if model_path:
            self.update_model_info(model_path)
            success, message = self.processor.load_model(model_path)
            self.statusBar().showMessage(message, 3000)
            self.check_ready_state()

    def load_default_model(self):
        """尝试加载默认模型(best.pt)"""
        if os.path.exists("best.pt"):
            self.update_model_info("best.pt")
            success, message = self.processor.load_model("best.pt")
            self.statusBar().showMessage(message, 3000)
            self.check_ready_state()

    def update_model_info(self, model_path):
        """更新模型信息显示"""
        self.current_model_path = model_path
        model_name = os.path.basename(model_path)

        try:
            mod_time = os.path.getmtime(model_path)
            mod_time_str = datetime.fromtimestamp(
                mod_time).strftime('%Y-%m-%d %H:%M')
            info_text = f"<b>模型:</b> {model_name} <b>修改时间:</b> {mod_time_str}"
        except Exception as e:
            info_text = f"<b>模型:</b> {model_name}"

        self.model_info_label.setText(info_text)

    def open_camera(self):
        """打开USB摄像头"""
        if self.processor.open_camera(0):  # 默认使用索引0的摄像头
            self.statusBar().showMessage("摄像头已打开", 3000)
            self.check_ready_state()
            # 立即开始检测
            if not self.timer.isActive():
                self.toggle_video()
        else:
            self.statusBar().showMessage("无法打开摄像头", 3000)

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

    def update_pulse_effect(self):
        """更新脉冲动画效果"""
        if not self.timer.isActive():
            self.pulse_timer.stop()
            self.reset_button_style()
            return

        self.pulse_phase += self.pulse_speed
        if self.pulse_phase > 1:
            self.pulse_phase = 0
        # 使用正弦函数创建平滑的脉冲效果
        alpha = 0.3 + 0.7 * \
            (0.5 + 0.5 * math.sin(self.pulse_phase * 2 * math.pi))
        color = f"rgba(0, 120, 215, {alpha})"  # 蓝色脉冲

        self.start_stop_btn.setStyleSheet(f"""
            background-color: {color};
            color: #FFFFFF;
            border: none;
            border-radius: 4px;
        """)

    def reset_button_style(self):
        """重置按钮样式"""
        self.start_stop_btn.setStyleSheet(self.BUTTON_STYLE)

    def add_confidence_slider(self, layout):
        """添加置信度调节滑块(使用HSV颜色空间)"""
        confidence_label = QLabel("置信度阈值: 0.5")
        confidence_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        confidence_label.setStyleSheet(
            "font-weight: bold; background-color: #272822; color: #FFFFFF;")
        layout.addWidget(confidence_label)

        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setRange(10, 100)  # 0.1到1.0，步长0.01
        self.confidence_slider.setValue(50)
        self.confidence_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.confidence_slider.setTickInterval(10)  # 每0.1一个刻度
        self.confidence_slider.setSingleStep(1)    # 步长0.01

        self.update_slider_style(50, confidence_label)
        self.confidence_slider.valueChanged.connect(
            lambda value: self.update_slider_style(value, confidence_label))
        layout.addWidget(self.confidence_slider)

    def hsv_to_hex(self, h, s, v):
        """将HSV颜色转换为十六进制"""
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return "#{:02X}{:02X}{:02X}".format(int(r*255), int(g*255), int(b*255))

    def update_slider_style(self, value, label):
        """更新滑块样式和标签(使用HSV颜色空间)"""
        confidence = value / 100.0
        label.setText(f"置信度阈值: {confidence:.2f}")
        self.processor.set_confidence(confidence)

        hue = (1.0 - confidence) * 240 / 360  # 归一化到0-1
        color_hex = self.hsv_to_hex(hue, 0.9, 0.9)

        tick_style = f"""
            QSlider::sub-page:horizontal {{
                background: {color_hex};
                height: 8px;
                border-radius: 4px;
            }}
            QSlider::groove:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0000FF,    /* 蓝色 */
                    stop:0.5 #00FF00,  /* 绿色 */
                    stop:1 #FF0000);   /* 红色 */
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
