#!/usr/bin/env python2

import sys, os
from ConfigParser import SafeConfigParser
import praw
import re
import mySQLHandler
import unicodedata
from datetime import datetime, timedelta
from time import sleep, time
from pprint import pprint
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

#configure logging
logger=LoggerManager().getLogger(__name__)

def main():
	while True:
		try:
			logger.info('Logging in as /u/'+username)
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
						clean_title = unicodedata.normalize('NFKD', post.title).encode('ascii','ignore')
						already_done.append(post.id)
						matchObj = re.search("\[(?:AF|AX|AL|DZ|AD|AO|AI|AQ|AG|AR|AM|AW|AU|EU-AT|AZ|BS|BH|BD|BB|BY|EU-BE|BZ|BJ|BM|BT|BO|BQ|BA|BW|BV|BR|IO|BN|EU-BG|BF|BI|KH|CM|CV|KY|CF|TD|CL|CN|CX|CC|CO|KM|CG|CD|CK|CR|CI|EU-HR|CU|CW|EU-CY|EU-CZ|EU-DK|DJ|DM|DO|EC|EG|SV|GQ|ER|EU-EE|ET|FK|FO|FJ|EU-FI|EU-FR|GF|PF|TF|GA|GM|GE|EU-DE|GH|GI|EU-GR|GL|GD|GP|GT|GG|GN|GW|GY|HT|HM|VA|HN|HK|EU-HU|IS|IN|ID|IR|IQ|EU-IE|IM|IL|EU-IT|JM|JP|JE|JO|KZ|KE|KI|KP|KR|KW|KG|LA|EU-LV|LB|LS|LR|LY|LI|EU-LT|EU-LU|MO|MK|MG|MW|MY|MV|ML|EU-MT|MH|MQ|MR|MU|YT|MX|FM|MD|MC|MN|ME|MS|MA|MZ|MM|NA|NR|NP|EU-NL|NC|NZ|NI|NE|NG|NU|NF|NO|OM|PK|PW|PS|PA|PG|PY|PE|PH|PN|EU-PL|EU-PT|QA|RE|EU-RO|RU|RW|BL|SH|KN|LC|MF|PM|VC|WS|SM|ST|SA|SN|RS|SC|SL|SG|SX|EU-SK|EU-SI|SB|SO|ZA|GS|SS|EU-ES|LK|SD|SR|SJ|SZ|EU-SE|CH|SY|TW|TJ|TZ|TH|TL|TG|TK|TO|TT|TN|TR|TM|TC|TV|UG|UA|AE|EU-UK|UY|UZ|VU|VE|VN|VG|WF|EH|YE|ZM|ZW|US-DC|US-AL|US-AK|US-AZ|US-AR|US-CA|US-CO|US-CT|US-DE|US-FL|US-GA|US-HI|US-ID|US-IL|US-IN|US-IA|US-KS|US-KY|US-LA|US-ME|US-MD|US-MA|US-MI|US-MN|US-MS|US-MO|US-MT|US-NE|US-NV|US-NH|US-NJ|US-NM|US-NY|US-NC|US-ND|US-OH|US-OK|US-OR|US-PA|US-RI|US-SC|US-SD|US-TN|US-TX|US-UT|US-VT|US-VA|US-WA|US-WV|US-WI|US-WI|US-AS|US-GU|US-MP|US-PR|US-UM|US-VI|US-UM|US-AA|US-AE|US-AP|CA-AB|CA-BC|CA-MB|CA-NB|CA-NL|CA-NS|CA-ON|CA-PE|CA-QC|CA-SK)\].*\[H\].*(\[W\].*)|(^\[META\].*)|(^\[GB\].*)|(^\[IC\].*)|(^\[Artisan\].*)|(^\[Vendor\].*)|(^\[Giveaway\].*)", post.title)
						match2Obj = re.search("(\[selling\])|(\[buying\])", post.title, re.IGNORECASE)
						if (not matchObj or match2Obj) and not post.distinguished:
							if post.author.name != username:
								logger.warn('Removed post: '+clean_title+' by '+post.author.name)
								if not post.approved_by:
									post.report()
									post.add_comment('REMOVED: Your post was automatically removed due to an incorrect title. Please read the [wiki](/r/' + subreddit + '/wiki/rules/rules) for posting rules').distinguish()
									post.remove()
								else:
									logger.warn('Bad post approved by: '+post.approved_by.name)
						else:
							buyingMatch = re.search("\[H\].*(cash|paypal|\$|google|ltc|btc|money).*\[W\]", post.title, re.IGNORECASE)
							sellingMatch = re.search("\[W\].*(cash|paypal|\$|google|ltc|btc|money).*", post.title, re.IGNORECASE)
							metaMatch = re.search("\[META\].*", post.title)
							icMatch = re.search("\[IC\].*", post.title)
							gbMatch = re.search("\[GB\].*", post.title)
							artisanMatch = re.search("\[Artisan\].*", post.title)
							vendorMatch = re.search("\[Vendor\].*", post.title)
							if not post.link_flair_text:
								if not post.distinguished:
									if sellingMatch:
										r.set_flair(subreddit, post, 'Selling', 'selling')
										logger.info("SELL: "+clean_title)
									elif buyingMatch:
										r.set_flair(subreddit, post, 'Buying', 'buying')
										logger.info("BUY: "+clean_title)
									elif metaMatch:
										r.set_flair(subreddit, post, 'META', 'meta')
										logger.info("META: "+clean_title)
									elif icMatch:
										r.set_flair(subreddit, post, 'Interest Check', 'interestcheck')
										logger.info("IC: "+clean_title)
									elif gbMatch:
										r.set_flair(subreddit, post, 'Group Buy', 'groupbuy')
										logger.info("GB: "+clean_title)
									elif artisanMatch:
										r.set_flair(subreddit, post, 'Artisan', 'artisan')
										logger.info("Artisan: "+clean_title)
									elif vendorMatch:
										r.set_flair(subreddit, post, 'Vendor', 'vendor')
										logger.info("Vendor: "+clean_title)
									else:
										r.set_flair(subreddit, post, 'Trading', 'trading')
										logger.info("TRADE: "+clean_title)
							else:
								logger.info("OTHER: "+clean_title)
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
								#have to check both flair class and regex match.  (flair class is none if just set)
								if botcomment == 0:
									age = str(datetime.utcfromtimestamp(post.author.created_utc))
									if str(post.author_flair_css_class) == "i-mod":
										post.add_comment('* Username: ' + str(post.author.name) + '\n* Join date: ' + age + '\n* Link karma: ' + str(post.author.link_karma) + '\n* Comment karma: ' + str(post.author.comment_karma) + '\n* Reputation: User is currently a moderator.\n* Flair text: ' + str(post.author_flair_text) + '\n\n^^This ^^information ^^does ^^not ^^guarantee ^^a ^^successful ^^swap. ^^It ^^is ^^being ^^provided ^^to ^^help ^^potential ^^trade ^^partners ^^have ^^more ^^immediate ^^background ^^information ^^about ^^with ^^whom ^^they ^^are ^^swapping. ^^Please ^^be ^^sure ^^to ^^familiarize ^^yourself ^^with ^^the ^^[RULES](https://www.reddit.com/r/' + subreddit + '/wiki/rules/rules) ^^and ^^other ^^guides ^^on ^^the ^^[WIKI](https://www.reddit.com/r/' + subreddit + '/wiki/index)').distinguish()
									else:
											if str(post.author_flair_text) == "None":
												heatware = "None"
												if str(post.author_flair_css_class) == "i-none":
													post.add_comment('* Username: ' + str(post.author.name) + '\n* Join date: ' + age + '\n* Link karma: ' + str(post.author.link_karma) + '\n* Comment karma: ' + str(post.author.comment_karma) + '\n* Reputation: No trades' '\n* Heatware: ' + heatware + '\n\n^^This ^^information ^^does ^^not ^^guarantee ^^a ^^successful ^^swap. ^^It ^^is ^^being ^^provided ^^to ^^help ^^potential ^^trade ^^partners ^^have ^^more ^^immediate ^^background ^^information ^^about ^^with ^^whom ^^they ^^are ^^swapping. ^^Please ^^be ^^sure ^^to ^^familiarize ^^yourself ^^with ^^the ^^[RULES](https://www.reddit.com/r/' + subreddit + '/wiki/rules/rules) ^^and ^^other ^^guides ^^on ^^the ^^[WIKI](https://www.reddit.com/r/' + subreddit + '/wiki/index)').distinguish()
												else:
													post.add_comment('* Username: ' + str(post.author.name) + '\n* Join date: ' + age + '\n* Link karma: ' + str(post.author.link_karma) + '\n* Comment karma: ' + str(post.author.comment_karma) + '\n* Reputation: ' + str(post.author_flair_css_class).translate(None, 'i-') + ' trade(s)' '\n* Heatware: ' + heatware + '\n\n^^This ^^information ^^does ^^not ^^guarantee ^^a ^^successful ^^swap. ^^It ^^is ^^being ^^provided ^^to ^^help ^^potential ^^trade ^^partners ^^have ^^more ^^immediate ^^background ^^information ^^about ^^with ^^whom ^^they ^^are ^^swapping. ^^Please ^^be ^^sure ^^to ^^familiarize ^^yourself ^^with ^^the ^^[RULES](https://www.reddit.com/r/' + subreddit + '/wiki/rules/rules) ^^and ^^other ^^guides ^^on ^^the ^^[WIKI](https://www.reddit.com/r/' + subreddit + '/wiki/index)').distinguish()
											else:
												heatware = "[" + str(post.author_flair_text) + "](" + str(post.author_flair_text) +")"
												if str(post.author_flair_css_class) == "i-none":
													post.add_comment('* Username: ' + str(post.author.name) + '\n* Join date: ' + age + '\n* Link karma: ' + str(post.author.link_karma) + '\n* Comment karma: ' + str(post.author.comment_karma) + '\n* Reputation: No trades' '\n* Heatware: ' + heatware + '\n\n^^This ^^information ^^does ^^not ^^guarantee ^^a ^^successful ^^swap. ^^It ^^is ^^being ^^provided ^^to ^^help ^^potential ^^trade ^^partners ^^have ^^more ^^immediate ^^background ^^information ^^about ^^with ^^whom ^^they ^^are ^^swapping. ^^Please ^^be ^^sure ^^to ^^familiarize ^^yourself ^^with ^^the ^^[RULES](https://www.reddit.com/r/' + subreddit + '/wiki/rules/rules) ^^and ^^other ^^guides ^^on ^^the ^^[WIKI](https://www.reddit.com/r/' + subreddit + '/wiki/index)').distinguish()
												else:
													post.add_comment('* Username: ' + str(post.author.name) + '\n* Join date: ' + age + '\n* Link karma: ' + str(post.author.link_karma) + '\n* Comment karma: ' + str(post.author.comment_karma) + '\n* Reputation: ' + str(post.author_flair_css_class).translate(None, 'i-') + ' trade(s)' '\n* Heatware: ' + heatware + '\n\n^^This ^^information ^^does ^^not ^^guarantee ^^a ^^successful ^^swap. ^^It ^^is ^^being ^^provided ^^to ^^help ^^potential ^^trade ^^partners ^^have ^^more ^^immediate ^^background ^^information ^^about ^^with ^^whom ^^they ^^are ^^swapping. ^^Please ^^be ^^sure ^^to ^^familiarize ^^yourself ^^with ^^the ^^[RULES](https://www.reddit.com/r/' + subreddit + '/wiki/rules/rules) ^^and ^^other ^^guides ^^on ^^the ^^[WIKI](https://www.reddit.com/r/' + subreddit + '/wiki/index)').distinguish()
	
				logger.debug('Sleeping for 2 minutes')
				sleep(120)
		except Exception as e:
			logger.error(e)
			sleep(120)

if __name__ == '__main__':
	main()
