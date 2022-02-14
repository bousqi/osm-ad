import os
import shutil
import unittest
import urllib

import requests

from package.api.constants import *
from package.api.osm_assets import OsmAssets

class testOsmAsset_API(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("----------------------------------")
        # testing from server will overwrite cache
        cls.cache_file = os.path.join(CACHE_DIR, CACHE_FILENAME)
        cls.backup_file = os.path.join(CACHE_DIR, CACHE_FILENAME) + ".backup"
        if os.path.exists(cls.cache_file):
            shutil.copy(cls.cache_file, cls.backup_file)
            os.remove(cls.cache_file)

    @classmethod
    def tearDownClass(cls) -> None:
        if os.path.exists(cls.backup_file):
            shutil.copy(cls.backup_file, cls.cache_file)

    def setUp(self) -> None:
        self.assets = OsmAssets()
        self.assets.load_index(True)

    def test_1_load_index(self):
        self.assets = OsmAssets()

        # feeding indexes from cache (not available)
        self.assets.load_index(True)
        assert len(self.assets) == 0

        # feeding indexes from server
        self.assets.load_index(False)
        count = len(self.assets)
        assert count > 0

        # feeding indexes from cache (available)
        self.assets.load_index(True)
        assert len(self.assets) == count

        assert count > 7000
        print("[INFO] - {} items in indexes".format(count))

    def test_2_categories(self):
        # extracting categories
        categories = self.assets.categories()
        assert categories is not None
        for cat in TYPE_ATTRIB.keys():
            assert cat in categories
        assert len(categories) >= len(TYPE_ATTRIB.keys())
        print("[INFO] - {:>4} categories : {}".format(len(categories), categories))

    def test_3_filters(self):
        # getting file list with filter applied
        # more files without filters than filtering on France
        sublist = self.assets.get_files("map", "France")
        count = len(sublist)
        assert count > 1

        sublist = self.assets.get_files("map")
        assert len(sublist)
        assert len(sublist) > count

        # checking that all categories are giving files to download
        for cat in TYPE_ATTRIB:
            assert len(self.assets.get_files(cat)) > 0

    def test_4_updatable(self):
        # testing setDownload attributes
        assert len(self.assets.updatable_list()) == 0
        target1 = self.assets.get_files("map", "France")[2]
        target2 = self.assets.get_files("fonts")[1]
        target3 = self.assets.get_files("slope")[10]

        self.assets[target1].watchme = True
        self.assets[target2].watchme = True
        self.assets[target3].watchme = True
        ddl_list = self.assets.updatable_list()
        assert len(ddl_list) == 3

        ddl_names = [item.name for item in ddl_list]
        assert target1 in ddl_names
        assert target2 in ddl_names
        assert target3 in ddl_names

        # adding non existing item to downlonad
        assert self.assets.get("DOESNOTEXISTS") is None

        # removing one item
        self.assets[target3].watchme = False
        ddl_list = self.assets.updatable_list()
        assert len(ddl_list) == 2

        ddl_names = [item.name for item in ddl_list]
        assert target1 in ddl_names
        assert target2 in ddl_names
        assert target3 not in ddl_names

    def test_5_urls_check(self):
        for key in TYPE_ATTRIB:
            sub_list = self.assets.filter(cat=key)
            first_key = next(iter(sub_list))
            asset = sub_list[first_key]
            # print(asset.url)
            r = requests.head(asset.url, proxies=urllib.request.getproxies(), verify=CFG_SSL_VERIFY)
            assert r.status_code == 200

    def test_6_watch_list(self):
        # remove existing watch list
        wl_file = os.path.join(CACHE_DIR, WATCH_LIST)
        if os.path.exists(wl_file):
            os.remove(wl_file)

        # load emtpy wl
        self.assets.load_watch_list()

        # check none are watched
        assert len(self.assets.watch_list()) == 0

        # adding three items
        target1 = self.assets.get_files("map", "France")[2]
        target2 = self.assets.get_files("fonts")[1]
        target3 = self.assets.get_files("slope")[10]

        self.assets[target1].watchme = True
        self.assets[target2].watchme = True
        self.assets[target3].watchme = True

        # check three are watch
        assert len(self.assets.watch_list()) == 3

        # removing one
        self.assets[target3].watchme = False
        assert len(self.assets.watch_list()) == 2

        # saving list
        self.assets.save_watch_list()

        # removed all
        self.assets[target1].watchme = False
        self.assets[target2].watchme = False
        assert len(self.assets.watch_list()) == 0

        # loading list
        self.assets.load_watch_list()
        assert len(self.assets.watch_list()) == 2

    def test_7_updatable(self):
        # reset assets
        self.assets.load_index(True)
        assert not self.assets.updatable_list()

        # reload watch list (2 items)
        self.assets.load_watch_list()
        up_list = self.assets.updatable_list()
        assert len(up_list) == 2

        # fake more recent local files
        for item in up_list:
            item.downloaded()
        # saving list
        self.assets.save_watch_list()

        # no more updates
        assert not self.assets.updatable_list()

        # reset assets
        self.assets.load_index(True)
        assert not self.assets.updatable_list()

        # reload watch list (2 items)
        self.assets.load_watch_list()
        # no more updates
        assert not self.assets.updatable_list()


if __name__ == '__main__':
    unittest.main()
