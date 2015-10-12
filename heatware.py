#!/usr/bin/env python2

import sys, os
from ConfigParser import SafeConfigParser
import praw
import re
from datetime import datetime, timedelta
from time import sleep, time
from log_conf import LoggerManager

# load config file
containing_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
cfg_file = SafeConfigParser()
path_to_cfg = os.path.join(containing_dir, 'config.cfg')
cfg_file.read(path_to_cfg)
username = cfg_file.get('reddit', 'username')
password = cfg_file.get('reddit', 'password')
subreddit = cfg_file.get('reddit', 'subreddit')
link_id = cfg_file.get('heatware', 'link_id')
respond = cfg_file.get('heatware', 'respond')
regex = cfg_file.get('heatware', 'regex')
multiprocess = cfg_file.get('reddit', 'multiprocess')

# Configure logging
logger=LoggerManager().getLogger(__name__)

def main():
	try:
		logger.info('Logging in as /u/'+username)
		if multiprocess == 'true':
			handler = MultiprocessHandler()
			r = praw.Reddit(user_agent=username, handler=handler)
		else:
			r = praw.Reddit(user_agent=username)
		r.login(username, password)

		# Get the submission and the comments
		submission = r.get_submission(submission_id=link_id)
		submission.replace_more_comments(limit=None, threshold=0)
		flat_comments = list(praw.helpers.flatten_tree(submission.comments))

		for comment in flat_comments:
			logger.debug("Processing comment: " + comment.id)
			if not hasattr(comment, 'author'):
				continue
			if comment.is_root == True:
				heatware = re.search(regex, comment.body)
				if heatware:
					url = heatware.group(0)
					if not comment.author_flair_text:
						replies_flat = list(praw.helpers.flatten_tree(comment.replies))
						for reply in replies_flat:
							if reply.author: 
								if str(reply.author.name) == username:
									break
						else:
							if comment.author:
								if comment.author_flair_css_class:
									comment.subreddit.set_flair(comment.author, url, comment.author_flair_css_class)
								else:
									comment.subreddit.set_flair(comment.author, url, 'i-none')
								logger.info('Set ' + comment.author.name + '\'s heatware to ' + url)
								if respond == 'yes':
									comment.reply('added')

	except Exception as e:
		logger.error(e)

if __name__ == '__main__':
	main()
