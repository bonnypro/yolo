import os
import glob
import cv2
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QCheckBox, QComboBox, QLineEdit,
                             QFrame, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from config import STYLES
from core.roi_handler import ROIHandler


class CoordinateTextBox(QLineEdit):
    """坐标输入文本框"""
    coordinateChanged = pyqtSignal(int, int, int)  # index, x, y
    
    def __init__(self, index, x, y, parent=None):
        super().__init__(parent)
        self.index = index
        self.setStyleSheet("""
            QLineEdit {
                background-color: #3E3D32;
                color: #FFFFFF;
                border: 1px solid #75715E;
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 11px;
                min-width: 90px;
                max-width: 90px;
            }
            QLineEdit:focus {
                border: 1px solid #A6E22E;
            }
        """)
        self.setText(f"({x}, {y})")
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.textChanged.connect(self._on_text_changed)
    
    def _on_text_changed(self):
        """文本变化时验证坐标"""
        result = ROIHandler.validate_coordinate(self.text())
        if result:
            x, y = result
            self.coordinateChanged.emit(self.index, x, y)
    
    def set_coordinate(self, x, y):
        """设置坐标值"""
        self.setText(f"({x}, {y})")


class ROIPanel(QWidget):
    """ROI控制面板"""
    roiEnabledChanged = pyqtSignal(bool)
    activeRoiChanged = pyqtSignal(str)
    roiNameChanged = pyqtSignal(str)
    coordinateChanged = pyqtSignal(int, int, int)
    clearRoiRequested = pyqtSignal()
    saveRoiRequested = pyqtSignal()
    createNewRoiRequested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.coordinate_boxes = []
        self.roi_folder = "roi_configs"  # ROI文件夹路径
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setStyleSheet(STYLES["BACKGROUND"])
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)
        
        # 第一行：启用ROI和ROI选择
        first_row = QHBoxLayout()
        first_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # 启用ROI复选框
        self.enable_roi_checkbox = QCheckBox("启用ROI")
        self.enable_roi_checkbox.setStyleSheet("""
            QCheckBox {
                color: #FFFFFF;
                font-size: 12px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #3E3D32;
                border: 1px solid #75715E;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #A6E22E;
                border: 1px solid #A6E22E;
                border-radius: 3px;
            }
        """)
        self.enable_roi_checkbox.toggled.connect(self.roiEnabledChanged)
        first_row.addWidget(self.enable_roi_checkbox)
        
        first_row.addSpacing(20)
        
        # ROI选择下拉框
        roi_select_label = QLabel("ROI选择:")
        roi_select_label.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: bold;")
        first_row.addWidget(roi_select_label)
        
        self.roi_selector = QComboBox()
        self.roi_selector.setStyleSheet("""
            QComboBox {
                background-color: #3E3D32;
                color: #FFFFFF;
                border: 1px solid #75715E;
                border-radius: 3px;
                padding: 2px 6px;
                font-size: 12px;
                min-width: 120px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #FFFFFF;
            }
        """)
        self.roi_selector.currentTextChanged.connect(self.activeRoiChanged)
        first_row.addWidget(self.roi_selector)
        
        first_row.addSpacing(20)
        
        # ROI数量显示
        self.roi_count_label = QLabel("ROI: 0/99")
        self.roi_count_label.setStyleSheet("color: #A6E22E; font-size: 11px; font-weight: bold;")
        first_row.addWidget(self.roi_count_label)
        
        first_row.addStretch()
        layout.addLayout(first_row)
        
        # 分隔线
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setStyleSheet("color: #75715E;")
        layout.addWidget(separator1)
        
        # 第二行：ROI名称和坐标列表
        second_row = QHBoxLayout()
        second_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # ROI名称
        roi_name_label = QLabel("ROI名称:")
        roi_name_label.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: bold;")
        second_row.addWidget(roi_name_label)
        
        self.roi_name_input = QLineEdit()
        self.roi_name_input.setStyleSheet("""
            QLineEdit {
                background-color: #3E3D32;
                color: #FFFFFF;
                border: 1px solid #75715E;
                border-radius: 3px;
                padding: 2px 6px;
                font-size: 12px;
                min-width: 100px;
                max-width: 100px;
            }
            QLineEdit:focus {
                border: 1px solid #A6E22E;
                outline: none;
            }
        """)
        self.roi_name_input.textChanged.connect(self.roiNameChanged)
        second_row.addWidget(self.roi_name_input)
        
        second_row.addSpacing(20)
        
        # 坐标列表标签
        coord_label = QLabel("坐标列表:")
        coord_label.setStyleSheet("color: #FFFFFF; font-size: 12px; font-weight: bold;")
        second_row.addWidget(coord_label)
        
        # 坐标列表容器
        self.coord_container = QWidget()
        self.coord_layout = QHBoxLayout()
        self.coord_layout.setContentsMargins(0, 0, 0, 0)
        self.coord_layout.setSpacing(6)
        self.coord_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.coord_container.setLayout(self.coord_layout)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.coord_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #272822;
                border: 1px solid #75715E;
                border-radius: 3px;
            }
            QScrollBar:horizontal {
                background-color: #272822;
                height: 10px;
                margin: 0px 15px 0 15px;
                border: 1px solid #75715E;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background-color: #75715E;
                min-width: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #A6E22E;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                background: none;
                border: none;
            }
        """)
        
        scroll_area.setFixedHeight(35)
        second_row.addWidget(scroll_area, 1) # 让滚动区域占据更多空间
        
        second_row.addStretch()
        layout.addLayout(second_row)
        
        # 分隔线
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet("color: #75715E;")
        layout.addWidget(separator2)
        
        # 第三行：操作按钮
        button_row = QHBoxLayout()
        button_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # 创建新的ROI按钮
        self.create_new_roi_btn = QPushButton("创建新的ROI")
        self.create_new_roi_btn.setStyleSheet(STYLES["BUTTON"])
        self.create_new_roi_btn.clicked.connect(self.createNewRoiRequested)
        button_row.addWidget(self.create_new_roi_btn)
        
        button_row.addSpacing(10)
        
        # 删除ROI按钮
        self.clear_roi_btn = QPushButton("删除ROI")
        self.clear_roi_btn.setStyleSheet(STYLES["BUTTON"])
        self.clear_roi_btn.clicked.connect(self.clearRoiRequested)
        button_row.addWidget(self.clear_roi_btn)
        
        button_row.addSpacing(10)
        
        # 保存ROI按钮
        self.save_roi_btn = QPushButton("保存ROI")
        self.save_roi_btn.setStyleSheet(STYLES["BUTTON"])
        self.save_roi_btn.clicked.connect(self.saveRoiRequested)
        button_row.addWidget(self.save_roi_btn)
        
        button_row.addStretch()
        layout.addLayout(button_row)
        
        self.setLayout(layout)
    
    def set_roi_enabled(self, enabled):
        """设置ROI启用状态"""
        self.enable_roi_checkbox.setChecked(enabled)
    
    def is_roi_enabled(self):
        """获取ROI启用状态"""
        return self.enable_roi_checkbox.isChecked()
    
    def update_roi_selector(self, roi_names: list, active_roi: str = ""):
        """更新ROI选择器。"""
        self.roi_selector.blockSignals(True)
        
        self.roi_selector.clear()
        self.roi_selector.addItem("")  # Add a blank item for "no selection"
        
        if roi_names:
            self.roi_selector.addItems(roi_names)
        
        if active_roi and active_roi in roi_names:
            self.roi_selector.setCurrentText(active_roi)
        else:
            self.roi_selector.setCurrentIndex(0) # Select blank

        self.roi_selector.blockSignals(False)
        self.update_roi_count_display(len(roi_names))
    
    def update_roi_count_display(self, count):
        """更新ROI数量显示"""
        self.roi_count_label.setText(f"ROI: {count}/99")
        
        # 根据数量设置颜色
        if count >= 99:
            self.roi_count_label.setStyleSheet("color: #F92672; font-size: 11px; font-weight: bold;")  # 红色
        elif count >= 80:
            self.roi_count_label.setStyleSheet("color: #FD971F; font-size: 11px; font-weight: bold;")  # 橙色
        else:
            self.roi_count_label.setStyleSheet("color: #A6E22E; font-size: 11px; font-weight: bold;")  # 绿色
    
    def set_active_roi(self, roi_name):
        """设置当前激活的ROI"""
        index = self.roi_selector.findText(roi_name)
        if index >= 0:
            self.roi_selector.setCurrentIndex(index)
    
    def get_active_roi(self):
        """获取当前激活的ROI"""
        return self.roi_selector.currentText()
    
    def set_roi_name(self, name):
        """设置ROI名称"""
        self.roi_name_input.setText(name)
    
    def get_roi_name(self):
        """获取ROI名称"""
        return self.roi_name_input.text()
    
    def update_coordinates(self, points):
        """更新坐标显示"""
        # 清除现有坐标框
        for box in self.coordinate_boxes:
            self.coord_layout.removeWidget(box)
            box.deleteLater()
        self.coordinate_boxes.clear()

        # 移除所有stretch（弹性空间）
        while self.coord_layout.count() > 0:
            item = self.coord_layout.itemAt(self.coord_layout.count() - 1)
            if item.spacerItem():
                self.coord_layout.takeAt(self.coord_layout.count() - 1)
            else:
                break

        # 添加新的坐标框
        for i, point in enumerate(points):
            x, y = point
            coord_box = CoordinateTextBox(i, x, y)
            coord_box.setAlignment(Qt.AlignmentFlag.AlignLeft)
            coord_box.coordinateChanged.connect(self.coordinateChanged)
            self.coord_layout.addWidget(coord_box)
            self.coordinate_boxes.append(coord_box)
        # 添加弹性空间
        self.coord_layout.addStretch()
    
    def get_coordinates(self):
        """获取所有坐标"""
        coordinates = []
        for box in self.coordinate_boxes:
            text = box.text()
            result = ROIHandler.validate_coordinate(text)
            if result:
                coordinates.append(list(result))
        return coordinates
    
    def set_panel_visible(self, visible):
        """设置面板可见性"""
        self.setVisible(visible) 