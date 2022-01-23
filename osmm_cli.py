from tqdm import *
import click

from osmm_data import *

g_indexes = None
g_order = None

'''
TODO list :
 - Commands to create :
    * Add item to watch list
    * View items in watch list
    * Download & Extract items
    * Clear watch list
 - Download using requests and chunks by chunks
 - Write watch list to a file
 - Read watch list from file
 - Extract item, and remove _2 suffix
'''

def cli_help(ctx, param, value):
    if value is False:
        return
    click.echo(ctx.get_help())
    ctx.exit()


def cli_print_header():
    print("{:^10} | {:^9} | {:^10} | {}".format("Type", "Size", "Date", "Name"))
    print("{:>10} | {:>9} | {} | {}".format("-"*10, "-"*9, "-"*10, "-"*100, ))
def cli_print_item(item):
    print("{:>10} | {:>6} MB | {} | {}".format(item["@type"], item["@size"], item["@date"], item["@name"]))

def cli_dump(indexes):
    cli_print_header()

    if g_order == 'name':
        sorted_indexes = sorted(indexes, key=lambda d: d["@"+g_order])
    elif g_order == 'size':
        sorted_indexes = sorted(indexes, key=lambda d: float(d["@"+g_order]))
    elif g_order == 'date':
        sorted_indexes = sorted(indexes, key=lambda d: d["@"+g_order])
    else:
        sorted_indexes = indexes

    # going through items
    for item in sorted_indexes:
        cli_print_item(item)

    print("\nDisplayed {} items among {}".format(len(indexes), len(g_indexes)))

def cli_dump_areas(indexes):
    countries = osmm_GetCountries(indexes)
    print("{:>4} items : {}".format(len(countries), countries))

def cli_dump_types(indexes):
    categories = osmm_GetCategories(indexes)
    print("{:>4} items : {}".format(len(categories), categories))

def cli_dump_date(item):
    if item is not None:
        print("{}".format(item["@date"]))
        return 0
    else:
        return 1


def cli_download(indexes):
    if indexes is None:
        print("Nothing to download.")
        return

    print("Processing download queue : {} item(s)".format(len(indexes)))

    for index, item in enumerate(indexes):
        filename = item["@name"]
        url = REMOTE + DOWNLOAD_FILE + filename

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
        file = "assets/" + filename

        # creating output file
        with open(file, mode) as f:
            # creating progress bar
            with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024,
                      desc="{}/{} - {:<40}".format(index+1, len(indexes), filename),
                      initial=initial_pos, miniters=1, dynamic_ncols=True) as pbar:
                # getting stream chunks to write
                for chunk in r.iter_content(512 * block_size):
                    f.write(chunk)
                    pbar.update(len(chunk))

@click.command()
@click.option('--feed',  '-f', "feed", is_flag=True, type=bool, help="Silent feed of assets (updates local cache)")
@click.option('--cache', '-c', "from_cache", is_flag=True, type=bool, help="Use cached file rather than online server")
@click.option('--list',  '-l', "lists", type=click.Choice(['ALL', 'AREAS', 'TYPES'], case_sensitive=False), default='ALL', help="List assets available")
@click.option('--type', '-t', "item_type", type=str, default=None, help="List only assets part of this type")
@click.option('--area', '-a', "item_area", type=str, default=None, help="List only assets part of this area")
@click.option('--date', '-d', "item_name", type=str, default=None, help="Retrieve date update for specified asset")
@click.option('--sort', '-s', "sort_order", type=click.Choice(['name', 'size', 'date'], case_sensitive=False), default='name', help="Order to use for list display")
@click.option('--verbose', '-v', "verbose", is_flag=True, type=bool, help="Verbose mode")
@click.pass_context
def main(ctx, lists, item_type, item_area, item_name, from_cache, feed, sort_order, verbose):
    global g_indexes
    global g_order

    # nothing to do ?
    if not lists and not from_cache and not feed:
        cli_help(ctx, None, value=True)

    # requested to feed
    if feed:
        verbose = False
        from_cache = False

    # using cache or server ?
    osmm_data.CACHE_ONLY = from_cache
    if verbose:
        if from_cache:
            print("< Feeding from cache >")
        else:
            print("< Feeding from server >")
    g_indexes = osmm_ProcessIndexes(osmm_data.osmm_FeedIndex())

    if item_name is not None:
        return cli_dump_date(osmm_GetItem(g_indexes, item_name))

    # sharing display order
    if item_type is None and item_area is None:
        sort_order = None
    g_order = sort_order

    # applying filters
    sub_indexes = g_indexes
    if item_type is not None:
        sub_indexes = osmm_FilterIndex(sub_indexes, cat=item_type)
    if item_area is not None:
        sub_indexes = osmm_FilterIndex(sub_indexes, country=item_area)

    # display results
    if not feed:
        if lists == 'ALL':
            cli_dump(sub_indexes)
        elif lists == 'AREAS':
            cli_dump_areas(sub_indexes)
        elif lists == 'TYPES':
            cli_dump_types(sub_indexes)

    return 0

def test_ddl():
    g_indexes = osmm_ProcessIndexes(osmm_data.osmm_FeedIndex())
    osmm_SetDownload(g_indexes, "France_new-aquitaine_europe_2.obf.zip")
    osmm_SetDownload(g_indexes, "France_auvergne-rhone-alpes_allier_europe_2.obf.zip")
    osmm_SetDownload(g_indexes, "da_0.voice.zip")
    osmm_SetDownload(g_indexes, "NotoSans-Korean.otf.zip")
    # osmm_UnsetDownload(g_indexes, "France_auvergne-rhone-alpes_allier_europe_2.obf.zip")
    sublist = osmm_GetDownloads(g_indexes)
    cli_download(sublist)

if __name__ == '__main__':
    main()
    # test_ddl()

# @click.option('--message', '-m', "msg", type=str, help="Message to send")
# @click.option('--no-title', '-n', "no_title", is_flag=True, is_eager=True, help="No title to be added to message")
# @click.option('--title', '-t', "title", type=str, help="Partial title to display")
# @click.option('--full-title', '-T', "full_title", type=str, help="Title to display")
# @click.option('--dest', '-d', "dest", default=OWNER, type=int, help="User ID to talk to")
# @click.option('--file', '-f', "file", type=click.Path(file_okay=True, dir_okay=False, exists=True, readable=True),
#               help="File to be sent")
# @click.option('--input', '-i', "from_stdin", is_flag=True, is_eager=True,
#               help="Message must be read from standard input")
# @click.option('--list-bot', '-l', is_flag=True, callback=print_bots, expose_value=False, is_eager=True,
#               help="List bot available")
# @click.pass_context

#
#
# def dump_ossm_index(od_index):
#     od_index = od_index["osmand_regions"]
#     for key in od_index.keys():
#         print(key)
#         if not key.startswith("@"):
#             if type(od_index[key]) is OrderedDict:
#                 dump_ossm_item(od_index[key])
#             if type(od_index[key]) is list:
#                 dump_ossm_items(od_index[key])
#
#
# def dump_ossm_item(ossm_item):
#     pass
#     # print("\t{} - {:>6}MB : {}".format(ossm_item["@date"], ossm_item["@size"], ossm_item["@name"]))
#
#
# def dump_ossm_items(ossm_items):
#     for item in ossm_items:
#         dump_ossm_item(item)
#
# indexes = osmm_FeedIndex()
# dump_ossm_index(indexes)
# indexes = osmm_ProcessIndexes(indexes)
#
# print(len(indexes))
#
# categories = osmm_GetCategories(indexes)
# print("{:>4} items : {}".format(len(categories), categories))
#
# for cat in categories:
#     sublist = osmm_GetCountries(indexes, cat)
#     print("{:>4} items : {}".format(len(sublist), sublist))
#
# sublist = osmm_GetFiles(indexes, "map", "France")
# print("{:>4} items : {}".format(len(sublist), sublist))
#
# sublist = osmm_GetFiles(indexes, "map")
# print("{:>4} items : {}".format(len(sublist), sublist))
#
# sublist = osmm_GetFiles(indexes, "fonts")
# print("{:>4} items : {}".format(len(sublist), sublist))
#
# sublist = osmm_GetFiles(indexes, "voice")
# print("{:>4} items : {}".format(len(sublist), sublist))
#
# sublist = osmm_FilterIndex(indexes, "fonts")
# print("{:>4} items : {}".format(len(sublist), sublist))
#
# osmm_SetDownload(indexes, "France_auvergne-rhone-alpes_allier_europe_2.obf.zip")
# osmm_SetDownload(indexes, "da_0.voice.zip")
# osmm_SetDownload(indexes, "NotoSans-Korean.otf.zip")
# osmm_UnsetDownload(indexes, "France_auvergne-rhone-alpes_allier_europe_2.obf.zip")
# sublist = osmm_GetDownloads(indexes)
# print("{:>4} items : {}".format(len(sublist), sublist))
