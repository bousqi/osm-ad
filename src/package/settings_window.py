import os.path
import shutil

from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6.QtWidgets import QDialog, QMessageBox

from package.api.config import AppConfig, CFG_DIR
from package.ui.ui_settings import Ui_Settings


class SettingsWindow(QDialog, Ui_Settings):
    def __init__(self):
        QDialog.__init__(self)
        Ui_Settings.__init__(self)

        # class instance vars init
        # UI init
        self.init_ui()

    def init_ui(self):
        self.setupUi(self)
        self.modify_widgets()
        self.setup_connections()

    def modify_widgets(self):
        # first tab
        self.le_config_dir.setReadOnly(True)
        self.le_config_dir.setEnabled(False)

        self.le_config_dir.setText(CFG_DIR)
        self.le_download_dir.setText(AppConfig.DIR_ASSETS)
        self.le_extract_dir.setText(AppConfig.DIR_OUTPUT)

        # second tab
        self.cb_disable_ssl_check.setCheckState(QtCore.Qt.CheckState.Unchecked if AppConfig.SSL_VERIFY else QtCore.Qt.CheckState.Checked)
        self.update_directories()

    def setup_connections(self):
        # first tab
        self.btn_open_folder_download.clicked.connect(self.open_folder_asset)
        self.btn_open_folder_extract.clicked.connect(self.open_folder_output)
        # save new params
        self.buttonBox.accepted.connect(self.update_config)
        # nothing to do
        # self.buttonBox.rejected.connect()

        # second tab
        self.btn_clean_asset.clicked.connect(lambda: self.clean_directory(AppConfig.DIR_ASSETS))
        self.btn_clean_output.clicked.connect(lambda: self.clean_directory(AppConfig.DIR_OUTPUT))

    def open_folder_asset(self):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(None, 'Select Asset Folder')
        self.le_download_dir.setText(os.path.normpath(folder_path))

    def open_folder_output(self):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(None, 'Select Output Folder')
        self.le_extract_dir.setText(os.path.normpath(folder_path))

    def update_config(self):
        AppConfig.DIR_ASSETS = self.le_download_dir.text()
        AppConfig.DIR_OUTPUT = self.le_extract_dir.text()
        AppConfig.SSL_VERIFY = not self.cb_disable_ssl_check.checkState()
        AppConfig.save()

    def update_directories(self):
        nb_files, size = self.parse_directory(AppConfig.DIR_ASSETS)
        self.le_dirstatus_asset.setText(f"{nb_files} files / {size // 1024 // 1024} MB")
        nb_files, size = self.parse_directory(AppConfig.DIR_OUTPUT)
        self.le_dirstatus_output.setText(f"{nb_files} files / {size // 1024 // 1024} MB")

    @staticmethod
    def parse_directory(path):
        total_size = 0
        count = 0
        for dir_path, dir_names, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dir_path, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
                    count += 1

        return count, total_size

    def clean_directory(self, path):
        valid_dlg = QMessageBox(QMessageBox.Question,
                                "Clean directory",
                                "Are you sure you want to remove all files ?",
                                QMessageBox.Yes | QMessageBox.No)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/base/setting.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        valid_dlg.setWindowIcon(icon)

        res = valid_dlg.exec()

        if res == QtWidgets.QMessageBox.Yes:
            try:
                shutil.rmtree(path)
                os.makedirs(path)
            except OSError as e:
                print("Error: %s - %s." % (e.filename, e.strerror))

            self.update_directories()
