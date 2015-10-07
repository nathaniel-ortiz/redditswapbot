#!/usr/bin/python

import sys, os
import re
from ConfigParser import SafeConfigParser
import logging
import praw
from praw.handlers import MultiprocessHandler
import time

containing_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
cfg_file = SafeConfigParser()
path_to_cfg = os.path.join(containing_dir, 'config.cfg')
cfg_file.read(path_to_cfg)

username = cfg_file.get('reddit', 'username')
password = cfg_file.get('reddit', 'password')
subreddit = cfg_file.get('reddit', 'subreddit')

def get_month():
	month = time.strftime('%B')
	return(month)

def login():
	r = praw.Reddit(user_agent=username)
	r.login(username, password)
	return(r)

def post_thread(r,month):
	post = r.submit(subreddit,'OFFICIAL [PRICE CHECK] THREAD - MONTH OF %s' % month, text='''This is the official [Price Check] thread for /r/mechmarket! The rules are simple:

* List what specific items you have and your questions about their value
* If you think you know what an item is worth, comment and tell the OP!
* ***OFFERING IS NOT ALLOWED***. Making offers will result in your comment being removed and a warning being issued.
* Once you're happy with the price you hear, feel free to make a trade post! Just make sure you follow all the rules and include a timestamped picture.

**It helps to sort by new!**''', send_replies=False)
	post.distinguish(as_made_by='mod')
	post.sticky(bottom=True)
	r.set_flair(subreddit, post, 'Meta', 'meta')
	
	#r.send_message('/r/'+subreddit, 'New Trade Thread', 'A new trade thread has been posted for the month and the sidebar has been updated.')
	return (post.id)

def change_sidebar(r, post_id):
	sr = r.get_subreddit(subreddit)
	sb = sr.get_settings()["description"]
	new_flair = r'[Price check thread](/'+post_id+')'
	new_sb = re.sub(r'\[Price check thread\]\(\/[a-z0-9]+\)',new_flair, sb, 1)
	sr.update_settings(description = new_sb)

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
	
if __name__ == '__main__':
	main()
