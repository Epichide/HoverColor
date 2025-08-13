import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow,QWidget
from PyQt5.QtGui import QPalette, QColor

class TransparentWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 设置窗口无边框和置顶（去掉 WA_TranslucentBackground）
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # 可选：设置窗口背景色（半透明），增强初始状态的可见性
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(255, 255, 255, 204))  # 白色，透明度80%（204/255≈0.8）
        self.setPalette(palette)

        # 设置窗口大小和初始透明度（0.8 对应80%不透明）
        self.setGeometry(100, 100, 300, 200)
        self.setWindowOpacity(0.8)

        # 添加标签
        label = QLabel("鼠标悬浮时透明度变化", self)
        label.setStyleSheet("color: black; font-size: 16px;")  # 黑色文字更清晰
        label.setAlignment(Qt.AlignCenter)
        label.setGeometry(50, 50, 200, 100)

    def enterEvent(self, event):
        # 鼠标进入时完全不透明
        self.setWindowOpacity(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        # 鼠标离开时恢复半透明
        self.setWindowOpacity(0.8)
        super().leaveEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TransparentWindow()
    window.show()
    sys.exit(app.exec_())