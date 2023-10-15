import glob
import os
import shutil
import time
import urllib
import zipfile
from typing import List

import requests
from PyQt5 import QtCore
from PyQt5.QtCore import QObject

from package.api.config import AppConfig
from package.api.osm_asset import OsmAsset
from package.gui_constants import *


class ExitException(Exception):
    pass


class DownloadWorker(QObject):
    signal_file_download_progress = QtCore.pyqtSignal(object, int)
    signal_file_expand_progress = QtCore.pyqtSignal(object, bool, bool)
    signal_bandwidth = QtCore.pyqtSignal(int)
    signal_finished = QtCore.pyqtSignal()
    signal_aborted = QtCore.pyqtSignal()

    def __init__(self, download_list: List[OsmAsset]):
        super().__init__()

        self.early_exit = False
        self.download_list = download_list
        self.total_size = 0

    def process(self):
        try:
            expand_list = self._download()
            self._expand(expand_list)
            self._rename()

            # All done. Request UI update
            self.signal_finished.emit()
        except ExitException:
            # All done. Request UI update
            self.signal_aborted.emit()

        pass

    def _download(self):
        asset: OsmAsset
        to_expand = []

        # checking assets dir exists before using it
        if not os.path.isdir(AppConfig.DIR_ASSETS):
            os.makedirs(AppConfig.DIR_ASSETS)

        # processing all files
        for index, asset in enumerate(self.download_list):
            if not self._already_downloaded(asset):
                res = self._download_asset(asset)
            else:
                res = True

            # to be expanded later
            to_expand.append(asset)

            # request UI update
            self.signal_file_download_progress.emit(asset, asset.c_size if res else -1)

            # abort request
            if self.early_exit:
                return

        return to_expand

    @staticmethod
    def _already_downloaded(asset: OsmAsset):
        if asset is None:
            return True

        path = os.path.join(AppConfig.DIR_ASSETS, asset.filename)
        # is file already there ?
        if not os.path.isfile(path):
            return False

        # comparing watchlist and remote timestamps
        # is existing file incomplete ?
        if asset.remote_ts > asset.local_ts and \
                int(os.path.getsize(path)) != int(asset.c_size):
            return False

        # no need to download
        return True

    def _download_asset(self, asset: OsmAsset):
        success = True

        # opening connection to resource
        for retry in range(5):
            try:
                r = requests.get(asset.url, headers=USER_AGENT,
                                proxies=urllib.request.getproxies(),
                                verify=AppConfig.SSL_VERIFY,
                                stream=True)
            except requests.exceptions.ConnectionError:
                r = None
            # is request success ?
            if r and r.status_code != requests.codes.ok:
                break
            
            time.sleep(1)

        # has one try succeeded ?
        if r is None or r.status_code != requests.codes.ok:
            #TODO : add failed status to item
            return False

        # downloading

        # Set configuration
        block_size = 1024
        file = os.path.join(AppConfig.DIR_ASSETS, asset.filename)

        ref_time = time.time()
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
                    cur_time = time.time()
                    if cur_time - ref_time > 1:  # 1s
                        # print(f"{ref_time} > {cur_time} = {cur_time-ref_time}s :\t{ref_bytes} > {pos} = {pos-ref_bytes} Bytes \t{(pos-ref_bytes)//(cur_time-ref_time)}B/s")
                        speed = ((pos - ref_bytes) / ((cur_time - ref_time)))
                        # updating UI
                        self.signal_bandwidth.emit(int(speed))
                        # updating ref for next time
                        ref_time = cur_time
                        ref_bytes = pos

                    # update UI
                    self.signal_file_download_progress.emit(asset, pos)

                    # abort request
                    if self.early_exit:
                        raise ExitException()

        except requests.exceptions.Timeout as e:
            # Maybe set up for a retry, or continue in a retry loop
            success = False
            self.statusbar.showMessage("ERROR: server timeout")
            print("ERROR: " + str(e))
        except requests.exceptions.TooManyRedirects as e:
            # Tell the user their URL was bad and try a different one
            success = False
            self.statusbar.showMessage("ERROR: too many redirects")
            print("ERROR: " + str(e))
        except requests.exceptions.RequestException:
            # catastrophic error, try next
            success = False
            pass

        return success

    def _expand(self, expand_list: List[OsmAsset]):
        if not expand_list:
            # nothing to expand
            return

        # checking output dir exists before using it
        if not os.path.isdir(AppConfig.DIR_OUTPUT):
            os.makedirs(AppConfig.DIR_OUTPUT)

        # downloaded size
        for item in expand_list:
            self.total_size += item.c_size

        # unzipping all files
        for asset in expand_list:
            # request UI update
            self.signal_file_expand_progress.emit(asset, False, False)

            # expanding
            # ....
            success = self._expand_asset(asset)

            # request UI update
            self.signal_file_expand_progress.emit(asset, True, not success)

            # abort request
            if self.early_exit:
                raise ExitException()
        pass

    @staticmethod
    def _expand_asset(asset: OsmAsset):
        asset_dir = os.path.join(AppConfig.DIR_OUTPUT, asset.output_dir)

        # creating asset output dir
        if not os.path.isdir(asset_dir):
            os.makedirs(asset_dir)

        if asset.filename.endswith(".zip"):
            try:
                # zip file handler
                zip_path = os.path.join(AppConfig.DIR_ASSETS, asset.filename)
                asset_zip = zipfile.ZipFile(zip_path)

                # list available files in the container
                # print(asset_zip.namelist())

                asset_zip.extractall(asset_dir)
            except zipfile.BadZipFile:
                return False
        else:
            try:
                # copying file
                shutil.copyfile(os.path.join(AppConfig.DIR_ASSETS, asset.filename),
                                os.path.join(asset_dir, asset.filename))
            except shutil.Error:
                return False

        return True

    @staticmethod
    def _rename():
        to_rename = glob.glob(AppConfig.DIR_OUTPUT + "*_2.*")
        to_rename_subdir = glob.glob(AppConfig.DIR_OUTPUT + "*/*_2.*")
        to_rename.extend(to_rename_subdir)

        for file in to_rename:
            target_name = file.replace("_2.", ".")

            # cleaning previous existing target
            if os.path.isfile(target_name):
                os.remove(target_name)

            os.rename(file, target_name)
