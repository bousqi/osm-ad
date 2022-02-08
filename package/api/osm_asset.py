import xmltodict

from constants import *


def extract_area(name, cat):
    # no country for depth category
    if cat in NOAREA_CATS:
        return NOAREA_NAME

    # filtering prefixes
    for prefix in FILE_PREFIXES:
        if name.startswith(prefix+"_"):
            name = name.replace(prefix+"_", "")
    return name.split("_")[0]

def get_assets():
	assets = []
	cache_file = os.path.join(CACHE_DIR, CACHE_FILENAME)

    # checking cache dir exists before using it
    if not os.path.isdir(CACHE_DIR):
        os.mkdir(CACHE_DIR)

	# feeding from internet, if requested
    if not CACHE_ONLY:
        try:
            r = requests.get(REMOTE + INDEX_FILE)
            with open(CACHE_DIR + CACHE_FILENAME, "w") as f_index:
                f_index.write(r.content)
        except:
            print("ERROR: Failed to feed indexes. Using cache")
            CACHE_ONLY = True

	# is cache index present
	if not os.path.exists(cache_file):
		return assets

	# reading index file
	with open(cache_file, "r") as f_index:
        dict_data = xmltodict.parse(f_index.read())

    indexes = indexes.get(INDEX_HEAD)

    for cat in indexes.keys():
    # processing one category & skipping fields
    if not cat.startswith("@"):
        # category is named cat
        sub_indexes = indexes[cat]
        if type(sub_indexes) is OrderedDict:
            item = sub_indexes
            # item["@type"] = cat
            assests.append(OsmAsset(item))
        if type(sub_indexes) is list:
            # list of OrderedDict to be parse
            for item in sub_indexes:
                # item["@type"] = cat
                assests.append(OsmAsset(item))

    return assests

class OsmAsset:
	'''
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

	'''

	def __init__(self, item):
		self.type = item.get("@type")
		self.name = item.get("@name")
		# TODO : convert to a real date 
		self.remote_ts = int(item.get("@timestamp"))
		self.c_size = item.get("@c_size")
		self.e_size = item.get("@e_size")

		# extracting area
		self.area = extract_area(self.name, self.type)

		# get local file date
		self.local_ts = 0

		# 
		self.watchme = False
		pass

	def __repr__(self):
	    print("{:>10} | {:>6} MB | {} | {}".format(self.type, self.size, self.date, self.name))

	def __str__(self):
		print(f"{self.name}")
		
	@property
	def url(self):
	    url = REMOTE + DOWNLOAD_FILE + self.name + TYPE_ATTRIB[self.type]["suffix"]
	    return url

	@property
	def update_available(self):
		return self.watchme and self.remote_ts > self.local_ts:
