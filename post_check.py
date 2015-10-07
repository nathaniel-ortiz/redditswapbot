#!/usr/bin/python

import sys, os
from ConfigParser import SafeConfigParser
import logging
import praw
import re
from datetime import datetime, timedelta
from time import sleep, time
from pprint import pprint

# load config file
containing_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
cfg_file = SafeConfigParser()
path_to_cfg = os.path.join(containing_dir, 'config.cfg')
cfg_file.read(path_to_cfg)
username = cfg_file.get('reddit', 'username')
password = cfg_file.get('reddit', 'password')
subreddit = cfg_file.get('reddit', 'subreddit')
multiprocess = cfg_file.get('reddit', 'multiprocess')

#configure logging
logging.basicConfig(level=logging.INFO, filename='actions.log', format='%(asctime)s - %(message)s')
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)


def main():
	while True:
		try:
			logging.info('POST_CHECK: Logging in as /u/'+username)
			if multiprocess == 'true':
				handler = MultiprocessHandler()
				r = praw.Reddit(user_agent=username, handler=handler)
			else:
				r = praw.Reddit(user_agent=username)
			r.login(username, password)

			already_done = []
	
			while True:
				data = r.get_subreddit(subreddit).get_new(limit=20)
				for post in data:
					if post.id not in already_done:
						already_done.append(post.id)
						matchObj = re.search("(^\[[A-Z]{2,}.*\].*\[H\].*\[W\].*)|(^\[META\].*)|(^\[GB\].*)|(^\[IC\].*)|(^\[Artisan\].*)", post.title)
						match2Obj = re.search("(\[selling\])|(\[buying\])", post.title, re.IGNORECASE)
						if (not matchObj or match2Obj) and not post.distinguished:
							if post.author.name != username:
								logging.info('POST_CHECK: Removed post: '+post.title+' by '+post.author.name)
								if not post.approved_by:
									post.report()
									post.add_comment('REMOVED: Please read the [wiki](/r/mechmarket/wiki/rules/rules) for posting rules').distinguish()
									post.remove()
								else:
									logging.info('POST_CHECK: Bad post approved by: '+post.approved_by.name)
						else:
							buyingMatch = re.search("\[H\].*(cash|paypal|\$|google|ltc|btc|money).*\[W\]", post.title, re.IGNORECASE)
							sellingMatch = re.search("\[W\].*(cash|paypal|\$|google|ltc|btc|money).*", post.title, re.IGNORECASE)
							metaMatch = re.search("\[META\].*", post.title)
							icMatch = re.search("\[IC\].*", post.title)
							gbMatch = re.search("\[GB\].*", post.title)
							artisanMatch = re.search("\[Artisan\].*", post.title)
							if not post.link_flair_text:
								if not post.distinguished:
									if sellingMatch:
										r.set_flair(subreddit, post, 'Selling', 'selling')
										logging.info("POST_CHECK: SELL: "+post.title)
									elif buyingMatch:
										r.set_flair(subreddit, post, 'Buying', 'buying')
										logging.info("POST_CHECK: BUY: "+post.title)
									elif metaMatch:
										r.set_flair(subreddit, post, 'META', 'meta')
										logging.info("POST_CHECK: META: "+post.title)
									elif icMatch:
										r.set_flair(subreddit, post, 'Interest Checl', 'interestcheck')
										logging.info("POST_CHECK: IC: "+post.title)
									elif gbMatch:
										r.set_flair(subreddit, post, 'Group Buy', 'groupbuy')
										logging.info("POST_CHECK: GB: "+post.title)
									elif artisanMatch:
										r.set_flair(subreddit, post, 'Artisan', 'artisan')
										logging.info("POST_CHECK: Artisan: "+post.title)
									else:
										r.set_flair(subreddit, post, 'Trading', 'trading')
										logging.info("POST_CHECK: TRADE: "+post.title)
							else:
								logging.info("POST_CHECK: OTHER: "+post.title)
							#check comments for info from bot
							if not post.distinguished:
								post.replace_more_comments(limit=None, threshold=0)
								flat_comments = list(praw.helpers.flatten_tree(post.comments))
								botcomment = 0
								for comment in flat_comments:
									if hasattr(comment.author, 'name'):
										if comment.author.name == username:
											botcomment = 1
								#otherwise spit out user information
								#post.add_comment('Username | Join date | Link karma | Comment karma | Confirmed trades | Heatware\n:- | :-: | -: | -: | -: | :-:\n' + post.author.name)
								if botcomment == 0 and ( not metaMatch or post.link_flair_css_class != "meta" ):
									#pprint(vars(post.author))
									age = str(datetime.utcfromtimestamp(post.author.created_utc))
									if str(post.author_flair_text) == "None":
										heatware = "None"
									else:
										heatware = "[" + str(post.author_flair_text) + "](" + str(post.author_flair_text) +")"
									#post.add_comment('Username | Join date | Link karma | Comment karma | Confirmed trades | Heatware\n:- | :-: | -: | -: | -: | :-:\n' + str(post.author.name) + ' | ' + age + ' | ' + str(post.author.link_karma) + ' | ' + str(post.author.comment_karma) + ' | ' + str(post.author_flair_css_class) + ' | ' + heatware + '\n\n^^This ^^information ^^does ^^not ^^guarantee ^^a ^^successful ^^swap. ^^It ^^is ^^being ^^provided ^^to ^^help ^^potential ^^trade ^^partners ^^have ^^more ^^immediate ^^background ^^information ^^about ^^with ^^whom ^^they ^^are ^^swapping.')
									post.add_comment('* Username: ' /u/+ str(post.author.name) + '\n* Join date: ' + age + '\n* Link karma: ' + str(post.author.link_karma) + '\n* Comment karma: ' + str(post.author.comment_karma) + '\n* Confirmed trades: ' + str(post.author_flair_css_class).translate(None, 'i-') + '\n* Heatware: ' + heatware + '\n\n^^This ^^information ^^does ^^not ^^guarantee ^^a ^^successful ^^swap. ^^It ^^is ^^being ^^provided ^^to ^^help ^^potential ^^trade ^^partners ^^have ^^more ^^immediate ^^background ^^information ^^about ^^with ^^whom ^^they ^^are ^^swapping. ^^Please ^^be ^^sure ^^to ^^familiarize ^^yourself ^^with ^^the ^^[RULES](https://www.reddit.com/r/mechmarket/wiki/rules/rules) ^^and ^^other ^^guides ^^on ^^the ^^[WIKI](https://www.reddit.com/r/mechmarket/wiki/index)')
	
				logging.info('Sleeping for 2 minutes')
				sleep(120)
		except Exception as e:
			logging.error(e)

if __name__ == '__main__':
	main()
