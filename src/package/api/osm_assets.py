import os
from collections import OrderedDict

import requests
import xmltodict

from package.api.constants import *
from package.api.osm_asset import OsmAsset


class OsmAssets(dict):
    def __init__(self, from_cache=False):
        super().__init__()
        self.from_cache = from_cache

    def load_index(self):
        cache_file = os.path.join(CACHE_DIR, CACHE_FILENAME)

        # checking cache dir exists before using it
        if not os.path.isdir(CACHE_DIR):
            os.mkdir(CACHE_DIR)

        # feeding from internet, if requested
        if not self.from_cache:
            try:
                r = requests.get(REMOTE + INDEX_FILE)
                with open(CACHE_DIR + CACHE_FILENAME, "w") as f_index:
                    f_index.write(r.content)
            except:
                print("ERROR: Failed to feed indexes. Using cache")
                self.from_cache = True

        # is cache index present
        if not os.path.exists(cache_file):
            return

        # reading index file
        with open(cache_file, "r") as f_index:
            dict_data = xmltodict.parse(f_index.read())

        indexes = dict_data.get(INDEX_HEAD)
        assets = []

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
                    # list of OrderedDict to be parse
                    for item in sub_indexes:
                        # item["@type"] = cat
                        asset = OsmAsset(item)
                        self[asset.filename] = asset

    def load_watch_list(self):
        # TODO
        pass

    def save_watch_list(self):
        # TODO
        pass

    def updatable_list(self):
        # returns a list of OsmAsset having an update pending
        return [self[key] for key in self.keys() if self[key].updatable]

'''
    * load watch list
    * save watch list 
    * apply
    including last dld update
'''
