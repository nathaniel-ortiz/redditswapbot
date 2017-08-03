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
curr_id = cfg_file.get('trade', 'link_id')

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
    post = r.subreddit(subreddit).submit('%s Confirmed Trade Thread' % month, selftext='''Post your confirmed trades below, When confirming a post put Confirmed only nothing else it makes the bot unhappy :(

If more proof is requested by the bot please send a [modmail](http://www.reddit.com/message/compose?to=%%2Fr%%2F%s) including the following:

* Screenshot of PM\'s between the users
* Permalink to trade confirmed thread comment''' % subreddit, send_replies=False)
    post.mod.distinguish()
    post.mod.sticky(bottom=False)
    #r.send_message('/r/'+subreddit, 'New Trade Thread', 'A new trade thread has been posted for the month and the sidebar has been updated.')
    return (post.id)

def change_sidebar(r, post_id, month):
    sb = r.subreddit(subreddit).mod.settings()["description"]
    new_flair = r'[Confirm your Trades](/' + post_id + ')'
    new_sb = re.sub(r'\[Confirm your Trades\]\(\/[a-z0-9]+\)', new_flair, sb, 1)
    r.subreddit(subreddit).mod.update(description=new_sb)

def update_config(post_id):
    cfg_file.set('trade', 'prevlink_id', curr_id)
    cfg_file.set('trade', 'link_id', post_id)
    with open(r'config.cfg', 'wb') as configfile:
        cfg_file.write(configfile)

def main():
    month = get_month()
    r = login()
    post_id = post_thread(r, month)
    change_sidebar(r, post_id, month)
    update_config(post_id)
    logger.info("Posted Trade Confirmation thread")

if __name__ == '__main__':
    main()
