#!/usr/bin/env python2

import sys, os
from ConfigParser import SafeConfigParser
import praw
from praw.handlers import MultiprocessHandler
import datetime
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
multiprocess = cfg_file.get('reddit', 'multiprocess')
link_id = cfg_file.get('trade', 'link_id')
equal_warning = cfg_file.get('trade', 'equal')
age_warning = cfg_file.get('trade', 'age')
karma_warning = cfg_file.get('trade', 'karma')
added_msg = cfg_file.get('trade', 'added')
age_check = cfg_file.get('trade', 'age_check')
karma_check = cfg_file.get('trade', 'karma_check')

logger=LoggerManager().getLogger(__name__)

def main():

	def conditions():
		if comment.id in completed:
			return False
		if not hasattr(comment.author, 'name'):
			return False
		if 'confirm' not in comment.body.lower():
			return False
		if comment.author.name == username:
			return False
		if comment.is_root == True:
			return False
		if comment.banned_by:
			return False
		return True

	def check_self_reply():
		if comment.author.name == parent.author.name:
			item.reply(equal_warning)
			item.report()
			parent.report()
			save()
			return False
		return True

	def verify(item):
		karma = item.author.link_karma + item.author.comment_karma
		age = (datetime.utcnow() - datetime.utcfromtimestamp(item.author.created_utc)).days

		if item.author_flair_css_class < 1:
			if age < age_check:
				item.report()
				item.reply(age_warning)
				save()
				return False
			if karma < karma_check:
				item.report()
				item.reply(karma_warning)
				save()
				return False
		return True

	def values(item):
		if not item.author_flair_css_class or item.author_flair_css_class == 'i-none':
			item.author_flair_css_class = 'i-1'
		elif (item.author_flair_css_class and 'i-mod' in item.author_flair_css_class):
			pass
		else:
			item.author_flair_css_class = ('i-%d' % (int(''.join([c for c in item.author_flair_css_class if c in '0123456789'])) + 1))
		if not item.author_flair_text:
			item.author_flair_text = ''

	def flair(item):
		if item.author_flair_css_class != 'i-mod':
			item.subreddit.set_flair(item.author, item.author_flair_text, item.author_flair_css_class)
			logger.info('FLAIR: Set ' + item.author.name + '\'s flair to ' + item.author_flair_css_class)

		for com in flat_comments:
			if hasattr(com.author, 'name'):
				if com.author.name == item.author.name:
					com.author_flair_css_class = item.author_flair_css_class

	def save():
		with open (link_id+".log", 'a') as myfile:
				myfile.write('%s\n' % comment.id)

	try:
		# Load old comments
		with open (link_id+".log", 'a+') as myfile:
			completed = myfile.read()

		# Log in
		logger.info('FLAIR: Logging in as /u/'+username)
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
			if not conditions():
				continue
			parent = [com for com in flat_comments if com.fullname == comment.parent_id][0]
			if not hasattr(parent.author, 'link_karma'):
				continue
			if not check_self_reply():
				continue

			# Check Account Age and Karma
			if not verify(comment):
				continue
			if not verify(parent):
				continue

			# Get Future Values to Flair
			values(comment)
			values(parent)

			# Flairs up in here
			flair(comment)
			flair(parent)
			comment.reply(added_msg)
			save()

	except Exception as e:
		logger.error(e)

if __name__ == '__main__':
	main()
