# coding: utf-8

from flask import Flask, redirect, render_template, url_for
import cStringIO
import pymongo
import re
import simplejson
import urllib2

app = Flask(__name__)

class Fetcher:
  BASE_URL = 'https://www.googleapis.com/plus/v1/'

  def __init__(self, user_id, key, storage):
    self._user_id = user_id
    self._key = key
    self._storage = storage

  def _activities_url(self):
    return (self.BASE_URL + 'people/' + self._user_id +
            '/activities/public?key=' + self._key)

  def fetch(self):
    data = simplejson.load(urllib2.urlopen(self._activities_url()))
    self._storage.storePosts(data['items'])

def isMeaningfulContent(content):
  # currently only checks the length
  return len(content) > 200

def isMeaningfulPost(post):
  if post.get('verb', '') == 'share':
    text_content = post['annotation']
  else:
    text_content = post['object']['content']
  return isMeaningfulContent(re.sub('<.*?>', '', text_content))

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
      if old_post and not old_post['updated'] == post['updated']:
        # update
        self.posts_.update({'id': post['id']}, {'$set', post})

  def getPost(self, id):
    return self.posts_.find_one({'id': id})

  def getLatestPosts(self):
    return self.posts_.find().sort([('published', pymongo.DESCENDING)]).limit(10)


storage = Storage()
fetcher = Fetcher( # fill here
  )

SERVER_ROOT = 'http://www.jmuk.org'

def process_post(post):
  post['self_url'] = SERVER_ROOT + url_for('get_post', activity_id=post['id'])


@app.route('/')
def main():
  posts = list(storage.getLatestPosts())
  for post in posts:
    process_post(post)
  return render_template('main.html', posts=posts)


@app.route('/post/<activity_id>')
def get_post(activity_id):
  post = storage.getPost(activity_id).__repr__()
  process_post
  return ''

@app.route('/forcefetch')
def forcefetch():
  fetcher.fetch()
  return redirect('/')

if __name__ == '__main__':
  app.run(debug=True)

