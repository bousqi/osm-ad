import shutil
import unittest

import osmm_data
from osmm_data import *
from collections import OrderedDict


class test_osmmaps_dl(unittest.TestCase):
    REF_CATEGORIES = ['depth', 'fonts', 'hillshade', 'map', 'road_map', 'slope', 'srtm_map', 'travel', 'voice',
                      'wikimap', 'wikivoyage']

    def setUp(self) -> None:
        print("----------------------------------")
        # testing from serve will overwrite cache
        shutil.copy(CACHE_FILENAME, CACHE_FILENAME+".backup")
        pass

    def tearDown(self) -> None:
        shutil.copy(CACHE_FILENAME+".backup", CACHE_FILENAME)
        pass

    def test_from_cache(self):
        osmm_data.CACHE_ONLY = True
        self._test_procedure()
        pass

    def test_from_server(self):
        osmm_data.CACHE_ONLY = False
        self._test_procedure()
        pass

    def _test_procedure(self):
        if osmm_data.CACHE_ONLY:
            print("[INFO] - feeding from cache file")
        else:
            print("[INFO] - feeding from Server")

        # feeding indexes
        indexes = osmm_FeedIndex()
        assert indexes is not None
        assert type(indexes) is OrderedDict

        assert len(indexes) == 1
        assert "osmand_regions" in indexes
        assert len(indexes["osmand_regions"]) > 10

        # converting to internal format
        indexes = osmm_ProcessIndexes(indexes)
        assert indexes is not None
        assert type(indexes) is list

        count = len(indexes)
        assert count > 7000
        print("[INFO] - {} items in indexes".format(count))

        # extracting categories
        categories = osmm_GetCategories(indexes)
        assert categories is not None
        for cat in self.REF_CATEGORIES:
            assert cat in categories
        assert len(categories) >= len(self.REF_CATEGORIES)
        print("[INFO] - {:>4} categories : {}".format(len(categories), categories))

        # getting file list with filter applied
        # more files without filters than filtering on France
        sublist = osmm_GetFiles(indexes, "map", "France")
        count = len(sublist)
        assert count > 1

        sublist = osmm_GetFiles(indexes, "map")
        assert len(sublist)
        assert len(sublist) > count

        # checking that all categories are giving files to download
        for cat in self.REF_CATEGORIES:
            assert len(osmm_GetFiles(indexes, cat)) > 0

        # testing setDownload attributes
        assert len(osmm_GetDownloads(indexes)) == 0
        target1 = osmm_GetFiles(indexes, "map", "France")[2]
        target2 = osmm_GetFiles(indexes, "fonts")[1]
        target3 = osmm_GetFiles(indexes, "slope")[10]

        osmm_SetDownload(indexes, target1)
        osmm_SetDownload(indexes, target2)
        osmm_SetDownload(indexes, target3)
        ddl_list = osmm_GetDownloads(indexes)
        assert len(ddl_list) == 3

        ddl_names = [item["@name"] for item in ddl_list]
        assert target1 in ddl_names
        assert target2 in ddl_names
        assert target3 in ddl_names

        osmm_UnsetDownload(indexes, target3)
        ddl_list = osmm_GetDownloads(indexes)
        assert len(ddl_list) == 2

        ddl_names = [item["@name"] for item in ddl_list]
        assert target1 in ddl_names
        assert target2 in ddl_names
        assert target3 not in ddl_names

        pass


if __name__ == '__main__':
    unittest.main()
