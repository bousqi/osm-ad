import glob
import os.path
import shutil
import urllib.request
import zipfile
from pathlib import Path

import click
import requests
from tqdm import *

from package.api import constants
from package.api.constants import *
from package.api.osm_assets import OsmAssets

osm_assets = OsmAssets()
g_order = None

ASSETS_DIR = "assets/"
OUTPUT_DIR = "out/"
USER_AGENT = {'User-agent': 'OsmAnd'}

CLI_VERSION = "0.9.5"

'''
TODO list :
'''

# --------------------------------------------------------------------------


def cli_print_header():
    print("{:^10} | {:^9} | {:^10} | {}".format("Type", "Size", "Date", "Name"))
    print("{:>10} | {:>9} | {} | {}".format("-"*10, "-"*9, "-"*10, "-"*100, ))


def cli_print_item(item):
    print("{:>10} | {:>6} MB | {} | {}".format(item.type, item.e_size//1024//1024, item.remote_date, item.name))


def cli_dump(assets):
    cli_print_header()

    if g_order is not None:
        sorted_assets = [assets[key] for key in assets.keys()]
        if g_order == 'name':
            sorted_assets = sorted(sorted_assets, key=lambda k: k.name)
        elif g_order == 'size':
            sorted_assets = sorted(sorted_assets, key=lambda k: float(k.e_size))
        elif g_order == 'date':
            sorted_assets = sorted(sorted_assets, key=lambda k: k.remote_ts)
    else:
        sorted_assets = [assets[key] for key in assets.keys()]

    # going through items
    for item in sorted_assets:
        cli_print_item(item)

    print("\nDisplayed {} items among {}".format(len(sorted_assets), len(assets)))


def cli_dump_areas(assets):
    countries = assets.countries()
    print("{:>4} items : {}".format(len(countries), countries))


def cli_dump_types(assets):
    categories = assets.categories()
    print("{:>4} items : {}".format(len(categories), categories))


def cli_dump_date(item):
    if item is not None:
        print("{}".format(item.remote_date))
        return 0
    else:
        return 1


def _already_downloaded(item):
    if item is None:
        return True

    # comparing watchlist and remote timestamps
    if item.remote_ts > item.local_ts:
        return False

    path = ASSETS_DIR + item.name
    # is file already there ?
    if not os.path.isfile(path):
        return False

    # is existing file incomplete ?
    if int(os.path.getsize(path)) != int(item.c_size):
        return False

    # no need to download
    return True


def cli_download(assets_list, no_prog):
    if not assets_list:
        print("Nothing to download.")
        return

    print("Processing download queue : {} item(s)".format(len(assets_list)))

    # checking assets dir exists before using it
    if not os.path.isdir(ASSETS_DIR):
        Path(ASSETS_DIR).mkdir(parents=True, exist_ok=True)

    # tracking new items
    new_indexes = []
    for index, item in enumerate(assets_list):
        # item to download ?
        if _already_downloaded(item):
            print("{:>2}/{:>2} - {:<50} - NO_UPDATE".format(index+1, len(assets_list), item.filename))
            continue

        # to download !

        # Getting file size
        # r = requests.head(url)
        # file_size = int(r.headers.get('content-length', 0))
        file_size = int(item.c_size)

        # requesting file
        # giving 3 tries to get the file
        r = None
        for retry in range(3):
            try:
                r = requests.get(item.url, headers=USER_AGENT,
                                 proxies=urllib.request.getproxies(), verify=CFG_SSL_VERIFY,
                                 stream=True)
                # click.echo(item.url)
            except requests.exceptions.ConnectionError:
                r = None

            if r and r.status_code == requests.codes.ok:
                break

            click.echo("{:>2}/{:>2} - {:<50} - Retry {}".format(index+1, len(assets_list), item.filename, retry+1))

        # has one try succeeded ?
        if r is None or r.status_code != requests.codes.ok:
            click.echo("{:>2}/{:>2} - {:<50} - ERROR 404, not found".format(index+1, len(assets_list), item.filename))
            click.echo("{} > {}".format(" "*58, item.url))
            continue

        # added to list of downloaded
        item.downloaded()
        new_indexes.append(item)

        # Set configuration
        block_size = 1024
        initial_pos = 0
        mode = 'wb'
        file = ASSETS_DIR + item.filename

        try:
            # creating output file
            with open(file, mode) as f:
                # creating progress bar
                with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024,
                          desc="{:>2}/{:>2} - {:<50}".format(index+1, len(assets_list), item.filename),
                          initial=initial_pos, miniters=1, dynamic_ncols=True) as pbar:
                    # getting stream chunks to write
                    for chunk in r.iter_content(32 * block_size):
                        f.write(chunk)
                        if not no_prog:
                            pbar.update(len(chunk))

                    if no_prog:
                        # only one update at the end
                        pbar.update(file_size)

        except requests.exceptions.Timeout as e:
            # Maybe set up for a retry, or continue in a retry loop
            click.echo("ERROR: " + str(e))
        except requests.exceptions.TooManyRedirects as e:
            # Tell the user their URL was bad and try a different one
            click.echo("ERROR: " + str(e))
        except requests.exceptions.RequestException:
            # catastrophic error, try next
            pass

    return new_indexes


def cli_expand(indexes):
    if indexes is None:
        click.echo("Nothing to Expand/Copy.")
        return

    # checking output dir exists before using it
    if not os.path.isdir(OUTPUT_DIR):
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # expanding
    print("\nExpanding/Copying : {} item(s)".format(len(indexes)))
    for index, item in enumerate(indexes):
        asset_dir = OUTPUT_DIR + item.output_dir

        # creating asset output dir
        if not os.path.isdir(asset_dir):
            Path(asset_dir).mkdir(parents=True, exist_ok=True)

        asset_filename = item.name
        print("{:>2}/{:>2} : {} in {}".format(index+1, len(indexes), asset_filename, asset_dir))

        if asset_filename.endswith(".zip"):
            try:
                # zip file handler
                asset_zip = zipfile.ZipFile(ASSETS_DIR + asset_filename)

                # list available files in the container
                # print(asset_zip.namelist())

                asset_zip.extractall(asset_dir)
            except zipfile.BadZipFile:
                click.echo("ERROR: Corrupted/Incomplete Zipfile")
        else:
            # copying file
            shutil.copyfile(ASSETS_DIR+asset_filename, asset_dir+asset_filename)

    # renaming
    to_rename = glob.glob(OUTPUT_DIR + "*_2.*")
    to_rename_subdir = glob.glob(OUTPUT_DIR + "*/*_2.*")
    to_rename.extend(to_rename_subdir)

    click.echo("\nUpdating names : {} item(s)".format(len(to_rename)))
    # click.echo(to_rename)

    for file in to_rename:
        dest_name = file.replace("_2.", ".")

        if os.path.isfile(dest_name):
            os.remove(dest_name)

        os.rename(file, dest_name)

# --------------------------------------------------------------------------


@click.group()
@click.version_option(CLI_VERSION, prog_name="OpenStreetMap asset downloader")
@click.option('--cache-dir',  '-cd', "cache_dir", type=click.Path(dir_okay=True, file_okay=False, readable=True, writable=True, exists=False), default=None, help="Path where to find cache files")
@click.option('--download-dir', '-dd', "ddl_dir", type=click.Path(dir_okay=True, file_okay=False, readable=True, writable=True, exists=False), default=None, help="Path where to download and extract assets")
def cli(cache_dir, ddl_dir,):
    global ASSETS_DIR, OUTPUT_DIR
    global osm_assets

    if cache_dir:
        constants.CACHE_DIR = os.path.join(cache_dir, '')

    if ddl_dir:
        OUTPUT_DIR = os.path.join(ddl_dir, OUTPUT_DIR)
        ASSETS_DIR = os.path.join(ddl_dir, ASSETS_DIR)

    osm_assets.load_index(from_cache=True)


@cli.command()  # @cli, not @click!
@click.option('--list',  '-l', "list", is_flag=True, type=bool, help="List all assets to watch")
@click.option('--clear', '-c', "clear", is_flag=True, type=bool, help="Remove all assets from watch list")
@click.option('--add',   '-a', "wadd", type=str, default=None, help="Add specified asset to watch list")
@click.option('--del',   '-d', "wdel", type=str, default=None, help="Remove specified asset from watch list")
def watch(wlist, clear, wadd, wdel):
    """Watch list management"""
    global osm_assets

    # reading list
    osm_assets.load_watch_list()
    watchlist = osm_assets.watch_list()

    if wlist or (not wlist and not clear and not wadd and not wdel):
        if len(watchlist) == 0:
            print("List is empty. Use --add")
            return

        # dumping list

        for index, item in enumerate(watchlist):
            print("{:>2}/{} - {}".format(index+1, len(watchlist), item.name))
    elif clear:
        # clearing list
        for item in watchlist:
            osm_assets[item].watchme = False
        osm_assets.save_watch_list()
        print("List cleared !")
    else:
        if wadd is not None:
            if [item for item in watchlist if item.name == wadd]:
                click.echo("ERROR: {} already in watchlist. Use watch -l command to check".format(wadd))
                return 1
            # refresh index from server
            osm_assets.load_index(from_cache=False)
            osm_assets.load_watch_list()
            if wadd not in osm_assets:
                click.echo("ERROR: {} is not a valid asset. Use list command to check".format(wadd))
                return 1
            osm_assets[wadd].watchme = True
            osm_assets.save_watch_list()
            click.echo("DONE : 1 item added to watch list, {} total".format(len(watchlist)))
        elif wdel is not None:
            print(watchlist)
            if not [item for item in watchlist if item.name == wdel]:
                click.echo("ERROR: {} not in watchlist. Use watch -l command to check".format(wadd))
                return 1
            osm_assets[wdel].watchme = False
            osm_assets.save_watch_list()
            click.echo("DONE : 1 item removed from watch list, {} left".format(len(watchlist)))


@cli.command()  # @cli, not @click!
@click.option('--no-progress', '-n', "no_prog", is_flag=True, type=bool, help="Disable progress bar during download")
def update(no_prog):
    """Download/Update assets based on watch list"""
    global osm_assets

    # feeding assets
    osm_assets.load_index(False)

    # reads watch list from file & apply
    osm_assets.load_watch_list()

    # download items
    dl_list = osm_assets.watch_list()
    dl_list = cli_download(dl_list, no_prog)

    # saving all downloaded files in watch list
    osm_assets.save_watch_list()

    # decompress assets
    cli_expand(dl_list)

    if len(dl_list):
        click.echo("\nDone !")


@cli.command()  # @cli, not @click!
def refresh():
    """Refresh cache from OpenStreet Map server"""
    global osm_assets

    click.echo("< Feeding from server >")
    osm_assets.load_index(from_cache=False)


@cli.command()  # @cli, not @click!
@click.option('--cache', '-c', "from_cache", is_flag=True, type=bool, help="Use cached file rather than online server")
@click.option('--list',  '-l', "lists", type=click.Choice(['ALL', 'AREAS', 'TYPES'], case_sensitive=False), default='ALL', help="List assets available")
@click.option('--type', '-t', "item_type", type=str, default=None, help="List only assets part of this type")
@click.option('--area', '-a', "item_area", type=str, default=None, help="List only assets part of this area")
@click.option('--date', '-d', "item_name", type=str, default=None, help="Retrieve date update for specified asset")
@click.option('--sort', '-s', "sort_order", type=click.Choice(['name', 'size', 'date'], case_sensitive=False), default='name', help="Order to use for list display")
def list(from_cache, lists, item_type, item_area, item_name, sort_order):
    """List assets available in cache"""
    global osm_assets
    global g_order

    if from_cache:
        print("< Feeding from cache >")
    else:
        print("< Feeding from server >")
    osm_assets.load_index(from_cache=from_cache)

    if item_name is not None:
        return cli_dump_date(osm_assets[item_name])

    # sharing display order
#    if item_type is None and item_area is None:
#        sort_order = None
    g_order = sort_order

    # applying filters
    filtered_assets = osm_assets
    if item_type is not None:
        filtered_assets = filtered_assets.filter(cat=item_type)
    if item_area is not None:
        filtered_assets = filtered_assets.filter(country=item_area)

    # display results
    if lists == 'ALL':
        cli_dump(filtered_assets)
    elif lists == 'AREAS':
        cli_dump_areas(filtered_assets)
    elif lists == 'TYPES':
        cli_dump_types(filtered_assets)

    return 0


if __name__ == '__main__':
    cli()
