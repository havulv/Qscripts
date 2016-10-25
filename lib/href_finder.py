#!/usr/bin/env python3

'''
    A general spider for searching for a specific url within a set of structured urls

    TODO:
        -Introduce logging to handle offsite emails etc.
        -extend to arbitrary element/tag
        -Document
        -Implement logging on failure instead of program stoppage
        -Combine this with other requests modules in this directory
'''

import logging as log
import requests, time, re, sys, csv, os
from bs4 import BeautifulSoup as bs
from requests.exceptions import MissingSchema, ConnectionError

LOG_DIR = os.path.join(os.getcwd(), os.path.normpath("log/"))

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
logfile = open(os.path.join(LOG_DIR, "href_find.log"), 'a')
logfile.close()

log.basicConfig(level=log.DEBUG, filename=os.path.join(LOG_DIR, "href_find.log"),
        format="%(asctime)s [%(levelname)s] ::: %(message)s")


# Requires the url to be given as a keyword argument for implementation
# in more places. There should be a "tries" keyword to support recursion
# limits
def connection_correct(func, *args, tries=0, **kwargs):
    if tries >= 4:
        raise Exception("Connection correction ultimately failed")
    try:
        func_ret = func(*args, **kwargs)
    except (MissingSchema, ConnectionError) as e:
        for key in kwargs:
            if key == 'url':
                url = kwargs['url'].split('/')
                if isinstance(e, ConnectionError):
                    log.warn("ConnectionError on {} : {}".format(
                                                    kwargs['url'], e))
                    if 's' not in url[0]:
                        kwargs['url'] = '/'.join(
                                ['https:'] + url[1:])
                    elif 's' in url[0]:
                        kwargs['url'] = '/'.join(
                                ['http:'] + url[1:])
                    else: raise e
                elif isinstance(e, MissingSchema):
                    log.warn("MissingSchema on {} : {}".format(
                                                kwargs['url'], e))
                    if 'http' not in url[0] and '' != [0]:
                        kwargs['url'] = '/'.join(
                                ['http', ''] + url)
                    elif 'http' not in url[0]:
                        kwargs['url'] = '/'.join(
                                    ['http'] + url)
                    else: raise e
            else:
                print("There was no url keyword supplied."
                        "Please refactor your code")
                raise e
        log.debug("Retrying url as {}".format(kwargs['url']))
        func_ret = connection_correct(func, *args,
                            tries=(tries+1), **kwargs)
    return func_ret

'''
    Note: There is the possibility that someone could overload tries so
    that connection_correct will automatically call it's exception. This
    should only happen if someone passes "tries" as a keyword through a
    decorated function.
'''

def connection_errors(func):
    def wrap_request(*args, **kwargs):
        func_ret = connection_correct(func, *args, **kwargs)
        return func_ret
    return wrap_request

@connection_errors
def goto(url="localhost"):
    headers = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) '
                            'AppleWebKit/537.36 (KHTML, like Gecko) '
                            'Chrome/32.0.1667.0 Safari/537.36'
                }
    req = requests.get(url, headers=headers)
    return req.text if req.status_code == 200 else None

# schema must already be regex compiled
def get_hrefs(text):
    log.debug("Getting hrefs for previous url")
    html = bs(text, 'html.parser')
    hrefs = {tag['href'].strip() for tag in html.find_all(href=True)}
    return hrefs

def match(hrefs, schema):
    log.debug("Matching {} against {}".format(hrefs, schema))
    return set(filter(lambda x: schema.search(x) and x[:7] != "mailto:", hrefs))

def user_in():
    url = input("What is the site you wish to crawl?\n").strip()
    find = re.compile("(" +
            input("What is the specific page you want to trace?"
                                                "\n").strip() + ")")
    schema = re.compile("(" +
            input("Is there a specific url structure to speed up"
                                        " searching?\n").strip() + ")")
    log.debug("User input: url={}, find={}, schema={}".format(url, find, schema))
    return url, find, schema

def validate_url(base_url, addendum):
    ret_url = addendum
    if "http" not in addendum:
        ret_url = '/'.join(base_url.split('/')[:-1] +
                            addendum.split('/')[1:])
    return ret_url

def on_site_only(base_url, urls):
    return set(filter( lambda x: x[:len(base_url)] == base_url, urls))

def loop(url, find, schema):
    base_url = url
    time_out = robot_read(base_url)
    pages, gone_to, to_go = [], set(), set()
    while True:
        print(":: Scraping {}".format(url))
        html = goto(url=url)

        if html == None:
            url = to_go.pop()
            gone_to.add(url)
            time.sleep(time_out)
            continue

        hrefs = get_hrefs(html)
        matched = on_site_only(base_url, map(
            lambda x: validate_url(base_url, x), match(hrefs, schema)))
        found = match(matched, find)
        log.debug("find : {}, match : {}".format(found, matched))
        if found:
            pages.append(url)

        to_go |= (matched - gone_to)
        log.debug("to_go : {}, gone_to : {}".format(to_go, gone_to))
        try:
            url = to_go.pop()
            gone_to.add(url)
            time.sleep(time_out)
        except KeyError:
            break
    print(pages)
    return pages

def robot_read(base_url):
    t_out = 5
    html = goto('/'.join(base_url.split('/') + ["robots.txt"]))
    for line in html.split('\n'):
        if "Crawl-delay:" == line[:12]:
            t_out = int(line[12:])
            break
    log.debug("Setting time out to {}".format(t_out))
    time.sleep(t_out)
    return t_out


def write_to(out, pages):
    sheet = open(out+".csv", 'w', newline="")
    log.debug("Writing to file {}.csv".format(out))
    writer = csv.writer(sheet)
    for page in pages:
        writer.writerow([page])
    sheet.close()

def main(out, seek_tuple):
    if not seek_tuple:
        pages = loop(*user_in())
    else:
        pages = loop(*seek_tuple)
    print(":: Writing to file")
    write_to(out, pages)
    print(":: File closed and exiting program.")

if __name__ == "__main__":
    try:
        out = sys.argv[1]
        seek_tuple = [sys.argv[1].strip()] + list(map(
            lambda x: re.compile("(" + x.strip() + ")"),
                [sys.argv[3], sys.argv[4]]))
    except IndexError:
        out = "Pages_With_URL"
        seek_tuple = None
    finally:
        main(out, seek_tuple)