#!/usr/bin/env python2

import sys, os
import re
from ConfigParser import SafeConfigParser
import praw
import time
from log_conf import LoggerManager

containing_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
cfg_file = SafeConfigParser()
path_to_cfg = os.path.join(containing_dir, 'config.cfg')
cfg_file.read(path_to_cfg)

username = cfg_file.get('reddit', 'username')
password = cfg_file.get('reddit', 'password')
app_key = cfg_file.get('reddit', 'app_key')
app_secret = cfg_file.get('reddit', 'app_secret')
subreddit = cfg_file.get('reddit', 'subreddit')

# configure logging
logger = LoggerManager().getLogger(__name__)

def get_month():
    month = time.strftime('%B')
    return(month)

def login():
    r = praw.Reddit(client_id=app_key,
                    client_secret=app_secret,
                    username=username,
                    password=password,
                    user_agent=username)
    return(r)

def post_thread(r,month):
    post = r.subreddit(subreddit).submit('OFFICIAL [PRICE CHECK] THREAD - MONTH OF %s' % month.upper(), selftext='''This is the official [Price Check] thread for /r/%s! The rules are simple:

* List what specific items you have and your questions about their value
* If you think you know what an item is worth, comment and tell the OP!
* ***OFFERING IS NOT ALLOWED***. Making offers will result in your comment being removed and a warning being issued.
* Once you're happy with the price you hear, feel free to make a trade post! Just make sure you follow all the rules and include a timestamped picture.

**It helps to sort by new!**''' % subreddit, send_replies=False)
    post.mod.distinguish()
    post.mod.sticky(bottom=True)
    post.mod.suggested_sort(sort='new')
    post.mod.flair(text='Meta', css_class='meta')

    #r.send_message('/r/'+subreddit, 'New Trade Thread', 'A new trade thread has been posted for the month and the sidebar has been updated.')
    return (post.id)

def change_sidebar(r, post_id):
    sb = r.subreddit(subreddit).mod.settings()["description"]
    new_flair = r'[Price check thread](/' + post_id + ')'
    new_sb = re.sub(r'\[Price check thread\]\(\/[a-z0-9]+\)', new_flair, sb, 1)
    r.subreddit(subreddit).mod.update(description=new_sb)

def update_config(post_id):
    cfg_file.set('price', 'link_id', post_id)
    with open(r'config.cfg', 'wb') as configfile:
        cfg_file.write(configfile)

def main():
    month = get_month()
    r = login()
    post_id = post_thread(r, month)
    change_sidebar(r, post_id)
    update_config(post_id)
    logger.info("Posted Price Check thread")

if __name__ == '__main__':
    main()
