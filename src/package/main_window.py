import PyQt5.QtGui
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QShortcut

from package.ui.ui_main import Ui_MainWindow
from package.api.osm_assets import OsmAssets
from package.gui_constants import *
from package.asset_tw_item import AssetTreeWidgetItem


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, app):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

        self.assets = OsmAssets()
        self.app = app

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
        self.btn_abort.setVisible(False)
        self.pgb_total.setVisible(False)

    def setup_connections(self):
        QShortcut(QtGui.QKeySequence("Space"), self.tw_assets, self.tw_check_item)
        self.tw_assets.itemPressed['QTreeWidgetItem*', 'int'].connect(self.tw_toggle_watchme)

        # self.tw_assets.itemPressed['QTreeWidgetItem*', 'int'].connect(self.toggleDownload_onItem)
        self.btn_grouped.clicked.connect(self.tw_update_list)
        self.btn_watched.clicked.connect(self.tw_update_list)
        self.btn_updates.clicked.connect(self.tw_update_list)

        self.btn_download.clicked.connect(self.download_start)
        self.btn_abort.clicked.connect(self.download_stop)

        self.le_filter.textChanged.connect(self.tw_update_list)

        # about modal config
        self.btn_about.clicked.connect(self.about_dlg)
        self.btn_refresh.clicked.connect(self.tw_refresh_assets)

    def tw_apply_filter(self):
        pass

    # DOWNLOAD ACTIONS

    def download_start(self):
        # updating UI
        self.btn_refresh.setEnabled(False)
        self.btn_download.setEnabled(False)
        self.btn_abort.setVisible(True)
        self.btn_about.setVisible(False)
        self.pgb_total.setVisible(True)

        # starting download
        pass

    def download_stop(self):
        self.btn_refresh.setEnabled(True)
        self.btn_download.setEnabled(True)
        self.btn_abort.setVisible(False)
        self.btn_about.setVisible(True)
        self.pgb_total.setVisible(False)
        # updating UI

        # stopping download
        pass

    # TREEWIDGET MANAGEMENT
    def tw_refresh_assets(self):
        self.btn_refresh.setEnabled(False)
        self.app.processEvents()                    # Trick to update UI

        self.assets.load_index()
        self.assets.load_watch_list()
        self.tw_update_list()

        self.btn_refresh.setEnabled(True)

    def tw_update_list(self):
        # empty the list
        self.tw_assets.clear()

        if self.btn_grouped.isChecked():
            # fill TreeWidget as a tree
            self.tw_populate_as_tree()
        else:
            # fill TreeWidget as a list
            self.tw_populate_as_list()

        #
        self.tw_assets.expandAll()

        self.tw_assets.sortItems(COL_TYPE, QtCore.Qt.AscendingOrder)

        # updating col width
        self.tw_assets.resizeColumnToContents(COL_TYPE)
        if self.tw_assets.columnWidth(COL_TYPE) < 120:
            self.tw_assets.setColumnWidth(COL_TYPE, 120)
        if self.tw_assets.columnWidth(COL_TYPE) > 200:
            self.tw_assets.setColumnWidth(COL_TYPE, 200)

        self.tw_assets.setColumnWidth(COL_NAME, 400)
        self.tw_assets.setColumnWidth(COL_DATE, 100)
        self.tw_assets.setColumnWidth(COL_COMP, 100)
        self.tw_assets.setColumnWidth(COL_SIZE, 100)
        self.tw_assets.setColumnWidth(COL_WTCH, 20)
        self.tw_assets.setColumnWidth(COL_UPDT, 20)

        self.sb_update_summary()

    def tw_populate_as_tree(self):
        asset_filter = self.le_filter.text()
        watched_only = self.btn_watched.isChecked()
        updates_only = self.btn_updates.isChecked()

        tree_root = {}

        if self.assets is None or len(self.assets) == 0:
            return

        # adding items
        for key in self.assets.keys():
            asset = self.assets[key]
            if asset_filter is not None and asset_filter.lower() not in asset.name.lower():
                continue
            if watched_only and not asset.watchme:
                continue
            if updates_only and not asset.updatable:
                continue

            cat = asset.type
            if cat not in tree_root:
                root_item = AssetTreeWidgetItem()
                root_item.setText(COL_TYPE, cat)
                tree_root[cat] = root_item
            else:
                root_item = tree_root[cat]

            AssetTreeWidgetItem(parent=root_item, asset=asset)

        for item in tree_root:
            self.tw_assets.addTopLevelItem(tree_root[item])

    def tw_populate_as_list(self):
        le_filter = self.le_filter.text()
        watched_only = self.btn_watched.isChecked()
        updates_only = self.btn_updates.isChecked()

        if self.assets is None or len(self.assets) == 0:
            return

        # adding items
        for key in self.assets.keys():
            asset = self.assets[key]
            if le_filter is not None and le_filter.lower() not in asset.name.lower():
                continue
            if watched_only and not asset.watchme:
                continue
            if updates_only and not asset.updatable:
                continue

            item = AssetTreeWidgetItem(asset=asset)
            self.tw_assets.addTopLevelItem(item)

    def tw_check_item(self):
        # toggle watch on each selected items
        for selected_item in self.tw_assets.selectedItems():
            self.tw_toggle_watchme(selected_item, COL_WTCH, False)
        # update tw_assets list if necessary (filters applied)
        self.tw_refresh()

    def tw_toggle_watchme(self, item, column, auto_refresh=True):
        if column != COL_WTCH:
            return

        if item is None:
            return

        # this item is a category
        if self.btn_grouped.isChecked() and item.parent() is None:
            return

        # inverting check state
        state = not item.checkState(COL_WTCH)

        item.asset.watchme = state
        item.setCheckState(COL_WTCH, (QtCore.Qt.Checked if state else QtCore.Qt.Unchecked))
        item.setText(COL_UPDT, ("Yes" if item.asset.updatable else ""))
        self.assets.save_watch_list()

        # update tw_assets list if necessary (filters applied)
        if auto_refresh:
            self.tw_refresh()

    def tw_refresh(self):
        if self.btn_watched.isChecked() or self.btn_updates.isChecked():
            self.tw_update_list()
        # update status in status bar
        self.sb_update_summary()

    # STATUS BAR
    def sb_update_summary(self):
        updated_list = self.assets.updatable_list()
        count_watched = len(self.assets.watch_list())
        count_updates = len(updated_list)
        total_size = 0
        for item in updated_list:
            total_size += item.c_size

        # item count
        count_items = 0
        if self.btn_grouped.isChecked():
            # counting children in case of grouping
            for index in range(self.tw_assets.topLevelItemCount()):
                parent = self.tw_assets.topLevelItem(index)
                count_items += parent.childCount()
        else:
            # not grouped
            count_items = self.tw_assets.topLevelItemCount()

        self.statusbar.showMessage(f"{count_updates} updates, {count_watched} watched,"
                                   f" {count_items}/{len(self.assets)} displayed, "
                                   f" {total_size//1024//1024} MB to download")

    # ABOUT ACTION
    def about_dlg(self):
        msg_box = QMessageBox(QMessageBox.Information, "About", OSMAD_ABOUT_INFO, QMessageBox.Ok)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/img/resources/base/maps.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        msg_box.setWindowIcon(icon)
        msg_box.setIconPixmap(QtGui.QPixmap(":/img/resources/base/maps.png").scaledToWidth(128, QtCore.Qt.SmoothTransformation))
        msg_box.setTextFormat(QtCore.Qt.MarkdownText)
        layout = msg_box.layout()
        widget = PyQt5.QtWidgets.QWidget()
        widget.setFixedSize(550, 1)
        layout.addWidget(widget, 3, 0, 1, 3)

        msg_box.exec()
