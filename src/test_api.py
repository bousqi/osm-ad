import os
import shutil
import unittest

from package.api.constants import *
from package.api.osm_assets import OsmAssets

class testOsmAsset_API(unittest.TestCase):

    def setUp(self) -> None:
        print("----------------------------------")
        # testing from server will overwrite cache
        self.cache_file = os.path.join(CACHE_DIR, CACHE_FILENAME)
        self.backup_file = os.path.join(CACHE_DIR, CACHE_FILENAME) + ".backup"
        if os.path.exists(self.cache_file):
            shutil.copy(self.cache_file, self.backup_file)

    def tearDown(self) -> None:
        if os.path.exists(self.backup_file):
            shutil.copy(self.backup_file, self.cache_file)

    # def test_from_server(self):
    #     assets = OsmAssets(from_cache=False)
    #     self._test_procedure(assets)

    def test_from_cache(self):
        assets = OsmAssets(from_cache=True)
        self._test_procedure(assets)

    def _test_procedure(self, assets):
        if assets.from_cache:
            print("[INFO] - feeding from cache file")
        else:
            print("[INFO] - feeding from Server")

        # feeding indexes
        assets.load_index()
        assert len(assets) > 10

        count = len(assets)
        assert count > 7000
        print("[INFO] - {} items in indexes".format(count))

        # extracting categories
        categories = assets.categories()
        assert categories is not None
        for cat in TYPE_ATTRIB.keys():
            assert cat in categories
        assert len(categories) >= len(TYPE_ATTRIB.keys())
        print("[INFO] - {:>4} categories : {}".format(len(categories), categories))

        # getting file list with filter applied
        # more files without filters than filtering on France
        sublist = assets.get_files("map", "France")
        count = len(sublist)
        assert count > 1

        sublist = assets.get_files("map")
        assert len(sublist)
        assert len(sublist) > count

        # checking that all categories are giving files to download
        for cat in TYPE_ATTRIB:
            assert len(assets.get_files(cat)) > 0

        # testing setDownload attributes
        assert len(assets.updatable_list()) == 0
        target1 = assets.get_files("map", "France")[2]
        target2 = assets.get_files("fonts")[1]
        target3 = assets.get_files("slope")[10]

        assets[target1].watchme = True
        assets[target2].watchme = True
        assets[target3].watchme = True
        ddl_list = assets.updatable_list()
        assert len(ddl_list) == 3

        ddl_names = [item.name for item in ddl_list]
        assert target1 in ddl_names
        assert target2 in ddl_names
        assert target3 in ddl_names

        # adding non existing item to downlonad
        assert assets.get("DOESNOTEXISTS") is None

        # removing one item
        assets[target3].watchme = False
        ddl_list = assets.updatable_list()
        assert len(ddl_list) == 2

        # ddl_names = [item["@name"] for item in ddl_list]
        # assert target1 in ddl_names
        # assert target2 in ddl_names
        # assert target3 not in ddl_names
        #


if __name__ == '__main__':
    unittest.main()
