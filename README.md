# redditswapbot

## Description

Scripts that are used on /r/mechmarket and /r/hardwareswap created by the mods of /r/hardwareswap and modified for use by /u/chankster, /u/NotMelNoGuitars, and /u/thelectronicnub

## Files

* flair.py - Watches the current confirmed trade post (specified in config.cfg) and updates user flair.
* heatware.py - Watches the current heatware thread (specified in config.cfg) and updates user flair.
* post_check.py - Monitors all new posts to ensure it matches specified regexs.  Attempts to set post flair based on title.  Adds comment to each post with specific details for the OP.
* monthly_trade_post.py - Creates a new trade post, stickies it in the top position, updates the sidebar based on regex, and updates config file.  Normally fired via cronjob.
* weekly_price_post.py - Creates a new price post, stickies it in the bottom position, updates the sidebar based on regex, updates config file.  Normally fired via cronjob.

## TODO

* Upgrade to OAuth2, since password-based login will be deprecated soon
* Switch to MySQL/SQLite for logging instead of a flatfile
* Implement multiproccess 
* Make the bot stricter so that it matches the username in the comment with the commenter's username
