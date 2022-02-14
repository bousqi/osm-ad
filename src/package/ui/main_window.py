import PyQt5.QtGui
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QShortcut

from package.ui.ui_main import Ui_MainWindow
from package.api.osm_assets import OsmAssets

""" CONSTANTS """

COL_TYPE = 0
COL_NAME = 1
COL_DATE = 2
COL_COMP = 3
COL_SIZE = 4
COL_WTCH = 5
COL_UPDT = 6
COL_PROG = 7


""" CLASSES """


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.assets = OsmAssets()

        # class instance vars init
        # UI init
        self.init_ui()

    def init_ui(self):
        self.setupUi(self)
        self.modify_widgets()
        self.setup_connections()
        self.tw_refresh_assets()

    def modify_widgets(self):
        # self.actionDownload.triggered.connect(self.startDownload) # type: ignore
        self.abortButton.setVisible(False)
        self.progressBar_Total.setVisible(False)

    def setup_connections(self):
        QShortcut(QtGui.QKeySequence("Space"), self.osmm_treeWidget, self.tw_check_item)
        self.osmm_treeWidget.itemPressed['QTreeWidgetItem*', 'int'].connect(self.tw_toggle_watchme)

        # self.osmm_treeWidget.itemPressed['QTreeWidgetItem*', 'int'].connect(self.toggleDownload_onItem)
        self.updates_cBox.clicked.connect(self.tw_update_list)
        self.grouped_cBox.clicked.connect(self.tw_update_list)

        self.downloadButton.clicked.connect(self.download_start)
        self.abortButton.clicked.connect(self.download_stop)

        self.leFilter.textChanged.connect(self.tw_update_list)

        # about modal config
        self.aboutButton.clicked.connect(self.about_dlg)
        self.refreshButton.clicked.connect(self.tw_refresh_assets)

    def tw_apply_filter(self):
        pass

    # DOWNLOAD ACTIONS

    def download_start(self):
        # updating UI
        self.refreshButton.setEnabled(False)
        self.downloadButton.setEnabled(False)
        self.abortButton.setVisible(True)
        self.aboutButton.setVisible(False)
        self.progressBar_Total.setVisible(True)

        # starting download
        pass

    def download_stop(self):
        self.refreshButton.setEnabled(True)
        self.downloadButton.setEnabled(True)
        self.abortButton.setVisible(False)
        self.aboutButton.setVisible(True)
        self.progressBar_Total.setVisible(False)
        # updating UI

        # stopping download
        pass

    # TREEWIDGET MANAGEMENT
    def tw_refresh_assets(self):
        self.assets.load_index()
        self.assets.load_watch_list()
        self.tw_update_list()

    def tw_update_list(self):
        # empty the list
        self.osmm_treeWidget.clear()

        if self.grouped_cBox.checkState():
            # fill TreeWidget as a tree
            self.tw_populate_as_tree()
        else:
            # fill TreeWidget as a list
            self.tw_populate_as_list()

        #
        self.osmm_treeWidget.expandAll()

        self.osmm_treeWidget.sortItems(COL_TYPE, QtCore.Qt.AscendingOrder)

        # updating col width
        self.osmm_treeWidget.resizeColumnToContents(COL_TYPE)
        if self.osmm_treeWidget.columnWidth(COL_TYPE) < 120:
            self.osmm_treeWidget.setColumnWidth(COL_TYPE, 120)
        if self.osmm_treeWidget.columnWidth(COL_TYPE) > 200:
            self.osmm_treeWidget.setColumnWidth(COL_TYPE, 200)

        self.osmm_treeWidget.setColumnWidth(COL_NAME, 400)
        self.osmm_treeWidget.setColumnWidth(COL_DATE, 100)
        self.osmm_treeWidget.setColumnWidth(COL_COMP, 100)
        self.osmm_treeWidget.setColumnWidth(COL_SIZE, 100)
        self.osmm_treeWidget.setColumnWidth(COL_WTCH, 20)
        self.osmm_treeWidget.setColumnWidth(COL_UPDT, 20)
        # self.UI_displayItemCount()

    def tw_populate_as_tree(self):
        asset_filter = self.leFilter.text()
        updates_only = self.updates_cBox.isChecked()

        tree_root = {}

        if self.assets is None or len(self.assets) == 0:
            return

        # adding items
        for key in self.assets.keys():
            asset = self.assets[key]
            if asset_filter is not None and asset_filter.lower() not in asset.name.lower():
                continue
            if updates_only and not asset.updatable:
                continue

            cat = asset.type
            if cat not in tree_root:
                root_item = PyQt5.QtWidgets.QTreeWidgetItem()
                root_item.setText(COL_TYPE, cat)
                tree_root[cat] = root_item
            else:
                root_item = tree_root[cat]

            item = PyQt5.QtWidgets.QTreeWidgetItem(root_item)
            item.asset = asset
            item.setText(COL_TYPE, asset.area)
            item.setText(COL_NAME, asset.name)
            item.setText(COL_DATE, asset.remote_date)
            item.setText(COL_COMP, str(asset.c_size // 1024 // 1024) + " MB")
            item.setTextAlignment(COL_COMP, QtCore.Qt.AlignRight)

            item.setText(COL_SIZE, str(asset.e_size // 1024 // 1024) + " MB")
            item.setTextAlignment(COL_SIZE, QtCore.Qt.AlignRight)
            item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            item.setCheckState(COL_WTCH, (QtCore.Qt.Checked if asset.watchme else QtCore.Qt.Unchecked))
            item.setTextAlignment(COL_WTCH, QtCore.Qt.AlignCenter)

        for item in tree_root:
            self.osmm_treeWidget.addTopLevelItem(tree_root[item])

    def tw_populate_as_list(self):
        le_filter = self.leFilter.text()
        updates_only = self.updates_cBox.isChecked()

        if self.assets is None or len(self.assets) == 0:
            return

        # adding items
        for key in self.assets.keys():
            asset = self.assets[key]
            if le_filter is not None and le_filter.lower() not in asset.name.lower():
                continue
            if updates_only and not asset.updatable:
                continue

            item = PyQt5.QtWidgets.QTreeWidgetItem()
            item.asset = asset
            item.setText(COL_TYPE, asset.type)
            item.setText(COL_NAME, asset.name)
            item.setText(COL_DATE, asset.remote_date)
            item.setTextAlignment(COL_DATE, QtCore.Qt.AlignCenter)

            item.setText(COL_COMP, str(asset.c_size // 1024 // 1024) + " MB")
            item.setTextAlignment(COL_COMP, QtCore.Qt.AlignRight)

            item.setText(COL_SIZE, str(asset.e_size // 1024 // 1024) + " MB")
            item.setTextAlignment(COL_SIZE, QtCore.Qt.AlignRight)
            item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            item.setCheckState(COL_WTCH, (QtCore.Qt.Checked if asset.watchme else QtCore.Qt.Unchecked))
            item.setTextAlignment(COL_WTCH, QtCore.Qt.AlignCenter)

            self.osmm_treeWidget.addTopLevelItem(item)

    def tw_check_item(self):
        for selected_item in self.osmm_treeWidget.selectedItems():
            self.tw_toggle_watchme(selected_item, COL_WTCH)

    def tw_toggle_watchme(self, item, column):
        if column != COL_WTCH:
            return

        if item is None:
            return

        # this item is a category
        if self.grouped_cBox.checkState() and item.parent() is None:
            return

        # inverting check state
        state = not item.checkState(COL_WTCH)

        item.asset.watchme = state
        item.setCheckState(COL_WTCH, (QtCore.Qt.Checked if state else QtCore.Qt.Unchecked))
        self.assets.save_watch_list()

    # ABOUT ACTION
    def about_dlg(self):
        msg_box = QMessageBox(QMessageBox.Information, "About", "OpenStreetMap - Asset Downloader", QMessageBox.Ok)
        msg_box.setIconPixmap(QtGui.QPixmap(":/icons/icons/base/app_icon.ico"))
        msg_box.exec()
