# coding: utf-8

from flask import Flask, redirect, render_template, abort, Blueprint
from cache import cached
from config import USER_ID, CLIENT_SECRET, SERVER_ROOT
from posts import processPost
from storage import Storage
from fetcher import Fetcher
import re
import signal

app_main = Blueprint('blog', __name__, static_folder='static')

storage = Storage()
fetcher = Fetcher(USER_ID, CLIENT_SECRET, storage)

@app_main.route('/')
@cached('main')
def main():
  posts = list(storage.getLatestPosts())
  for post in posts:
    processPost(post)
  fetcher.maybe_post_fetch()
  return render_template(
    'main.html', posts=posts, archive_items=storage.getDates())

@app_main.route('/post/<activity_id>')
def get_post(activity_id):
  post = storage.getPost(activity_id)
  processPost(post)
  fetcher.maybe_single_fetch(activity_id)
  return render_template(
    'single_entry.html', post=post, archive_items=storage.getDates())

@app_main.route('/archive/<datespec>')
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

@app_main.route('/feed')
@cached('feed')
def atomFeed():
  posts = list(storage.getLatestPosts())
  global_updated = max([post['updated'] for post in posts])
  for post in posts:
    processPost(post)

  return render_template(
    'atom.xml', posts=posts, SERVER_ROOT=SERVER_ROOT,
    global_updated=global_updated)

@app_main.route('/forcefetch')
def forcefetch():
  fetcher.post_fetch()
  return redirect('/')

if __name__ == '__main__':
  try:
    fetcher.fetch_all_posts()
    app = Flask(__name__)
    app.register_blueprint(app_main, url_prefix='/blog')
    app.run(debug=True)
  finally:
    fetcher.finish_thread()
