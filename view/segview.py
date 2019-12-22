from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSlider
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from view.imagelabel import ImageLabel

class SegView(QMainWindow):

    WINDOW_WIDTH = 1024
    WINDOW_HEIGHT = 900

    def __init__(self, model, controller):
        super().__init__()
        self._model = model
        self._zoom = 1.0
        self._old_mouse_pos = None
        self._controller = controller
        self.initUI()

        self.file_open_menu.triggered.connect(self._controller.on_file_open)
        self.slider.valueChanged[int].connect(self._controller.on_slider_change)
        self.zoom_in_act.triggered.connect(lambda: self.on_zoom_change(1.25))
        self.zoom_out_act.triggered.connect(lambda: self.on_zoom_change(0.8))
        self.zoom_reset_act.triggered.connect(lambda: self.on_zoom_change(0))
        self.fit_act.toggled.connect(self.on_fit_to_window_change)
        self.grid_act.toggled.connect(self._controller.on_grid_change)
        self.img_label.size_change.connect(self._controller.image_label_size_change)
        self.img_label.mousePressEvent = self._controller.on_image_click
        self.img_label.mousePressEvent = self.mouse_press
        self.img_label.mouseMoveEvent = self.mouse_move
        self.keyPressEvent = self._controller.key_press_event
        #self.img_label.resizeEvent =  self._controller.image_label_size_change
        for b in [self.minus_100_button, self.minus_5_button, self.minus_1_button, self.plus_1_button, self.plus_5_button, self.plus_100_button]:
            b.clicked.connect(self._controller.on_number_button_click)
        # index_change
        # controller -> view
        self._model.index_change.connect(self._controller.index_change)
        self._model.index_change.connect(self.on_index_change)
        self._model.image_change.connect(self.on_image_change)
        self._model.color_result_change.connect(self.on_color_result_change)
        # alpha_change
        self._model.alpha_change.connect(self.on_alpha_change)
        self._model.grid_change.connect(lambda: self.img_label.setPixmap(self._controller.update_pixmap()))

    def initUI(self):
        self.img_label = ImageLabel()
        self.img_label.setBackgroundRole(QPalette.Base)
        self.img_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.img_label.setScaledContents(True)

        self.scroll_area = QScrollArea()
        self.scroll_area.setBackgroundRole(QPalette.Light)
        self.scroll_area.setWidget(self.img_label)
        self.scroll_area.setVisible(True)

        self.file_menu = self.menuBar().addMenu('&File')

        self.file_open_menu = self.file_menu.addAction(self.tr('Open'))
        self.file_open_menu.setShortcut(QKeySequence.Open)
        self.file_open_menu.setStatusTip('select directory with data and media')

        self.view_menu = self.menuBar().addMenu(self.tr('&View'))

        self.zoom_in_act = self.view_menu.addAction(self.tr('Zoom &In'))
        self.zoom_in_act.setShortcut(QKeySequence.ZoomIn)

        self.zoom_out_act = self.view_menu.addAction(self.tr('Zoom &Out'))
        self.zoom_out_act.setShortcut(QKeySequence.ZoomOut)

        self.zoom_reset_act = self.view_menu.addAction(self.tr('Zoom &Reset'))
        self.zoom_reset_act.setShortcut(self.tr('Ctrl+N'))

        self.fit_act = self.view_menu.addAction(self.tr('&Fit Window'))
        self.fit_act.setShortcut(self.tr('Ctrl+F'))
        self.fit_act.setCheckable(True)
    
        self.view_menu.addSeparator()

        self.grid_act = self.view_menu.addAction(self.tr('Grid'))
        self.grid_act.setShortcut('Ctrl+G')
        self.grid_act.setCheckable(True)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMaximum(10)

        self.data_button = QPushButton('Data')
        self.media_button = QPushButton('Media')
        self.minus_100_button = QPushButton('-100')
        self.minus_5_button = QPushButton('-5')
        self.minus_1_button = QPushButton('-1')
        self.plus_1_button = QPushButton('+1')
        self.plus_5_button = QPushButton('+5')
        self.plus_100_button = QPushButton('+100')

        self.index_label = QLabel('000/000')

        hbox = QHBoxLayout()
        hbox.addStretch()
        for w in [self.data_button, self.minus_100_button, self.minus_5_button, self.minus_1_button, self.index_label, self.plus_1_button, self.plus_5_button, self.plus_100_button, self.media_button]:
            hbox.addWidget(w)
        hbox.addStretch()
        vbox = QVBoxLayout()
        vbox.addWidget(self.scroll_area)
        #vbox.addStretch()
        vbox.addWidget(self.slider)
        vbox.addLayout(hbox)
        cw = QWidget()
        cw.setLayout(vbox)

        self.setCentralWidget(cw)
        self.statusBar().showMessage('')
        self.setGeometry(0, 0, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

    def on_index_change(self):
        self.index_label.setText('{:03d}/{:03d}'.format(self._model.index + 1, self._model.img_count()))
        self.setWindowFilePath(self._model.media_path)

    def on_image_change(self):
        if self._model.media_pixmap == None:
            self.img_label.setText('{} is not found'.format(self._model.data_path))
        else:
            self.img_label.setPixmap(self._controller.update_pixmap())
            # TODO:フォルダ読み込み時はimg_labelが小さいままでうまく画像が読み込めない為、無理やりzoomを変えた事にしてimg_labelのリサイズを行う
            self.on_zoom_change(1)

    def on_zoom_change(self, scale):
        if scale == 0:
            self._zoom = 1.0
        else:
            self._zoom = self._zoom * scale
        self.img_label.resize(self._zoom * self.img_label.pixmap().size())
        self.adjust_scroll_bar(self.scroll_area.horizontalScrollBar(), scale)
        self.adjust_scroll_bar(self.scroll_area.verticalScrollBar(), scale)
        #self.img_label.adjustSize()

    def on_alpha_change(self):
        self.img_label.setPixmap(self._controller.update_pixmap())

    def on_color_result_change(self, color_result):
        self.statusBar().showMessage(color_result)

    def on_fit_to_window_change(self):
        self.scroll_area.setWidgetResizable(self.fit_act.isChecked())
        if self.fit_act.isChecked() == False:
            self.on_zoom_change(0)
    
    def adjust_scroll_bar(self, bar, scale):
        bar.setValue(int(scale * bar.value() + ((scale - 1) * bar.pageStep() / 2)))

    def mouse_press(self, e):
        self._controller.on_image_click(e)
        self._old_mouse_pos = e.pos()

    def mouse_move(self, e):
        newX = e.pos().x()
        newY = e.pos().y()
        off_x = self._old_mouse_pos.x() - newX
        off_y = self._old_mouse_pos.y() - newY

        if off_x > 3 or off_x < -3:
            self.scroll_area.horizontalScrollBar().setValue(self.scroll_area.horizontalScrollBar().value() + off_x)
            # スクロールバーをずらした分だけマウスポインタの位置もずらす
            newX = newX + off_x
        if off_y > 3 or off_y < -3:
            self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().value() + off_y)
            newY = newY + off_y
        self._old_mouse_pos = QPoint(newX, newY)