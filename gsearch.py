#!/usr/bin/env python

import BeautifulSoup
import urllib2
import cookielib
import os
import time
import urllib
import urlparse

homeurl          = "http://www.google.%(tld)s/"
searchurl        = "http://www.google.%(tld)s/search?hl=%(lang)s&q=%(query)s&btnG=Google+Search"

# Cookie jar. Stored at the user's home folder.
home_folder = os.getenv('HOME')
if not home_folder:
    home_folder = os.getenv('USERHOME')
    if not home_folder:
        home_folder = '.'   # Use the current folder on error.
cookie_jar = cookielib.LWPCookieJar(
                            os.path.join(home_folder, '.google-cookie'))
try:
    cookie_jar.load()
except Exception:
    pass

# Request the given URL and return the response page, using the cookie jar.
def get_page(url):
    """
    Request the given URL and return the response page, using the cookie jar.

    @type  url: str
    @param url: URL to retrieve.

    @rtype:  str
    @return: Web page retrieved for the given URL.

    @raise IOError: An exception is raised on error.
    @raise urllib2.URLError: An exception is raised on error.
    @raise urllib2.HTTPError: An exception is raised on error.
    """
    request = urllib2.Request(url)
    request.add_header('User-Agent',
                       # 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)')
                       'Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11')
    cookie_jar.add_cookie_header(request)
    response = urllib2.urlopen(request)
    cookie_jar.extract_cookies(response, request)
    html = response.read()
    response.close()
    cookie_jar.save()
    return html

# Returns a generator that yields URLs.
def search(query, tld='com', lang='en', num=10, start=0, stop=None, pause=2.0):
    """
    Search the given query string using Google.

    @type  query: str
    @param query: Query string. Must NOT be url-encoded.

    @type  tld: str
    @param tld: Top level domain.

    @type  lang: str
    @param lang: Languaje.

    @type  num: int
    @param num: Number of results per page.

    @type  start: int
    @param start: First result to retrieve.

    @type  stop: int
    @param stop: Last result to retrieve.
        Use C{None} to keep searching forever.

    @type  pause: float
    @param pause: Lapse to wait between HTTP requests.
        A lapse too long will make the search slow, but a lapse too short may
        cause Google to block your IP. Your mileage may vary!

    @rtype:  generator
    @return: Generator (iterator) that yields found URLs. If the C{stop}
        parameter is C{None} the iterator will loop forever.
    """

    # Set of hashes for the results found.
    # This is used to avoid repeated results.
    hashes = set()

    # Prepare the search string.
    query = urllib.quote_plus(query)

    # Grab the cookie from the home page.
    get_page(homeurl % vars())

    # Prepare the URL of the first request.
    if num == 10:
        url = searchurl % vars()
    else:
        url = searchurl % vars()

    # Request the Google Search results page.
    html = get_page(url)

    soup = BeautifulSoup.BeautifulSoup(html)

    divs = soup.findAll('div')
    anchors = soup.findall('a')
    apr = None
    asu = None
    loc = None
    for i in divs:
        try:
            if i['class']=='answer_predicate':
                apr = i.contents[0]
            elif i['class']=='answer_subject':
                asu = i.contents[0]
        except KeyError:
            continue
    if not apr:
        for i in anchors:
            try:
                if 'maps.google.com/maps?' in i['href']:
                    q = ' '.join([j for j in i['href'].split("&") if j.startswith('q=')][0][2:].split('+'))
                    loc = q
                    break
            except KeyError:
                continue
    return apr, asu, loc



# When run as a script, take all arguments as a search query and run it.
if __name__ == "__main__":
    import sys
    query = ' '.join(sys.argv[1:])
    if query:
        print search(query, stop=20)
