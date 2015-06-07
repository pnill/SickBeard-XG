# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.


import urllib
import httplib
import datetime

import sickbeard

from lib import MultipartPostHandler
import urllib2
import cookielib
try:
    import json
except ImportError:
    from lib import simplejson as json

from sickbeard.common import USER_AGENT
from sickbeard import logger
from sickbeard.exceptions import ex


def sendPack(pack):
    """
    Sends an XDLink to XG so XG knows where to connect and grab the pack needed
    """

    if sickbeard.XG_APIKEY != None:
        apikey = sickbeard.XG_APIKEY

    xdlink = pack.url.split('/')
    params = {}
    params["ApiKey"] = apikey
    params["Server"] = xdlink[0]
    params["Channel"] = xdlink[2]
    params["Bot"] = xdlink[3]
    params["PacketId"] = xdlink[4]
    params["PacketName"] = xdlink[5]

    url = sickbeard.XG_HOST + "api/1.0/parseXDCC"

    logger.log(u"Sending Pack to XG: %s" % pack.name)
    logger.log(u"Pack URL: " + url, logger.DEBUG)

    try:
        data = urllib.urlencode(params)
        request = urllib2.Request(url,data)
        request.add_header('Authorization', apikey)
        f = urllib2.urlopen(request)

    except urllib2.HTTPError, e:
        if(e.code == 401):
            logger.log(u"Unable to connecto XG: Bad API Key")
            logger.log(u"If the API key is good it's probably not enabled in XG")
            logger.log(u"Api Key:" + params["ApiKey"])
        else:
            logger.log(u"Unable to connect to XG: HTTPEror = " + str(e.code))

        return False

    except urllib2.URLError, e:
        logger.log(u"Unable to connect to XG: UrlError = " + str(e.reason))
        return False

    except urllib2.HTTPException, e:
        logger.log(u"Unable to connect to XG: HTTPException")
        return False

    except (EOFError, IOError), e:
        logger.log(u"Unable to connect to XG: " + ex(e), logger.ERROR)
        return False

    except httplib.InvalidURL, e:
        logger.log(u"Invalid XG host, check your config: " + ex(e), logger.ERROR)
        return False

    # this means we couldn't open the connection or something just as bad
    if f is None:
        logger.log(u"No data returned from XG, XDlink not sent", logger.ERROR)
        return False

    # if we opened the URL connection then read the result from SAB
    try:
        result = f.readlines()
    except Exception, e:
        logger.log(u"Error trying to get result from XG, XDlink not sent: " + ex(e), logger.ERROR)
        return False

    # SAB shouldn't return a blank result, this most likely (but not always) means that it timed out and didn't receive the NZB
    if len(result) == 0:
        logger.log(u"No data returned from XG, XDlink not sent", logger.ERROR)
        return False

    # massage the result a little bit
    sabText = result[0].strip()

    logger.log(u"Result text from XG: " + sabText, logger.DEBUG)

    # do some crude parsing of the result text to determine what SAB said
    if sabText == "ok":
        logger.log(u"Pack sent to XG successfully", logger.DEBUG)
        return True
    elif sabText == "Missing authentication":
        logger.log(u"Incorrect username/password sent to SAB, NZB not sent", logger.ERROR)
        return False
    else:
        logger.log(u"Unknown failure sending link to XG. Return text is: " + sabText, logger.ERROR)
        return False


def _checkSabResponse(f):
    try:
        result = f.readlines()
    except Exception, e:
        logger.log(u"Error trying to get result from SAB" + ex(e), logger.ERROR)
        return False, "Error from SAB"

    if len(result) == 0:
        logger.log(u"No data returned from SABnzbd, NZB not sent", logger.ERROR)
        return False, "No data from SAB"

    sabText = result[0].strip()
    sabJson = {}
    try:
        sabJson = json.loads(sabText)
    except ValueError, e:
        pass

    if sabText == "Missing authentication":
        logger.log(u"Incorrect username/password sent to SAB", logger.ERROR)
        return False, "Incorrect username/password sent to SAB"
    elif 'error' in sabJson:
        logger.log(sabJson['error'], logger.ERROR)
        return False, sabJson['error']
    else:
        return True, sabText


def _sabURLOpenSimple(url,apikey):
    try:
        request = urlib2.request(url)
        request.add_header('Authorization',apikey)
        f = urllib2.urlopen(request)

    except (EOFError, IOError), e:
        logger.log(u"Unable to connect to SAB: " + ex(e), logger.ERROR)
        return False, "Unable to connect"
    except httplib.InvalidURL, e:
        logger.log(u"Invalid SAB host, check your config: " + ex(e), logger.ERROR)
        return False, "Invalid SAB host"
    if f is None:
        logger.log(u"No data returned from SABnzbd", logger.ERROR)
        return False, "No data returned from SABnzbd"
    else:
        return True, f


def getSabAccesMethod(host=None, username=None, password=None, apikey=None):
    url = host + "api?mode=auth"

    result, f = _sabURLOpenSimple(url,apikey)
    if not result:
        return False, f

    result, sabText = _checkSabResponse(f)
    if not result:
        return False, sabText

    return True, sabText


def testAuthentication(host=None, username=None, password=None, apikey=None):
    """
    Sends a simple API request to XG to determine if the given connection information is connect

    apikey: The API key to provide to XG

    Returns: A tuple containing the success boolean and a message
    """

    url = host + "api/1.0/ApiTest" 
    
    logger.log(u"XG test URL: " + url, logger.DEBUG)
   

    result, f = _sabURLOpenSimple(url)
    if not result:
        return False, f

    try:
        result = f.readlines()
    except Exception, e:
        logger.log("Exception reading the result from XG")

    sabText = result[0].strip()

    logger.log(u"Result text from XG: " + sabText, logger.DEBUG)

    if sabText == "ok":
        logger.log(u"Connected to XG Successfully", logger.DEBUG)
        return True, "Success"
    else:
        return False, "Failed"
