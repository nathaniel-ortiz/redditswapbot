#!/usr/bin/env python2

import sys, os
import re
from ConfigParser import SafeConfigParser
import praw
from praw.handlers import MultiprocessHandler
import time
from log_conf import LoggerManager

containing_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
cfg_file = SafeConfigParser()
path_to_cfg = os.path.join(containing_dir, 'config.cfg')
cfg_file.read(path_to_cfg)

username = cfg_file.get('reddit', 'username')
password = cfg_file.get('reddit', 'password')
subreddit = cfg_file.get('reddit', 'subreddit')

logger=LoggerManager().getLogger(__name__)

def get_month():
	month = time.strftime('%B')
	return(month)

def login():
	r = praw.Reddit(user_agent=username)
	r.login(username, password)
	return(r)

def post_thread(r,month):
	post = r.submit(subreddit,'%s Improvements Thread' % month, text='''Post improvements to the subreddit that you'd like to see implemented.

Show your support by upvoting the ideas you like the most.

* If an idea gains a relatively large amount of support, the moderators will take it into consideration.
* If the moderators decided to make it a rule, the rules will be amended.
* If the idea is vetoed, we will explain why the idea was shot down.''')
	post.distinguish(as_made_by='mod')
	post.sticky(bottom=True)
	r.set_flair(subreddit, post, 'Meta', 'meta')
	return (post.id)

def change_sidebar(r, post_id, month):
	sr = r.get_subreddit(subreddit)
	sb = sr.get_settings()["description"]
	new_flair = r'[Monthly Improvement Thread](/'+post_id+')'
	new_sb = re.sub(r'\[Monthly Improvement Thread\]\(\/[a-z0-9]+\)',new_flair, sb, 1)
	sr.update_settings(description = new_sb)

def main():
	month = get_month()
	r = login()
	post_id = post_thread(r, month)
	change_sidebar(r, post_id, month)
	logger.info("Posted Montly Improvement Thread thread")

if __name__ == '__main__':
	main()
