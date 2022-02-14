# Open Street Map - Assets Downloader (CLI &amp; GUI)

OsmAnd Android application has a free version with a limitation on maps updates.
This tool was created to run a CRON job on a specific set of map and feed the latest 
maps when available.

## Usage

### Command Line Interface
````
Usage: osmad_cli.py [OPTIONS] COMMAND [ARGS]...

Options:
  --version                      Show the version and exit.
  -cd, --cache-dir DIRECTORY     Path where to find cache files
  -dd, --download-dir DIRECTORY  Path where to download and extract assets
  --help                         Show this message and exit.

Commands:
  list     List assets available in cache
  refresh  Refresh cache from OpenStreet Map server
  update   Download/Update assets based on watch list
  watch    Watch list management
````
### Graphical User Interface
![](./res/screenshot.png)

## HowTo

### Prepare env

Prepare a Vitrual environment for your project and install requirements
```
$ python -m venv venv
```

Switch to your venv 
* on linux `$ source venv/bin/activate`
* on Windows `$ .\venv\Scripts\activate.bat`

Install dependencies
```
$ python -m pip install -r requirements_cli.txt
$ python -m pip install -r requirements_gui.txt
```

### Build

#### GUI
Before launching the application, you must build UIs and Resource file with the following commands
##### Generate UIs
	$ pyuic5 gui/main.ui -o gui/main.py
	$ pyuic5 gui/about.ui -o gui/about.py

##### Generate Res file
	$ pyrcc5 osmad_res.qrc -o osmad_res_rc.py


### Create native executable

In order to create a native executable (easier to deploy), you should proceed as following :

1. Install dependencies `$ python -m pip install pyinstaller`
2. Generate self contained binary


#### CLI
```
$ pyinstaller osmad_cli.spec
...
$ dist\osmad_cli.exe
```

#### GUI
```
$ pyinstaller osmad_gui.spec
...
$ dist\osmad_gui.exe
```