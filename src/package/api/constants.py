REMOTE = "https://download.osmand.net"
# INDEX_FILE="/get_indexes?gzip"
INDEX_FILE = "/get_indexes"
DOWNLOAD_FILE = "/download?file="

INDEX_HEAD = "osmand_regions"

CACHE_DIR = "cache/"
CACHE_FILENAME = "indexes.xml"
CACHE_ONLY = False
WATCH_LIST = "watch.list"

NOAREA_CATS = ["fonts", "depth", "voice"]
NOAREA_NAME = "N/A"

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
