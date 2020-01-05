import glob
import json
import os
import platform
import re
import subprocess
import sys

from collections import defaultdict
from enum import Enum
from threading import Timer

from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QRect
from PyQt5.QtCore import QRectF
from PyQt5.QtCore import QSize
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QBrush
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QKeySequence
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtWidgets import QGraphicsSimpleTextItem
from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSlider
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

'''
セグメンテーション支援ツール
カスタマイズされたPythonが外部ファイルをimportさせてくれないので、
無理やり一つのファイルにまとめた。超見辛い。

auther:
    nabedroid <nabedroid@gmail.com>
version:
    1.00
date:
    31 Dec 2019
TODO:
    設定メニューを実装したい
        色->オブジェクト名の追加・削除、透過率変更、グリッド幅の変更
'''

class ConfigFormatError(Exception):
    '''コンフィグエラークラス
    コンフィグファイルの設定値に漏れがある場合に使用
    '''

    def __init__(self, filepath, item):
        '''コンストラクタ
        Args:
            filepath (str): configファイルパス
            item (str): 項目
        '''
        self.message = '{} is not found in {}'.format(item, filepath)

class QColorPickerDialog(QFileDialog):
    '''QFileDialog拡張クラス
    ファイルパスのセパレーターをOSに準拠したセパレーターに変換して返す
    '''
    @classmethod
    def getExistingDirectory(self, parent = None, caption = '', dir = '', options = QFileDialog.ShowDirsOnly):
        dir = super().getExistingDirectory(parent, caption, dir, options)
        return dir.replace('/', os.path.sep)
    @classmethod
    def getOpenFileName(self, parent = None, caption = '', dir = '', filter = '', selectedFilter = None, options = QFileDialog.Options()):
        f = super().getOpenFileName(parent, caption, dir, filter, selectedFilter, options)
        return f[0].replace('/', os.path.sep)

class ColorPickerUtil():
    '''Utilクラス
    クラスに依存しない機能を集めたクラス
    '''

    __singleton = None
    '''シングルトン
    マルチスレッドには非対応
    '''

    def __new__(cls):
        '''__init__の前処理
        一度だけインスタンスを生成する
        '''
        if cls.__singleton == None:
            cls.__singleton = super().__new__(cls)
        return cls.__singleton

    def __init__(self):
        '''コンストラクタ
        不明な色の場合のオブジェクト名を初期化
        '''
        # 不明な色の場合は"?"
        self._color_dic = defaultdict(lambda: '?')
        self._data_re = re.compile(r'\{([0-9])\}')
        self._data_dir = None
        self._media_dir = None
        # OSに応じてビューアー実行コマンドを選択
        pf = platform.system()
        if pf == 'Windows':
            self._os_imageviewer = lambda filepath: subprocess.run(args = [filepath], shell = True)
        elif pf == 'Darwin':
            self._os_imageviewer = lambda filepath: subprocess.run(args = [filepath])
        elif pf == 'Linux':
            self._os_imageviewer = lambda filepath: subprocess.run(args = [filepath])
        else:
            raise Exception('unknwon os')

    def load(self, filepath):
        '''コンフィグ読み込み
        config.json を読み込み各種プロパティを初期化する
        設定値に漏れがある場合はエラーを投げる

        Args:
            filepath (str): コンフィグファイルのパス
        Raises:
            ConfigFormatError: 設定値に漏れがあった場合
        '''
        self._color_dic.clear()
        self._media_dir = None
        self._data_dir = None
        with open(filepath) as f:
            j = json.load(f)
            # colors
            colors = j.get('colors')
            if not colors: raise ConfigFormatError(filepath, 'colors')
            for name in colors:
                self._color_dic[int(colors[name], 16)] = name
            # media_filepath_to_data_filepath
            patterns = j.get('media_filepath_to_data_filepath')
            if not patterns: raise ConfigFormatError(filepath, 'media_filepath_to_data_filepath')
            self._media_re = re.compile(patterns[0])
            self._data_pattern = patterns[1].replace('\\', os.path.sep).replace('/', os.path.sep)
            # media_extension
            self._media_extension = j.get('media_extension')
            if not self._media_extension: raise ConfigFormatError(filepath, 'media_extension')
            # data_extension
            self._data_extension = j.get('data_extension')
            if not self._data_extension: raise ConfigFormatError(filepath, 'data_extension')

    @property
    def color_dic(self):
        return self._color_dic

    @property
    def media_dir(self):
        return self._media_dir

    @media_dir.setter
    def media_dir(self, media_dir):
        self._media_dir = media_dir

    @property
    def data_dir(self):
        return self._data_extension

    @data_dir.setter
    def data_dir(self, data_dir):
        self._data_extension = data_dir

    def get_media_filepaths(self, media_filepath):
        '''mediaファイル一覧取得
        mediaファイルの一覧を取得する

        Args:
            media_filepath (str): mediaファイルの基底パス
        Return:
            list: mediaファイルの一覧
        '''
        return glob.glob(os.path.join(media_filepath, '**', '*' + self._media_extension), recursive = True)

    def media_filepath_to_data_filepath(self, media_filepath):
        '''media filepath -> data filepath
        設定ファイルの置き換え情報を元にmediaファイルパスをdataファイルパスに変換する
        処理にセンスの欠片もない

        Args:
            media_filepath (str): mediaファイルのパス
        Return:
            str: dataファイルのパス
        '''
        data_filepath = self._data_pattern
        media_m = self._media_re.findall(media_filepath)[0]
        i = 0
        while(self._data_re.search(data_filepath)):
            data_filepath = data_filepath.replace('{' + str(i + 1) + '}', media_m[i])
            i = i + 1
        return data_filepath.replace(self._media_dir, self._data_extension)

    def color_to_object_name(self, color):
        '''color -> object name
        色（0xRRGGBB）をオブジェクト名に変換する

        Args:
            color (int): RGB
        Return:
            str: オブジェクト名
        '''
        return self._color_dic[color]
    
    def exe_os_imageviewer(self, filepath):
        '''イメージビューアー起動
        OSに準拠したイメージビューアーを起動する

        Args:
            filepath (str): 画像ファイルのパス

        TODO:
            OS任せで拡張子に関連付けられたアプリケーションを起動しているだけなので、設定によってはビューアーが開かない可能性あり
            MACで未検証
        '''
        # 空のファイルパスの場合は何もしない
        if not filepath: return 0
        return self._os_imageviewer(filepath)

class QPixmapItem(QGraphicsPixmapItem):
    '''QGaphicsPixmapItem拡張クラス
    読み込んだ画像のファイルパスを保持し（なお使用していない模様）、指定ピクセルの色データをRGBで取得する
    '''
    def __init__(self, filepath = ''):
        super().__init__()
        self.filepath = filepath
        self._image = None

    @property
    def filepath(self):
        return self._filepath

    @filepath.setter
    def filepath(self, filepath):
        '''filepath setter
        ファイルパスの設定と同時にpixmapも設定する

        Args:
            filepath (str): media/dataファイルパス
        '''
        self._filepath = filepath
        pixmap = QPixmap(filepath)
        if pixmap:
            self.setPixmap(pixmap)
            self._image = pixmap.toImage()
        else:
            self.setPixmap(None)
            self._image = None

    def pixel(self, pos):
        '''ピクセルの色取得
        引数のQPointで指定されたピクセルの色（0xRRGGBB）を取得する

        Args:
            pos (QPoint): ピクセルの位置
        Return:
            int: RGB
        '''
        # 0xAARRGGBBからAlphaを取り除く
        return self._image.pixel(pos) & 0x00FFFFFF
    
    @property
    def image(self):
        return self._image

class QPopupItem(QGraphicsSimpleTextItem):
    '''ポップアップアイテムクラス
    クリックした位置に n 秒間テキストを表示する
    QGraphicsTextItemを継承すると謎のmouseMoveEventが発生するので諦めた
    '''
    def __init__(self, text = ''):
        super().__init__(text)
        # Viewのscaleを無視して描画
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self._background_brush = Qt.black
        self._timer = None

    def paint(self, painter, option, widget):
        painter.fillRect(self.boundingRect(), self._background_brush)
        super().paint(painter, option, widget)

    def popup(self, text, pos, sec = 1.0):
        '''ポップアップの表示
        text を pos の位置に sec 秒間表示する

        Args:
            text (str): テキスト
            pos (QPoint): 表示する位置
            sec (:obj:`float`, optional): 表示する時間（デフォルトは1秒）
        '''
        # タイマーが開始していたらキャンセルして破棄
        if self._timer: self._timer.cancel()
        self.setText(text)
        self.setPos(pos)
        self.setVisible(True)
        # sec秒後に非表示とするタイマー開始
        self._timer = Timer(sec, lambda: self.setVisible(False))
        self._timer.start()

    def setTextBrush(self, brush):
        self.setBrush(brush)

    def setBackgroundBrush(self, brush):
        self._background_brush = brush

class QGridItem(QGraphicsItem):
    '''グリッドクラス
    グリッド線を表示するクラス
    '''

    def __init__(self, width = 100, height = 100, grid_color = Qt.gray, grid_gap = 20, grid_vertical_visible = False, grid_horizontal_visible = False, parent = None):
        '''コンストラクタ
        各種プロパティを初期化する

        Args:
            width (:obj:`int`, optional): 横幅
            height (:obj:`int`, optional): 縦幅
            grid_color (:obj:`QColor`, optional): グリッド線の色
            grid_gap (:obj:`int`, optional): グリッド線の間隔
            grid_vertical_visible (:obj:`bool`, optional): 縦線の表示有無
            grid_horizontal_visible (:obj:`bool`, optional): 横線の表示有無
            parent (QWidget): 親Widget？
        '''
        super().__init__(parent)
        self._width = width
        self._height = height
        self.grid_vertical_visible = grid_vertical_visible
        self.grid_horizontal_visible = grid_horizontal_visible
        self.grid_color = grid_color
        self.grid_gap = grid_gap

    def boundingRect(self):
        '''矩形の取得
        短径の位置とサイズを取得する

        Return:
            QRectF: 0, 0, 横幅, 縦幅
        '''
        #pen_width = 1
        #return QRectF(-width / 2 - pen_width / 2, -height / 2 - pen_width / 2, width + pen_width, height + pen_width)
        return QRectF(0, 0, self._width, self._height)

    @property
    def width(self):
        return self._width
    
    @width.setter
    def width(self, width):
        self._width = width
    
    @property
    def height(self):
        return self._height
    
    @height.setter
    def height(self, height):
        self._height = height

    @property
    def grid_color(self):
        return self._grid_color

    @grid_color.setter
    def grid_color(self, color):
        self._grid_color = color

    @property
    def grid_gap(self):
        return self._grid_gap
    
    @grid_gap.setter
    def grid_gap(self, grid_gap):
        self._grid_gap = grid_gap

    @property
    def grid_vertical_visible(self):
        return self._grid_vertical_visible
    
    @grid_vertical_visible.setter
    def grid_vertical_visible(self, visible):
        self._grid_vertical_visible = visible

    @property
    def grid_horizontal_visible(self):
        return self._grid_horizontal_visible
    
    @grid_horizontal_visible.setter
    def grid_horizontal_visible(self, visible):
        self._grid_horizontal_visible = visible

    def paint(self, painter, option, widget):
        '''描画
        グリッド線を描画する

        Args:
            painter (QPaint): ペイント
            option (QOption): オプション
            widget (QWidget): Widget
        '''
        gap = self.grid_gap
        painter.setPen(self.grid_color)
        if self.grid_horizontal_visible:
            for h in range(gap, self._height, gap):
                painter.drawLine(0, h, self._width, h)
        if self.grid_vertical_visible:
            for w in range(gap, self._width, gap):
                painter.drawLine(w, 0, w, self._height)

class QColorPickerScene(QGraphicsScene):
    '''QGraphicsScene拡張クラス
    画像部分を表示するSceneクラス
    '''
    def __init__(self):
        '''コンストラクタ
        UIとUtilの初期化を行う
        '''
        super().__init__()
        self._util = ColorPickerUtil()
        self.init_ui()
    
    def init_ui(self):
        '''UI初期化
        data/media画像アイテム、グリッドアイテム、ポップアップアイテムの初期化を行う
        '''
        self._data_pixmap_item = QPixmapItem()
        self._data_pixmap_item.mousePressEvent = self.data_pixmap_click

        self._media_pixmap_item = QPixmapItem()
        self._media_pixmap_item.setOpacity(0)
        self._media_pixmap_item.setParentItem(self._data_pixmap_item)

        self._grid_item = QGridItem(grid_gap = 50, grid_horizontal_visible = True)
        self._grid_item.setParentItem(self._data_pixmap_item)
        self._grid_item.setVisible(False)

        self._popup_item = QPopupItem()
        self._popup_item.setParentItem(self._data_pixmap_item)
        self._popup_item.setBackgroundBrush(Qt.white)
        self._popup_item.setFont(QFont('ＭＳ ゴシック', 18, QFont.Bold))

        self.addItem(self._data_pixmap_item)
    
    def data_pixmap_click(self, event):
        '''画像クリックイベント
        画像が読み込まれている場合はクリック位置の少し右にポップアップを表示する
        '''
        if not self._data_pixmap_item.pixmap(): return

        color = self._data_pixmap_item.pixel(event.pos().toPoint())
        self._popup_item.popup(self._util.color_to_object_name(color), QPoint(event.pos().x() + 15, event.pos().y()), 1.0)

    @property
    def data_filepath(self):
        return self._data_pixmap_item.filepath
    
    @data_filepath.setter
    def data_filepath(self, filepath):
        '''data_filepath setter
        data画像ファイルを設定する
        更に画像ファイルのサイズを元にグリッドのサイズ変更も行う
        '''
        self._data_pixmap_item.filepath = filepath
        if self._data_pixmap_item.pixmap():
            self._grid_item.width = self._data_pixmap_item.pixmap().width()
            self._grid_item.height = self._data_pixmap_item.pixmap().height()

    @property
    def media_filepath(self):
        return self._media_pixmap_item.filepath
    
    @media_filepath.setter
    def media_filepath(self, filepath):
        self._media_pixmap_item.filepath = filepath

    @property
    def media_opacity(self):
        return self._media_pixmap_item.opacity()
    
    @media_opacity.setter
    def media_opacity(self, opacity):
        self._media_pixmap_item.setOpacity(opacity)
    
    def setGridVisible(self, visible):
        self._grid_item.setVisible(visible)
    
    def hasImage(self):
        return (not self._data_pixmap_item.pixmap().isNull()) and (not self._media_pixmap_item.pixmap().isNull())

class GView(QGraphicsView):
    '''QGraphicsView拡張クラス
    QQColorPickerSceneを表示するViewクラス
    マウスホイールのズームアウトやドラッグ時のスクロール機能を持つ
    '''

    def __init__(self):
        super().__init__()
        # 移動前のマウス位置
        self._old_mouse_point = None
        # window fit フラグ
        self._fitting = False

        scene = QColorPickerScene()
        self.setScene(scene)
    
        scene.setBackgroundBrush(Qt.lightGray)

    def mousePressEvent(self, event):
        '''クリックイベント
        移動前のマウス位置を設定し、イベントを後続に渡す

        Args:
            event (QMouseEvent): マウスイベント
        '''
        self._old_mouse_point = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        '''ドラッグイベント
        マウスの移動距離に応じてスクロールさせる

        Args:
            event (QMouseEvent): マウスイベント
        '''
        off_x = self._old_mouse_point.x() - event.pos().x()
        off_y = self._old_mouse_point.y() - event.pos().y()
        off_x = off_x if abs(off_x) > 2 else 0
        off_y = off_y if abs(off_y) > 2 else 0
        
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + off_x)
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() + off_y)

        self._old_mouse_point = QPoint(event.pos().x(), event.pos().y())

    def wheelEvent(self, event):
        '''ホイールイベント
        ホイールの動きに応じてズームイン、ズームアウトを行う
        '''
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        '''ズームイン
        1.25倍にする

        TODO:
            マウス位置を中心にズームさせたい
        '''
        if not self._fitting: self.scale(1.25, 1.25)
    
    def zoom_out(self):
        '''ズームアウト
        0.8倍にする

        TODO:
            マウス位置を中心にズームアウトさせたい
        '''
        if not self._fitting: self.scale(0.8, 0.8)
    
    def zoom_reset(self):
        '''ズームリセット
        fit中でなければズームのリセットを行う
        '''
        if not self._fitting: self.resetTransform()

    def fit_on(self):
        '''Fit on
        Window FitをONにする
        TODO:
            拡大してからFITさせると微妙な余白が生まれる
        '''
        self._fitting = True
        self.hasImage()
        self.fitInView(self.scene().sceneRect(), Qt.KeepAspectRatio)
        
        #self.fitInView(QRectF(self.contentsRect()), Qt.KeepAspectRatio)

    def fit_off(self):
        '''Fit off
        Window FitをOFFにする
        '''
        self._fitting = False
        self.resetTransform()
    
    def grid_on(self):
        '''Grid on
        グリッドを表示する
        '''
        self.scene().setGridVisible(True)
    
    def grid_off(self):
        '''Grid off
        グリッドを非表示にする
        '''
        self.scene().setGridVisible(False)

    def hasImage(self):
        return self.scene().hasImage()

class QIndexLabel(QLabel):
    '''インデックスラベル
    現在のインデックス／全体の形式でラベルを表示する
    '''
    def __init__(self, parent = None):
        super().__init__(parent)
        self._index = 0
        self._max_index = 0

    @property
    def index(self):
        return self._index
    
    @index.setter
    def index(self, index):
        self._index = index
        self.setText('{:03d}/{:03d}'.format(self._index, self._max_index))
    
    @property
    def max_index(self):
        return self._max_index
    
    @max_index.setter
    def max_index(self, max_index):
        self._max_index = max_index
        self.setText('{:03d}/{:03d}'.format(self._index, self._max_index))

class MainWindow(QMainWindow):
    '''メインウィンドウクラス
    メニュー、メニューバー、ボタン、スライダーを持つ
    '''
    def __init__(self, parent = None):
        '''コンストラクタ
        主にイベントの関連付けを行う

        Args:
            parent (QWidget): 親ウィジェット
        '''
        super().__init__()
        self._project_open_dialog = QProjectOpenDialog(parent = self)
        self._key_config_dialog = QKeyConfigDialog(parent = self)
        self._keyconfig = ColorPickerKeyConfig()
        self._util = ColorPickerUtil()
        self._media_filepaths = None

        # ui初期化
        self.init_ui()
        # event初期化
        # menu
        self._open_act.triggered.connect(self.on_file_open)
        self._quit_act.triggered.connect(self.close)
        self._zoom_in_act.triggered.connect(self._gview.zoom_in)
        self._zoom_out_act.triggered.connect(self._gview.zoom_out)
        self._zoom_reset_act.triggered.connect(self._gview.zoom_reset)
        self._fit_act.toggled.connect(lambda checked: self._gview.fit_on() if checked else self._gview.fit_off())
        self._grid_act.toggled.connect(lambda checked: self._gview.grid_on() if checked else self._gview.grid_off())
        self._key_config_act.triggered.connect(self.on_key_config)
        # button
        for b in self._index_buttons:
            b.clicked.connect(self.on_index_button_click)
        self._media_button.clicked.connect(self.on_media_button_click)
        self._data_button.clicked.connect(self.on_data_button_click)
        # slider
        self._slider.valueChanged[int].connect(self.on_slider_change)

    def init_ui(self):
        '''UIの初期化
        メニュー、メニューバー、ボタン、スライダーにおけるUI関連の初期化を行う
        '''
        # file menu
        self._file_menu = self.menuBar().addMenu('&File')
        self._open_act = self._file_menu.addAction(self.tr('Project &Open'))
        self._open_act.setShortcut(QKeySequence.Open)
        self._open_act.setStatusTip('select directory with data, media and config.json')
        self._file_menu.addSeparator()
        self._quit_act = self._file_menu.addAction(self.tr('&Quit'))
        self._quit_act.setShortcut(QKeySequence.Quit)
        # view menu
        self._view_menu = self.menuBar().addMenu(self.tr('&View'))
        self._zoom_in_act = self._view_menu.addAction(self.tr('Zoom &In'))
        #self._zoom_in_act.setShortcut(QKeySequence.ZoomIn)
        self._zoom_in_act.setShortcut(self._keyconfig.zoom_in)
        self._zoom_in_act.setEnabled(False)
        self._zoom_out_act = self._view_menu.addAction(self.tr('Zoom &Out'))
        self._zoom_out_act.setShortcut(self._keyconfig.zoom_out)
        self._zoom_out_act.setEnabled(False)
        self._zoom_reset_act = self._view_menu.addAction(self.tr('Zoom &Reset'))
        self._zoom_reset_act.setShortcut(self._keyconfig.zoom_reset)
        self._zoom_reset_act.setEnabled(False)
        self._fit_act = self._view_menu.addAction(self.tr('&Fit Window'))
        self._fit_act.setShortcut(self._keyconfig.fit)
        self._fit_act.setCheckable(True)
        self._fit_act.setEnabled(False)
        self._view_menu.addSeparator()
        self._grid_act = self._view_menu.addAction(self.tr('Grid'))
        self._grid_act.setShortcut(self._keyconfig.grid)
        self._grid_act.setCheckable(True)
        self._grid_act.setEnabled(False)
        # setting menu
        self._setting_menu = self.menuBar().addMenu(self.tr('&Setting'))
        self._key_config_act = self._setting_menu.addAction(self.tr('&Key Config'))
        # slider
        self._slider = QSlider(Qt.Vertical)
        self._slider.setMaximum(10)
        # index label
        self._index_label = QIndexLabel()
        self._index_label.setAlignment(Qt.AlignCenter)
        # button
        self._index_buttons = [QPushButton("{:+d}".format(num)) for num in [-100, -5, -1, 1, 5, 100]]
        self._media_button = QPushButton('media')
        self._data_button = QPushButton('data')
        # image view
        self._gview = GView()
        # layout
        lower = QHBoxLayout()
        lower.addWidget(self._media_button)
        lower.addWidget(self._index_buttons[0])
        lower.addWidget(self._index_buttons[1])
        lower.addWidget(self._index_buttons[2])
        lower.addWidget(self._index_label)
        lower.addWidget(self._index_buttons[3])
        lower.addWidget(self._index_buttons[4])
        lower.addWidget(self._index_buttons[5])
        lower.addWidget(self._data_button)
        upper = QHBoxLayout()
        upper.addWidget(self._gview)
        upper.addWidget(self._slider)
        layout = QVBoxLayout()
        layout.addLayout(upper)
        layout.addLayout(lower)
        w = QWidget()
        w.setLayout(layout)
    
        self.setCentralWidget(w)
        self.statusBar().showMessage('')

    def keyPressEvent(self, event):
        '''キー押下イベント
        インデックスを1戻す
        インデックスを1進める
        透過率を最大/最小に切り替える
        '''
        key = self._keyconfig.keyevent_to_keysquence(event).toString()
        if key == self._keyconfig.next:
            self._index_buttons[3].clicked.emit()
        elif key == self._keyconfig.prev:
            self._index_buttons[2].clicked.emit()
        elif key == self._keyconfig.opacity:
            if self._slider.value() < 10:
                self._slider.setValue(10)
            else:
                self._slider.setValue(0)

    def on_index_button_click(self):
        '''インデックスボタンクリック
        インデックスの増減を行う
        最大（最小）を逸脱する場合は最大（最小）に補正して設定する
        '''
        if not self._media_filepaths: return
        index = self._index_label.index
        button = int(self.sender().text())
        new_index = index + button

        if new_index >= len(self._media_filepaths):
            new_index = len(self._media_filepaths)
        elif new_index <= 0:
            new_index = 1
        # media/data画像の更新
        scene = self._gview.scene()
        scene.media_filepath = self._media_filepaths[new_index - 1]
        scene.data_filepath = self._util.media_filepath_to_data_filepath(self._media_filepaths[new_index - 1])
        # インデックスラベルの更新
        self._index_label.index = new_index
        # ウィンドウファイルパスの更新
        self.setWindowFilePath(self._media_filepaths[new_index - 1])
        # viewメニューの活性状態更新
        self._update_view_act()

    def on_media_button_click(self):
        '''mediaボタン押下
        外部のビューアーでmedia画像を表示する
        '''
        self._util.exe_os_imageviewer(self._gview.scene().media_filepath)
    
    def on_data_button_click(self):
        '''dataボタン押下
        外部のビューアーでdata画像を表示する
        '''
        self._util.exe_os_imageviewer(self._gview.scene().data_filepath)

    def on_file_open(self):
        '''project open
        プロジェクト選択ダイアログを表示し、
        '''
        # プロジェクトオープンダイアログを開く
        result = self._project_open_dialog.exec()
        # cancel もしくは不正な入力だった場合何もしない
        if result == QDialog.Rejected: return
        # ファイルを読み込む
        self._util.load(self._project_open_dialog.config())
        self._util.media_dir = self._project_open_dialog.media()
        self._util.data_dir = self._project_open_dialog.data()
        self._media_filepaths = self._util.get_media_filepaths(self._project_open_dialog.media())
        # インデックスを0に戻してから+1ボタンシグナルを発火
        self._index_label.index = 0
        self._index_label.max_index = len(self._media_filepaths)
        self._index_buttons[3].clicked.emit()

    def on_slider_change(self, value):
        '''スライダーチェンジ
        スライダーの増減に応じて透過率を設定する

        Args:
            value (QSliderEvent): スライダーイベント
        '''
        self._gview.scene().media_opacity = value / 10
    
    def on_key_config(self):
        print(self._key_config_dialog.result())
        self._key_config_dialog.exec()
        print(self._key_config_dialog.result())
        if self._key_config_dialog.result() == QDialog.Accepted:
            print(self._keyconfig.zoom_reset)
            self._zoom_in_act.setShortcut(self._keyconfig.zoom_reset)
            self._zoom_out_act.setShortcut(self._keyconfig.zoom_out)
            self._zoom_reset_act.setShortcut(self._keyconfig.zoom_reset)
            self._fit_act.setShortcut(self._keyconfig.fit)
            self._grid_act.setShortcut(self._keyconfig.grid)
        print('end')
    
    def _update_view_act(self):
        '''Viewメニューの活性状態を更新する
        sceneの画像有無に応じてメニューの活性化、非活性を切り替える
        '''
        enable = self._gview.hasImage()
        self._zoom_in_act.setEnabled(enable)
        self._zoom_out_act.setEnabled(enable)
        self._zoom_reset_act.setEnabled(enable)
        self._fit_act.setEnabled(enable)
        self._grid_act.setEnabled(enable)

class QProjectOpenDialog(QDialog):
    '''プロジェクトオープンダイアログ
    media画像、data画像の基底ディレクトリと設定ファイルを選択するダイアログ
    '''
    def __init__(self, parent = None, f = Qt.WindowFlags()):
        '''コンストラクタ
        主にイベント処理の関連付けを行う

        Args:
            parent (QWidget): 親Widget
            f (Qt.WindowFlag): フラグ一覧
        '''
        super().__init__(parent, f)
        self.init_ui()

        self._media_button.pressed.connect(self.on_browse_button_click)
        self._data_button.pressed.connect(self.on_browse_button_click)
        self._config_button.pressed.connect(self.on_browse_button_click)
        self._ok_button.pressed.connect(self.on_ok_cancel_button_click)
        self._cancel_button.pressed.connect(self.on_ok_cancel_button_click)

    def init_ui(self):
        '''UI初期化
        各種パーツの初期化と配置を行う
        '''
        self._media_label = QLabel('Media')
        self._media_edit = QLineEdit()
        self._media_button = QPushButton('Browse')

        self._data_label = QLabel('Data')
        self._data_edit = QLineEdit()
        self._data_button = QPushButton('Browse')

        self._config_label = QLabel('Config')
        self._config_edit = QLineEdit()
        self._config_button = QPushButton('Browse')

        self._ok_button = QPushButton('OK')
        self._ok_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._cancel_button = QPushButton('Cancel')
        self._cancel_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        grid = QGridLayout()
        grid.addWidget(self._media_label, 0, 0)
        grid.addWidget(self._media_edit, 0, 1)
        grid.addWidget(self._media_button, 0, 2)
        grid.addWidget(self._data_label, 1, 0)
        grid.addWidget(self._data_edit, 1, 1)
        grid.addWidget(self._data_button, 1, 2)
        grid.addWidget(self._config_label, 2, 0)
        grid.addWidget(self._config_edit, 2, 1)
        grid.addWidget(self._config_button, 2, 2)
        hbox = QHBoxLayout()
        hbox.addWidget(self._ok_button)
        hbox.addWidget(self._cancel_button)
        layout = QVBoxLayout()
        layout.addLayout(grid)
        layout.addSpacing(10)
        layout.addLayout(hbox)
        self.setLayout(layout)
        self.setFixedWidth(500)
        self.setWindowTitle('Project Open')

    def on_browse_button_click(self):
        '''browseボタン押下
        ディレクトリ（ファイル）選択ダイアログを表示する
        '''
        sender = self.sender()
        if sender == self._media_button:
            self._media_edit.setText(QColorPickerDialog.getExistingDirectory(parent = self, caption = 'select media base directory'))
        elif sender == self._data_button:
            self._data_edit.setText(QColorPickerDialog.getExistingDirectory(parent = self, caption = 'select data base directory'))
        else:
            self._config_edit.setText(QColorPickerDialog.getOpenFileName(parent = self, caption = 'select config json file', filter = 'config (*.json)'))

    def on_ok_cancel_button_click(self):
        '''ok(cancel)ボタン押下
        OKボタンかつ各種データが妥当な場合はresultにQDialog.Acceptを設定し非表示にする
        '''
        if self.sender() == self._ok_button and os.path.isdir(self.media()) and os.path.isdir(self.data()) and os.path.isfile(self.config()):
            self.setResult(QDialog.Accepted)
        else:
            self.setResult(QDialog.Rejected)
        self.hide()

    def media(self):
        '''mediaディレクトリパス

        Return:
            str: mediaディレクトリのパス
        '''
        return self._media_edit.text()
    
    def data(self):
        '''dataディレクトリパス

        Return:
            str: dataディレクトリのパス
        '''
        return self._data_edit.text()

    def config(self):
        '''configファイルパス

        Return:
            str: configファイルのパス
        '''
        return self._config_edit.text()    

class QKeyConfigDialog(QDialog):
    '''キーコンフィグダイアログ
    キーコンフィグの設定ダイアログ
    '''
    def __init__(self, parent = None, f = Qt.WindowFlags()):
        '''コンストラクタ
        主にイベント処理の関連付けを行う

        Args:
            parent (QWidget): 親Widget
            f (Qt.WindowFlag): フラグ一覧
        '''
        super().__init__(parent, f)
        self._keyconfig = ColorPickerKeyConfig()
        self._close_index = 0
        self.init_ui()
        for child in self.children():
            if type(child) == QLineEdit and child != self._edit_name: child.keyPressEvent = self.on_key_press
        self._combo_config.currentIndexChanged.connect(self.update_lineedit)
        self._ok_button.pressed.connect(self.on_ok_button_click)
        self._cancel_button.pressed.connect(self.on_cancel_button_click)

    def showEvent(self, event):
        '''表示イベント
        再表示された際に、コンフィグコンボボックスのインデックス位置を前回選択された位置に設定する

        Args:
            event (QShowEvent) : QShowEvent
        '''
        self._combo_config.setCurrentIndex(self._close_index)
        super().showEvent(event)

    def init_ui(self):
        '''UIの初期化
        UIの初期化を行う
        '''
        self._edit_name = QLineEdit()
        self._edit_next = QLineEdit()
        self._edit_prev = QLineEdit()
        self._edit_opacity = QLineEdit()
        self._edit_fit = QLineEdit()
        self._edit_zoom_in = QLineEdit()
        self._edit_zoom_out = QLineEdit()
        self._edit_zoom_reset = QLineEdit()
        self._edit_grid = QLineEdit()

        self._combo_config = QComboBox()
        for i in range(0, self._keyconfig.count()):
            self._keyconfig.index = i
            self._combo_config.addItem(self._keyconfig.name)
        self.update_lineedit()

        self._ok_button = QPushButton('OK')
        self._cancel_button = QPushButton('Cancel')

        grid = QGridLayout()
        def grid_add(title, edit_line):
            r = grid.rowCount()
            grid.addWidget(QLabel(title), r, 0)
            grid.addWidget(edit_line, r, 1)
        grid_add('名前', self._edit_name)
        grid_add('進む', self._edit_next)
        grid_add('戻る', self._edit_prev)
        grid_add('透過切り替え', self._edit_opacity)
        grid_add('画面フィット', self._edit_fit)
        grid_add('拡大', self._edit_zoom_in)
        grid_add('縮小', self._edit_zoom_out)
        grid_add('リセット', self._edit_zoom_reset)
        grid_add('グリッド', self._edit_grid)

        hbox = QHBoxLayout()
        hbox.addWidget(self._ok_button)
        hbox.addWidget(self._cancel_button)
        layout = QVBoxLayout()
        layout.addWidget(self._combo_config)
        layout.addLayout(grid)
        layout.addSpacing(10)
        layout.addLayout(hbox)
        self.setLayout(layout)

    def update_lineedit(self):
        '''lineeditの更新
        選択されているコンフィグのインデックスを元に各LineEditを更新する
        '''
        self._keyconfig.index = self._combo_config.currentIndex()

        self._edit_name.setText(self._keyconfig.name)
        self._edit_next.setText(self._keyconfig.next)
        self._edit_prev.setText(self._keyconfig.prev)
        self._edit_opacity.setText(self._keyconfig.opacity)
        self._edit_fit.setText(self._keyconfig.fit)
        self._edit_zoom_in.setText(self._keyconfig.zoom_in)
        self._edit_zoom_out.setText(self._keyconfig.zoom_out)
        self._edit_zoom_reset.setText(self._keyconfig.zoom_reset)
        self._edit_grid.setText(self._keyconfig.grid)

    def on_key_press(self, event):
        '''キー押下イベント
        LineEditに「押下されたキーの名前」を設定する

        Args:
            event (QKeyEvent): QKeyEvent
        '''
        if type(self.focusWidget()) == QLineEdit:
            # QKeyEventをQKeySequenceに変換してキーの文字列を設定
            self.focusWidget().setText(self._keyconfig.keyevent_to_keysquence(event).toString())

    def on_ok_button_click(self):
        '''okボタン押下
        OKボタンかつデフォルト設定以外が選択されている場合は設定を保存する
        '''
        self._close_index = self._combo_config.currentIndex()
        if 0 < self._close_index:
            self._keyconfig.name = self._edit_name.text()
            self._keyconfig.next = self._edit_next.text()
            self._keyconfig.prev = self._edit_prev.text()
            self._keyconfig.opacity = self._edit_opacity.text()
            self._keyconfig.fit = self._edit_fit.text()
            self._keyconfig.zoom_in = self._edit_zoom_in.text()
            self._keyconfig.zoom_out = self._edit_zoom_out.text()
            self._keyconfig.zoom_reset = self._edit_zoom_reset.text()
            self._keyconfig.grid = self._edit_grid.text()
            self._keyconfig.save()
        self.setResult(QDialog.Accepted)
        self.hide()

    def on_cancel_button_click(self):
        '''cancelボタン押下
        ダイアログを非表示にする
        '''
        self.setResult(QDialog.Rejected)
        self.hide()

class ColorPickerKeyConfig():
    '''キーコンフィグクラス
    キーコンフィグを管理するクラス
    実行ファイル直下に存在する key_config.json を読み込み初期化する
    '''
    __FILENAME = 'key_config.json'
    __singleton = None
    '''シングルトン
    マルチスレッドには非対応
    '''

    def __new__(cls):
        '''__init__の前処理
        一度だけインスタンスを生成する
        '''
        if cls.__singleton == None:
            cls.__singleton = super().__new__(cls)
        return cls.__singleton

    def __init__(self):
        '''コンストラクタ
        '''
        self._key_dic = {}
        '''設定ファイル
        読み込んだjsonをそのまま保持
        '''
        self._index = "0"
        '''設定インデックス
        設定1～6のインデックス（0はデフォルト設定）
        '''

        with open(self.__FILENAME, encoding = 'utf8') as f:
            self._key_dic = json.load(f)
            #for index in range(0, len(j)):
            #    self._key_dic[str(index)] = {e : j[str(index)][e.value] for e in ColorPickerKey}

    @property
    def index(self):
        return int(self._index)

    @index.setter
    def index(self, index):
        if index <= self.count():
            self._index = str(index)

    @property
    def next(self):
        return self._key_dic[self._index]['next']
    
    @next.setter
    def next(self, key):
        self._key_dic[self._index]['next'] = key
    
    @property
    def prev(self):
        return self._key_dic[self._index]['prev']
    
    @prev.setter
    def prev(self, key):
        self._key_dic[self._index]['prev'] = key
    
    @property
    def opacity(self):
        return self._key_dic[self._index]['opacity']
    
    @opacity.setter
    def opacity(self, key):
        self._key_dic[self._index]['opacity'] = key

    @property
    def zoom_in(self):
        return self._key_dic[self._index]['zoom_in']
    
    @zoom_in.setter
    def zoom_in(self, key):
        self._key_dic[self._index]['zoom_in'] = key
    
    @property
    def zoom_out(self):
        return self._key_dic[self._index]['zoom_out']
    
    @zoom_out.setter
    def zoom_out(self, key):
        self._key_dic[self._index]['zoom_out'] = key
    
    @property
    def zoom_reset(self):
        return self._key_dic[self._index]['zoom_reset']
    
    @zoom_reset.setter
    def zoom_reset(self, key):
        self._key_dic[self._index]['zoom_reset'] = key
    
    @property
    def fit(self):
        return self._key_dic[self._index]['fit']
    
    @fit.setter
    def fit(self, key):
        self._key_dic[self._index]['fit'] = key
    
    @property
    def grid(self):
        return self._key_dic[self._index]['grid']
    
    @grid.setter
    def grid(self, key):
        self._key_dic[self._index]['grid'] = key
    
    @property
    def name(self):
        return self._key_dic[self._index]['name']
    
    @name.setter
    def name(self, key):
        self._key_dic[self._index]['name'] = key

    def count(self):
        '''コンフィグ設定数取得
        コンフィグの設定上限数を取得する
        '''
        return len(self._key_dic)

    def save(self):
        '''設定保存
        現在の情報を上書き保存する
        '''
        with open(self.__FILENAME, 'w', encoding = 'utf8') as f:
            json.dump(self._key_dic, f, ensure_ascii = False, indent = 4, sort_keys = True)

    def keyevent_to_keysquence(self, event):
        '''QKeyEvent->文字列変換
        QKeyEventをQKeySequenceに変換する

        Args:
            event (QKeyEvent): QKeyEvent
        Return:
            str: キー文字列
        '''
        modifier = ''
        if (event.modifiers() & Qt.ShiftModifier):
            modifier += "Shift+"
        if (event.modifiers() & Qt.ControlModifier):
        	modifier += "Ctrl+"
        if (event.modifiers() & Qt.AltModifier):
        	modifier += "Alt+"
        if (event.modifiers() & Qt.MetaModifier):
        	modifier += "Meta+"
        key = QKeySequence(event.key()).toString()
        return QKeySequence(modifier + key)

if __name__ == '__main__':
    '''メイン処理
    スクリーンサイズに応じてウィンドウサイズを設定し
    メインウィンドウを表示する
    '''
    app = QApplication(sys.argv)
    app.setApplicationDisplayName('Color Picker')
    # window size calc
    s_size = app.desktop().availableGeometry().size()
    w_size = QSize(int(s_size.width() * 9 / 10), int(s_size.height() * 9 / 10))
    w_pos = QPoint(int((s_size.width() - w_size.width()) / 2), int((s_size.height() - w_size.height()) / 2))
    main = MainWindow()
    main.setGeometry(QRect(w_pos, w_size))
    main.show()
    sys.exit(app.exec())