#!/usr/bin/env python2

import sys, os
from ConfigParser import SafeConfigParser
import praw
import re
import sqlite3
import unicodedata
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
app_key = cfg_file.get('reddit', 'app_key')
app_secret = cfg_file.get('reddit', 'app_secret')
subreddit = cfg_file.get('reddit', 'subreddit')
flair_db = cfg_file.get('trade', 'flair_db')
regex = cfg_file.get('post_check', 'regex')
rules = cfg_file.get('post_check', 'rules')
upper_hour = cfg_file.getint('post_check', 'upper_hour')
lower_min = cfg_file.getint('post_check', 'lower_min')

# configure logging
logger = LoggerManager().getLogger(__name__)

def main():
    while True:
        try:
            try:
                con = sqlite3.connect(flair_db, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
                con.row_factory = sqlite3.Row
            except sqlite3.Error, e:
                logger.error("Error %s:" % e.args[0])

            curs = con.cursor()

            logger.debug('Logging in as /u/' + username)
            r = praw.Reddit(client_id=app_key,
                            client_secret=app_secret,
                            username=username,
                            password=password,
                            user_agent=username)

            already_done = []

            while True:
                data = r.subreddit(subreddit).new(limit=20)
                for post in data:
                    if post.id not in already_done:
                        clean_title = unicodedata.normalize('NFKD', post.title).encode('ascii', 'ignore')
                        removedpost = False
                        already_done.append(post.id)
                        matchObj = re.search(regex, post.title)
                        match2Obj = re.search("(\[selling\])|(\[buying\])", post.title, re.IGNORECASE)
                        if (not matchObj or match2Obj) and not post.distinguished:
                            if post.author.name != username:
                                logger.warn('Removed post: ' + clean_title + ' by ' + post.author.name)
                                if not post.approved_by:
                                    post.report('Bad title')
                                    post.reply('REMOVED: Your post was automatically removed due to an incorrect title. Please read the [wiki](/r/' + subreddit + rules + ') for posting rules').mod.distinguish()
                                    post.mod.remove()
                                else:
                                    logger.warn('Bad post approved by: ' + post.approved_by.name)
                        else:
                            log_msg = ""
                            log_msg_level = ""
                            buyingMatch = re.search("\[H\].*(cash|paypal|\$|google w|ltc|btc|bitcoin|money).*\[W\]", post.title, re.IGNORECASE)
                            sellingMatch = re.search("\[W\].*(cash|paypal|\$|google w|ltc|btc|bitcoin|money).*", post.title, re.IGNORECASE)
                            metaMatch = re.search("\[META\].*", post.title)
                            icMatch = re.search("\[IC\].*", post.title)
                            gbMatch = re.search("\[GB\].*", post.title)
                            artisanMatch = re.search("\[Artisan\].*", post.title)
                            vendorMatch = re.search("\[Vendor\].*", post.title)
                            if not post.link_flair_text:
                                if not post.distinguished:
                                    if sellingMatch:
                                        post.link_flair_text = 'Selling'
                                        post.mod.flair(text='Selling', css_class='selling')
                                        log_msg = "SELL: " + clean_title
                                    elif buyingMatch:
                                        post.link_flair_text = 'Buying'
                                        post.mod.flair(text='Buying', css_class='buying')
                                        log_msg = "BUY: " + clean_title
                                    elif metaMatch:
                                        post.link_flair_text = 'META'
                                        post.mod.flair(text='META', css_class='meta')
                                        log_msg = "META: " + clean_title
                                    elif icMatch:
                                        post.mod.flair(text='Interest Check', css_class='interestcheck')
                                        log_msg = "IC: " + clean_title
                                    elif gbMatch:
                                        post.mod.flair(text='Group Buy', css_class='groupbuy')
                                        log_msg = "GB: " + clean_title
                                    elif artisanMatch:
                                        post.mod.flair(text='Artisan', css_class='artisan')
                                        log_msg = "Artisan: " + clean_title
                                    elif vendorMatch:
                                        post.mod.flair(text='Vendor', css_class='vendor')
                                        log_msg = "Vendor: " + clean_title
                                    else:
                                        post.link_flair_text = 'Trading'
                                        post.mod.flair(text='Trading', css_class='trading')
                                        log_msg = "TRADE: " + clean_title
                            else:
                                log_msg = "OTHER: " + clean_title

                            if post.link_flair_text == 'Selling' or post.link_flair_text == 'Trading':
                                #logging.info('Checking timestamp')
                                timestampMatch = re.search('http[s]?:\/\/(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', post.selftext, re.IGNORECASE)
                                if not timestampMatch:
                                    log_msg = 'BAD POST (timestamp) - ' + post.id + ' - ' + clean_title + ' - by: ' + post.author.name
                                    log_msg_level = 'warn'
                                    post.report('Missing timestamp')
                                    post.reply('REMOVED: Missing timestamps. Please read [wiki](/r/' + subreddit + rules + ') for posting rules. **Do not delete or repost**, just add the timestamp to the post and send a modmail indicating it\'s been added.\n\nIf this is a buying post, you may repost but do not include money related terms on the [W] side of the title.').mod.distinguish()
                                    post.mod.remove()
                                    removedpost = True

                            curs.execute('''SELECT username, lastid, lastpost as "lastpost [timestamp]" FROM flair WHERE username=?''', (post.author.name,))

                            row = curs.fetchone()

                            # ensure that time of last post is > 24hrs
                            if row is not None:
                                if not row['lastid']:
                                    lastid = ""
                                else:
                                    lastid = row['lastid']
                                if row['lastpost']:
                                    if (((((datetime.utcnow() - row['lastpost']).total_seconds() / 3600) < upper_hour) and (((datetime.utcnow() - row['lastpost']).total_seconds() / 60) > lower_min)) and (lastid != "") and (post.id != lastid) and not post.approved_by):
                                        log_msg = 'BAD POST (24hr) - ' + post.id + ' - ' + clean_title + ' - by: ' + post.author.name
                                        log_msg_level = 'warn'
                                        post.report('24 hour rule')
                                        post.reply('REMOVED: Posting too frequently.  Please read [wiki](/r/' + subreddit + rules ') for posting time limits.  If you believe this is a mistake, please message the [moderators](http://www.reddit.com/message/compose?to=%2Fr%2F' + subreddit + ').').mod.distinguish()
                                        post.mod.remove()
                                        removedpost = True

                            # check comments for info from bot
                            if not post.distinguished:
                                post.comments.replace_more(limit=0)
                                flat_comments = post.comments.list()
                                botcomment = 0
                                for comment in flat_comments:
                                    if hasattr(comment.author, 'name'):
                                        if comment.author.name == username:
                                            if not removedpost:
                                                botcomment = 1
                                # otherwise spit out user information
                                # have to check both flair class and regex match.  (flair class is none if just set)
                                if botcomment == 0 and (not metaMatch or post.link_flair_text != "Meta"):
                                    age = str(datetime.utcfromtimestamp(post.author.created_utc))
                                    if str(post.author_flair_text) == "None":
                                        heatware = "None"
                                    else:
                                        heatware = "[" + str(post.author_flair_text) + "](" + str(post.author_flair_text) + ")"
                                    if str(post.author_flair_css_class) == "None":
                                        post.author.flair_css_class = "i-none"
                                    if str(post.author_flair_css_class) == "i-mod":
                                        post.reply('* Username: ' + str(post.author.name) + '\n* Join date: ' + age + '\n* Link karma: ' + str(post.author.link_karma) + '\n* Comment karma: ' + str(post.author.comment_karma) + '\n* Reputation: User is currently a moderator.\n* Flair text: ' + str(post.author_flair_text) + '\n\n^^This ^^information ^^does ^^not ^^guarantee ^^a ^^successful ^^swap. ^^It ^^is ^^being ^^provided ^^to ^^help ^^potential ^^trade ^^partners ^^have ^^more ^^immediate ^^background ^^information ^^about ^^with ^^whom ^^they ^^are ^^swapping. ^^Please ^^be ^^sure ^^to ^^familiarize ^^yourself ^^with ^^the ^^[RULES](https://www.reddit.com/r/' + subreddit + rules + ') ^^and ^^other ^^guides ^^on ^^the ^^[WIKI](https://www.reddit.com/r/' + subreddit + '/wiki/index)').mod.distinguish()
                                    else:
                                        if str(post.author_flair_css_class) == "i-none":
                                            post.reply('* Username: /u/' + str(post.author.name) + '\n* Join date: ' + age + '\n* Link karma: ' + str(post.author.link_karma) + '\n* Comment karma: ' + str(post.author.comment_karma) + '\n* Reputation: No trades' '\n* Heatware: ' + heatware + '\n\n^^This ^^information ^^does ^^not ^^guarantee ^^a ^^successful ^^swap. ^^It ^^is ^^being ^^provided ^^to ^^help ^^potential ^^trade ^^partners ^^have ^^more ^^immediate ^^background ^^information ^^about ^^with ^^whom ^^they ^^are ^^swapping. ^^Please ^^be ^^sure ^^to ^^familiarize ^^yourself ^^with ^^the ^^[RULES](https://www.reddit.com/r/' + subreddit + rules + ') ^^and ^^other ^^guides ^^on ^^the ^^[WIKI](https://www.reddit.com/r/' + subreddit + '/wiki/index)').mod.distinguish()
                                        else:
                                            post.reply('* Username: /u/' + str(post.author.name) + '\n* Join date: ' + age + '\n* Link karma: ' + str(post.author.link_karma) + '\n* Comment karma: ' + str(post.author.comment_karma) + '\n* Reputation: ' + str(post.author_flair_css_class).translate(None, 'i-') + ' trade(s)' '\n* Heatware: ' + heatware + '\n\n^^This ^^information ^^does ^^not ^^guarantee ^^a ^^successful ^^swap. ^^It ^^is ^^being ^^provided ^^to ^^help ^^potential ^^trade ^^partners ^^have ^^more ^^immediate ^^background ^^information ^^about ^^with ^^whom ^^they ^^are ^^swapping. ^^Please ^^be ^^sure ^^to ^^familiarize ^^yourself ^^with ^^the ^^[RULES](https://www.reddit.com/r/' + subreddit + rules + ') ^^and ^^other ^^guides ^^on ^^the ^^[WIKI](https://www.reddit.com/r/' + subreddit + '/wiki/index)').mod.distinguish()

                            if (log_msg_level == 'warn'):
                                logger.warning(log_msg)
                            else:
                                logger.info(log_msg)

                            # add time to sql
                            if row is not None:
                                if (post.id == lastid):
                                    continue
                            if (removedpost):
                                continue
                            curs.execute('''UPDATE OR IGNORE flair SET lastpost=?, lastid=? WHERE username=?''', (datetime.utcnow(), post.id, post.author.name, ))
                            curs.execute('''INSERT OR IGNORE INTO flair (username, lastpost, lastid) VALUES (?, ?, ?)''', (post.author.name, datetime.utcnow(), post.id, ))
                            con.commit()

                logger.debug('Sleeping for 2 minutes')
                sleep(120)
        except Exception as e:
            logger.error(e)
            sleep(120)

if __name__ == '__main__':
    main()
