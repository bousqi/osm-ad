# OsmAnd Maps downloader (CLI &amp; GUI)

OsmAnd Android application has a free version with a limitation on maps updates.
This tool was created to run a CRON job on a specific set of map and feed the latest 
maps when available.


## HowTo
### Create native executable
```
$ python setup.py install
$ python setup.py py2exe
...
$ dist\osmm_cli.exe
```