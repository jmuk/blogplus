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

    self._thread = threading.Thread(
      target=self._fetcher_thread, name="Fetcher")
    self._should_run = True
    self._thread.start()

  def _activities_url(self):
    return (self.BASE_URL + 'people/' + self._user_id +
            '/activities/public?num=100&key=' + self._key)

  def _fetch(self):
    data = simplejson.load(urllib2.urlopen(self._activities_url()))
    self._storage.storePosts(data['items'])

  def _fetcher_thread(self):
    while True:
      self._event.wait(self.TIMEOUT)
      if not self._should_run:
        break
      self._event.clear()
      self._fetch()

  def post_fetch(self):
    """Post a fetch request to the thread."""
    self._event.set()

  def maybe_post_fetch(self):
    """Probably not usable in our current traffic though..."""
    self._fetch_count += 1
    if self._fetch_count > self.FETCHER_COUNT:
      self._fetch_count = 0
      self.post_fetch()

  def finish_thread(self):
    self._should_run = False
    self._event.set()
    self._thread.join()
