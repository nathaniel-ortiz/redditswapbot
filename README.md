# redditswapbot

## Description

Scripts that are used on /r/mechmarket and /r/hardwareswap created by the mods of /r/hardwareswap and modified for use by /u/chankster, /u/NotMelNoGuitars, and /u/thelectronicnub. There are three currently running instances of the bot, /u/hwsbot, /u/mechkbot, /u/funkoswapbot.  Finally updated to support Praw v5.

## Files

* **flair.py**
  * Watches the current confirmed trade post (specified in config.cfg) and updates user flair.
  * Normally fired via cronjob.
  * Accepts -m (curr,prev) to allow for processing of the previous month.
  * Checks flairs against a database and will warn if the flair deviates more than the value in the config.  Helps to catch users that accidently hide flair and end up getting reset
  * Easier manual flair processing.  Simply send the bot a message with the URL of the root comment in the body (click permalink first).  The bot will flair the users, delete the warning message, approve the reported comment, reply with 'added', and send a confirming PM to the mod.
  * **The flair import must be run before this can be run!**
* **heatware.py**
  * Watches the current heatware thread (specified in config.cfg) and updates user flair.
  * Normally fired via cronjob.
* **post_check.py**
  * Monitors all new posts to ensure it matches specified regexs.
  * Attempts to set post flair based on title.
  * Adds comment to each post with specific details for the OP.
  * Removes posts created < 24 hours after the previous post.
  * Checks all selling and trading posts for a timestamp.
  * **The flair import script must be run before this script**
* **monthly_trade_post.py**
  * Creates a new trade post, stickies it in the top position, updates the sidebar based on regex, and updates config file.
  * Normally fired via cronjob.
* **monthly_price_post.py**
  * Creates a new price post, stickies it in the bottom position, updates the sidebar based on regex, updates config file.
  * Normally fired via cronjob.
* **util/flair_sql_import.py** 
  * Used to seed the sqlite database with initial flair values.
  * Extract the current subreddit flair values to json using [modutils](https://github.com/praw-dev/prawtools).
  * **Must be done before running flair.py otherwise any flair > flairdev in config will be reported as a deviation.**
* **util/flair_sub_import.py**
  * Set subreddit flair via csv or json files

## TODO

