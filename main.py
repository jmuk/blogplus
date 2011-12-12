# coding: utf-8

from flask import Flask, redirect, render_template, abort
from config import CLIENT_KEY, CLIENT_SECRET, SERVER_ROOT
from posts import processPost
from storage import Storage
from fetcher import Fetcher
import re
import signal

app = Flask(__name__)

storage = Storage()
fetcher = Fetcher(CLIENT_KEY, CLIENT_SECRET, storage)

@app.route('/')
def main():
  posts = list(storage.getLatestPosts())
  for post in posts:
    processPost(post)
  fetcher.maybe_post_fetch()
  return render_template(
    'main.html', posts=posts, archive_items=storage.getDates())

@app.route('/post/<activity_id>')
def get_post(activity_id):
  post = storage.getPost(activity_id)
  processPost(post)
  return render_template(
    'single_entry.html', post=post, archive_items=storage.getDates())

@app.route('/archive/<datespec>')
def archive(datespec):
  if not re.match(r'\d+-\d+', datespec):
    abort(404)

  posts = list(storage.getArchivedPosts(datespec))
  if len(posts) == 0:
    abort(404)

  for post in posts:
    processPost(post)
  return render_template(
    'main.html', posts=posts, archive_items=storage.getDates())

@app.route('/feed')
def atomFeed():
  posts = list(storage.getLatestPosts())
  global_updated = max([post['updated'] for post in posts])
  for post in posts:
    processPost(post)

  return render_template(
    'atom.xml', posts=posts, SERVER_ROOT=SERVER_ROOT,
    global_updated=global_updated)

@app.route('/forcefetch')
def forcefetch():
  fetcher.post_fetch()
  return redirect('/')

if __name__ == '__main__':
  try:
    app.run(debug=True)
  finally:
    fetcher.finish_thread()
