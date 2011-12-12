from flask import url_for, render_template
from config import SERVER_ROOT
import re

def isMeaningfulContent(content):
  # currently only checks the length
  return len(content) > 200

def isMeaningfulPost(post):
  """Check the meaningfulness of a post. """
  # nothing for reshares.
  if post.get('verb', '') == 'share':
    return False

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

def processPost(post):
  post['self_url'] = SERVER_ROOT + url_for('.get_post', activity_id=post['id'])
  formAttachments(post)
