from tqdm import *
import click, requests, datetime, os.path
import osmm_data

g_indexes = None
g_order = None

OUTPUT_DIR = "./assets/"

'''
TODO list :
 - Commands to create :
    * Add item to watch list
    * View items in watch list
    * Download & Extract items
    * Clear watch list
 - Write watch list to a file
 - Read watch list from file
 - Extract item, and remove _2 suffix
'''

# --------------------------------------------------------------------------


def cli_print_header():
    print("{:^10} | {:^9} | {:^10} | {}".format("Type", "Size", "Date", "Name"))
    print("{:>10} | {:>9} | {} | {}".format("-"*10, "-"*9, "-"*10, "-"*100, ))


def cli_print_item(item):
    print("{:>10} | {:>6} MB | {} | {}".format(item["@type"], item["@size"], item["@date"], item["@name"]))


def cli_dump(indexes):
    cli_print_header()

    sorted_indexes = indexes
    if g_order is not None:
        if g_order == 'name':
            sorted_indexes = sorted(indexes, key=lambda d: d["@"+g_order])
        elif g_order == 'size':
            sorted_indexes = sorted(indexes, key=lambda d: float(d["@"+g_order]))
        elif g_order == 'date':
            sorted_indexes = sorted(indexes, key=lambda d: d["@"+g_order])

    # going through items
    for item in sorted_indexes:
        cli_print_item(item)

    print("\nDisplayed {} items among {}".format(len(indexes), len(g_indexes)))


def cli_dump_areas(indexes):
    countries = osmm_data.osmm_GetCountries(indexes)
    print("{:>4} items : {}".format(len(countries), countries))


def cli_dump_types(indexes):
    categories = osmm_data.osmm_GetCategories(indexes)
    print("{:>4} items : {}".format(len(categories), categories))


def cli_dump_date(item):
    if item is not None:
        print("{}".format(item["@date"]))
        return 0
    else:
        return 1


def _already_downloaded(item):
    if item is None:
        return True

    filename = OUTPUT_DIR + item["@name"]

    # is file already there ?
    if not os.path.isfile(filename):
        return False

    # is there an update for this file
    item_date = item["@date"].split('.')
    ts = datetime.datetime(int(item_date[2]), int(item_date[1]), int(item_date[0]), 0, 0).timestamp()
    if os.path.getctime(filename) < ts:
        return False

    # is existing file incomplete ?
    if int(os.path.getsize(filename)) != int(item["@containerSize"]):
        return False

    # no need to download
    return True


def cli_download(indexes):
    if indexes is None:
        print("Nothing to download.")
        return

    print("Processing download queue : {} item(s)".format(len(indexes)))

    # checking assets dir exists before using it
    if not os.path.isdir(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    for index, item in enumerate(indexes):
        filename = item["@name"]

        # item to download ?
        if _already_downloaded(item):
            print("{}/{} - {:<40} - SKIPPED".format(index+1, len(indexes), filename))
            continue

        url = osmm_data.REMOTE + osmm_data.DOWNLOAD_FILE + filename

        # Getting file size
        # r = requests.head(url)
        # file_size = int(r.headers.get('content-length', 0))
        file_size = int(item["@containerSize"])

        # requesting file
        r = requests.get(url, stream=True)

        # Set configuration
        block_size = 1024
        initial_pos = 0
        mode = 'wb'
        file = OUTPUT_DIR + filename

        # creating output file
        with open(file, mode) as f:
            # creating progress bar
            with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024,
                      desc="{}/{} - {:<40}".format(index+1, len(indexes), filename),
                      initial=initial_pos, miniters=1, dynamic_ncols=True) as pbar:
                # getting stream chunks to write
                for chunk in r.iter_content(32 * block_size):
                    f.write(chunk)
                    pbar.update(len(chunk))


# --------------------------------------------------------------------------


@click.group()
def cli():
    pass


@cli.command()  # @cli, not @click!
@click.option('--list',  '-l', "list", is_flag=True, type=bool, help="List all assets to watch")
@click.option('--clear', '-c', "clear", is_flag=True, type=bool, help="Remove all assets from watch list")
@click.option('--add',   '-a', "wadd", type=str, default=None, help="Add specified asset to watch list")
@click.option('--del',   '-d', "wdel", type=str, default=None, help="Remove specified asset from watch list")
def watch(list, clear, wadd, wdel):
    """Watch list management"""
    click.echo('Watch list')


@cli.command()  # @cli, not @click!
def update():
    """Download/Update assets based on watch list"""

    global g_indexes
    g_indexes = osmm_data.osmm_ProcessIndexes(osmm_data.osmm_FeedIndex())
    osmm_data.osmm_SetDownload(g_indexes, "France_new-aquitaine_europe_2.obf.zip")
    osmm_data.osmm_SetDownload(g_indexes, "France_auvergne-rhone-alpes_allier_europe_2.obf.zip")
    osmm_data.osmm_SetDownload(g_indexes, "da_0.voice.zip")
    osmm_data.osmm_SetDownload(g_indexes, "NotoSans-Korean.otf.zip")
    # osmm_UnsetDownload(g_indexes, "France_auvergne-rhone-alpes_allier_europe_2.obf.zip")
    sublist = osmm_data.osmm_GetDownloads(g_indexes)
    cli_download(sublist)



@cli.command()  # @cli, not @click!
def refresh():
    """Refresh cache from OpenStreet Map server"""
    osmm_data.CACHE_ONLY = False
    click.echo("< Feeding from server >")
    osmm_data.osmm_FeedIndex()


@cli.command()  # @cli, not @click!
@click.option('--cache', '-c', "from_cache", is_flag=True, type=bool, help="Use cached file rather than online server")
@click.option('--list',  '-l', "lists", type=click.Choice(['ALL', 'AREAS', 'TYPES'], case_sensitive=False), default='ALL', help="List assets available")
@click.option('--type', '-t', "item_type", type=str, default=None, help="List only assets part of this type")
@click.option('--area', '-a', "item_area", type=str, default=None, help="List only assets part of this area")
@click.option('--date', '-d', "item_name", type=str, default=None, help="Retrieve date update for specified asset")
@click.option('--sort', '-s', "sort_order", type=click.Choice(['name', 'size', 'date'], case_sensitive=False), default='name', help="Order to use for list display")
def list(from_cache, lists, item_type, item_area, item_name, sort_order):
    """List assets available in cache"""
    global g_indexes
    global g_order

    osmm_data.CACHE_ONLY = from_cache
    if from_cache:
        print("< Feeding from cache >")
    else:
        print("< Feeding from server >")
    g_indexes = osmm_data.osmm_ProcessIndexes(osmm_data.osmm_FeedIndex())

    if item_name is not None:
        return cli_dump_date(osmm_data.osmm_GetItem(g_indexes, item_name))

    # sharing display order
    if item_type is None and item_area is None:
        sort_order = None
    g_order = sort_order

    # applying filters
    sub_indexes = g_indexes
    if item_type is not None:
        sub_indexes = osmm_data.osmm_FilterIndex(sub_indexes, cat=item_type)
    if item_area is not None:
        sub_indexes = osmm_data.osmm_FilterIndex(sub_indexes, country=item_area)

    # display results
    if lists == 'ALL':
        cli_dump(sub_indexes)
    elif lists == 'AREAS':
        cli_dump_areas(sub_indexes)
    elif lists == 'TYPES':
        cli_dump_types(sub_indexes)

    return 0


if __name__ == '__main__':
    cli()