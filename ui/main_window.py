import os
import sys
import cv2
import time
import colorsys
import math
import platform
from datetime import datetime
import numpy as np
from enum import Enum, auto
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QFileDialog, QFrame, QSlider, QMessageBox)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QTimer

from config import (APP_VERSION, APP_TITLE, DEFAULT_SETTINGS, STYLES, 
                   FUNCTION_BUTTONS, FILE_FILTERS, VIDEO_CODECS)
from core.model_handler import ModelHandler
from core.video_handler import VideoHandler
from core.roi_handler import ROIHandler
from ui.roi_panel import ROIPanel


class UIState(Enum):
    IDLE = auto()      # 空闲状态
    VIEWING = auto()   # 正在查看一个已保存的ROI
    CREATING = auto()  # 正在创建一个新的ROI


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化处理器
        self.model_handler = ModelHandler()
        self.video_handler = VideoHandler()
        self.roi_handler = ROIHandler()
        
        # 初始化UI状态
        self.timer = QTimer(self)
        self.pulse_timer = QTimer(self)
        self.record_timer = QTimer(self)
        self.pulse_phase = 0
        self.recording_mode = False
        self.roi_mode = False
        self.ui_state = UIState.IDLE  # 初始化UI状态
        self.is_editing_roi = False
        self.unscaled_pixmap = None
        self.confidence_threshold = 0.5
        self.last_frame_time = time.time()
        # ROI警告闪烁相关
        self.roi_alert_flash = False
        self.roi_alert_timer = QTimer(self)
        self.roi_alert_timer.setInterval(200)
        self.roi_alert_timer.timeout.connect(self._toggle_roi_alert_flash)
        
        self.init_ui()
        self.setup_timers()
        self.load_default_model()
        self.setup_roi_connections()
        self._set_ui_state(UIState.IDLE)  # 设置初始UI状态

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
        # roi_alert_timer已在__init__中连接

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
        # 启用鼠标事件
        self.video_label.mousePressEvent = self.video_mouse_press_event
        video_layout.addWidget(self.video_label, stretch=1)

        # ROI控制面板
        self.roi_panel = ROIPanel()
        self.roi_panel.setVisible(False)
        video_layout.addWidget(self.roi_panel)

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

    def setup_roi_connections(self):
        """设置ROI面板信号连接"""
        self.roi_panel.roiEnabledChanged.connect(self.on_roi_enabled_changed)
        self.roi_panel.activeRoiChanged.connect(self.on_active_roi_changed)
        self.roi_panel.roiNameChanged.connect(self.on_roi_name_changed)
        self.roi_panel.coordinateChanged.connect(self.on_coordinate_changed)
        self.roi_panel.clearRoiRequested.connect(self.on_clear_roi_requested)
        self.roi_panel.saveRoiRequested.connect(self.on_save_roi_requested)
        self.roi_panel.createNewRoiRequested.connect(self.on_create_new_roi_requested)

    def _set_ui_state(self, new_state: UIState):
        """根据状态统一管理UI控件的启用/禁用"""
        self.ui_state = new_state
        
        if self.ui_state == UIState.IDLE:
            self.roi_panel.create_new_roi_btn.setEnabled(True)
            self.roi_panel.save_roi_btn.setEnabled(False)
            self.roi_panel.clear_roi_btn.setEnabled(True)
            self.roi_panel.roi_selector.setEnabled(True)
            self.roi_panel.clear_roi_btn.setText("删除ROI")
        
        elif self.ui_state == UIState.VIEWING:
            self.roi_panel.create_new_roi_btn.setEnabled(True)
            self.roi_panel.save_roi_btn.setEnabled(False) # 只能在创建或编辑后保存
            self.roi_panel.clear_roi_btn.setEnabled(True)
            self.roi_panel.roi_selector.setEnabled(True)
            self.roi_panel.clear_roi_btn.setText("删除ROI")

        elif self.ui_state == UIState.CREATING:
            self.roi_panel.create_new_roi_btn.setEnabled(False)
            self.roi_panel.save_roi_btn.setEnabled(True)
            self.roi_panel.clear_roi_btn.setEnabled(True)
            self.roi_panel.roi_selector.setEnabled(False)
            self.roi_panel.clear_roi_btn.setText("取消创建")

    def video_mouse_press_event(self, event):
        """视频区域的鼠标点击事件"""
        if not self.roi_mode:
            return
        
        if event.button() == Qt.MouseButton.LeftButton:
            # 任何添加点的行为都应视为开始编辑
            self.is_editing_roi = True
            
            # 获取点击位置（相对于QLabel的坐标）
            pos = event.pos()
            # 转换为图像坐标
            image_x, image_y = self.window_to_image_coords(pos.x(), pos.y())
            if image_x is not None:
                if len(self.roi_handler.get_current_points()) >= 100:
                    self.statusBar().showMessage("ROI点数已达上限（100个）", 2000)
                    return
                self.roi_handler.add_point(image_x, image_y)
                self.update_roi_display()

    def window_to_image_coords(self, label_x, label_y):
        """将QLabel内的坐标转换为图像坐标"""
        # 使用存储的未缩放pixmap进行计算
        pixmap = self.unscaled_pixmap
        
        if pixmap is None:
            return None, None
        
        # 获取原始图像尺寸
        original_width = pixmap.width()
        original_height = pixmap.height()
        
        # 获取QLabel的当前尺寸
        label_width = self.video_label.width()
        label_height = self.video_label.height()
        
        # 计算缩放后的图像尺寸（保持宽高比）
        scale_factor = min(label_width / original_width, label_height / original_height)
        scaled_width = int(original_width * scale_factor)
        scaled_height = int(original_height * scale_factor)
        
        # 计算图像在QLabel中的偏移量（居中显示）
        offset_x = (label_width - scaled_width) // 2
        offset_y = (label_height - scaled_height) // 2
        
        # 调整点击坐标（减去偏移量）
        adjusted_x = label_x - offset_x
        adjusted_y = label_y - offset_y
        
        # 检查点击是否在图像区域内
        if (adjusted_x < 0 or adjusted_x >= scaled_width or
            adjusted_y < 0 or adjusted_y >= scaled_height):
            return None, None
        
        # 转换到原始图像坐标
        image_x = int(adjusted_x / scale_factor)
        image_y = int(adjusted_y / scale_factor)
        
        # 确保坐标在有效范围内
        image_x = max(0, min(image_x, original_width - 1))
        image_y = max(0, min(image_y, original_height - 1))
        
        return image_x, image_y

    def update_roi_display(self):
        """更新ROI在视频帧上的显示"""
        # 确保我们有最新的帧来进行绘制
        frame, ret = self.video_handler.get_frame()
        if not ret or frame is None:
            # 如果没有可用的视频源，则显示空白屏幕
            if self.unscaled_pixmap:
                blank_pixmap = QPixmap(self.unscaled_pixmap.size())
                blank_pixmap.fill(Qt.GlobalColor.black)
                self.video_label.setPixmap(blank_pixmap.scaled(self.video_label.size(),
                                                               Qt.AspectRatioMode.KeepAspectRatio,
                                                               Qt.TransformationMode.SmoothTransformation))
            return

        points = self.roi_handler.get_current_points()
        
        if len(points) > 0:
            np_points = np.array(points, np.int32)
            
            if self.is_editing_roi:
                # 编辑模式: 绿色线条和蓝色顶点
                # 绘制ROI区域
                if len(points) > 2:
                    cv2.polylines(frame, [np_points], isClosed=True, color=(0, 255, 0), thickness=2)
                elif len(points) > 1:
                    cv2.polylines(frame, [np_points], isClosed=False, color=(0, 255, 0), thickness=2)

                # 绘制顶点
                for point in points:
                    cv2.circle(frame, tuple(point), 5, (255, 0, 0), -1)
            else:
                # 非编辑（保存/预览）模式: 半透明灰色线条
                if len(points) > 2:
                    overlay = np.full_like(frame, (200, 200, 200), dtype=np.uint8)
                    cv2.fillPoly(overlay, [np_points], (0, 0, 0))
                    alpha = 0.18
                    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
                    cv2.fillPoly(mask, [np_points], 255)
                    inv_mask = cv2.bitwise_not(mask)
                    for c in range(3):
                        frame[..., c] = np.where(
                            inv_mask == 255,
                            cv2.addWeighted(overlay[..., c], alpha, frame[..., c], 1 - alpha, 0),
                            frame[..., c]
                        )
                    cv2.polylines(frame, [np_points], isClosed=True, color=(150, 150, 150), thickness=2)

        self.display_frame(frame)
        
        # 更新ROI面板中的坐标显示（但不调用完整的update_roi_panel）
        if self.is_editing_roi and len(points) > 0:
            self.roi_panel.update_coordinates(points)

    def display_frame(self, frame):
        """显示帧"""
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format.Format_RGB888)
        
        # 存储原始的、未缩放的pixmap
        self.unscaled_pixmap = QPixmap.fromImage(qt_image)
        
        # 将缩放后的pixmap设置到标签上
        self.video_label.setPixmap(self.unscaled_pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

    def on_roi_enabled_changed(self, enabled):
        """处理ROI启用/禁用状态变化的槽函数"""
        self.roi_handler.set_roi_enabled(enabled)
        self.update_roi_display() # 总是更新显示，无论视频是否运行

    def on_active_roi_changed(self, roi_name):
        """处理当前活动ROI变化的槽函数"""
        if roi_name:  # 只有当选择了有效的ROI名称时才处理
            self.roi_handler.set_active_roi(roi_name)
            self.is_editing_roi = False  # 切换ROI时，默认为非编辑状态
            self.update_roi_display()
            self.statusBar().showMessage(f"已切换到ROI: {roi_name}", 2000)
            self._set_ui_state(UIState.VIEWING) # 进入查看状态
        else:
            self._set_ui_state(UIState.IDLE) # 进入空闲状态

    def on_roi_name_changed(self, name):
        """处理ROI名称变化的槽函数"""
        current_name = self.roi_handler.get_active_roi_name()
        if current_name and name and current_name != name:
            self.roi_handler.rename_roi(current_name, name)
            # 更新ROI选择器以反映名称变化
            self.update_roi_panel()

    def on_coordinate_changed(self, index, x, y):
        """处理坐标变化的槽函数"""
        active_roi = self.roi_handler.get_active_roi_name()
        if active_roi:
            points = self.roi_handler.get_roi_points(active_roi)
            if 0 <= index < len(points):
                points[index] = [x, y]
                if self.roi_handler.update_roi_points(active_roi, points):
                    self.update_roi_display()

    def on_clear_roi_requested(self):
        """处理清除ROI请求的槽函数"""
        # 根据当前状态决定是"取消创建"还是"删除ROI"
        if self.ui_state == UIState.CREATING:
            # 取消创建
            self.roi_handler.clear_drawing_points()
            self.roi_panel.set_roi_name("")
            self.update_roi_display()
            self.statusBar().showMessage("已取消创建ROI", 2000)
            self._set_ui_state(UIState.IDLE)
        
        elif self.ui_state == UIState.VIEWING:
            # 删除已存在的ROI
            active_roi_name = self.roi_handler.get_active_roi_name()
            if not active_roi_name:
                return

            reply = QMessageBox.question(self, '确认删除', 
                                         f"您确定要永久删除ROI '{active_roi_name}' 吗？",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                # 获取删除前的ROI列表和索引
                all_rois_before_delete = self.roi_handler.get_roi_names()
                try:
                    deleted_index = all_rois_before_delete.index(active_roi_name)
                except ValueError:
                    deleted_index = -1

                if self.roi_handler.clear_current_roi():
                    self.statusBar().showMessage(f"已删除ROI: {active_roi_name}", 3000)

                    # 确定下一个要选中的ROI
                    remaining_rois = self.roi_handler.get_roi_names()
                    next_roi_to_select = ""
                    if remaining_rois:
                        next_index = min(deleted_index, len(remaining_rois) - 1)
                        if next_index >= 0:
                            next_roi_to_select = remaining_rois[next_index]

                    # 在处理器中设置新的活动ROI
                    self.roi_handler.set_active_roi(next_roi_to_select)
                    
                    # 更新整个UI以反映新状态
                    self.update_roi_panel()
                    self.update_roi_display()
                    
                    # 根据是否还有活动ROI来设置最终的UI状态
                    if self.roi_handler.has_active_roi():
                        self._set_ui_state(UIState.VIEWING)
                    else:
                        self._set_ui_state(UIState.IDLE)
                else:
                    self.statusBar().showMessage(f"删除ROI '{active_roi_name}' 失败", 3000)

    def on_save_roi_requested(self):
        """处理保存ROI请求的槽函数"""
        if not self.roi_handler.get_current_points():
            self.statusBar().showMessage("ROI为空, 无法保存", 2000)
            return

        roi_name = self.roi_panel.get_roi_name().strip()
        if not roi_name:
            self.statusBar().showMessage("请输入ROI名称后再保存", 2000)
            return
            
        # 关键检查：在写入前检查文件是否存在于硬盘
        if self.roi_handler.is_roi_file_exists(roi_name):
            self.statusBar().showMessage(f"保存失败：文件 '{roi_name}.json' 已存在", 4000)
            QMessageBox.warning(self, "名称冲突", f"名为 '{roi_name}' 的ROI文件已存在，请使用其他名称。")
            return

        # 检查ROI数量限制
        if not self.roi_handler.can_create_roi():
            max_count = self.roi_handler.get_max_roi_count()
            self.statusBar().showMessage(f"ROI数量已达上限({max_count})，无法创建新ROI", 3000)
            return

        if self.roi_handler.finish_roi_drawing(roi_name):
            self.statusBar().showMessage(f"ROI '{roi_name}' 已成功保存", 3000)
            
            # 统一调用UI更新方法，该方法会刷新列表并选中新ROI
            self.update_roi_panel()
            self.update_roi_display()

            # 保存成功后进入查看状态
            self._set_ui_state(UIState.VIEWING)
        else:
            self.statusBar().showMessage("保存失败，请确保ROI至少包含3个点", 3000)

    def on_create_new_roi_requested(self):
        """处理创建新ROI的请求"""
        # 确保处于ROI模式
        if not self.roi_mode:
            self.setup_roi_mode()

        # 进入创建状态
        self._set_ui_state(UIState.CREATING)
        
        # 清除之前的绘制点和活动ROI
        self.roi_handler.clear_drawing_points()
        self.roi_handler.set_active_roi(None)
        
        # 开始绘制新ROI
        self.roi_handler.start_drawing()
        self.is_editing_roi = True
        
        # 生成唯一的ROI名称并设置
        auto_name = self.roi_handler.generate_unique_roi_name()
        self.roi_panel.set_roi_name(auto_name)
        
        # 更新显示
        self.update_roi_display()
        
        # 设置焦点到名称输入框
        self.roi_panel.roi_name_input.setFocus()
        
        current_count = self.roi_handler.get_roi_count()
        max_count = self.roi_handler.get_max_roi_count()
        self.statusBar().showMessage(f"开始创建新ROI，点击视频区域添加顶点 (当前: {current_count}/{max_count})", 3000)

    def update_roi_panel(self):
        """更新ROI面板的UI状态"""
        roi_names = self.roi_handler.get_roi_names()
        active_roi = self.roi_handler.get_active_roi_name()
        # 如果有ROI但当前未激活任何ROI，自动激活第一个
        if roi_names and (not active_roi or active_roi not in roi_names):
            first_roi = roi_names[0]
            self.roi_handler.set_active_roi(first_roi)
            self.roi_panel.update_roi_selector(roi_names, first_roi)
            # 强制触发一次activeRoiChanged信号，确保UI和状态同步
            self.on_active_roi_changed(first_roi)
            return
        self.roi_panel.update_roi_selector(roi_names, active_roi)
        # 进入设置ROI区域时，强制触发一次activeRoiChanged，保证UI和状态同步
        if active_roi:
            self.on_active_roi_changed(active_roi)
        # 更新ROI启用状态
        self.roi_panel.set_roi_enabled(self.roi_handler.is_roi_enabled())
        # 更新坐标显示
        if self.roi_handler.has_active_roi():
            points = self.roi_handler.get_roi_points(active_roi)
            self.roi_panel.update_coordinates(points)
            self.roi_panel.set_roi_name(self.roi_handler.get_active_roi_name())
        # 如果定时器仍在运行，则停止它
        if self.timer.isActive():
            self.timer.stop()

    def setup_roi_mode(self):
        """设置ROI模式"""
        self.roi_mode = True
        self.roi_handler.roi_mode = True
        
        # 默认打开摄像头
        if not self.video_handler.is_video_ready():
            if self.video_handler.open_camera(0):
                self.statusBar().showMessage("ROI模式：摄像头已打开", 3000)
            else:
                self.statusBar().showMessage("无法打开摄像头", 3000)
                return
        
        # 停止检测
        if self.timer.isActive():
            self.toggle_video()
        # 强制停止脉冲闪烁
        if self.pulse_timer.isActive():
            self.pulse_timer.stop()
        self.start_stop_btn.setEnabled(False)
        self.start_stop_btn.setText("开始检测")
        self.start_stop_btn.setStyleSheet(STYLES["DISABLED_BUTTON"])
        self.fps_label.setText("FPS: --")
        
        # 显示ROI面板
        self.roi_panel.setVisible(True)
        self.record_panel.setVisible(False)
        # self.recording_label.setVisible(False)
        
        # 更新ROI面板
        self.update_roi_panel()
        
        # 开始视频显示
        self.timer.start(DEFAULT_SETTINGS["fps_update_interval"])
        self.start_stop_btn.setEnabled(False)
        self.start_stop_btn.setText("开始检测")
        self.start_stop_btn.setStyleSheet(STYLES["DISABLED_BUTTON"])
        self.fps_label.setText("FPS: --")
        
        self.statusBar().showMessage("ROI模式：点击视频区域添加ROI顶点", 3000)

    def exit_roi_mode(self):
        """退出ROI模式"""
        if self.roi_mode:
            self.roi_mode = False
            self.roi_handler.roi_mode = False
            self.roi_handler.clear_drawing_points()
            
            if self.timer.isActive():
                self.timer.stop()
            
            self.roi_panel.setVisible(False)
            self.start_stop_btn.setEnabled(True)
            self.start_stop_btn.setText("开始检测")
            self.start_stop_btn.setStyleSheet(STYLES["START_BUTTON"])
            self.fps_label.setText("FPS: --")

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
        self.confidence_threshold = confidence  # 同步更新MainWindow的置信度阈值
        
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
        self.exit_roi_mode()
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
        self.exit_roi_mode()
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
        self.exit_roi_mode()
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
        if self.recording_mode or self.roi_mode:
            self.start_stop_btn.setEnabled(False)
            self.start_stop_btn.setText("开始检测")
            self.start_stop_btn.setStyleSheet(STYLES["DISABLED_BUTTON"])
        else:
            enabled = self.model_handler.is_model_loaded() and self.video_handler.is_video_ready()
            self.start_stop_btn.setEnabled(enabled)
            if self.timer.isActive():
                self.start_stop_btn.setText("停止检测")
                self.start_stop_btn.setStyleSheet(STYLES["STOP_BUTTON"])
            else:
                self.start_stop_btn.setText("开始检测")
                self.start_stop_btn.setStyleSheet(STYLES["START_BUTTON"])

    def toggle_video(self):
        """切换视频检测状态"""
        if self.recording_mode or self.roi_mode:
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
        """更新视频帧"""
        if not self.video_handler.is_running():
            return
        
        start_time = time.time()
        
        frame, ret = self.video_handler.get_frame()
        if not ret:
            self.statusBar().showMessage("无法读取视频帧", 2000)
            return

        # 录制模式下：只显示和录制原始帧，不做推理和ROI mask
        if self.recording_mode:
            self.display_frame(frame)
            if self.video_handler.is_recording():
                self.video_handler.write_frame(frame)
            self.last_frame_time = time.time()
            fps = 1.0 / (self.last_frame_time - start_time) if (self.last_frame_time - start_time) > 0 else 0
            self.fps_label.setText(f"FPS: {fps:.2f}")
            return

        # 非ROI模式下，进行目标检测
        active_roi = self.roi_handler.get_active_roi_name() if self.roi_handler.is_roi_enabled() else None
        
        # 首先对原始帧进行处理
        processed_frame, detected_class0 = self.model_handler.process_frame(
            frame,
            confidence_threshold=self.confidence_threshold,
            roi=self.roi_handler if active_roi else None
        )

        # ROI外部颜色逻辑
        if active_roi:
            points = self.roi_handler.get_roi_points(active_roi)
            if len(points) > 2:
                np_points = np.array(points, np.int32)
                # 检查是否需要红色闪烁
                if detected_class0:
                    if not self.roi_alert_timer.isActive():
                        self.roi_alert_flash = True
                        self.roi_alert_timer.start()
                    color = (0, 0, 255) if self.roi_alert_flash else (200, 200, 200)
                    alpha = 0.28 if self.roi_alert_flash else 0.18
                else:
                    if self.roi_alert_timer.isActive():
                        self.roi_alert_timer.stop()
                        self.roi_alert_flash = False
                    color = (200, 200, 200)
                    alpha = 0.18
                overlay = np.full_like(processed_frame, color, dtype=np.uint8)
                cv2.fillPoly(overlay, [np_points], (0, 0, 0))
                mask = np.zeros(processed_frame.shape[:2], dtype=np.uint8)
                cv2.fillPoly(mask, [np_points], 255)
                inv_mask = cv2.bitwise_not(mask)
                for c in range(3):
                    processed_frame[..., c] = np.where(
                        inv_mask == 255,
                        cv2.addWeighted(overlay[..., c], alpha, processed_frame[..., c], 1 - alpha, 0),
                        processed_frame[..., c]
                    )
                cv2.polylines(processed_frame, [np_points], isClosed=True, color=(150, 150, 150), thickness=1)

        self.display_frame(processed_frame)
        
        # ... 计算并显示FPS ...
        self.last_frame_time = time.time()
        fps = 1.0 / (self.last_frame_time - start_time) if (self.last_frame_time - start_time) > 0 else 0
        self.fps_label.setText(f"FPS: {fps:.2f}")

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
        self.exit_roi_mode()
        self.recording_mode = True
        if self.video_handler.open_camera(0):
            self.statusBar().showMessage("准备录制训练数据", 3000)
            self.record_panel.setVisible(True)
            # self.recording_label.setVisible(True)
            if self.timer.isActive():
                self.toggle_video()
            # 强制停止脉冲闪烁
            if self.pulse_timer.isActive():
                self.pulse_timer.stop()
            self.timer.start(DEFAULT_SETTINGS["fps_update_interval"])
            self.start_stop_btn.setEnabled(False)
            self.start_stop_btn.setText("开始检测")
            self.start_stop_btn.setStyleSheet(STYLES["DISABLED_BUTTON"])
            self.fps_label.setText("FPS: --")
        else:
            self.statusBar().showMessage("无法打开摄像头", 3000)
            self.recording_mode = False
            self.record_panel.setVisible(False)
            # self.recording_label.setVisible(False)
            self.start_stop_btn.setEnabled(True)
            self.start_stop_btn.setText("开始检测")
            self.start_stop_btn.setStyleSheet(STYLES["START_BUTTON"])

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
            # self.recording_label.setVisible(False)
            self.recording_mode = False
            self.start_stop_btn.setEnabled(True)
            self.start_stop_btn.setText("开始检测")
            self.start_stop_btn.setStyleSheet(STYLES["START_BUTTON"])
            self.fps_label.setText("FPS: --")

    def select_record_path(self):
        """选择录制保存路径（仅支持mp4）"""
        default_path = os.path.join(os.getcwd(), DEFAULT_SETTINGS["training_data_dir"])
        if not os.path.exists(default_path):
            os.makedirs(default_path)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_file = os.path.join(default_path, f"training_{timestamp}.mp4")
        file_filter = "视频文件 (*.mp4)"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存训练视频", default_file, file_filter)

        if file_path:
            if not file_path.lower().endswith('.mp4'):
                file_path += '.mp4'
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
            # self.recording_label.setText("录制中...")
            # self.recording_label.setStyleSheet(STYLES["RECORDING_ACTIVE"])
            self.record_timer.start(DEFAULT_SETTINGS["record_timer_interval"])
            self.statusBar().showMessage("开始录制训练数据", 3000)
        else:
            self.statusBar().showMessage(message, 3000)

    def stop_recording(self):
        """停止录制"""
        success, message = self.video_handler.stop_recording()
        self.record_btn.setText("开始录制")
        self.record_btn.setStyleSheet(STYLES["LARGE_BUTTON"])
        # self.recording_label.setText("未录制")
        # self.recording_label.setStyleSheet(STYLES["RECORDING_LABEL"])
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
        
        # 退出ROI模式
        if self.roi_mode:
            self.exit_roi_mode()

        # 释放资源
        self.video_handler.release()
        
        event.accept() 

    def _toggle_roi_alert_flash(self):
        self.roi_alert_flash = not self.roi_alert_flash
        # 强制刷新帧
        self.update_frame() 