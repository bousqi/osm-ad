import typing
from PyQt6 import QtWidgets, QtCore

from package.api.osm_asset import OsmAsset
from package.gui_constants import *


class AssetTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    asset: OsmAsset

    def __init__(self, parent=None, asset=None):
        QtWidgets.QTreeWidgetItem.__init__(self, parent)
        self.asset = asset
        for col in range(COL_PROG+1):
            self.setTextAlignment(col, self.textAlignment(col))

        self.progress_bar = None

        # not a parent
        if self.asset:
            # checkbox on Watch col
            self.setCheckState(COL_WTCH, QtCore.Qt.Unchecked)
            self.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

    def __lt__(self, other_item):
        column = self.treeWidget().sortColumn()

        # is item or other item a group
        if not self.asset or not other_item.asset:
            return self.text(column).lower() < other_item.text(column).lower()

        # Size compare
        if column == COL_SIZE:
            return self.asset.e_size < other_item.asset.e_size
        if column == COL_COMP:
            return self.asset.c_size < other_item.asset.c_size

        # date compare
        if column == COL_DATE:
            return self.asset.remote_ts < other_item.asset.remote_ts

        # extended sorting on type
        if column == COL_TYPE:
            if self.asset.type.lower() == other_item.asset.type.lower():
                return self.asset.name.lower() < other_item.asset.name.lower()
            return self.asset.type.lower() < other_item.asset.type.lower()

        # sorting by download state
        if column == COL_WTCH:
            if self.asset.watchme == other_item.asset.watchme:
                return self.asset.name.lower() < other_item.asset.name.lower()
            return self.asset.watchme < other_item.asset.watchme

        # simple text compare
        return self.text(column).lower() < other_item.text(column).lower()

    def textAlignment(self, column: int) -> int:
        if column in [COL_WTCH, COL_UPDT, COL_DATE]:
            return QtCore.Qt.AlignCenter
        if column in [COL_COMP, COL_SIZE]:
            return QtCore.Qt.AlignRight

        return super().textAlignment(column)

    def data(self, column: int, role: int) -> typing.Any:
        if role != QtCore.Qt.DisplayRole:
            return super().data(column, role)

        if not self.asset:
            return super().data(column, role)

        # we have an asset
        if column == COL_TYPE:
            return self.asset.area
        if column == COL_NAME:
            return self.asset.name
        if column == COL_DATE:
            return self.asset.remote_date
        if column == COL_DATE:
            return self.asset.remote_date
        if column == COL_COMP:
            return str(self.asset.c_size // 1024 // 1024) + "MB"
        if column == COL_SIZE:
            return str(self.asset.e_size // 1024 // 1024) + "MB"
        if column == COL_WTCH:
            if self.asset.watchme != self.checkState(COL_WTCH):
                self.setCheckState(COL_WTCH, (QtCore.Qt.Checked if self.asset.watchme else QtCore.Qt.Unchecked))
            return ""
        if column == COL_UPDT:
            return "Yes" if self.asset.updatable else ""

        # default behavior
        return super().data(column, role)



