# https://download.osmand.net/get_indexes?gzip
# https://download.osmand.net/download?event=2&file=France_new-aquitaine_vienne_europe_2.obf.zip
import os.path
from collections import OrderedDict
import requests
import xmltodict

REMOTE = "https://download.osmand.net"
# INDEX_FILE="/get_indexes?gzip"
INDEX_FILE = "/get_indexes"
DOWNLOAD_FILE = "/download?file="

CACHE_DIR = "cache/"
CACHE_FILENAME = "indexes.xml"
CACHE_ONLY = True
# CACHE_ONLY = False
WATCH_LIST = "watch.list"

NOAREA_CATS = ["fonts", "depth", "voice"]
FILE_PREFIXES = ["Hillshade", "Slope"]

TYPE_ATTRIB = {
    "depth":     {"out": "",         "suffix" : "&inapp=depth"},
    "fonts":     {"out": "fonts/",   "suffix" : "&fonts=yes"},
    "hillshade": {"out": "tiles/",   "suffix" : "&hillshade=yes"},
    "map":       {"out": "",         "suffix" : ""},
    "road_map":  {"out": "roads/",   "suffix" : "&road=yes"},
    "slope":     {"out": "tiles/",   "suffix" : "&slope=yes"},
    "srtm_map":  {"out": "srtm/",    "suffix" : "&srtmcountry=yes"},
    "travel":    {"out": "travel/",  "suffix" : "&wikivoyage=yes"},
    "voice":     {"out": "voice/",   "suffix" : ""},
    "wikimap":   {"out": "wiki/",    "suffix" : "&wiki=yes"},
    "wikivoyage":{"out": "travel/",  "suffix" : "&wikivoyage=yes"},
}


def osmm_FeedIndex():
    global CACHE_ONLY

    # checking cache dir exists before using it
    if not os.path.isdir(CACHE_DIR):
        os.mkdir(CACHE_DIR)

    # first try
    if not CACHE_ONLY:
        try:
            r = requests.get(REMOTE + INDEX_FILE)
            dict_data = xmltodict.parse(r.content)
            with open(CACHE_DIR + CACHE_FILENAME, "wb") as f_index:
                f_index.write(r.content)
        except:
            print("ERROR: Failed to feed indexes. Using cache")
            CACHE_ONLY = True

    # plan b ?
    if CACHE_ONLY:
        with open(CACHE_DIR + CACHE_FILENAME, "rb") as f_index:
            dict_data = xmltodict.parse(f_index.read())

    return dict_data


def osmm_ProcessIndexes(indexes):
    osmmIndexes = list()

    if indexes is None:
        return None

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


def osmm_OutputDir(item):
    cat = item["@type"]
    if cat not in TYPE_ATTRIB:
        return ""

    # path depends on type
    path = TYPE_ATTRIB[cat]["out"]

    # for voice type, subfolder required
    if cat == "voice":
        path = path + item["@name"].replace("_0.voice.zip", "/")

    return path


def osmm_GetCategories(indexes):
    return sorted(set([item["@type"] for item in indexes]))


def osmm_GetCountries(indexes, cat = None):
    if cat is not None:
        filtered_indexes = [item for item in indexes if item["@type"] == cat]
    else:
        filtered_indexes = indexes
    return sorted(set([item["@country"] for item in filtered_indexes]))


def osmm_GetItem(indexes, filename):
    if filename is None or indexes is None:
        return None

    # looking
    for item in indexes:
        if item["@name"] == filename:
            return item
    # not found
    return None


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
            item["@osmm_get"] = state


def osmm_UnsetDownload(indexes, filename):
    osmm_SetDownload(indexes, filename, False)


def osmm_GetDownloads(indexes):
    return osmm_FilterIndex(indexes, toget=True)


def osmm_GetDownloadURL(item):
    cat = item["@type"]
    url = REMOTE + DOWNLOAD_FILE + item["@name"] + TYPE_ATTRIB[cat]["suffix"]

    return url

def osmm_WatchRead():
    wlist=[]
    try:
        with open(CACHE_DIR + WATCH_LIST, 'r') as wfile:
            wlist = wfile.read().splitlines()
    except FileNotFoundError:
        pass

    return wlist


def osmm_WatchWrite(wlist):
    with open(CACHE_DIR + WATCH_LIST, 'w') as wfile:
        wfile.writelines("%s\n" % l for l in wlist)
