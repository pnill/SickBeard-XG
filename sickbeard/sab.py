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


def sendNZB(nzb):
    """
    Sends an NZB to SABnzbd via the API.

    nzb: The NZBSearchResult object to send to SAB
    """

    xdlink = nzb.url.split('/')
    logger.log(u"IRC Server: "+xdlink[0])
    logger.log(u"Channel: "+xdlink[2])
    logger.log(u"Bot: "+xdlink[3])
    logger.log(u"PacketId: "+xdlink[4])
    logger.log(u"PacketName: "+xdlink[5])

    #params = {}
    #params['Server'] = xdlink[0]
    #params['Channel'] = xdlink[2]
    #params['Bot'] = xdlink[3]
    #params['PacketId'] = xdlink[4]
    #params['PacketName'] = xdlink[5]
    
    parameters = {'ApiKey' : 'ba663f95-6375-4f9c-ba92-e472a8fa661e','Server' : xdlink[0], 'Channel' : xdlink[2], 'Bot' : xdlink[3], 'PacketId' : xdlink[4], 'PacketName' : xdlink[5] }
    
    url = sickbeard.SAB_HOST + "api/1.0/parseXDCC"

    logger.log(u"Sending XDLink to XG: %s" % nzb.name)
    logger.log(u"XDlink: " + url, logger.DEBUG)

    try:
        data = urllib.urlencode(parameters)
        request = urllib2.Request(url,data)
        request.add_header('Authorization', 'ba663f95-6375-4f9c-ba92-e472a8fa661e')
        f = urllib2.urlopen(request)


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
        logger.log(u"XDlink sent to XG successfully", logger.DEBUG)
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


def _sabURLOpenSimple(url):
    try:
        f = urllib.urlopen(url)
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

    result, f = _sabURLOpenSimple(url)
    if not result:
        return False, f

    result, sabText = _checkSabResponse(f)
    if not result:
        return False, sabText

    return True, sabText


def testAuthentication(host=None, username=None, password=None, apikey=None):
    """
    Sends a simple API request to SAB to determine if the given connection information is connect

    host: The host where SAB is running (incl port)
    username: The username to use for the HTTP request
    password: The password to use for the HTTP request
    apikey: The API key to provide to SAB

    Returns: A tuple containing the success boolean and a message
    """

    # build up the URL parameters
    params = {}
    params['mode'] = 'queue'
    params['output'] = 'json'
    params['ma_username'] = username
    params['ma_password'] = password
    params['apikey'] = apikey
    url = host + "api?" + urllib.urlencode(params)

    # send the test request
    logger.log(u"SABnzbd test URL: " + url, logger.DEBUG)
    result, f = _sabURLOpenSimple(url)
    if not result:
        return False, f

    # check the result and determine if it's good or not
    result, sabText = _checkSabResponse(f)
    if not result:
        return False, sabText

    return True, "Success"
