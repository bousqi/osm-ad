# https://download.osmand.net/get_indexes?gzip
# https://download.osmand.net/download?event=2&file=France_new-aquitaine_vienne_europe_2.obf.zip

from collections import OrderedDict
import requests
import xmltodict

REMOTE = "https://download.osmand.net"
# INDEX_FILE="/get_indexes?gzip"
INDEX_FILE = "/get_indexes"

CACHE_FILENAME = "cache/indexes.xml"
CACHE_ONLY = True
# CACHE_ONLY = False

NOAREA_CATS = ["fonts", "depth", "voice"]
FILE_PREFIXES = ["Hillshade", "Slope"]

def osmm_FeedIndex():

    if CACHE_ONLY:
        with open(CACHE_FILENAME, "rb") as f_index:
            dict_data = xmltodict.parse(f_index.read())
    else:
        r = requests.get(REMOTE + INDEX_FILE)
        with open(CACHE_FILENAME, "wb") as f_index:
            f_index.write(r.content)
        dict_data = xmltodict.parse(r.content)

    return dict_data

def osmm_ProcessIndexes(indexes):
    osmmIndexes = list()

    # osmmIndexes = {category : "TBC" for category in indexes["osmand_regions"] if not category.startswith("@") }
    indexes = indexes["osmand_regions"]
    for cat in indexes.keys():
        # processing one category & skipping fields
        if not cat.startswith("@"):
            # category is named cat
            sub_indexes = indexes[cat]
            if type(sub_indexes) is OrderedDict:
                item = sub_indexes
                # item["@type"] = cat
                item["@country"] = osmm_ExtractArea(item["@name"], item["@type"])
                osmmIndexes.append(item)
            if type(sub_indexes) is list:
                # list of OrderedDict to be parse
                for item in sub_indexes:
                    # item["@type"] = cat
                    item["@country"] = osmm_ExtractArea(item["@name"], item["@type"])
                    osmmIndexes.append(item)

    return osmmIndexes

def osmm_ExtractArea(filename, cat):
    # no country for depth category
    if cat in NOAREA_CATS:
        return "N/A"

    # filtering prefixes
    for prefix in FILE_PREFIXES:
        if filename.startswith(prefix+"_"):
            filename = filename.replace(prefix+"_", "")
    return filename.split("_")[0]

def osmm_GetCategories(indexes):
    return sorted(set([item["@type"] for item in indexes]))

def osmm_GetCountries(indexes, cat):
    filtered_indexes = [item for item in indexes if item["@type"] == cat]
    return sorted(set([item["@country"] for item in filtered_indexes]))

def osmm_GetFiles(indexes, cat, country = None):
    filtered_indexes = osmm_FilterIndex(indexes, cat, country)
    return sorted(set([item["@name"] for item in filtered_indexes]))

def osmm_FilterIndex(indexes, cat = None, country = None, toget = None):
    if cat is None and country is None and toget is None:
        return indexes

    filtered_indexes = list()
    for item in indexes:
        to_add = True
        if not cat is None and item["@type"] != cat:
            to_add = False
        if not country is None and item["@country"] != country:
            to_add = False
        if not toget is None:
            if not "@ossm_get" in item:
                # can't compare, not to be added
                to_add = False
            elif item["@ossm_get"] != toget:
                # comparing
                to_add = False
        if to_add:
            filtered_indexes.append(item)

    return filtered_indexes

def osmm_SetDownload(indexes, filename, state = True):
    for item in indexes:
        if item["@name"] == filename:
            item["@ossm_get"] = state
def osmm_UnsetDownload(indexes, filename):
    osmm_SetDownload(indexes, filename, False)

def osmm_GetDownloads(indexes):
    return osmm_FilterIndex(indexes, toget=True)
