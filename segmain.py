import sys

from PyQt5.QtWidgets import QApplication
from controller.segcontroller import SegController
from model.segmodel import SegModel
from view.segview import SegView

class SegApplication(QApplication):

    def __init__(self, argv):
        super(SegApplication, self).__init__(argv)
        self.model = SegModel()
        self.controller = SegController(self.model)
        self.view = SegView(self.model, self.controller)
        self.setApplicationDisplayName(self.tr('Segmentation Check Tool'))
        self.view.show()

if __name__ == '__main__':
    app = SegApplication(sys.argv)
    sys.exit(app.exec_())
