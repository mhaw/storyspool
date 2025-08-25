from flask import current_app
from feedgen.feed import FeedGenerator
from .store import list_user_articles
from .users import user_display_name

def user_feed_url(uid: str) -> str:
    if not uid: return None
    return f"{current_app.config['BASE_URL']}/u/{uid}/feed.xml"

def build_user_feed(uid: str) -> str:
    fg = FeedGenerator()
    fg.id(user_feed_url(uid))
    fg.title(f"StorySpool - {user_display_name(uid)}")
    fg.link(href=user_feed_url(uid), rel='self')
    fg.language('en')
    for a in list_user_articles(uid):
        fe = fg.add_entry()
        fe.id(a['id'])
        fe.title(a.get('title','(untitled)'))
        fe.link(href=a.get('audio_url'))
        if a.get('summary'): fe.description(a['summary'])
    return fg.rss_str(pretty=True).decode()
