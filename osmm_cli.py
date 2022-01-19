import osmm_data
from osmm_data import *
from collections import OrderedDict
import click


def cli_help(ctx, param, value):
    if value is False:
        return
    click.echo(ctx.get_help())
    ctx.exit()


def cli_dump(indexes):
    print("TODO")
def cli_dump_areas(indexes):
    print("TODO-AREAS")
def cli_dump_types(indexes):
    print("TODO-TYPES")


@click.command()
@click.option('--list',  '-l', "lists", type=click.Choice(['ALL', 'AREAS', 'TYPES'], case_sensitive=False), default='ALL', help="List assets available")
@click.option('--cache', '-c', "from_cache", is_flag=True, type=bool, help="Use cached file rather than online server")
@click.pass_context
def main(ctx, lists, from_cache):
    if not lists and not from_cache:
        cli_help(ctx, None, value=True)

    osmm_data.CACHE_ONLY = from_cache
    indexes = osmm_ProcessIndexes(osmm_data.osmm_FeedIndex())

    if lists == 'ALL':
        cli_dump(indexes)
    elif lists == 'AREAS':
        cli_dump_areas(indexes)
    elif lists == 'TYPES':
        cli_dump_types(indexes)


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
