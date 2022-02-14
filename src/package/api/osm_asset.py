from datetime import datetime

from package.api.constants import *


def extract_area(name, cat):
    # no country for depth category
    if cat in NOAREA_CATS:
        return NOAREA_NAME

    # filtering prefixes
    for prefix in FILE_PREFIXES:
        if name.startswith(prefix+"_"):
            name = name.replace(prefix+"_", "")
    return name.split("_")[0]


class OsmAsset:
    """
        type
        filename
        date
        compressed size
        extracted size

        description
        timestamp

        <region
        type="map"
        date="01.01.2022"
        size="0.6"
        targetsize="1.0"
        containerSize="652419"
        contentSize="1032469"
        description="Map, Roads, POI, Transport, Address data for Saint-pierre-and-miquelon northamerica"
        name="Saint-pierre-and-miquelon_northamerica_2.obf.zip"
        timestamp="1640995200000"/>
    """

    def __init__(self, item):
        self.type = item.get("@type")                       # type / category
        self.name = item.get("@name")                       # filename
        self.desc = item.get("@description")                # description
        self.remote_ts = int(item.get("@timestamp"))        # last remote update
        self.local_ts = int(0)                              # last local update
        self.c_size = int(item.get("@containerSize"))       # compressed size
        self.e_size = int(item.get("@contentSize"))         # expanded size

        # get local file date
        self.local_ts = 0

        # building implicit fields
        self.area = extract_area(self.name, self.type)      # geographical area
        self.watchme = False                                # is the file part of watch list
        self.url = REMOTE + DOWNLOAD_FILE + self.name + TYPE_ATTRIB[self.type]["suffix"]

    def __repr__(self):
        return "{:>10} | {:>6} MB | {} | {}".format(self.type, self.e_size//1024//1024, self.remote_date, self.name)

    def __str__(self):
        return self.name

    @property
    def remote_date(self):
        date = datetime.fromtimestamp(self.remote_ts//1000)
        return "{:>02}.{:>02}.{:>04}".format(date.day, date.month, date.year)

    @property
    def local_date(self):
        date = datetime.fromtimestamp(self.local_ts//1000)
        return "{:>02}.{:>02}.{:>04}".format(date.day, date.month, date.year)

    @property
    def filename(self):
        return self.name

    @property
    def output_dir(self):
        if self.type not in TYPE_ATTRIB:
            return ""

        # path depends on type
        path = TYPE_ATTRIB[self.type]["out"]

        # for voice type, subfolder required
        if self.type == "voice":
            path = path + self.name.replace("_0.voice.zip", "/")

        return path

    @property
    def updatable(self):
        return self.watchme and self.remote_ts > self.local_ts

    def downloaded(self):
        self.local_ts = self.remote_ts
