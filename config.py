import os
from datetime import datetime

# 应用信息
APP_VERSION = "v0.1.0 by Chang"
APP_TITLE = "AI蒙皮铝屑观察助手"

# 默认设置
DEFAULT_SETTINGS = {
    "confidence": 0.5,
    "window_size": (1200, 800),
    "window_position": (100, 100),
    "sidebar_width": 250,
    "video_min_size": (800, 600),
    "fps_update_interval": 50,
    "pulse_speed": 0.05,
    "record_timer_interval": 500,
    "default_model": "best.pt",
    "training_data_dir": "training_data"
}

# 模型相关设置
DETECTABLE_CLASSES = [0]  # 要检测的类别ID列表，None表示检测所有类别

# UI样式定义
STYLES = {
    "BACKGROUND": "background-color: #272822; color: #FFFFFF;",
    "BUTTON": "background-color: #3E3D32; color: #FFFFFF; border: none; border-radius: 4px;",
    "TITLE": "font-weight: bold; font-size: 14px; background-color: #272822; color: #FFFFFF;",
    "STATUS_BAR": """
        QStatusBar {
            background-color: #272822;
            color: #FFFFFF;
            border-top: 1px solid #75715E;
            font-family: Microsoft YaHei;
        }
        QLabel {
            color: #FFFFFF;
        }
    """,
    "FPS_LABEL": """
        font-weight: bold; 
        font-size: 16px; 
        background-color: #3E3D32; 
        border-radius: 4px;
        color: #FFFFFF;
    """,
    "RECORD_BUTTON": """
        background-color: #FF0000;
        color: #FFFFFF;
        border: none;
        border-radius: 4px;
        font-size: 16px;
        padding: 8px 16px;
    """,
    "LARGE_BUTTON": """
        background-color: #3E3D32;
        color: #FFFFFF;
        border: none;
        border-radius: 4px;
        font-size: 16px;
        padding: 8px 16px;
    """,
    "START_BUTTON": """
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 16px;
        padding: 12px 24px;
        font-weight: bold;
    """,
    "STOP_BUTTON": """
        background-color: #F44336;
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 16px;
        padding: 12px 24px;
        font-weight: bold;
    """,
    "RECORDING_LABEL": "color: #FFFFFF; font-weight: bold; font-size: 16px;",
    "RECORDING_ACTIVE": "color: #FF0000; font-weight: bold; font-size: 16px;",
    "CONFIDENCE_LABEL": "font-weight: bold; background-color: #272822; color: #FFFFFF;",
    "DISABLED_BUTTON": """
        background-color: #BDBDBD;
        color: #FFFFFF;
        border: none;
        border-radius: 4px;
        font-size: 16px;
        padding: 12px 24px;
        font-weight: bold;
    """
}

# 功能按钮配置
FUNCTION_BUTTONS = [
    ("加载AI模型", "load_model"),
    ("使用USB摄像头", "open_camera"),
    ("使用视频文件", "open_video"),
    ("设置ROI区域", "setup_roi_mode"),
    ("录制训练数据", "setup_recording_mode"),
]

# 文件过滤器
FILE_FILTERS = {
    "model": "模型文件 (*.pt)",
    "video": "视频文件 (*.mp4 *.avi *.mov)",
    "save_video_windows": "视频文件 (*.mp4)",
    "save_video_linux": "视频文件 (*.avi)"
}

# 视频编码器配置
VIDEO_CODECS = {
    "Windows": "mp4v",
    "Linux": "XVID"
}

# ROI相关配置
ROI_CONFIG = {
    "roi_folder": "roi_configs",
    "max_roi_count": 99,
    "temp_roi_file": "temp_roi.json",
    "main_config_file": "roi_config.json",
    "roi_file_pattern": "ROI_{}.json",
    "max_points": 100
} 