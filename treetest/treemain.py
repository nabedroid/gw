import sys
from treeitem import TreeItem
from treemodel import TreeModel
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)
with open('view/default.txt', 'r', encoding='utf8') as f:
    model = TreeModel(f.read())
view = QTreeView()
view.setModel(model)
view.setWindowTitle("Simple Tree Model")
view.show()
sys.exit(app.exec())
