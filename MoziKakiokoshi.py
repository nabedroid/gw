
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt
from glob import glob
import sys
import os
import random

class Example(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.basePath = ''
        self.__path = ''

    def initUI(self):
        #super().__init__(parent)
       
        tree_widget = QTreeWidget()
        self.tree_widget = tree_widget
        tree_widget.setAlternatingRowColors(True)
        
        def addItem(branch, name, cnt):
            item = QTreeWidgetItem(branch)
            item.setText(0, name)
            item.setText(1, str(cnt[0]))
            item.setText(2, str(cnt[1]))
        
        #jsonファイル取得
        self.basePath = "result" + os.sep
        filePaths = glob(self.basePath + "**" + os.sep + "*.json")
        print(self.basePath, filePaths)
        branch = None
        for fp in filePaths:
            dirname = os.path.dirname(fp).replace(self.basePath, "")
            branch = tree_widget.findItems(dirname, Qt.MatchExactly)
            if len(branch) == 0:
                branch = QTreeWidgetItem()
                tree_widget.addTopLevelItem(branch)
                branch.setText(0, dirname)
                branch.setExpanded(True)
            else:
                branch = branch[0]
            cnt = [random.randint(0, 100), random.randint(0, 100)]
            addItem(branch, os.path.basename(fp), cnt)
        cnt = [0, 0]
        for i in range(tree_widget.topLevelItemCount()):
            c = [0, 0]
            branch = tree_widget.topLevelItem(i)
            for j in range(branch.childCount()):
                item = branch.child(j)
                c[0] = c[0] + int(item.text(1))
                c[1] = c[1] + int(item.text(2))
            addItem(branch, "subtotal", c)
            cnt[0] = cnt[0] + c[0]
            cnt[1] = cnt[1] + c[1]
        addItem(tree_widget, "total", cnt)

        tree_widget.setColumnCount(3)
        tree_widget.setHeaderLabels(["File", "count", "without space"])
       
        button = QPushButton("Check")
        button.clicked.connect(self.buttonClicked)
       
        layout = QVBoxLayout()
        layout.addWidget(tree_widget)
        layout.addWidget(button)
       
        self.setLayout(layout)
       
        self.setWindowTitle("tree")
        self.show()

    def buttonClicked(self):
        for i in range(self.tree_widget.topLevelItemCount()):
            branch = self.tree_widget.topLevelItem(i)
            print(branch.text(0))
            for j in range(branch.childCount()):
                item = branch.child(j)
                print("  ", end="")
                for k in range(item.columnCount()):
                    print(item.text(k), end=" ")
                print()
        print("find: lemon")
        items = self.tree_widget.findItems("lemon", Qt.MatchRecursive)
        item = items[0]
        print("  ", end="")
        for k in range(item.columnCount()):
            print(item.text(k), end=" ")
        print()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
