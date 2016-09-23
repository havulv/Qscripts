#!/usr/bin/env python3

from bs4 import BeautifulSoup as bs
import requests, sys

def html(sitename):
    req = requests.get(sitename)
    return req.text if req.status_code == 200 else req.status_code

def sift(html):
    page = bs(html, 'html.parser')
    dscrp = page.find('meta', {'name' : 'description'})
    if not dscrp:
        dscrp = page.find('meta', {'property' : 'og:description'})
    return dscrp.get('content')

def main():
    try:
        site = sys.argv[1]
    except IndexError:
        site = input("WHAT IS THE SITENAME????")
    pg = html(site)
    if isinstance(pg, str):
        print(sift(pg))
    else:
        raise ValueError("{0} Error".format(pg))

if __name__ == "__main__":
    main()
