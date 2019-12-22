import os
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal

class SegModel(QObject):
    index_change = pyqtSignal(int)
    media_dir_change = pyqtSignal(str)
    alpha_change = pyqtSignal(int)
    image_change = pyqtSignal()
    color_result_change = pyqtSignal(str)
    grid_change = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._index = 1
        self._media_dir = 'media'
        self._media_paths = []
        self._media_pixmap = None
        self._data_dir = 'data'
        self._data_pixmap = None
        self._data_image = None
        self._color_result = ''
        self._alpha = 0
        self._grid = False

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, idx):
        if not self.media_paths or idx < 0:
            self._index = 0
        elif len(self.media_paths) <= idx:
            self._index = len(self.media_paths) - 1
        else:
            self._index = idx
        self.index_change.emit(idx)

    @property
    def media_dir(self):
        return self._media_dir

    @media_dir.setter
    def media_dir(self, path):
        self._media_dir = path.replace('/', os.path.sep)
        self.media_dir_change.emit(path)

    @property
    def media_path(self):
        if len(self._media_paths) > self._index:
            return self._media_paths[self._index]
        return ''

    @property
    def media_paths(self):
        return self._media_paths

    @media_paths.setter
    def media_paths(self, paths):
        self._media_paths = paths

    @property
    def media_pixmap(self):
        return self._media_pixmap

    @media_pixmap.setter
    def media_pixmap(self, pixmap):
        self._media_pixmap = pixmap

    @property
    def data_dir(self):
        return self._data_dir

    @data_dir.setter
    def data_dir(self, path):
        self._data_dir = path.replace('/', os.path.sep)

    @property
    def data_path(self):
        if self.media_path != None:
            return os.path.join(os.path.dirname(self.media_path).replace(self._media_dir, self._data_dir), 'PNG', os.path.basename(self.media_path).replace('jpg', 'png'))
        return ''

    @property
    def data_pixmap(self):
        return self._data_pixmap

    @data_pixmap.setter
    def data_pixmap(self, pixmap):
        self._data_pixmap = pixmap
        self.image_change.emit()

    @property
    def data_image(self):
        return self._data_image

    @data_image.setter
    def data_image(self, img):
        self._data_image = img

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, alpha):
        self._alpha = alpha
        self.alpha_change.emit(alpha)
  
    @property
    def color_result(self):
        return self._color_result

    @color_result.setter
    def color_result(self, color_result):
        self._color_result = color_result
        self.color_result_change.emit(color_result)
  
    @property
    def grid(self):
        return self._grid

    @grid.setter
    def grid(self, grid):
        self._grid = grid
        self.grid_change.emit()

    def img_count(self):
        return len(self._media_paths)

    def __str__(self):
        return '\n'.join([
            'index     : ' + str(self._index),
            'media dir : ' + self._media_dir,
            'media path: ' + self.media_path,
            'data  dir : ' + self._data_dir,
            'data path : ' + self.data_path,
            'alpha     : ' + str(self._alpha)
        ])

if __name__ ==  '__main__':
    m = SegModel()
    print(m)
    print(m.media_path)
