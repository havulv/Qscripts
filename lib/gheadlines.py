#!/usr/bin/env python3

from pprint import pprint as pp

import requests, sys
from bs4 import BeautifulSoup as bs

def findurl(gquery):
    return gquery[gquery.find("https://"):gquery.find("&sa=")]

def filterSrch(rslt):
    return rslt[0] != "Cached" and rslt[0] and "/url" in rslt[1]

def get(site, topic):
    headers = {'User-Agent' : 'Mozilla/5.0'}
    req = requests.get("https://www.google.com/search?q=site:" + \
            site + "+" + topic + "&tbs=qdr:y", headers=headers)
    return req.text if req.status_code == 200 else req.status_code

def get5(html):
    html = bs(html, "html.parser")
    headlines = [ (tag.text, tag.get('href')) for tag in \
                                            html.find_all('a')]
    headlines = list(filter( filterSrch, headlines))

    headlines = [(x[0], findurl(x[1])) for x in headlines]
    return headlines[:5]

def main():
    sitename, topic = (sys.argv[1], sys.argv[2])
    request = get(sitename, topic)
    if not isinstance(request, int):
        pp(get5(request))
    else:
        print("Your google request failed with {0}".format(request))

if __name__ == "__main__":
    main()

