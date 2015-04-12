try:
	import urllib.request as urllib2
except:
	import urllib2
import functools
try:
  import json
except ImportError:
  import simplejson as json
try:
	import urllib.parse as parse
except:
	import urllib as parse

import re
import sys

class cache(object):

  def __init__(self, fn):
    self.fn = fn
    self._cache = {}
    functools.update_wrapper(self, fn)

  def __call__(self, *args, **kwargs):
    key = str(args) + str(kwargs)
    if key in self._cache:
      ret = self._cache[key]
    else:
      ret = self._cache[key] = self.fn(*args, **kwargs)

    return ret

  def clear_cache(self):
    self._cache = {}

API_URL = 'http://en.wikipedia.org/w/api.php'
RATE_LIMIT = False
RATE_LIMIT_MIN_WAIT = None
RATE_LIMIT_LAST_CALL = None
USER_AGENT = 'wikipedia (https://github.com/goldsmith/Wikipedia/)'

def set_lang(prefix):
  '''
  Change the language of the API being requested.
  Set `prefix` to one of the two letter prefixes found on the `list of all Wikipedias <http://meta.wikimedia.org/wiki/List_of_Wikipedias>`_.

  After setting the language, the cache for ``search``, ``suggest``, and ``summary`` will be cleared.

  .. note:: Make sure you search for page titles in the language that you have set.
  '''
  global API_URL
  API_URL = 'http://' + prefix.lower() + '.wikipedia.org/w/api.php'

  for cached_func in (search, suggest, summary):
    cached_func.clear_cache()

def set_user_agent(user_agent_string):
  '''
  Set the User-Agent string to be used for all requests.

  Arguments:

  * user_agent_string - (string) a string specifying the User-Agent header
  '''
  global USER_AGENT
  USER_AGENT = user_agent_string

@cache
def search(query, results=10, suggestion=False):
  '''
  Do a Wikipedia search for `query`.

  Keyword arguments:

  * results - the maxmimum number of results returned
  * suggestion - if True, return results and suggestion (if any) in a tuple
  '''

  search_params = {
    'list': 'search',
    'srprop': '',
    'srlimit': results,
    'limit': results,
    'srsearch': query
  }
  if suggestion:
    search_params['srinfo'] = 'suggestion'

  raw_results = _wiki_request(search_params)

  if 'error' in raw_results:
    if raw_results['error']['info'] in ('HTTP request timed out.', 'Pool queue is full'):
      raise HTTPTimeoutError(query)
    else:
      raise WikipediaException(raw_results['error']['info'])

  search_results = (d['title'] for d in raw_results['query']['search'])

  if suggestion:
    if raw_results['query'].get('searchinfo'):
      return list(search_results), raw_results['query']['searchinfo']['suggestion']
    else:
      return list(search_results), None

  return list(search_results)

def _wiki_request(params):
  '''
  Make a request to the Wikipedia API using the given search parameters.
  Returns a parsed dict of the JSON response.
  '''
  global RATE_LIMIT_LAST_CALL
  global USER_AGENT

  params['format'] = 'json'
  if not 'action' in params:
    params['action'] = 'query'

  headers = {
    'User-Agent': USER_AGENT
  }

  if RATE_LIMIT and RATE_LIMIT_LAST_CALL and \
    RATE_LIMIT_LAST_CALL + RATE_LIMIT_MIN_WAIT > datetime.now():

    # it hasn't been long enough since the last API call
    # so wait until we're in the clear to make the request

    wait_time = (RATE_LIMIT_LAST_CALL + RATE_LIMIT_MIN_WAIT) - datetime.now()
    time.sleep(int(wait_time.total_seconds()))

  # r = requests.get(API_URL, params=params, headers=headers)
  if sys.version_info[0] == 2:
    r = json.loads(urllib2.urlopen(API_URL,parse.urlencode(params)).read().decode("utf-8"))
  else:
    r = json.loads(urllib2.urlopen(API_URL,bytes(parse.urlencode(params),'utf-8')).read().decode("utf-8"))

  if RATE_LIMIT:
    RATE_LIMIT_LAST_CALL = datetime.now()

  return r

@cache
def summary(title, sentences=0, chars=0, auto_suggest=True, redirect=True):
  '''
  Plain text summary of the page.

  .. note:: This is a convenience wrapper - auto_suggest and redirect are enabled by default

  Keyword arguments:

  * sentences - if set, return the first `sentences` sentences (can be no greater than 10).
  * chars - if set, return only the first `chars` characters (actual text returned may be slightly longer).
  * auto_suggest - let Wikipedia find a valid page title for the query
  * redirect - allow redirection without raising RedirectError
  '''

  # use auto_suggest and redirect to get the correct article
  # also, use page's error checking to raise DisambiguationError if necessary
  page_info = page(title, auto_suggest=auto_suggest, redirect=redirect)
  title = page_info.title
  print (title)
  pageid = page_info.pageid

  query_params = {
    'prop': 'extracts',
    'explaintext': '',
    'titles': title
  }

  if sentences:
    query_params['exsentences'] = sentences
  elif chars:
    query_params['exchars'] = chars
  else:
    query_params['exintro'] = ''

  request = _wiki_request(query_params)
  summary = request['query']['pages'][pageid]['extract']

  summary = re.sub(r'\([^)]*\)', '', summary)

  return [summary, page_info.url]


def page(title=None, pageid=None, auto_suggest=True, redirect=True, preload=False):
  '''
  Get a WikipediaPage object for the page with title `title` or the pageid
  `pageid` (mutually exclusive).

  Keyword arguments:

  * title - the title of the page to load
  * pageid - the numeric pageid of the page to load
  * auto_suggest - let Wikipedia find a valid page title for the query
  * redirect - allow redirection without raising RedirectError
  * preload - load content, summary, images, references, and links during initialization
  '''

  if title is not None:
    if auto_suggest:
      results, suggestion = search(title, results=1, suggestion=True)
      try:
        title = suggestion or results[0]
      except IndexError:
        # if there is no suggestion or search results, the page doesn't exist
        raise KeyError(title)
    return WikipediaPage(title, redirect=redirect, preload=preload)
  elif pageid is not None:
    return WikipediaPage(pageid=pageid, preload=preload)
  else:
    raise ValueError("Either a title or a pageid must be specified")

class WikipediaPage(object):
  '''
  Contains data from a Wikipedia page.
  Uses property methods to filter data from the raw HTML.
  '''

  def __init__(self, title=None, pageid=None, redirect=True, preload=False, original_title='', url=''):
    if title is not None:
      self.title = title
      self.original_title = original_title or title
    elif pageid is not None:
      self.pageid = pageid
    else:
      raise ValueError("Either a title or a pageid must be specified")

    self.__load(redirect=redirect, preload=preload)

    if preload:
      for prop in ('content', 'summary', 'images', 'references', 'links', 'sections'):
        getattr(self, prop)

  def __repr__(self):
    return stdout_encode(u'<WikipediaPage \'{}\'>'.format(self.title))

  def __eq__(self, other):
    try:
      return (
        self.pageid == other.pageid
        and self.title == other.title
        and self.url == other.url
      )
    except:
      return False

  def __load(self, redirect=True, preload=False):
    '''
    Load basic information from Wikipedia.
    Confirm that page exists and is not a disambiguation/redirect.

    Does not need to be called manually, should be called automatically during __init__.
    '''
    query_params = {
      'prop': 'info|pageprops',
      'inprop': 'url',
      'ppprop': 'disambiguation',
      'redirects': '',
    }
    if not getattr(self, 'pageid', None):
      query_params['titles'] = self.title
    else:
      query_params['pageids'] = self.pageid

    request = _wiki_request(query_params)

    query = request['query']

    pageid = list(query['pages'].keys())[0]
    page = query['pages'][pageid]
    url = page['fullurl']

    # missing is present if the page is missing
    if 'missing' in page:
      if hasattr(self, 'title'):
        raise KeyError(self.title)
      else:
        raise KeyError("pageid: "+str(self.pageid))

    # same thing for redirect, except it shows up in query instead of page for
    # whatever silly reason
    elif 'redirects' in query:
      if redirect:
        redirects = query['redirects'][0]

        if 'normalized' in query:
          normalized = query['normalized'][0]
          assert normalized['from'] == self.title, ODD_ERROR_MESSAGE

          from_title = normalized['to']

        else:
          from_title = self.title

        assert redirects['from'] == from_title, ODD_ERROR_MESSAGE

        # change the title and reload the whole object
        self.__init__(redirects['to'], redirect=redirect, preload=preload, url=url)

      else:
        raise RedirectError(getattr(self, 'title', page['title']))

    # since we only asked for disambiguation in ppprop,
    # if a pageprop is returned,
    # then the page must be a disambiguation page
    elif 'pageprops' in page:
      query_params = {
        'prop': 'revisions',
        'rvprop': 'content',
        'rvparse': '',
        'rvlimit': 1
      }
      if hasattr(self, 'pageid'):
        query_params['pageids'] = self.pageid
      else:
        query_params['titles'] = self.title
      request = _wiki_request(query_params)
      html = request['query']['pages'][pageid]['revisions'][0]['*']

      lis = BeautifulSoup(html).find_all('li')
      filtered_lis = [li for li in lis if not 'tocsection' in ''.join(li.get('class', []))]
      may_refer_to = [li.a.get_text() for li in filtered_lis if li.a]

      raise DisambiguationError(getattr(self, 'title', page['title']), may_refer_to)

    else:
      self.pageid = pageid
      self.title = page['title']
      self.url = page['fullurl']

if __name__=="__main__":
	print (search('obama'))
	print (summary('obama',sentences=1))