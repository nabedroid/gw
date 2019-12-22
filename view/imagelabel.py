from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLabel

class ImageLabel(QLabel):

    size_change = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()

    def resizeEvent(self, e):
        self.size_change.emit(e.size().width(), e.size().height())