#!/usr/bin/env python2

import sys, os
import json
import argparse
import sqlite3 as lite

con = None

def extant_file(x):
    if not os.path.exists(x):
        raise argparse.ArgumentError("{0} does not exist".format(x))
    return x

def main():
    parser = argparse.ArgumentParser(description="Import flairs")
    parser.add_argument("-f", "--file", dest="filename", help="json input file", metavar="FILE", type=extant_file, required=True)
    args = parser.parse_args()

    try:
        con = lite.connect('flair.db')
    except lite.Error, e:
        print "Error %s:" % e.args[0]
        sys.exit(1)

    curs = con.cursor()

    curs.execute('''CREATE TABLE IF NOT EXISTS flair (
username TEXT PRIMARY KEY NOT NULL ,
flair_text TEXT,
flair_css_class TEXT,
lastpost timestamp,
lastpostid TEXT,
lastid TEXT DEFAULT ''
)''')

    flair_json = json.load(open(args.filename))

    curs.executemany('INSERT INTO flair (username, flair_text, flair_css_class) VALUES (:user, :flair_text, :flair_css_class)', flair_json)

    con.commit()

    if con:
        con.close()

if __name__ == "__main__":
    main()
