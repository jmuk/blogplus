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
            '/activities/public?num=100&key=' + self._key)

  def fetch(self):
    data = simplejson.load(urllib2.urlopen(self._activities_url()))
    self._storage.storePosts(data['items'])

def isMeaningfulContent(content):
  # currently only checks the length
  return len(content) > 200

def isMeaningfulPost(post):
  """Check the meaningfulness of a post. """
  # nothing for reshares.
  if post.get('verb', '') == 'share':
    return False

  # okay to publish video posts ;)
  attachments = post['object'].get('attachments', [])
  for attachment in attachments:
    if attachment['objectType'] == 'video':
      return True

  return isMeaningfulContent(re.sub('<.*?>', '', post['object']['content']))

def formAttachments(post):
  attachments = post['object'].get('attachments', [])
  attachments_len = len(attachments)
  if attachments_len == 0:
    post['formed_attachment'] = ''
  elif attachments_len == 1:
    attachment = attachments[0]
    if attachment['objectType'] in ['video', 'photo']:
      post['formed_attachment'] = render_template(
        'image_attachment.html', attachment=attachment)
    elif attachment['objectType'] == 'article':
      post['formed_attachment'] = render_template(
        'text_attachment.html', visual_attachments=[],
        text_attachments=attachments)
  else:
    visual_attachments = []
    text_attachments = []
    for attachment in attachments:
      if attachment['objectType'] == 'article':
        text_attachments.append(attachment)
      else:
        visual_attachments.append(attachment)
    post['formed_attachment'] = render_template('text_attachment.html',
      visual_attachments=visual_attachments, text_attachments=text_attachments)

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

  def getDates(self):
    result = {}
    for post in self.posts_.find({}, {'published': 1}):
      published = post['published']
      (y, m, remaining) = published.split('-')
      published_month = y + '-' + m
      result[published_month] = result.get(published_month, 0) + 1
    return sorted(result.items())


storage = Storage()
fetcher = Fetcher(
  '102550604876259086885', 'AIzaSyBrefCdRhjBh2tnFPPpzaTGIt4aDLbc1Tw', storage)

SERVER_ROOT = 'http://www.jmuk.org'

def processPost(post):
  post['self_url'] = SERVER_ROOT + url_for('get_post', activity_id=post['id'])
  formAttachments(post)

@app.route('/')
def main():
  posts = list(storage.getLatestPosts())
  for post in posts:
    processPost(post)
  return render_template(
    'main.html', posts=posts, archive_items=storage.getDates())


@app.route('/post/<activity_id>')
def get_post(activity_id):
  post = storage.getPost(activity_id)
  processPost(post)
  return render_template(
    'single_entry.html', post=post, archive_items=storage.getDates())

@app.route('/forcefetch')
def forcefetch():
  fetcher.fetch()
  return redirect('/')

if __name__ == '__main__':
  app.run(debug=True)
