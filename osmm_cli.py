import osmm_data
from osmm_data import *
from collections import OrderedDict
import click

g_indexes = None

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
    for item in indexes:
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


@click.command()
@click.option('--feed',  '-f', "feed", is_flag=True, type=bool, help="Silent feed of assets (updates local cache)")
@click.option('--list',  '-l', "lists", type=click.Choice(['ALL', 'AREAS', 'TYPES'], case_sensitive=False), default='ALL', help="List assets available")
@click.option('--type', '-t', "item_type", type=str, default=None, help="List only assets part of this type")
@click.option('--area', '-a', "item_area", type=str, default=None, help="List only assets part of this area")
@click.option('--date', '-d', "asset", type=str, default=None, help="Retrieve date update for specified asset")
@click.option('--cache', '-c', "from_cache", is_flag=True, type=bool, help="Use cached file rather than online server")
@click.option('--verbose', '-v', "verbose", is_flag=True, type=bool, help="Verbose mode")
@click.pass_context
def main(ctx, lists, item_type, item_area, asset, from_cache, feed, verbose):
    global g_indexes

    # nothing to do ?
    if not lists and not from_cache and not silent:
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

    if asset is not None:
        cli_dump_date(osmm_GetItem(g_indexes, asset))
        return

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


if __name__ == '__main__':
    main()

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
