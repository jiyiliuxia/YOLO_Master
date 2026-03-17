"""
main.py — YOLO-Studio 程序入口
"""
import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from app.ui.main_window import MainWindow


def load_stylesheet(qss_path: str) -> str:
    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def main():
    # 高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("YOLO-Studio")
    app.setOrganizationName("YoloMaster")

    # 加载暗黑主题 QSS
    qss_path = os.path.join(os.path.dirname(__file__), "app", "ui", "styles.qss")
    qss = load_stylesheet(qss_path)
    if qss:
        app.setStyleSheet(qss)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
