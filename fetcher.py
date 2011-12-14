# coding: utf-8
import simplejson
import threading
import urllib2

class Fetcher:
  BASE_URL = 'https://www.googleapis.com/plus/v1/'
  TIMEOUT = 3600 # sec
  FETCHER_COUNT = 1000

  def __init__(self, user_id, key, storage):
    self._user_id = user_id
    self._key = key
    self._storage = storage
    self._event = threading.Event()
    self._event.clear()
    self._fetch_count = 0
    self._fetch_counts = {}
    self._fetch_activity_id = None
    self._fetch_etag = None

    self._thread = threading.Thread(
      target=self._fetcher_thread, name="Fetcher")
    self._should_run = True
    self._thread.start()

  def _activities_url(self):
    request = urllib2.Request(self.BASE_URL + 'people/' + self._user_id +
                              '/activities/public?num=100&key=' + self._key)
    if self._fetch_etag:
      request.add_header('If-None-Match', self._fetch_etag)
    return request

  def _paged_activities_url(self, page_token):
    return urllib2.Request(
      self.BASE_URL + 'people/' + self._user_id +
      '/activities/public?num=100&pageToken=%s&key=%s' % (
        page_token, self._key))

  def _single_post_url(self, activity_id):
    return (self.BASE_URL + 'activities/%s?num=100&key=%s' % (
        activity_id, self._key))

  def _fetch(self):
    try:
      loaded = urllib2.urlopen(self._activities_url())
      self._fetch_etag = loaded.info().getheader('ETag')
      data = simplejson.load(loaded)
      self._storage.storePosts(data['items'])
    except urllib2.HTTPError as e:
      # fetcher errors.  Including 30x.
      print 'fetcher error: ', e.code

  def _fetch_a_post(self, activity_id):
    try:
      data = simplejson.load(
        urllib2.urlopen(self._single_post_url(activity_id)))
      self._storage.storePosts([data])
    except urllib2.HTTPError as e:
      print 'fetcher error: ', e.code

  def _fetcher_thread(self):
    while True:
      self._event.wait(self.TIMEOUT)
      if not self._should_run:
        break
      self._event.clear()
      if self._fetch_activity_id:
        self._fetch_a_post(self._fetch_activity_id)
        self._fetch_activity_id = None
      else:
        self._fetch()

  def fetch_all_posts(self):
    try:
      latest_ids = set([post['id'] for post in self._storage.getLatestPosts()])
      print 'fetch the latest...'
      data = simplejson.load(urllib2.urlopen(self._activities_url()))
      all_items = []
      while len(data['items']) > 0:
        if any(map(lambda e: e['id'] in latest_ids, data['items'])):
          break

        all_items.extend(data['items'])
        if 'nextPageToken' not in data:
          break
        token = data['nextPageToken']
        data = simplejson.load(
          urllib2.urlopen(self._paged_activities_url(token)))
      self._storage.storePosts(all_items)
    except urllib2.HTTPError as e:
      print 'fetcher error: ', e.code

  def post_fetch(self):
    self._event.set()

  def maybe_post_fetch(self):
    """Probably not usable in our current traffic though..."""
    self._fetch_count += 1
    if self._fetch_count > self.FETCHER_COUNT:
      self._fetch_count = 0
      self.post_fetch()

  def maybe_single_fetch(self, activity_id):
    do_fetch = False
    if activity_id not in self._fetch_counts:
      do_fetch = True
      self._fetch_counts[activity_id] = 0
    self._fetch_counts[activity_id] += 1
    if self._fetch_counts[activity_id] > self.FETCHER_COUNT:
      self._fetch_counts[activity_id] = 0
      do_fetch = True

    if do_fetch:
      self._fetch_activity_id = activity_id
      self._event.set()

  def finish_thread(self):
    self._should_run = False
    self._event.set()
    self._thread.join()
