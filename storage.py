# coding: utf-8

from cache import cached, clear_cache
from posts import isMeaningfulPost
import pymongo

class Storage:
  def __init__(self):
    self.db_ = pymongo.Connection()['blogplus']
    self.posts_ = self.db_['items']

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
        self.posts_.update({'id': post['id']}, {'$set': post})
    clear_cache()

  def getPost(self, id):
    return self.posts_.find_one({'id': id})

  @cached('last_post')
  def getLatestPosts(self):
    return list(
      self.posts_.find().sort([('published', pymongo.DESCENDING)]).limit(10))

  @cached('dates')
  def getDates(self):
    result = {}
    for post in self.posts_.find({}, {'published': 1}):
      published = post['published']
      (y, m, remaining) = published.split('-')
      published_month = y + '-' + m
      result[published_month] = result.get(published_month, 0) + 1
    # We just reverse the order because most people are just interested in
    # recent items rather than ancient ones.
    return sorted(result.items(), reverse=True)

  def getArchivedPosts(self, datespec):
    return self.posts_.find({'published': {'$regex': '^' + datespec}}).sort([('published', pymongo.DESCENDING)])
