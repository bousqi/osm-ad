import os
import time
import urllib
from typing import List

import requests
import PyQt5.QtGui
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QShortcut

from package.api.osm_asset import OsmAsset
from package.download_worker import DownloadWorker
from package.ui.ui_main import Ui_MainWindow
from package.api.osm_assets import OsmAssets
from package.gui_constants import *
from package.asset_tw_item import AssetTreeWidgetItem

"""
TODO : 
 * Create thread ans worker for download
 * Improve thread with QThreadPool
 * loop on dld item to extract
 * rename extracted items
"""


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, app):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

        self.worker: DownloadWorker = None
        self.thread: QtCore.QThread = None

        self.assets = OsmAssets()
        self.app = app
        self.early_exit = False
        self.sb_message = ""

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
        self.btn_abort.clicked.connect(self.download_abort)

        self.le_filter.textChanged.connect(self.tw_update_list)

        # about modal config
        self.btn_about.clicked.connect(self.about_dlg)
        self.btn_refresh.clicked.connect(self.tw_refresh_assets)

    def tw_apply_filter(self):
        pass

    # DOWNLOAD ACTIONS

    def download_process(self, dld_list: List[OsmAsset]) -> List[OsmAsset]:
        asset: OsmAsset
        to_expand = []

        # checking assets dir exists before using it
        if not os.path.isdir(CFG_DIR_ASSETS):
            os.makedirs(CFG_DIR_ASSETS)

        # processing all files
        for index, asset in enumerate(dld_list):
            if not self.download_is_complete(asset):
                res = self.download_asset(asset)
            else:
                res = True

            to_expand.append(asset)
            self.download_slot_file_finished(asset, res)

            # abort request
            if self.early_exit:
                return

            self.download_slot_all_progress(index+1)

        return to_expand

    def download_is_complete(self, asset: OsmAsset):
        if asset is None:
            return True

        # comparing watchlist and remote timestamps
        if asset.remote_ts > asset.local_ts:
            return False

        path = os.path.join(CFG_DIR_ASSETS, asset.filename)
        # is file already there ?
        if not os.path.isfile(path):
            return False

        # is existing file incomplete ?
        if int(os.path.getsize(path)) != int(asset.c_size):
            return False

        # no need to download
        return True

    def download_asset(self, asset: OsmAsset):
        # opening connection to resource
        try:
            r = requests.get(asset.url, headers=USER_AGENT,
                             proxies=urllib.request.getproxies(),
                             verify=CFG_SSL_VERIFY,
                             stream=True)
        except requests.exceptions.ConnectionError:
            r = None
        # is request success ?
        if r and r.status_code != requests.codes.ok:
            return False

        # downloading

        # Set configuration
        block_size = 1024
        file = os.path.join(CFG_DIR_ASSETS, asset.filename)

        ref_time = time.time() * 1000
        ref_bytes = 0

        try:
            pos = 0
            # creating output file
            with open(file, "wb") as f:
                # getting stream chunks to write
                for chunk in r.iter_content(64 * block_size):
                    f.write(chunk)
                    pos += len(chunk)

                    # speed calculation
                    cur_time = time.time() * 1000
                    if cur_time - ref_time > 1000:  # 1s
                        speed = ((pos - ref_bytes) / ((cur_time - ref_time)/1000))
                        # updating UI
                        self.sb_update_bandwidth(speed)
                        # updating ref for next time
                        ref_time = cur_time
                        ref_bytes = pos

                    # update UI
                    self.slot_download_file_progress(asset, pos)
                    self.app.processEvents()

                    # abort request
                    if self.early_exit:
                        return False

        except requests.exceptions.Timeout as e:
            # Maybe set up for a retry, or continue in a retry loop
            self.statusbar.showMessage("ERROR: server timeout")
            print("ERROR: " + str(e))
        except requests.exceptions.TooManyRedirects as e:
            # Tell the user their URL was bad and try a different one
            self.statusbar.showMessage("ERROR: too many redirects")
            print("ERROR: " + str(e))
        except requests.exceptions.RequestException:
            # catastrophic error, try next
            pass

        return True

    def expand_process(self, exp_list: List[OsmAsset]):
        self.download_slot_all_progress(0)

        if not exp_list:
            return

        for index, asset in enumerate(exp_list):
            self.expand_asset(asset)
            self.download_slot_all_progress(index)

    def expand_asset(self, asset: OsmAsset):
        self.slot_expand_file(asset)
        time.sleep(3)
        self.slot_expand_file_done(asset)

    def download_start(self):
        dld_list = self.assets.updatable_list()
        if not dld_list:
            # nothing to download
            return

        # UI prep for download
        self.slot_download_begin()

        # starting download
        # self.early_exit = False
        # to_expand_list = self.download_process(dld_list)
        # self.expand_process(to_expand_list)
        # self.slot_download_all_finished()

        self.worker = DownloadWorker(dld_list)
        self.thread = QtCore.QThread()
        self.worker.moveToThread(self.thread)

        # connecting slots
        self.thread.started.connect(self.worker.process)
        self.worker.signal_finished.connect(self.thread.quit)
        self.worker.signal_finished.connect(self.slot_download_finished)
        self.worker.signal_aborted.connect(self.slot_download_aborted)
        
        self.worker.signal_file_download_progress.connect(self.slot_download_file_progress)

        # running
        self.thread.start()

    def download_abort(self):
        print("DOWNLOAD ABORT")
        if self.worker:
            self.worker.early_exit = True

    def slot_download_begin(self):
        print("DOWNLOAD BEGIN")

        # updating UI
        self.btn_refresh.setEnabled(False)
        self.btn_download.setEnabled(False)
        self.btn_abort.setVisible(True)
        self.btn_about.setVisible(False)
        self.pgb_total.setVisible(True)

        #
        self.pgb_total.setRange(0, 100)
        self.pgb_total.setValue(0)

    def slot_download_aborted(self):
        print("SLOT ABORT")
        self.thread.quit()
        self.slot_download_finished()

        for asset in self.worker.download_list:
            asset_item = self.tw_get_item(asset)
            self.tw_assets.removeItemWidget(asset_item, COL_PROG)
            asset_item.progress_bar = None

            if asset.updatable:
                asset_item.setText(COL_PROG, "Aborted")

    def slot_download_finished(self):
        print("SLOT FINISHED")
        # updating UI
        self.btn_refresh.setEnabled(True)
        self.btn_download.setEnabled(True)
        self.btn_abort.setVisible(False)
        self.btn_about.setVisible(True)
        self.pgb_total.setVisible(False)

        self.btn_download.setEnabled(len(self.assets.updatable_list()) > 0)

        # saving assets changes (file downloaded)
        # self.assets.save_watch_list()

    def slot_download_file_progress(self, asset: OsmAsset, current_size):
        asset_item = self.tw_get_item(asset)

        if not asset_item.progress_bar:
            max_height = self.tw_assets.visualItemRect(asset_item).height()

            # progressBar on last col
            asset_item.progress_bar = PyQt5.QtWidgets.QProgressBar()
            asset_item.progress_bar.setMaximumHeight(max_height)
            asset_item.progress_bar.setRange(0, asset.c_size)
            self.tw_assets.setItemWidget(asset_item, COL_PROG, asset_item.progress_bar)

        asset_item.progress_bar.setValue(current_size)

    def download_slot_file_finished(self, asset: OsmAsset, success):
        if success:
            asset.downloaded()

        item = self.tw_get_item(asset)
        item.emitDataChanged()
        self.sb_update_summary()

        item.setText(COL_PROG, "Done" if success else "Failed")

    def download_slot_all_progress(self, current):
        self.pgb_total.setValue(current)
        # force ui redraw
        self.app.processEvents()

    def slot_download_all_finished(self):
        self.slot_download_finished()
        # force ui redraw
        self.app.processEvents()

    def slot_expand_file(self, asset: OsmAsset):
        asset_item = self.tw_get_item(asset)

        # asset_item.progress_bar: PyQt5.QtWidgets.QProgressBar
        # asset_item.progress_bar.setVisible(False)

        self.tw_assets.removeItemWidget(asset_item, COL_PROG)

        asset_item.setText(COL_PROG, "Expanding...")
        # force ui redraw
        self.app.processEvents()

    def slot_expand_file_done(self, asset: OsmAsset):
        asset_item = self.tw_get_item(asset)
        asset_item.setText(COL_PROG, "Done")
        # force ui redraw
        self.app.processEvents()

    # TREE WIDGET MANAGEMENT
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

        # updating other elements
        self.btn_download.setEnabled(len(self.assets.updatable_list()) > 0)
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
                # new cat to be created
                root_item = AssetTreeWidgetItem()
                root_item.setText(COL_TYPE, cat)
                # adding to tree
                self.tw_assets.addTopLevelItem(root_item)
                # saving to dict
                tree_root[cat] = root_item
            else:
                root_item = tree_root[cat]

            # item to be added in a specific cat
            AssetTreeWidgetItem(parent=root_item, asset=asset)

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

            # create and add item to treeWidget
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
        # update download button
        self.btn_download.setEnabled(len(self.assets.updatable_list()) > 0)

    def tw_get_item(self, asset: OsmAsset) -> AssetTreeWidgetItem:
        if self.btn_grouped.isChecked():
            # searching in tree
            cat_item: AssetTreeWidgetItem
            for index in range(self.tw_assets.topLevelItemCount()):
                cat_item = self.tw_assets.topLevelItem(index)
                if asset.type == cat_item.text(COL_TYPE):
                    for child_index in range(cat_item.childCount()):
                        asset_item = cat_item.child(child_index)
                        if asset == asset_item.asset:
                            return asset_item
        else:
            # searching in list
            asset_item: AssetTreeWidgetItem
            for index in range(self.tw_assets.topLevelItemCount()):
                asset_item = self.tw_assets.topLevelItem(index)
                if asset == asset_item.asset:
                    return asset_item
        return None

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

        self.sb_message = f"{count_updates} updates, {count_watched} watched," \
                          f" {count_items}/{len(self.assets)} displayed, " \
                          f" {total_size//1024//1024} MB to download"
        self.statusbar.showMessage(self.sb_message)

    def sb_update_bandwidth(self, speed):
        unit = "B/s"
        if speed > 1024:
            unit = "KB/s"
            speed = speed / 1024
        if speed > 1024:
            unit = "MB/s"
            speed = speed / 1024

        self.statusbar.showMessage(f"{self.sb_message} [ {speed:.2f} {unit} ]")

    # ABOUT ACTION
    def about_dlg(self):
        msg_box = QMessageBox(QMessageBox.Information, "About", OSMAD_ABOUT_INFO, QMessageBox.Ok)

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/img/resources/base/maps.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        msg_box.setWindowIcon(icon)

        pixmap = QtGui.QPixmap(":/img/resources/base/maps.png").scaledToWidth(128, QtCore.Qt.SmoothTransformation)
        msg_box.setIconPixmap(pixmap)
        msg_box.setTextFormat(QtCore.Qt.MarkdownText)

        layout = msg_box.layout()
        widget = PyQt5.QtWidgets.QWidget()
        widget.setFixedSize(550, 1)
        layout.addWidget(widget, 3, 0, 1, 3)

        msg_box.exec()
