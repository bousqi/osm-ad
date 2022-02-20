from typing import List

from PyQt5 import QtCore
from PyQt5.QtCore import QObject

from package.api.osm_asset import OsmAsset


class ExitException(Exception):
    pass


class DownloadWorker(QObject):
    signal_file_download_progress = QtCore.pyqtSignal(object, int)
    signal_file_extract_progress = QtCore.pyqtSignal(object, int)
    signal_finished = QtCore.pyqtSignal()

    def __init__(self, download_list: List[OsmAsset]):
        super().__init__()

        self.early_exit = False
        self.download_list = download_list
        self.total_size = 0
        if self.download_list:
            for item in download_list:
                self.total_size += item.c_size

    def process(self):
        try:
            expand_list = self._download()
            self._expand(expand_list)
            self._rename()

            # All done. Request UI update
            self.signal_finished.emit()
        except ExitException:
            # All done. Request UI update
            self.signal_finished.emit()

        pass

    def _download(self):
        for asset in self.download_list:
            self._download_asset(asset)
            # request UI update
            self.signal_file_download_progress.emit()

        return self.download_list

    def _download_asset(self):
        # abort request
        if self.early_exit:
            raise ExitException()
        pass

    def _expand(self, expand_list: List[OsmAsset]):
        for asset in expand_list:
            # expanding
            # ....

            # request UI update
            self.signal_file_extract_progress.emit()

            # abort request
            if self.early_exit:
                raise ExitException()
        pass

    def _rename(self):
        # abort request
        if self.early_exit:
            raise ExitException()
        pass
