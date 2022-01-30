from datetime import datetime
from PyQt5 import QtWidgets

import gui.osmm_main

class AssetTreeWidgetItem(QtWidgets.QTreeWidgetItem):

    def __init__(self, parent=None):
        QtWidgets.QTreeWidgetItem.__init__(self, parent)

    def __lt__(self, otherItem):
        column = self.treeWidget().sortColumn()
        # Size compare
        if column == gui.osmm_main.COL_SIZE or column == gui.osmm_main.COL_COMP:
            if self.text(column) != "" and otherItem.text(column) != "":
                return float(self.text(column).split(' ')[0]) < float(otherItem.text(column).split(' ')[0])

        # date compare
        if column == gui.osmm_main.COL_DATE:
            if self.text(column) != "" and otherItem.text(column) != "":
                return datetime.strptime(self.text(column), '%d.%m.%Y') < datetime.strptime(otherItem.text(column), '%d.%m.%Y')

        # extended sorting on type
        if column == gui.osmm_main.COL_TYPE:
            if self.text(column).lower() == otherItem.text(column).lower():
                return self.text(gui.osmm_main.COL_NAME).lower() < otherItem.text(gui.osmm_main.COL_NAME).lower()

        # sorting by download state
        if column == gui.osmm_main.COL_DOWN:
            if self.checkState(column) == otherItem.checkState(column):
                return self.text(gui.osmm_main.COL_NAME).lower() < otherItem.text(gui.osmm_main.COL_NAME).lower()
            return self.checkState(column) < otherItem.checkState(column)

        # simple text compare
        return self.text(column).lower() < otherItem.text(column).lower()