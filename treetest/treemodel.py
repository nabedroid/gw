from treeitem import TreeItem
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QVariant
from PyQt5.QtCore import QModelIndex
from PyQt5.QtCore import QAbstractItemModel
import sys
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QApplication

class TreeModel(QAbstractItemModel):

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.rootItem = TreeItem([self.tr('title'), self.tr('summary')])
        self.setupModelData(data.split('\n'), self.rootItem)

    def __del__(self):
        # delete self.rootItem
        pass

    def columnCount(self, parent):
        '''
        QModelIndex.internalPointer() -> TreeItem
        Args:
            parent (QModelIndex): QModelIndex
        '''
        if parent.isValid():
            return parent.internalPointer().columnCount()
        return self.rootItem.columnCount()

    def data(self, index, role):
        if not index:
            return QVariant()
        if role != Qt.DisplayRole:
            return QVariant()
        item = index.internalPointer()

        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        return QAbstractItemModel.flags(self, index)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section)
        return QVariant()

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parentItem = None

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        childItem = index.internalPointer()
        parentItem = childItem.parentItem()
    
        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent=QModelIndex()):
        parentItem = None
        if parent.column() > 0:
            return 0
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def setupModelData(self, lines, parent):
        parents = []
        indentations = []
        parents.append(parent)
        indentations.append(0)

        number = 0
        while number < len(lines):
            position = 0
            while position < len(lines[number]):
                if lines[number][position] != ' ':
                    break
                position = position + 1

            lineData = lines[number][position:].strip()

            if lineData:
                # Read the column data from the rest of the line.
                columnStrings = [x for x in lineData.split('\t') if x]
                columnData = [None] * len(columnStrings)

                for i, columnString in enumerate(columnStrings):
                    columnData[i] = columnString
                if position > indentations[-1]:
                    # The last child of the current parent is now the new parent
                    # unless the current parent has no children.
                    if parents[-1].childCount() > 0:
                        parents.append(parents[-1].child(parents[-1].childCount() - 1))
                        indentations.append(position)
                else:
                    while position < indentations[-1] and len(parents) > 0:
                        parents.pop(-1)
                        indentations.pop(-1)

                # Append a new item to the current parent's list of children.
                parents[-1].appendChild(TreeItem(columnData, parents[-1]))
            number = number + 1

if __name__ == '__main__':
    app = QApplication(sys.argv)
    with open('view/default.txt', 'r', encoding='utf8') as f:
        model = TreeModel(f.read())
    view = QTreeView()
    view.setModel(model)
    view.setWindowTitle("Simple Tree Model")
    view.show()
    sys.exit(app.exec())
