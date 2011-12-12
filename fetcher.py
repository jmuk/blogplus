# coding: utf-8
import simplejson
import urllib2

class Fetcher:
  BASE_URL = 'https://www.googleapis.com/plus/v1/'

  def __init__(self, user_id, key, storage):
    self._user_id = user_id
    self._key = key
    self._storage = storage

  def _activities_url(self):
    return (self.BASE_URL + 'people/' + self._user_id +
            '/activities/public?num=100&key=' + self._key)

  def fetch(self):
    data = simplejson.load(urllib2.urlopen(self._activities_url()))
    self._storage.storePosts(data['items'])

