from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QPen

import glob
import os
import sys

class SegController(QObject):

    #COLOR_DIC = {
    #    '#000000' : 'Black', '#0000FF' : 'BLUE', '#000002' : '', '#000003' : '', '#000004' : '',
    #    '#000005' : 'Black', '#000006' : '', '#000007' : '', '#000008' : '', '#000009' : '',
    #    '#000010' : 'Black', '#000011' : '', '#000012' : '', '#000013' : '', '#000014' : '',
    #    '#000015' : 'Black', '#000016' : '', '#ffffff' : 'Other'
    #}

    COLOR_DIC = {
        0x000000 : 'BLACK', 0x0000FF : 'BLUE', 0x00FF00 : 'GREEN', 0xFF0000 : 'RED', 0xFFFFFF : 'WHITE'
    }

    PEN = QPen(Qt.DotLine)

    def __init__(self, model):
        super().__init__()
        self.BLANK_PIXMAP = QPixmap()
        self._model = model
        self.PEN.setColor(Qt.white)

    def on_file_open(self):
        media_dir = QFileDialog.getExistingDirectory(caption = 'Open Media Directory')
        if not media_dir : return
        data_dir = QFileDialog.getExistingDirectory(caption = 'Open Data Directory')
        if not data_dir: return

        self._model.media_dir = media_dir
        self._model.media_paths = glob.glob(os.path.join(self._model.media_dir, '**', '*.jpg'), recursive=True)
        self._model.data_dir = data_dir
        self._model.index = 0

    def on_slider_change(self, value):
        self._model.alpha = value

    def on_number_button_click(self):
        self._model.index = self._model.index + int(self.sender().text())

    def index_change(self):
        if os.path.isfile(self._model.media_path) and os.path.isfile(self._model.data_path):
            self._model.media_pixmap = QPixmap(self._model.media_path)
            self._model.data_pixmap = QPixmap(self._model.data_path)
            self._model.data_image = self._model.data_pixmap.toImage()
        else:
            self._model.media_pixmap = None
            self._model.data_pixmap = None
            self._model.data_image = None

    def image_label_size_change(self, w, h):
        self._model.data_image = self._model.data_pixmap.scaled(w, h).toImage()

    def on_grid_change(self, e):
        self._model.grid = e

    def update_pixmap(self):
        if not self._model.media_pixmap or not self._model.data_pixmap: return self.BLANK_PIXMAP
        p = QPainter()
        img = self._model.data_pixmap.toImage()

        p.begin(img)
        p.setOpacity(self._model.alpha / 10)
        p.drawPixmap(0, 0, self._model.media_pixmap)
        if self._model.grid:
            p.setPen(self.PEN)
            p.setOpacity(1)
            for h in range(20, img.height(), 20):
                p.drawLine(0, h, img.width(), h)
        p.end()
        return QPixmap.fromImage(img)

    def on_image_click(self, event):
        if not self._model.data_image: return
        x = event.x()
        y = event.y()
        # remove alpha (0xAARRGGBB -> 0xRRGGBB)
        rgb = self._model.data_image.pixel(x, y) & 0x00ffffff
        self._model.color_result = '{},{} : {}'.format(x, y, self.COLOR_DIC.get(rgb))

    def key_press_event(self, e):
        key = e.key()
        if key == Qt.Key_C:
            if self._model.alpha < 100:
                self._model.alpha = 100
            else:
                self._model.alpha = 0
