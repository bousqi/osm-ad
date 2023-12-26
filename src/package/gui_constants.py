""" CONSTANTS """

COL_TYPE = 0
COL_NAME = 1
COL_DATE = 2
COL_COMP = 3
COL_SIZE = 4
COL_WTCH = 5
COL_UPDT = 6
COL_PROG = 7

USER_AGENT = {'User-agent': 'OsmAnd'}
RETRY_COUNT = 5

OSMAD_ABOUT_INFO_HTML = """
<h2><b>OpenStreetMap - Asset Downloader</b></h2>
<br />


<u>Purpose</u> : This application is a PoC that allows to list contents from OsmAnd 
server, download and extract them. Next you can those copy files onto your
mobile to get an always up to date maps in OsmAnd free app (free version allows
only 7 updates).<br />
  
<b>If you like OsmAnd, buy it.</b><br />
<br />

Powered by Python 3, PyQT 5<br />
<br />

Icons are provided freely by <a href="www.icons8.com">icon8</a> and <a href="www.flaticon.com">flaticon</a><br />
 
Maps are provided by <a href="www.osmand.net">OsmAnd</a>"""