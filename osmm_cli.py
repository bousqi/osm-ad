from tqdm import *
import click, requests, datetime, os.path
import osmm_data

g_indexes = None
g_order = None
g_watchlist = []

ASSETS_DIR = "./assets/"
OUTPUT_DIR = "./out/"

'''
TODO list :
 - Extract item, 
    * remove _2 suffix
    * use appropriate subdir
'''

# --------------------------------------------------------------------------


def _assets_feed(from_cache = False):
    global g_indexes

    osmm_data.CACHE_ONLY = from_cache
    g_indexes = osmm_data.osmm_ProcessIndexes(osmm_data.osmm_FeedIndex())
    return g_indexes

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

    filename = ASSETS_DIR + item["@name"]

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


def _watch_read():
    global g_watchlist
    g_watchlist = osmm_data.osmm_WatchRead()


def _watch_write():
    global g_watchlist
    osmm_data.osmm_WatchWrite(g_watchlist)


def _watch_apply(indexes):
    global g_watchlist
    for name in g_watchlist:
        osmm_data.osmm_SetDownload(indexes, name)


def cli_download(indexes):
    if indexes is None:
        print("Nothing to download.")
        return

    print("Processing download queue : {} item(s)".format(len(indexes)))

    # checking assets dir exists before using it
    if not os.path.isdir(ASSETS_DIR):
        os.mkdir(ASSETS_DIR)

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
        file = ASSETS_DIR + filename

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


def cli_expand(indexes):
    if indexes is None:
        print("Nothing to download.")
        return

    # checking output dir exists before using it
    if not os.path.isdir(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    print("Expanding : {} item(s)".format(len(indexes)))
    for index, item in enumerate(indexes):
        print("{}/{} : {}".format(index+1, len(indexes), item["@name"]))


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
    global g_watchlist
    global g_indexes

    # reading list
    _watch_read()

    if list:
        if g_watchlist is None or len(g_watchlist) == 0:
            print("List is empty. Use --add")
            return

        # dumping list
        for index, item in enumerate(g_watchlist):
            print("{}/{} - {}".format(index+1, len(g_watchlist), item))
    elif clear:
        # clearing list
        g_watchlist = []
        _watch_write()
        print("List cleared !")
    else:
        if wadd is not None:
            if wadd in g_watchlist:
                click.echo("ERROR: {} already in watchlist. Use watch -l command to check".format(wadd))
                return 1
            _assets_feed(True)
            if osmm_data.osmm_GetItem(g_indexes, wadd) is None:
                click.echo("ERROR: {} is not a valid asset. Use list command to check".format(wadd))
                return 1
            g_watchlist.append(wadd)
            _watch_write()
            click.echo("DONE : 1 item added to watch list, {} total".format(len(g_watchlist)))
        elif wdel is not None:
            if wdel not in g_watchlist:
                click.echo("ERROR: {} not in watchlist. Use watch -l command to check".format(wadd))
                return 1
            g_watchlist.remove(wdel)
            _watch_write()
            click.echo("DONE : 1 item removed from watch list, {} left".format(len(g_watchlist)))


@cli.command()  # @cli, not @click!
def update():
    """Download/Update assets based on watch list"""

    # feeding assets
    indexes = _assets_feed()

    # reads watch list from file & apply
    _watch_read()
    _watch_apply(indexes)

    # download items
    dl_list = osmm_data.osmm_GetDownloads(indexes)
    cli_download(dl_list)

    # decompress assets
    cli_expand(dl_list)


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

    if from_cache:
        print("< Feeding from cache >")
    else:
        print("< Feeding from server >")
    _assets_feed(from_cache)

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