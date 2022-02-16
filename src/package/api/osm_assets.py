import json
import os
import urllib.request
import xml
from collections import OrderedDict

import requests
import xmltodict
from typing import List, Dict

from package.api.constants import *
from package.api.osm_asset import OsmAsset


class OsmAssets(dict):
    def __init__(self):
        super().__init__()

    ''' FEEDING ASSETS '''
    def load_index(self, from_cache=False):
        # removing all previous entries
        self.clear()

        cache_file = os.path.join(CACHE_DIR, CACHE_FILENAME)

        # checking cache dir exists before using it
        if not os.path.isdir(CACHE_DIR):
            os.mkdir(CACHE_DIR)

        # feeding from internet, if requested
        if not from_cache:
            try:
                r = requests.get(REMOTE + INDEX_FILE, proxies=urllib.request.getproxies(), verify=CFG_SSL_VERIFY)
                with open(CACHE_DIR + CACHE_FILENAME, "wb") as f_index:
                    f_index.write(r.content)
            except:
                print("ERROR: Failed to feed indexes. Using cache")

        # is cache index present
        if not os.path.exists(cache_file):
            return

        # reading index file
        try:
            with open(cache_file, "r") as f_index:
                dict_data = xmltodict.parse(f_index.read())
        except xml.parsers.expat.ExpatError:
            return

        indexes = dict_data.get(INDEX_HEAD)

        for cat in indexes.keys():
            # processing one category & skipping fields
            if not cat.startswith("@"):
                # category is named cat
                sub_indexes = indexes[cat]
                if type(sub_indexes) is OrderedDict:
                    item = sub_indexes
                    # item["@type"] = cat
                    asset = OsmAsset(item)
                    self[asset.filename] = asset
                if type(sub_indexes) is list:
                    # list of OrderedDict to be parsed
                    for item in sub_indexes:
                        # item["@type"] = cat
                        asset = OsmAsset(item)
                        self[asset.filename] = asset

    ''' DICT MANAGEMENT '''
    def categories(self):
        return sorted(set([self[key].type for key in self.keys()]))

    def countries(self, cat=None):
        filtered_indexes = self.filter(cat=cat)
        return sorted(set([filtered_indexes[key].area for key in filtered_indexes.keys()]))

    def filter(self, cat=None, country=None, updatable=None) -> Dict[str, OsmAsset]:
        # no filters
        if cat is None and country is None and updatable is None:
            return self

        # current dict is empty
        if len(self) == 0:
            return self

        filtered_assets = OsmAssets()
        for key in self.keys():
            item = self[key]
            to_add = True
            if cat and item.type != cat:
                to_add = False
            if country and item.area != country:
                to_add = False
            if updatable and item.updatable != updatable:
                to_add = False
            if to_add:
                filtered_assets[key] = item

        return filtered_assets

    def get_files(self, cat, country=None):
        filtered_indexes = self.filter(cat=cat, country=country)
        return sorted(set([filtered_indexes[key].name for key in filtered_indexes]))

    def updatable_list(self) -> List[OsmAsset]:
        # returns a list of OsmAsset having an update pending
        return [self[key] for key in self.keys() if self[key].updatable]

    ''' WATCH LIST MANAGEMENT '''
    def load_watch_list(self):
        wl_file = os.path.join(CACHE_DIR, WATCH_LIST)

        # is the file there ?
        if not os.path.exists(wl_file):
            return

        # file is there
        with open(wl_file, "r") as f:
            watches = json.load(f)

        for watch in watches:
            asset = self.get(watch[0])
            if asset:
                asset.watchme = True
                asset.local_ts = int(watch[1])

    def save_watch_list(self):
        watches = []
        for asset in self.watch_list():
            watches.append((asset.filename, str(asset.local_ts)))

        wl_file = os.path.join(CACHE_DIR, WATCH_LIST)
        with open(wl_file, "w") as f:
            json.dump(watches, f, indent=4)

    def watch_list(self) -> List[OsmAsset]:
        return [self[key] for key in self.keys() if self[key].watchme]

