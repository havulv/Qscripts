#!/usr/bin/env python3

'''
    Scraper for similarweb so I don't have to go to the site every time
'''

import requests, re
from bs4 import BeautifulSoup as bs

def get_sweb(site):
    sw_url = 'https://www.similarweb.com/website/' + site
    req = requests.get(sw_url)
    return req if req.status_code == 200 else False

def get_stats(req):
    soup = bs(req.text, 'html.parser')
    vals = soup.find_all('div', {'class' : 'engagementInfo-line'})
    site_stats = [] # type: list
    for tag in vals:
        try:
            site_stats.append(
                tag.find(
                    'span',
                    { 'class' :
                        'engagementInfo-valueNumber js-countValue'}
                    ).string
                )
        except AttributeError:
            site_stats.append(
                tag.find(
                    'span',
                    { 'class' :
                    'engagementInfo-value u-text-ellipsis js-countValue'}
                    ).string
                )

    # Could do a filter object here but there is no need for lazy evals
    site_stats = ["N/A" if stat == None else stat for stat in tag]

    if site_stats[0][-1] == 'B':
        site_stats[0] = int(float(site_stats[0][:-1])*(10**9))
    elif site_stats[0][-1] == 'M':
        site_stats[0] = int(float(site_stats[0][:-1])*(10**6))
    elif site_stats[0][-1] == 'K':
        site_stats[0] = int(float(site_stats[0][:-1])*(10**3))
    return site_stats

def printer(site_list):
    b4_com = re.compile('(.*)//(.*)')
    prnt_str = "{0:<20} {1:^16} {2:^16} {3:^16} {4:^16}"
    print(prnt_str.format('Site', 'Total Visits',
        'Avg. Visit Dur.','Pages per Visit', 'Bounce Rate'))
    for i in site_list:
        for j in range(len(i)):
            if isinstance(i[j], str):
                if b4_com.match(i[j]):
                    i[j] = b4_com.split(i[j])[2]
            elif isinstance(i[j], int):
                continue
            if len(i[j]) > 20:
                i[j] = i[j][:18]+ '...'
        print("{0:<20} {1:^16,} {2:^16} {3:^16} {4:^16}".format(*i))


def main(*args):
    ret_sites = []
    for i in args:
        site = get_sweb(i)
        if site:
            ret_sites.append([i, *(get_stats(site))])
        else: raise Exception("THERE WAS A STATUS CODE ERROR!!\n"
                "THEIR ON TO US, ABORT -- ABORT!!")
    printer(ret_sites)

if __name__ == "__main__":
    from sys import argv
    main(*argv[1:])

