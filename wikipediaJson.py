import aiohttp
import asyncio
import requests
import webbrowser
import concurrent.futures
import re
from concurrent.futures import ThreadPoolExecutor

# chosen so that there's very few false positives, could choose
# a more lenient regex, but I prefer the Sketch ones to be nearly
# exclusively not real. If you were looking for a different category
# of domains, then you would change this RegEx to capture for those
# instead
USURPED_PATTERN = r"((Hongkong|HK|Result|Toto) (HK|Pools|Prize)|Togel Live|Live (Casino|Draw|Slot)|(Casino|Slot|Bola|Judi|Game|Gacor) Online|Roulette Blog|[ ](Judi|Mostbet([.]com)?|Chia s?|Giris|Siteleri|Canli|Bahis|Bonusu|Dotdash)($|[ ]))"

# just the default names of files expected.

# these are domains that you want to sort for whether or not their
# html contains "sketch" things (as defined by the USURPED_PATTERN above)
NAME_PRE_PROCESS = "domainsOnWikiToPreProcess.txt"
# these are ones from the above list that have some content that matchs
# the USURPED_PATTERN above in all of the HTML of the home page
NAME_SKETCH_OUTPUT = "domainsThatHaveSketch.txt"
# these ones do not match (or did not load). Frequently this still has many
# domains that are usurped so it's still a good idea to check it too!
NAME_LESS_CLEAR_OUTPUT = "domainsWhichAreLessClear.txt"

# name of file of domains that could plausibly be usurped that you want to check
# whether they are on Wikipedia. It will only print out the domain if it has
# not already been checked (i.e. is in NAME_ALREADY_CHECKED_DOMAIN)
NAME_CHECK_IF_ON_WIKI = "toCheck.txt"

# domains that have already been checked whether they're on Wikipedia/usurped
# includes both ones that are and aren't on Wikipedia and isn't particularly
# filtered for being usurped. Also contains a buncha junk words, but those
# are kinda ignored
NAME_ALREADY_CHECKED_DOMAIN = "alreadyChecked.txt"

# name of file that will be checked to see the path that the redirect
# takes (say redirecting from foo.com to foo1.com to foo2.com)
NAME_REDIRECTS = "redirectsToCheck.txt"
# all the redirects found (that aren't already present in NAME_ALREADY_CHECKED_DOMAIN)
NAME_REDIRECTS_FOUND = "allRedirects.txt"

# what tabs you want opened in Chrome
NAME_TABS_TO_OPEN = "tabsToOpen.txt"

# uh, really bad way of doing it, but it works. Basically figure out
# what JSON response from Wikipedia corresponds to having a search that
# fails.
url="https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=insource:%22medicaleduca3tionfutures.org%22&utf8=&format=json&srlimit=1"
response = requests.get(url)
NO_RESULTS_JSON_RESP = response.json()

# if Wikipedia ever has a problem with a search request, will be appended and
# printed out.
didntWork = []

# make super sure that the concurrent requests value isn't too high
# (run it with a super small value, then make sure that the number of
# domains found when using a bigger value matches)
MAX_WORKERS = 16
MAX_CONCURRENT_REQUESTS = 100
TIMEOUT_TIME = 60
# limits the number of http requests you can have going at once
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

# finds all domains in fileName (as defined by the RegEx in extract_domains)
# makes them lower-case and removes duplicates.
def getDomainsFromFile(fileName):
     with open(fileName, 'r') as file:
        domains = extract_domains(file.read())
        domains = [domain.lower() for domain in domains] # make it all lowercase
        domains = list(set(domains))
        return domains

# prints out theUrl if it's present on Wikipedia and has not already
# been checked
def printIfOnWikipedia(theUrl):
    # only check if it hasn't already been added to the list
    if theUrl not in ALREADY_ADDED_LIST:
        queryUrl = "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=insource:%22"
        queryUrl += theUrl
        queryUrl += "\%22&utf8=&format=json&srlimit=1"
        response = requests.get(queryUrl)
        result = response.json()
        if (result != NO_RESULTS_JSON_RESP):
            print(":* " + theUrl)
        if response.status_code != 200:
            didntWork.append(theUrl)

# extract all domains from a string. Gets rid of schemes before the domain
# like https or http. Returns a list of domains
def extract_domains(text):
    # Regular expression to capture domains, optionally with a scheme (http, https, ftp, etc.)
    url_pattern = r'(?:(?:https?|ftp):\/\/)?(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'

    # Find all matches
    domains = re.findall(url_pattern, text)

    # Remove schemes (http://, https://, ftp://, etc.) from the results
    clean_domains = [re.sub(r'^(?:https?|ftp):\/\/', '', domain) for domain in domains]

    return clean_domains

# a list of all domains checked
ALREADY_ADDED_LIST = getDomainsFromFile(NAME_ALREADY_CHECKED_DOMAIN)

# checks all domains in NAME_PRE_PROCESS, and writes them to
# NAME_SKETCH_OUTPUT and NAME_LESS_CLEAR_OUTPUT depending on whether
# they appear to have "sketch" content according to the USURPED_PATTERN
def preProcessDomains():
    domains = getDomainsFromFile(NAME_PRE_PROCESS)
    domainsWithHttps = ["https://" + domain for domain in domains]
    print(len(domains), "to pre-process")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(hasSketchContent, domainsWithHttps))

    with open(NAME_SKETCH_OUTPUT, 'w') as file:
        for i in range(len(domains)):
            if results[i]:
                file.write(":* " + domains[i] + '\n')
    with open(NAME_LESS_CLEAR_OUTPUT, 'w') as file:
       for i in range(len(domains)):
            if not results[i]:
                file.write(":* " + domains[i] + '\n')

# returns False if it does not match the RegEx. Returns what it matched
# with if it does match the RegEx (probably would be faster to just return True
# and make the RegEx non-capture-grouping but I don't understand RegEx well enough
# to do that lol)
def hasSketchContent(url):
    try:
        response = requests.get(url, timeout=15) # can't just let requests go on forever
    except requests.exceptions.RequestException as e:
        return False # if there's an error, then we can't consider it to have sketch
        # plausibly, this should be a third case because checking these has
        # different vibes than checking lessClear, but I haven't gotten around
        # to implementing that. I guess I'll check in TODO here :-)

    result = re.search(USURPED_PATTERN, response.text, re.IGNORECASE)
    if result:
        return result.group(0)
    return False

# checks the domains in NAME_CHECK_IF_ON_WIKI and prints them
# out if they are both present on the English wikipedia and also
# have not already been checked
def checkToCheckOnWiki():
    domains = getDomainsFromFile(NAME_CHECK_IF_ON_WIKI)

    print("Domains to process:", len(domains))
    # be nice on wikipedia's servers and only do 5 parallel, uh, occasionally
    # it does print two on one line which is kinda weird, but it makes sense
    # that print wouldn't exactly be thread-safe (I don't really know what that
    # word means tbh)
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(printIfOnWikipedia, domains)

    print(didntWork)

# get a domain from a url that may have http or the like.
# also removes www. from the domain
def getDomainFromUrl(urlWithHttp):
     # Regular expression to capture domains, optionally with a scheme (http, https, ftp, etc.)
    url_pattern = r'https?://(?:www\.)?([^/]+)'

    # Find the match, don't want www.
    match = re.search(url_pattern, urlWithHttp)

    if match:
        domain = match.group(1)
        return domain
    # if no match, return empty string I guess
    return ""


# Function to asynchronously get all intermediate redirects
async def get_redirect_url(session, url):
    async with semaphore:
        try:
            # session.head rather than session.get since we don't actually care
            # about the content
            async with session.head(url, allow_redirects=True, timeout = TIMEOUT_TIME) as response:
                return [str(resp.url) for resp in response.history] + [str(response.url)]
        except Exception as e: # if exception, who cares
            return []

# Function to manage asynchronous requests
async def fetch_redirects(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [get_redirect_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

# Function to run the async call in a thread. I'm not sure this is
# actually faster, but I like having it I guess?
def run_async_fetch_redirects(urls):
    return asyncio.run(fetch_redirects(urls))

# writes all the places that the domains in NAME_REDIRECTS redirect to
# that are not already present in alreadyChecked.txt
def getNewRedirects():
    domains = getDomainsFromFile(NAME_REDIRECTS)
    # add prefix
    domainsWithHttps = ["https://" + domain for domain in domains]
    print(len(domainsWithHttps), "domains to check for redirects")

    # results = asyncio.run(fetch_redirects(domainsWithHttps))
    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future = executor.submit(run_async_fetch_redirects, domainsWithHttps)
        results = future.result()

    flattenResults = [getDomainFromUrl(domain)
                            for domainLists in results
                                for domain in domainLists
                    ]
    flattenResultsDeDup = list(set(flattenResults))
    ALREADY_ADDED_LIST = getDomainsFromFile(NAME_ALREADY_CHECKED_DOMAIN)

    print(len(flattenResultsDeDup), "domains found redirected")
    with open(NAME_REDIRECTS_FOUND, 'w') as file:
        for domain in flattenResultsDeDup:
            if domain not in ALREADY_ADDED_LIST:
                file.write(domain + '\n')

# opens the tabs in NAME_TABS_TO_OPEN in Chrome
def openTabs():
    path = webbrowser.get("open -a /Applications/Google\ Chrome.app %s")
    domains = getDomainsFromFile(NAME_TABS_TO_OPEN)
    # add prefix
    domainsWithHttps = ["https://" + domain for domain in domains]
    [path.open(url) for url in domainsWithHttps]

# print all domains in file1 not in file2
def printDiff(file1, file2):
    fileOne = getDomainsFromFile(file1)
    fileTwo = getDomainsFromFile(file2)
    for domain in fileOne:
        if domain not in fileTwo:
            print(":* " + domain)

# just comment out the one you want to run currently
if __name__ == '__main__':
    pass

    # openTabs()


# given toCheck.txt, print out the ones that are on wikipedia
    # checkToCheckOnWiki()

# look at domainsOnWikiToPreProcess.txt and look at each url and what
# is actually on each and see if it matches a regex (this regex is defined
# at the very top, and it has very very few false positives)
    # preProcessDomains()

# make a new file with all the domains that have not been checked before
# that are redirects from domains in redirectsToCheck.txt (sorry future
# me for writing meaningless stuff)
    # getNewRedirects()

# seems like you get a bunch extra if you just run getNewRedirects
# on the contents of alreadyChecked every once and a while

# suggested order of execution if you find new urls that may be usurped
# first getNewRedirects, then checkToCheckOnWiki, then preProcess them,
# then use openTabs a number of times to manually check them. For those
# which have sketch, it's fine to just do a batch of like 40 and look
# at them with your eyes to see if they indeed have sketch. For those
# that are less clear, I like to do closer to 10 and delete the ones
# that don't have sketch as I notice them