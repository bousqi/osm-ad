import os.path

import PyQt5
from PyQt5.QtWidgets import QDialog

from package.api.config import AppConfig, CFG_FILE, CFG_DIR
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
        self.le_config_dir.setReadOnly(True)
        self.le_config_dir.setEnabled(False)

        self.le_config_dir.setText(CFG_DIR)
        self.le_download_dir.setText(AppConfig.DIR_ASSETS)
        self.le_extract_dir.setText(AppConfig.DIR_OUTPUT)

    def setup_connections(self):
        self.btn_open_folder_download.clicked.connect(self.open_folder_asset)
        self.btn_open_folder_extract.clicked.connect(self.open_folder_output)
        # save new params
        self.buttonBox.accepted.connect(self.update_config)
        # nothing to do
        # self.buttonBox.rejected.connect()

    def open_folder_asset(self):
        folder_path = PyQt5.QtWidgets.QFileDialog.getExistingDirectory(None, 'Select Asset Folder')
        self.le_download_dir.setText(os.path.normpath(folder_path))

    def open_folder_output(self):
        folder_path = PyQt5.QtWidgets.QFileDialog.getExistingDirectory(None, 'Select Output Folder')
        self.le_extract_dir.setText(os.path.normpath(folder_path))

    def update_config(self):
        AppConfig.DIR_ASSETS = self.le_download_dir.text()
        AppConfig.DIR_OUTPUT = self.le_extract_dir.text()
        AppConfig.save()
