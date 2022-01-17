from PyQt5.QtWidgets import QMainWindow

from osmm import *
from osmm_data import *


class osmm_gui(QMainWindow, Ui_MainWindow):
    # Dictionary format
    # "rom_id" (made of lower case rom-name, without variants)
    # (rom_name, [[variant, file_name, to_delete], ....]

    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

        # class instance vars init
        self.indexes = {}
        # UI init
        self.initUI()

    def initUI(self):
        self.setupUi(self)

        # overloading app behavior
        self.actionRefresh.triggered.connect(self.UI_updateIndexList)
        self.UI_displayItemCount()

    def UI_updateIndexList(self):
        self.indexes = osmm_ProcessIndexes(osmm_FeedIndex())

        # empty the list
        self.osmm_treeWidget.clear()

        # adding items
        categories = osmm_GetCategories(self.indexes)
        for cat in categories:
            item = QtWidgets.QTreeWidgetItem()
            item.setText(0, cat)

            # getting Countries/Areas
            areas = osmm_GetCountries(self.indexes, cat)
            for area in areas:
                item_area = QtWidgets.QTreeWidgetItem(item)
                item_area.setText(0, area)

                sub_indexes = osmm_FilterIndex(self.indexes, cat, area)
                for ossm_item in sub_indexes:
                    sub_item = QtWidgets.QTreeWidgetItem(item_area)
                    sub_item.setText(2, ossm_item["@name"])
                    sub_item.setText(3, ossm_item["@date"])
                    sub_item.setText(4, ossm_item["@size"] + " MB")
                    sub_item.setTextAlignment(4, QtCore.Qt.AlignRight)
                    sub_item.setText(5, ossm_item["@targetsize"] + " MB")
                    sub_item.setTextAlignment(5, QtCore.Qt.AlignRight)
                    sub_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.osmm_treeWidget.addTopLevelItem(item)

        self.osmm_treeWidget.setColumnWidth(0, 100)
        self.osmm_treeWidget.setColumnWidth(1, 150)
        self.osmm_treeWidget.setColumnWidth(2, 300)
        self.osmm_treeWidget.setColumnWidth(3, 100)
        self.osmm_treeWidget.setColumnWidth(4, 100)
        self.osmm_treeWidget.setColumnWidth(5, 100)
        # self.osmm_treeWidget.collapseAll()

        self.UI_displayItemCount()


    def UI_displayItemCount(self):
        self.statusbar.showMessage("{} - {}/{}     (Disp - Download/Total)".format(len(self.indexes),
                                                                                   len(osmm_GetDownloads(self.indexes)),
                                                                                   len(self.indexes)))
