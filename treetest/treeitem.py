from PyQt5.QtCore import QVariant

class TreeItem():

    def __init__(self, data, parent=None):
        # QVector<TreeItem>
        # ぶら下がってるアイテム 行
        self.m_childItems = []
        # QVector<TreeItemData>
        # 自身のアイテム 列
        self.m_itemData = data
        # parent TreeItem
        self.m_parentItem = parent

    def __del__(self):
        pass
        #self.qDeleteAll(m_childItems)

    def appendChild(self, item):
        self.m_childItems.append(item)

    def child(self, row):
        if row < 0 or row >= len(self.m_childItems):
            return None
        return self.m_childItems[row]

    def childCount(self):
        return len(self.m_childItems)

    def columnCount(self):
        return len(self.m_itemData)

    def data(self, column):
        if column < 0 or column >= len(self.m_itemData):
            return QVariant()
        return self.m_itemData[column]

    def parentItem(self):
        return self.m_parentItem

    def row(self):
        if self.m_parentItem:
            return self.m_parentItem.m_childItems.index(self)
        return 0
