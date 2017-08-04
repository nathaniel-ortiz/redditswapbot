#!/usr/bin/env python2

import sys, os
import praw
import sqlite3
import datetime
from ConfigParser import SafeConfigParser
from datetime import datetime, timedelta
from time import sleep, time
from log_conf import LoggerManager
import argparse
# determine curr or prev month
parser = argparse.ArgumentParser(description="Process flairs")
parser.add_argument("-m", action="store", dest="month", default="curr", help="curr or prev month? (default: curr)")
results = parser.parse_args()
conf_link_id = 'link_id'
if results.month == "prev":
    conf_link_id = 'prevlink_id'

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
link_id = cfg_file.get('trade', conf_link_id)
equal_warning = cfg_file.get('trade', 'equal')
age_warning = cfg_file.get('trade', 'age')
karma_warning = cfg_file.get('trade', 'karma')
dev_warning = cfg_file.get('trade', 'dev')
added_msg = cfg_file.get('trade', 'added')
age_check = int(cfg_file.get('trade', 'age_check'))
karma_check = int(cfg_file.get('trade', 'karma_check'))
flair_db = cfg_file.get('trade', 'flair_db')
flair_dev = cfg_file.get('trade', 'flair_dev')

# Configure logging
logger = LoggerManager().getLogger(__name__)

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
        if comment.is_root is True:
            return False
        if comment.banned_by:
            return False
        return True

    def check_self_reply():
        if comment.author.name == parent.author.name:
            item.reply(equal_warning)
            item.report('Flair: Self Reply')
            parent.report('Flair: Self Reply')
            save()
            return False
        return True

    def verify(item):
        karma = item.author.link_karma + item.author.comment_karma
        age = (datetime.utcnow() - datetime.utcfromtimestamp(item.author.created_utc)).days

        curs.execute('''SELECT * FROM flair WHERE username=?''', (item.author.name,))

        row = curs.fetchone()

        if row is not None:
            if not item.author_flair_css_class:
                item.author_flair_css_class = ''
            if not row['flair_css_class']:
                db_flair_css_class = ''
            if item.author_flair_css_class == "i-mod":
                return True
            if (int(item.author_flair_css_class.translate(None, 'i-') or 0) > (int(row['flair_css_class'].translate(None, 'i-') or 0) + int(flair_dev))) or (int(item.author_flair_css_class.translate(None, 'i-') or 0) < (int(row['flair_css_class'].translate(None, 'i-') or 0) - int(flair_dev))):
                logger.info('Rechecking deviation: ' + item.author.name)
                second_chance = next(r.subreddit(subreddit).flair(item.author.name))
                if second_chance['flair_css_class'] == item.author_flair_css_class:
                    item.report('Flair: Deviation between DB and Reddit')
                    #item.reply(dev_warning)
                    r.subreddit(subreddit).message('Flair Devation Detected', 'User: /u/' + item.author.name + '\n\nDB: ' + str(row['flair_css_class']) + '\n\nReddit: ' + str(item.author_flair_css_class))
                    logger.info('Flair Deviation - User: ' + item.author.name + ', DB: ' + str(row['flair_css_class']) + ', Reddit: ' + str(item.author_flair_css_class))
                    save()
                    return True

        if item.author_flair_css_class < 1:
            if age < age_check:
                item.report('Flair: Account Age')
                item.reply(age_warning)
                save()
                return False
            if karma < karma_check:
                item.report('Flair: Account Karma')
                item.reply(karma_warning)
                save()
                return False
        return True

    def values(item):
        if not item.author_flair_css_class or item.author_flair_css_class == 'i-none':
            item.author_flair_css_class = 'i-1'
        elif (item.author_flair_css_class and ('i-mod' in item.author_flair_css_class or 'i-vendor' in item.author_flair_css_class)):
            pass
        else:
            item.author_flair_css_class = ('i-%d' % (int(''.join([c for c in item.author_flair_css_class if c in '0123456789'])) + 1))
        if not item.author_flair_text:
            item.author_flair_text = ''

    def flair(item):
        if item.author_flair_css_class != 'i-mod':
            r.subreddit(subreddit).flair.set(item.author, item.author_flair_text, item.author_flair_css_class)
            logger.info('Set ' + item.author.name + '\'s flair to ' + item.author_flair_css_class)
            # Set flair in database
            curs.execute('''UPDATE OR IGNORE flair SET flair_text=?, flair_css_class=? WHERE username=?''', (item.author_flair_text, item.author_flair_css_class, item.author.name, ))
            curs.execute('''INSERT OR IGNORE INTO flair (username, flair_text, flair_css_class) VALUES (?, ?, ?)''', (item.author.name, item.author_flair_text, item.author_flair_css_class, ))
            con.commit()

        for com in flat_comments:
            if hasattr(com.author, 'name'):
                if com.author.name == item.author.name:
                    com.author_flair_css_class = item.author_flair_css_class

    def save():
        with open(link_id + ".log", 'a') as myfile:
                myfile.write('%s\n' % comment.id)

    try:
        # Load old comments
        with open(link_id + ".log", 'a+') as myfile:
            completed = myfile.read()

        try:
            con = sqlite3.connect(flair_db)
            con.row_factory = sqlite3.Row
        except sqlite3.Error, e:
            logger.exception("Error %s:" % e.args[0])

        curs = con.cursor()

        # Log in
        logger.info('Logging in as /u/' + username)
        r = praw.Reddit(client_id=app_key,
                        client_secret=app_secret,
                        username=username,
                        password=password,
                        user_agent=username)

        # Get the submission and the comments
        logger.info('Starting to grab comments')
        submission = r.submission(id=link_id)
        submission.comments.replace_more(limit=None, threshold=0)
        flat_comments = submission.comments.list()

        logger.info('Finished grabbing comments')

        for comment in flat_comments:
            if not hasattr(comment, 'author'):
                continue
            if not conditions():
                continue
            parent = [com for com in flat_comments if com.fullname == comment.parent_id][0]
            if not hasattr(parent.author, 'link_karma'):
                continue
            if not check_self_reply():
                continue

            if not comment.author.name.lower() in parent.body.lower():
                continue

            # Check Account Age, Karma, and Flair Deviation
            logger.debug('Verifying comment id: ' + comment.id + ' and parent id: ' + parent.id)
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
