from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

import glob
import os
import sys

class Seg029(QMainWindow):

    WINDOW_WIDTH = 1024
    WINDOW_HEIGHT = 900
    IMAGE_WIDTH = 1024
    IMAGE_HEIGHT = 768
    COLOR_DIC = {
        '#000000' : 'Black', '#000001' : '', '#000002' : '', '#000003' : '', '#000004' : '',
        '#000005' : 'Black', '#000006' : '', '#000007' : '', '#000008' : '', '#000009' : '',
        '#000010' : 'Black', '#000011' : '', '#000012' : '', '#000013' : '', '#000014' : '',
        '#000015' : 'Black', '#000016' : '', '#ffffff' : 'Other'
    }

    def __init__(self):
        super().__init__()
        self.mediaPaths = glob.glob('media/**/*.jpg', recursive=True)
        self.pixmaps = [QPixmap(), QPixmap()]
        self.image = None
        self.initUI()

    def initUI(self):
        super().__init__(self)

        self.imgLabel = QLabel('img')
        self.imgLabel.imageMode = 'png'
        self.imgLabel.mousePressEvent = self.onImageClicked

        self.minus100Button = QPushButton('-100')
        self.minus5Button = QPushButton('-5')
        self.minus1Button = QPushButton('-1')
        self.plus1Button = QPushButton('+1')
        self.plus5Button = QPushButton('+5')
        self.plus100Button = QPushButton('+100')
        for b in [self.minus100Button, self.minus5Button, self.minus1Button, self.plus1Button, self.plus5Button, self.plus100Button]:
            b.clicked.connect(self.onButtonClicked)
        self.indexLabel = QLabel('001')

        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(self.minus100Button)
        hbox.addWidget(self.minus5Button)
        hbox.addWidget(self.minus1Button)
        hbox.addWidget(self.indexLabel)
        hbox.addWidget(self.plus1Button)
        hbox.addWidget(self.plus5Button)
        hbox.addWidget(self.plus100Button)
        hbox.addStretch()
        vbox = QVBoxLayout()
        vbox.addWidget(self.imgLabel)
        vbox.addLayout(hbox)
        cw = QWidget()
        cw.setLayout(vbox)

        self.setCentralWidget(cw)
        self.setWindowTitle('Color Picker')
        self.statusBar().showMessage('')
        self.setGeometry(0, 0, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.loadImage()
        self.show()

    def keyPressEvent(self, e):
        key = e.key()
        if key == Qt.Key_N:
            self.plus1Button.clicked.emit()
        elif key == Qt.Key_B:
            self.minus1Button.clicked.emit()
        elif key == Qt.Key_C:
            if self.pixmaps[0].isNull() == False and self.pixmaps[1].isNull() == False:
                if self.imgLabel.imageMode == 'png':
                    self.imgLabel.setPixmap(self.pixmaps[0])
                    self.imgLabel.imageMode = 'jpg'
                else:
                    self.imgLabel.setPixmap(self.pixmaps[1])
                    self.imgLabel.imageMode = 'png'
        else:
            super().keyPressEvent(e)

    def loadImage(self):
        mp = self.mediaPaths[int(self.indexLabel.text()) - 1]
        dp = os.path.join(os.path.dirname(mp.replace('media', 'data')), 'PNG', os.path.basename(mp).replace('jpg', 'png'))
        self.pixmaps[0] = QPixmap(mp)
        self.pixmaps[1] = QPixmap(dp)
        if self.pixmaps[1].isNull() or self.pixmaps[1].isNull():
            self.imgLabel.setPixmap(QPixmap())
            self.imgLabel.setText('jpg/png file not found')
            self.image = None
        else:
            for i, px in enumerate(self.pixmaps): self.pixmaps[i] = px.scaled(self.IMAGE_WIDTH, self.IMAGE_HEIGHT)
            self.imgLabel.setPixmap(self.pixmaps[1])
            self.imgLabel.imageMode = 'png'
            self.image = self.pixmaps[1].toImage()
            self.setWindowTitle(dp)

    def onImageClicked(self, event):
        if self.image != None:
            color = self.image.pixelColor(event.x(), event.y())
            self.statusBar().showMessage('{} -> {}'.format(color.name(), self.COLOR_DIC.get(color.name(), '?')))
        else:
            self.statusBar().showMessage('no image')

    def onButtonClicked(self):
        newIdx = int(self.indexLabel.text()) + int(self.sender().text())
        if 0 < newIdx <= len(self.mediaPaths):
            self.indexLabel.setText('{:03d}'.format(newIdx))
            self.loadImage()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Seg029()
    sys.exit(app.exec_())
