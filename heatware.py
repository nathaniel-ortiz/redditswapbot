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
app_key = cfg_file.get('reddit', 'app_key')
app_secret = cfg_file.get('reddit', 'app_secret')
subreddit = cfg_file.get('reddit', 'subreddit')
link_id = cfg_file.get('heatware', 'link_id')
reply = cfg_file.get('heatware', 'reply')
regex = cfg_file.get('heatware', 'regex')

# Configure logging
logger = LoggerManager().getLogger(__name__)

def main():
    try:
        logger.debug('Logging in as /u/' + username)
        r = praw.Reddit(client_id=app_key,
                        client_secret=app_secret,
                        username=username,
                        password=password,
                        user_agent=username)

        # Get the submission and the comments
        submission = r.submission(id=link_id)
        submission.comments.replace_more(limit=None, threshold=0)
        flat_comments = submission.comments.list()

        for comment in flat_comments:
            logger.debug("Processing comment: " + comment.id)
            if not hasattr(comment, 'author'):
                continue
            if comment.is_root is True:
                heatware = re.search(regex, comment.body)
                if heatware:
                    url = heatware.group(0)
                    if not comment.author_flair_text:
                        replies_flat = comment.replies.list()
                        for reply in replies_flat:
                            if reply.author:
                                if str(reply.author.name) == username:
                                    break
                        else:
                            if comment.author:
                                if comment.author_flair_css_class:
                                    r.subreddit(subreddit).flair.set(comment.author, url, comment.author_flair_css_class)
                                else:
                                    r.subreddit(subreddit).flair.set(comment.author, url, '')
                                logger.info('Set ' + comment.author.name + '\'s heatware to ' + url)
                                if reply:
                                    comment.reply(reply)

    except Exception as e:
        logger.error(e)

if __name__ == '__main__':
    main()
