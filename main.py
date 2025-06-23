#!/usr/bin/env python3
"""
AI蒙皮铝屑观察助手
主程序入口
"""

import sys
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QTimer
from ui.main_window import MainWindow
import time
from config import DEFAULT_SETTINGS


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 启动动画：全透明背景SplashScreen
    splash_pix = QPixmap(480, 280)
    splash_pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(splash_pix)
    # 只绘制logo和文字，不绘制任何背景色块
    painter.setPen(Qt.GlobalColor.white)
    painter.setFont(QFont('WenQuanYi Micro Hei', 32, QFont.Weight.Bold))
    painter.drawText(splash_pix.rect(), Qt.AlignmentFlag.AlignCenter, "AI蒙皮铝屑观察助手")
    painter.setFont(QFont('WenQuanYi Micro Hei', 14))
    painter.drawText(0, 220, 480, 40, Qt.AlignmentFlag.AlignCenter, "正在加载主程序，请稍候...")
    painter.end()
    splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
    splash.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    splash.show()
    app.processEvents()

    # 模拟加载进度（可根据实际加载步骤动态更新）
    for i in range(1, 6):
        splash.showMessage(f"加载进度：{i*20}%", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, Qt.GlobalColor.white)
        app.processEvents()
        time.sleep(0.15)  # 可根据实际加载速度调整

    # 创建主窗口
    window = MainWindow()

    # 计算主窗口新位置，使视频区中心和SplashScreen中心重合
    screen = app.primaryScreen()
    screen_rect = screen.geometry()
    splash_center_x = screen_rect.x() + screen_rect.width() // 2
    splash_center_y = screen_rect.y() + screen_rect.height() // 2

    win_w, win_h = DEFAULT_SETTINGS["window_size"]
    sidebar_w = DEFAULT_SETTINGS["sidebar_width"]
    video_w, video_h = DEFAULT_SETTINGS["video_min_size"]
    # 视频区中心相对于主窗口左上角的位置
    video_center_x = sidebar_w + video_w // 2
    video_center_y = win_h // 2
    # 计算主窗口左上角应放置的位置
    win_x = splash_center_x - video_center_x
    win_y = splash_center_y - video_center_y
    window.move(win_x, win_y)

    window.show()
    app.processEvents()

    # 延迟1秒后关闭SplashScreen
    QTimer.singleShot(1000, lambda: splash.finish(window))

    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 