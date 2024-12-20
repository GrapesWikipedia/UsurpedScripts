Uhh, this is probably a good thing to have. The code itself is in wikipediaJson.py
Which is kinda terrible name. Feel free to use/modify the code however you want, for
Whatever purposes you want. I think it probably kinda works, but I'm not gonna
Make any such guarantees

# Description of Files:
* `alreadyChecked.txt`
    * File with domains that have been run through `toCheck.txt`. A lot of these
    Could plausibly have gambling or other usurped stuff on them, but I know
    That not all of them do.

* `definitelyUsurped.txt`
    * Mostly domains that are present on Wikipedia that I know are usurped, or
    Redirects of ones that I know are usurped. Domains only get added here if
    They have been manually checked as usurped or are redirected from a domain
    That has been manually checked as usurped.

* `example3Added.txt`
    * The example3 pages that I have added to `allRedirects.txt` to find all the
    Redirects. Note that it only shows you the first 2000 pages, which is kinda
    Annoying, so if anyone figures out how to show more than that, that'd be super
    Helpful!!

* `tabsToOpen.txt`, `domainsOnWikiToPreProcess.txt`, `toCheck.txt`, `redirectsToCheck.txt`
    * Given blank files to make copying and pasting between things easier.

# How to even run stuff:
So I have a sorta suggested procedure that I've been using. No idea whether it's
Ideal or whatever, but it's worked so far :-). The steps I've been going through
Are as follows.
* Get a collection of domains that could plausibly be usurped
* Paste those into a file called `redirectsToCheck.txt`
* Run the function `getNewRedirects()`
* Take the contents of the created file `allRedirects.txt` and paste them into
 a file called `toCheck.txt`
* Run the function `checkToCheckOnWiki()`
* Paste what that function printed out into a file called `domainsOnWikiToPreProcess.txt`
* Manually check the ones in `domainsThatHaveSketch.txt` and `domainsWhichAreLessClear.txt`
    * I've been using `openTabs()` to more quickly open tabs and lets me simply just glance
    At the page to see if it's indeed usurped or not.
* Once you have done all that, paste in the contents of `toCheck.txt` into `alreadyChecked.txt`
 Since they have, after all, now been checked.

## Dunno, a note??
One collection of domains that could plausibly be usurped is `alreadyChecked.txt`, which
I on occasion run through the steps above and frequently the various redirect links
Shift and I find some more domains to check. You can do that too.

# Limitations:
* Doesn't really handle IP address domains with any grace (kinda just ignores them)

# Pip requirements
There's a few required packages not already included with Python which are in requirements.txt. You can download those by running the command `pip install requirements.txt` in your Terminal.

# Running Stuff
Uh, one super important thing is that near the top there's the lines with
```
MAX_WORKERS = 16
MAX_CONCURRENT_REQUESTS = 100
TIMEOUT_TIME = 60
```
Which work well for my machine, but may need to be messed with for your machine. I don't have any idea how to recommend numbers, though I think the high timeout is somewhat valuable (though it can get annoying if you're checking very few domains). It will generally go faster if `MAX_WORKERS` and `MAX_CONCURRENT_REQUESTS` are bigger, but sometimes it misses redirects if those are too high, so uh, mess around with those and pick values that work well for your computer.