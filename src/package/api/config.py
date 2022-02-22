import os
import json
from pathlib import Path

CFG_DEFAULT_SSL_VERIFY = True
CFG_DEFAULT_DIR_ASSETS = "assets/"
CFG_DEFAULT_DIR_OUTPUT = "out/"

CFG_DIR = os.path.join(Path.home(), ".osm-ad")
CFG_FILE = os.path.join(CFG_DIR, "config.json")
CFG_DEBUG = True


class AppConfig:
    DIR_ASSETS = CFG_DEFAULT_DIR_ASSETS
    DIR_OUTPUT = CFG_DEFAULT_DIR_OUTPUT
    SSL_VERIFY = CFG_DEFAULT_SSL_VERIFY

    @staticmethod
    def load():
        if not os.path.exists(CFG_FILE):
            # no config available, creation initial config
            AppConfig.save()

        with open(CFG_FILE, "r") as fc:
            config = json.load(fc)
            AppConfig.DIR_ASSETS = config.get("dir_asset")
            AppConfig.DIR_OUTPUT = config.get("dir_output")
            AppConfig.SSL_VERIFY = config.get("ssl_verify")

    @staticmethod
    def save():
        config = {"dir_asset": AppConfig.DIR_ASSETS,
                  "dir_output": AppConfig.DIR_OUTPUT,
                  "ssl_verify": AppConfig.SSL_VERIFY}

        # checking config dir exists
        if not os.path.exists(os.path.dirname(CFG_FILE)):
            os.mkdir(os.path.dirname(CFG_FILE))

        # saving config file
        with open(CFG_FILE, "w") as fc:
            json.dump(config, fc, indent=4)

