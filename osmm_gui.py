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
        self.index_dict = {}
        # UI init
        self.initUI()

    def initUI(self):
        self.setupUi(self)

        # overloading app behavior
        self.actionRefresh.triggered.connect(self.UI_updateIndexList)
        self.refreshButton.clicked.connect(self.UI_updateIndexList)
        self.UI_displayItemCount()

    def UI_updateIndexList(self):
        self.index_dict = osmm_FeedIndex()

        # empty the list
        self.osmm_treeWidget.clear()
        # # adding items
        # for ossm_item in self.index_dict:
        #     # to be displayed, creating main entry
        #     item = QtWidgets.QTreeWidgetItem()
        #     item.setText(0, self.index_dict[ossm_item])
        #
        #     self.osmm_treeWidget.addTopLevelItem(item)
        #
        self.osmm_treeWidget.expandAll()



    def UI_displayItemCount(self):
        count = 0

        # counting current displayed items in list

        self.statusbar.showMessage("{} - {}/{}     (Disp - Download/Total)".format(count, count, count))
