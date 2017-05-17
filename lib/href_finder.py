#!/usr/bin/env python3

'''
    A general spider for searching for a specific url within a set of structured urls

    TODO:
        -Introduce logging to handle offsite emails etc.
        -extend to arbitrary element/tag
        -Document
        -Combine this with other requests modules in this directory

    FIXME:
        -Refactor everything, this entire thing is terrible

    POSITIVES:
        -Although the code is terrible, the logic is relatively straightforward
'''

from time import sleep as slp
import logging as log
import requests
import argparse
import re
import csv
import os
import sys
from bs4 import BeautifulSoup as bs
from requests.exceptions import MissingSchema, ConnectionError

TERM_ROW, TERM_COL = os.get_terminal_size()

LOG_DIR = os.path.join(os.getcwd(), os.path.normpath("log/"))

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
logfile = open(os.path.join(LOG_DIR, "href_find.log"), 'a')
logfile.close()

log.basicConfig(level=log.DEBUG,
                filename=os.path.join(LOG_DIR, "href_find.log"),
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
                    log.warn(
                        "ConnectionError on {} : {}".format(kwargs['url'], e))
                    if 's' not in url[0]:
                        kwargs['url'] = '/'.join(['https:'] + url[1:])
                    elif 's' in url[0]:
                        kwargs['url'] = '/'.join(['http:'] + url[1:])
                    else:
                        raise e
                elif isinstance(e, MissingSchema):
                    log.warn("MissingSchema on {} : {}".format(kwargs['url'], e))
                    if 'http' not in url[0] and '' != [0]:
                        kwargs['url'] = '/'.join(['http', ''] + url)
                    elif 'http' not in url[0]:
                        kwargs['url'] = '/'.join(['http'] + url)
                    else:
                        raise e
            else:
                print("There was no url keyword supplied."
                      "Please refactor your code")
                raise e
        wait = 4
        while wait > 0:
            log.debug("Sleeping until retry")
            slp(1)
            wait -= 1

        log.info("Retrying url as {}".format(kwargs['url']))
        func_ret = connection_correct(
            func, *args,
            tries=(tries + 1), **kwargs)
    return func_ret


def ctrl_c(func):
    def wrap(*args, **kwargs):
        func_ret = func(*args, **kwargs)
        return func_ret
    return wrap


def connection_errors(func):
    def wrap_request(*args, **kwargs):
        func_ret = connection_correct(func, *args, **kwargs)
        return func_ret
    return wrap_request


def reg_compiler(string):
    return re.compile(
        '(' + string.strip("\" ").replace(".", "\.").replace("/", "\/") + ')')


@connection_errors
def goto(url="localhost"):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/32.0.1667.0 Safari/537.36'}

    req = requests.get(url, headers=headers)
    return req.text if req.status_code == 200 else None


# schema must already be regex compiled
def get_hrefs(text):
    log.debug("Getting hrefs for previous url")
    html = bs(text, 'html.parser')
    hrefs = {tag['href'].strip() for tag in html.find_all(href=True)}
    return hrefs


def get_tags(tag, text):
    log.debug("Getting {} for previous url".format(tag))
    html = bs(text, 'html.parser')
    elements = [i.contents[0] for i in html.find_all(tag)]
    return elements


# TODO Refactor
def match(hrefs, schema):
    '''
        Matches hrefs against a regex -> schema

        This was originally a really hacky way of banning the bot
        from going to specific URLs (media, etc.) but, I have
        refactored so that the bot will never visit a URL with a
        file extension that is less than 4 characters. So the bot
        will still visit .html, but not .css or .js

        This can still be refactored further, as the idiom below is shit
    '''
    log.debug("Matching {} against {}".format(hrefs, schema))
    retval = set()
    try:
        iter_schema = iter(schema)
    except TypeError:
        retval = set(filter(
            lambda x: re.search(schema, x) and x[:7] != "mailto:", hrefs))
    else:
        for i in iter_schema:
            for j in filter(
                    lambda x: re.search(i, x) and x[:7] != "mailto:", hrefs):
                retval.add(j)

    return retval


def sift(html, tag):
    page = bs(html, 'html.parser')
    tagged = page.find('meta', {'name': tag})
    if not tagged:
        tagged = page.find('meta', {'property': 'og:' + tag})
    return tagged.get('content') if tagged is not None else ("No %s" % tag)


def validate_url(base_url, addendum):
    ret_url = addendum
    # Somehow this seems redundant. Fix later FIXME
    if "http" not in addendum:
        b_split = base_url[:-1] if base_url[-1] == '/' else base_url
        ret_url = '/'.join(b_split.split('/') +
                           addendum.split('/')[1:])
    return ret_url


def on_site_only(base_url, urls):
    return set(filter(lambda x: x[:len(base_url)] == base_url,
                      filter(lambda x: "." not in x[-4:], urls)))


def get_elements(outfile, tag):
    log.debug("Getting {} at urls listed in {}".format(tag, outfile))
    href_file = open(outfile + ".csv", "r", newline='')
    href = []
    read_csv = csv.reader(href_file)
    for row in read_csv:
        href.append([i.strip() for i in row])
    href_file.close()

    # You are guaranteed to get only one href
    for index, urls in enumerate(href):
        href[index] = href[index] + get_tags(tag, goto(urls[0]))

    return href


# I could clean up some of this logic with functions but, function
# calls take additional time.
# TODO test run time on standard site with and without broken out

# Consider doing this with coroutines. That is, wait until the request
# comes in, pass the source to another thread, wait the main thread,
# and then sift through the response in the secondary thread
# Could run into problems with requests blocking behavior.
#   i.e. does it block across all threads?
@ctrl_c
def loop(url, find, schema, ignore, test=False):
    pages, gone_to, to_go = [[] for i in range(len(find))], set(), set()
    try:
        base_url = url
        time_out, disallow = robot_read(base_url)
        while True:
            print("\r" + " " * (TERM_ROW - 3), end='')
            prnt = "\r:: Scraping {}".format(
                url.encode('ascii', 'ignore').decode('ascii'))
            if len(prnt) > (TERM_ROW - 9):
                prnt = prnt[:(TERM_ROW - 9)] + "..."
            print(prnt, end='')
            sys.stdout.flush()
            html = goto(url=url)

            if html is None:
                url = to_go.pop()
                gone_to.add(url)
                slp(time_out)
                continue

            hrefs = get_hrefs(html)
            hrefs = hrefs - disallow
            if ignore:
                for ign in ignore:
                    hrefs = hrefs - match(hrefs, ign)
            matched = set(map(lambda x: validate_url(base_url, x), match(hrefs, schema)))
            for ind, finder in enumerate(find):
                found = match(matched, finder)
                if found:
                    pages[ind].append(url)
                log.info("Found : {}, matched against : {}.".format(
                    len(found), len(matched)))
                log.debug("find : {}, match : {}".format(found, matched))

            matched = on_site_only(base_url, matched)
            to_go |= (matched - gone_to)
            log.info("Urls to check : {}, Urls checked : {}".format(
                     len(to_go), len(gone_to)))
            log.debug("to_go : {}, gone_to : {}".format(to_go, gone_to))
            try:
                url = to_go.pop()
                gone_to.add(url)
                slp(time_out)
            except KeyError:
                break
            if test:
                print(find)
                print(gone_to)
                print(to_go)
                break
    except KeyboardInterrupt:
        pass
    return pages


def robot_read(base_url):
    t_out, disallow = 2.5, set()
    html = goto('/'.join(base_url.split('/') + ["robots.txt"]))
    for line in html.split('\n'):
        if "Crawl-delay:" == line[:12]:
            t_out = int(line[12:])
        elif "Disallow" in line and "#" not in line:
            disallow.add(validate_url(base_url,
                         line.strip("^M \n").split(" ")[-1]))
    log.info("Robots.txt found. Setting timeout to {}".format(t_out))
    log.info("Disallowing : {}".format(" ".join(disallow)))
    slp(t_out)
    return t_out, disallow


def write_to(out, pages):
    print("\n:: Writing to file {}.csv".format(out))
    sheet = open(out + ".csv", 'w', newline="")
    log.info("Writing to file {}.csv".format(out))
    writer = csv.writer(sheet)
    for page in pages:
        writer.writerow([page])
    sheet.close()
    print(":: File closed.")


def read_csv(fname):
    urls = None
    if os.path.isfile(fname):
        with open(fname, 'r') as getter:
            urls = [line.strip(' \n') for line in getter.readlines()]
        for url in urls:
            assert("http" in url)
    else:
        raise FileNotFoundError
    return urls


def main():
    options = parse_args()
    log.info("User input :: " + ", ".join(map(" = ".join,
             [[k, str(v)] for k, v in {**vars(options)}.items()])))
    base = options.url[0].strip()

    if options.debug:
        log.getLogger().setLevel(log.DEBUG)
    else:
        log.getLogger().setLevel(log.INFO)

    if options.get_meta[0]:
        pages = [sift(goto(options.url[0].strip()), tag=options.get_meta[0])]
    elif options.getelement[0]:
        href_N_tag = get_elements(options.outfile[0], options.getelement[0])
        write_to(options.outfile[0], href_N_tag)
    else:
        schema = reg_compiler(options.schema[0])
        if options.ignore[0]:
            ignore = [reg_compiler(ign) for ign in options.ignore]
        else:
            ignore = None
        if options.fname:
            urls = list(map(reg_compiler, read_csv(options.fname[0])))
            pages = loop(base, urls, schema, ignore, test=options.test)
            for url, data in zip(urls, pages):
                clean_url = url.__repr__().split('\\\\/')
                if clean_url[-1] == ")')":
                    outfile = "{}_results".format(
                        "url_" + clean_url[-2])
                else:
                    outfile = "{}_results".format(
                        "url_" + clean_url[-1].replace(")')", ""))
                write_to(outfile, data)
        else:
            pages = loop(base, [reg_compiler(options.find[0])], schema, ignore, test=options.test)
            write_to(options.outfile[0], pages)

    print(":: Exiting Program.")


def parse_args():
    parser = argparse.ArgumentParser(
        description=("Crawl a domain for a specific hyperlink. Use the"
                     " 'schema' to try and cut down on the run-time"))
    parser.add_argument(
        "url", metavar="url", nargs=1, type=str,
        help=("The domain that is to be crawled. Please include 'http' "
              "or 'https' and end with '/'"))
    parser.add_argument(
        "-s", "--schema", metavar="schema", nargs=1, type=str, help=(
            "A schema to narrow down the urls that need to be searched. "
            "Without this, the crawl might take some time. (Especially if "
            "the site has some insane crawl rate like 10 seconds) This is "
            "essentially: only look at urls that have SCHEMA within them "
            "and ignore all other pages."),
        default='/')
    parser.add_argument(
        "-o", "--outfile", metavar="Output-File", nargs=1, type=str,
        help=("Specify the name of the file to output to. Always "
              "outputs in the .csv format. Defaults to "
              "Href_Finder_Results.csv"),
        default=["Href_Finder_Results"])
    parser.add_argument(
        "-i", "--ignore", metavar="ignore", nargs='*', type=str,
        help=("Specify parts of the domain to ignore. Please delineate"
              "different sections by enclosing them in '/'. You can "
              "think of ignore as NOT (ignore AND ignore ...) if that"
              " makes it easier."),
        default=[None])
    parser.add_argument(
        "-g", "--getelement", metavar="get", nargs=1, type=str,
        help=("Retrieve the given element of the urls once they have "
              "been found. Useful only when there are a small number of "
              "links and only finds the elements of the resultant pages"
              ),
        default=[None])
    parser.add_argument(
        "-gm", "--get-meta", metavar="tag", nargs=1, type=str,
        help=("Retrieve the given meta element from a SINGLE webpage. "
              "Note that this will not do any crawling of the site. And"
              " will most likely only cooperate for meta tags."),
        default=[None])
    parser.add_argument(
        "-t", "--test", action="store_true", default=False,
        help=("Test the url, schema, etc for one run through the site "
              "to check that you are searching for the correct item."))
    parser.add_argument(
        "-d", "--debug", action="store_true", default=False,
        help=("Set the debug level for the logfile. Defaults to info "
              "and moves to debug when this argument is used"))

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-fn", "--fname", metavar="Input-File", nargs=1, type=str,
        help=("Input a csv for which to read the urls from. The "
              "subsequent findings are saved as csv files labeled after"
              "the last page path."), default=None)
    group.add_argument(
        "-f", "--find", metavar="find", nargs=1, type=str,
        help=("The url or piece of the url to find. Be careful what you"
              " put in because you can't go back once you put this in."
              ),
        default=None)
    opts = parser.parse_args()
    return opts


if __name__ == "__main__":
    main()
