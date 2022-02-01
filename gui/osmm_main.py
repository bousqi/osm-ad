from time import sleep

from PyQt5.QtCore import QThread, QObject, pyqtSignal
from PyQt5.QtWidgets import QMainWindow

import osmm_data
from gui.AssetTreeWidgetItem import AssetTreeWidgetItem
from gui.about import Ui_About
from gui.main import *
from osmm_data import *

COL_TYPE = 0
COL_NAME = 1
COL_DATE = 2
COL_COMP = 3
COL_SIZE = 4
COL_DOWN = 5


'''
TODO : 
    - set selected state
    - remove selected state
    - trigger action on download
    - create thread on download with list
    - add callback on download item (instead of tqdm)
    - two signals (total progress and current progress)
    
    - detect updates
'''

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def run(self):
        gui_main.indexes = osmm_ProcessIndexes(osmm_FeedIndex())
        self.finished.emit()


class gui_main(QMainWindow, Ui_MainWindow):
    # Dictionary format
    # "rom_id" (made of lower case rom-name, without variants)
    # (rom_name, [[variant, file_name, to_delete], ....]
    thread = None
    worker = None
    indexes = {}

    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

        # class instance vars init
        # UI init
        self.initUI()

    def initUI(self):
        self.setupUi(self)

        # overloading app behavior
        self.osmm_treeWidget.itemPressed['QTreeWidgetItem*', 'int'].connect(self.toggleDownload_onItem)
        self.updates_cBox.clicked.connect(self.UI_applyFilter)
        self.grouped_cBox.clicked.connect(self.UI_applyFilter)

        self.refreshButton.clicked.connect(self.startThreadFeed)
        self.leFilter.textChanged.connect(self.UI_applyFilter)
        self.UI_displayItemCount()

        # self.actionDownload.triggered.connect(self.startDownload) # type: ignore
        self.progressBar_Curr.setVisible(False)
        self.abortButton.setVisible(False)
        self.progressBar_Total.setVisible(False)

        self.osmm_treeWidget.installEventFilter(self)

        # about modal config
        self.aboutButton.clicked.connect(self.showAbout)

    def showAbout(self):
        About = QtWidgets.QDialog()
        ui = Ui_About()
        ui.setupUi(About)
        About.exec_()

    def eventFilter(self, obj, event):
        if obj == self.osmm_treeWidget:
            if  event.type() == QtCore.QEvent.KeyPress:
                if event.key() == QtCore.Qt.Key_Delete:
                    # self.setRemove_onCurrent()
                    pass
                elif event.key() == QtCore.Qt.Key_Space:
                    self.toggleDownload_onCurrent()
        return super(gui_main, self).eventFilter(obj, event)

    def reportProgress(self, n):
        self.progressBar_Total.setValue(n)
        self.statusbar.showMessage(f"Long-Running Step: {n}")

    def startThreadDownload(self):
        pass

    def startThreadFeed(self):
        self.leFilter.setText("")
        self.progressBar_Total.setVisible(True)
        self.progressBar_Total.setMaximum(5)
        self.progressBar_Total.setValue(2)

        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = Worker()
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Final resets
        self.actionRefresh.setEnabled(False)
        self.thread.finished.connect(lambda: self.actionRefresh.setEnabled(True))
        self.thread.finished.connect(lambda: self.progressBar_Total.setVisible(False))
        self.thread.finished.connect(self.UI_updateIndexList)
        # Step 6: Start the thread
        self.thread.start()


    def UI_applyFilter(self):
        self.UI_updateIndexList()


    def UI_updateIndexList(self):
        # empty the list
        self.osmm_treeWidget.clear()

        if self.grouped_cBox.checkState():
            # fill TreeWidget as a tree
            self.dispAssetsTreeLvl1()
        else:
            # fill TreeWidget as a list
            self.dispAssetsSimple()

        self.osmm_treeWidget.setColumnWidth(COL_TYPE, 100)
        self.osmm_treeWidget.setColumnWidth(COL_NAME, 300)
        self.osmm_treeWidget.setColumnWidth(COL_DATE, 100)
        self.osmm_treeWidget.setColumnWidth(COL_COMP, 100)
        self.osmm_treeWidget.setColumnWidth(COL_SIZE, 100)
        self.osmm_treeWidget.setColumnWidth(COL_DOWN, 20)

        #
        self.osmm_treeWidget.expandAll()

        self.osmm_treeWidget.sortItems(COL_TYPE, QtCore.Qt.AscendingOrder)
        self.osmm_treeWidget.resizeColumnToContents(COL_TYPE)

        self.UI_displayItemCount()

    def dispAssetsTree(self):
        # adding items
        categories = osmm_GetCategories(self.indexes)
        for cat in categories:
            item = AssetTreeWidgetItem()
            item.setText(COL_TYPE, cat)

            # getting Countries/Areas
            areas = osmm_GetCountries(self.indexes, cat)
            for area in areas:
                item_area = AssetTreeWidgetItem(item)
                item_area.setText(COL_TYPE, area)

                sub_indexes = osmm_FilterIndex(self.indexes, cat, area)
                for ossm_item in sub_indexes:
                    sub_item = AssetTreeWidgetItem(item_area)
                    sub_item.setText(COL_NAME, ossm_item["@name"])
                    sub_item.setText(COL_DATE, ossm_item["@date"])
                    sub_item.setText(COL_COMP, ossm_item["@size"] + " MB")
                    sub_item.setTextAlignment(COL_COMP, QtCore.Qt.AlignRight)
                    sub_item.setText(COL_SIZE, ossm_item["@targetsize"] + " MB")
                    sub_item.setTextAlignment(COL_SIZE, QtCore.Qt.AlignRight)
                    sub_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.osmm_treeWidget.addTopLevelItem(item)

        pass

    def dispAssetsTreeLvl1(self):
        filter = self.leFilter.text()
        updates_only = self.updates_cBox.isChecked()

        tree_root = {}

        if self.indexes is None or len(self.indexes) == 0:
            return

        # adding items
        for osmm_item in self.indexes:
            if filter is not None and filter.lower() not in osmm_item["@name"].lower():
                continue
            if updates_only and ("@osmm_get" not in osmm_item or not osmm_item["@osmm_get"]):
                continue

            cat = osmm_item["@type"]
            if cat not in tree_root:
                root_item = AssetTreeWidgetItem()
                root_item.setText(COL_TYPE, cat)
                tree_root[cat] = root_item
            else:
                root_item = tree_root[cat]

            item = AssetTreeWidgetItem(root_item)
            item.setText(COL_TYPE, osmm_item["@country"])
            item.setText(COL_NAME, osmm_item["@name"])
            item.setText(COL_DATE, osmm_item["@date"])
            item.setText(COL_COMP, osmm_item["@size"] + " MB")
            item.setTextAlignment(COL_COMP, QtCore.Qt.AlignRight)

            item.setText(COL_SIZE, osmm_item["@targetsize"] + " MB")
            item.setTextAlignment(COL_SIZE, QtCore.Qt.AlignRight)
            item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            if "@osmm_get" in osmm_item and osmm_item["@osmm_get"]:
                item.setCheckState(COL_DOWN, QtCore.Qt.Checked)
            else:
                item.setCheckState(COL_DOWN, QtCore.Qt.Unchecked)
            item.setTextAlignment(COL_DOWN, QtCore.Qt.AlignCenter)

        for item in tree_root:
            self.osmm_treeWidget.addTopLevelItem(tree_root[item])

    def dispAssetsSimple(self):
        filter = self.leFilter.text()
        updates_only = self.updates_cBox.isChecked()

        if self.indexes is None or len(self.indexes) == 0:
            return

        # adding items
        for osmm_item in self.indexes:
            if filter is not None and filter.lower() not in osmm_item["@name"].lower():
                continue
            if updates_only and ("@osmm_get" not in osmm_item or not osmm_item["@osmm_get"]):
                continue

            item = AssetTreeWidgetItem()
            item.setText(COL_TYPE, osmm_item["@type"])
            item.setText(COL_NAME, osmm_item["@name"])
            item.setText(COL_DATE, osmm_item["@date"])
            item.setTextAlignment(COL_DATE, QtCore.Qt.AlignCenter)

            item.setText(COL_COMP, osmm_item["@size"] + " MB")
            item.setTextAlignment(COL_COMP, QtCore.Qt.AlignRight)

            item.setText(COL_SIZE, osmm_item["@targetsize"] + " MB")
            item.setTextAlignment(COL_SIZE, QtCore.Qt.AlignRight)
            item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            if "@osmm_get" in osmm_item and osmm_item["@osmm_get"]:
                item.setCheckState(COL_DOWN, QtCore.Qt.Checked)
            else:
                item.setCheckState(COL_DOWN, QtCore.Qt.Unchecked)
            item.setTextAlignment(COL_DOWN, QtCore.Qt.AlignCenter)

            self.osmm_treeWidget.addTopLevelItem(item)

    def UI_displayItemCount(self):
        count = 0
        if self.grouped_cBox.checkState():
            # counting children in case of grouping
            for index in range(self.osmm_treeWidget.topLevelItemCount()):
                parent = self.osmm_treeWidget.topLevelItem(index)
                count += parent.childCount()
        else:
            # not grouped
            count = self.osmm_treeWidget.topLevelItemCount()

        self.statusbar.showMessage("{} - {}/{}     (Disp - Download/Total)".format(count,
                                                                                   len(osmm_GetDownloads(self.indexes)),
                                                                                   len(self.indexes)))

    def toggleDownload_onCurrent(self):
        selectedItem = self.osmm_treeWidget.currentItem()
        self.toggleDownload_onItem(selectedItem, COL_DOWN)

    def toggleDownload_onItem(self, item, column):
        if column != COL_DOWN:
            return

        if item is None:
            return

        # this item is a categorie
        if self.grouped_cBox.checkState() and item.parent() is None:
            return

        # inverting check state
        state = not item.checkState(COL_DOWN)

        osmm_data.osmm_SetDownload(self.indexes, item.text(COL_NAME), state)
        # self.__setRemoveState(item, state)
        self.__UI_updateDownState(item, state)

    def __UI_updateDownState(self, item, toDownload):
        if item is None:
            return

        # changing state
        if toDownload:
            item.setCheckState(COL_DOWN, QtCore.Qt.Checked)
            brush = QtGui.QBrush(QtGui.QColor(170, 0, 0, 25))
            brush.setStyle(QtCore.Qt.DiagCrossPattern)
        else:
            item.setCheckState(COL_DOWN, QtCore.Qt.Unchecked)
            brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 255))
            brush.setStyle(QtCore.Qt.NoBrush)
        for i in range(COL_DOWN):
            item.setBackground(i, brush)
