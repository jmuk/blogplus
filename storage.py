# coding: utf-8

from posts import isMeaningfulPost
import pymongo

class Storage:
  def __init__(self):
    self.db_ = pymongo.Connection()['blogplus']
    self.posts_ = self.db_['items']
    self._latest_cache = None
    self._dates_cache = None

  def storePosts(self, posts):
    ids = [post['id'] for post in posts]
    old_posts = dict([
        (post['id'], post) for post in self.posts_.find({'id': {'$in': ids}})])
    new_posts = [post for post in posts if post['id'] not in old_posts
                 if isMeaningfulPost(post)]
    if len(new_posts) > 0:
      self.posts_.insert(new_posts)
    for post in posts:
      old_post = old_posts.get(post['id'])
      if old_post and post != old_post:
        # update
        self.posts_.update({'id': post['id']}, {'$set', post})
    self._latest_cache = None
    self._dates_cache = None

  def getPost(self, id):
    return self.posts_.find_one({'id': id})

  def getLatestPosts(self):
    if self._latest_cache:
      return self._latest_cache

    self._latest_cache = list(
      self.posts_.find().sort([('published', pymongo.DESCENDING)]).limit(10))
    return self._latest_cache

  def getDates(self):
    if self._dates_cache:
      return self._dates_cache

    result = {}
    for post in self.posts_.find({}, {'published': 1}):
      published = post['published']
      (y, m, remaining) = published.split('-')
      published_month = y + '-' + m
      result[published_month] = result.get(published_month, 0) + 1
    self._dates_cache = sorted(result.items())
    return self._dates_cache

  def getArchivedPosts(self, datespec):
    result = {}
    return self.posts_.find({'published': {'$regex': '^' + datespec}}).sort([('published', pymongo.DESCENDING)])
