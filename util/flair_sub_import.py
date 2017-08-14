#!/usr/bin/env python2

import sys, os
import json
import argparse
import praw
from ConfigParser import SafeConfigParser

containing_dir = os.path.dirname(os.path.abspath(os.path.dirname(sys.argv[0])))
cfg_file = SafeConfigParser()
path_to_cfg = os.path.join(containing_dir, 'config.cfg')
cfg_file.read(path_to_cfg)
username = cfg_file.get('reddit', 'username')
password = cfg_file.get('reddit', 'password')
app_key = cfg_file.get('reddit', 'app_key')
app_secret = cfg_file.get('reddit', 'app_secret')
subreddit = cfg_file.get('reddit', 'subreddit')

def extant_file(x):
    if not os.path.exists(x):
        raise argparse.ArgumentError("{0} does not exist".format(x))
    return x

def main():
    parser = argparse.ArgumentParser(description="Import flairs to subreddit")
    parser.add_argument("-f", "--file", dest="filename", help="input file", metavar="FILE", type=extant_file, required=True)
    parser.add_argument("-t", "--type", dest="filetype", help="json or csv", metavar="TYPE", type=str, choices=['json', 'csv'], required=True)
    args = parser.parse_args()

    r = praw.Reddit(client_id=app_key,
                    client_secret=app_secret,
                    username=username,
                    password=password,
                    user_agent=username)

    if args.filetype == "json":
        r.subreddit(subreddit).flair.update(load_json(args.filename))
    elif args.filetype == "csv":
        r.subreddit(subreddit).flair.update(load_csv(args.filename))

def load_json(file):
    flair_json = json.load(open(file))
    for entry in flair_json:
        if entry['flair_css_class'] is None:
            entry['flair_css_class'] = "i-none"
        if 'i-' not in entry['flair_css_class']:
            entry['flair_css_class'] = "i-" + entry['flair_css_class']
        print("Setting username: \'" + entry['user'] + "\' to flair_css_class: \'" + entry['flair_css_class'] + "\' and flair_text to: \'" + str(entry['flair_text']) + "\'")

    return flair_json

def load_csv(file):
    flair_dict = []
    print "start"
    with open(file) as flair:
        for line in flair:
            username, flair_css, flair_text = line.rstrip().split(',')
            if 'i-' not in flair_css:
                flair_css = "i-" + flair_css
            print("Setting username: \'" + username + "\' to flair_css_class: \'" + flair_css + "\' and flair_text to: \'" + flair_text + "\'")
            i = {
                'user': username,
                'flair_css_class': flair_css,
                'flair_text': flair_text,
            }
            flair_dict.append(i)

    return flair_dict

if __name__ == "__main__":
    main()
