#!/bin/bash

# URLS_LOC=cache/URLs.txt
URL_PREFIX="https://download.osmand.net/download?event=2&file="

function date2sec {
	dd=$(cut -d'.' -f 1 <<< $1)
	mm=$(cut -d'.' -f 2 <<< $1)
	yyyy=$(cut -d'.' -f 3 <<< $1)
	echo $(date -d "$yyyy-$mm-$dd" +%s)
}

# updating cache index
python3 osmm_cli.py -f

# clean previous
URLS_LOC=$(mktemp)

for f in assets/*; 
do
	asset_name=$(basename "$f")
	date_update=$(python3 osmm_cli.py -c -d "$asset_name")
	if [[ $? -eq 0 ]]; then
		date_ref=$(date -r $f +%d.%m.%Y)
		echo -n "$asset_name : $date_ref -> $date_update - "

		ds_update=$(date2sec $date_update)
		ds_ref=$(date2sec $date_ref)
		# compare update date with file date
		if [[ "$ds_update" -gt "$ds_ref" ]]; then
			echo "TO DOWNLOAD"
			# adding item to URLs to be downloaded
			echo "$URL_PREFIX$asset_name" >> $URLS_LOC
		else
			echo "SKIPPED"
		fi
	fi
done

if [[ $(cat $URLS_LOC | wc -l) -eq "0" ]];
then
	echo "No Updates"
else
	echo "Starting ARIA2...."
	aria2c -i $URLS_LOC -s6 -x10 -c --auto-file-renaming=false
fi

