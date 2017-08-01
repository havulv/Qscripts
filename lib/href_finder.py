#!/usr/bin/env python3

'''
    HREF Finder
      -+- By John Andersen -+-
      -+- November 2016?   -+-

    A general scraper for searching for a specific urls on a single site
        Gives a csv of pages on which the url appears, and obeys a site's
        robots.txt to a certain point.

    TODO:
        - Extend to arbitrary element/tag
'''

import re
import csv
import os
import sys
import requests
from requests.exceptions import MissingSchema, ConnectionError

import argparse
import logging as log
from time import sleep as slp
from bs4 import BeautifulSoup as bs

# Grab the terminal size for output
TERM_ROW, TERM_COL = os.get_terminal_size()

# Create the log directory under ./log/
LOG_DIR = os.path.join(os.getcwd(), os.path.normpath("log"))
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Build on top of existing log file, create if it doesn't exist
logfile = open(os.path.join(LOG_DIR, "href_find.log"), 'a')
logfile.close()

log.basicConfig(level=log.DEBUG,
                filename=os.path.join(LOG_DIR, "href_find.log"),
                format="%(asctime)s [%(levelname)s] ::: %(message)s")


''' Begin decorator section '''


def connection_correct(func, *args, wait=4, tries=0, **kwargs):
    '''
        A function for handling urls that could have been inputted incorrectly.
            Reads through the the kwargs looking for a 'url' key if there is
            a connection or schema error, and handles each appropriately.

        Arguments:
            func        :: A function with a mandatory keyword argument of 'url'
            *args       :: Arguments to apply
            tries       :: recursive value for failure -- not to be passed in.
            wait        :: Time to sleep in between connection requests
            **kwargs    :: Keyword arguments to apply

        Returns:
            Completed function return value

    '''
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
                    if 's' not in url[0]:  # http be https
                        kwargs['url'] = '/'.join(['https:'] + url[1:])
                    elif 's' in url[0]:  # https should be http
                        kwargs['url'] = '/'.join(['http:'] + url[1:])
                    else:  # A different ConnectionError occurred
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
                      "Connection_correct should not be composed"
                      " without such a keyword")
                raise e
        log.debug("Sleeping until retry")
        slp(wait)

        log.info("Retrying url as {}".format(kwargs['url']))

        func_ret = connection_correct(
            func, *args, wait,
            tries=(tries + 1), **kwargs)
    return func_ret


def connection_errors(func):
    ''' A decorator for handling connection correction '''
    def wrap_request(*args, **kwargs):
        func_ret = connection_correct(func, *args, **kwargs)
        return func_ret
    return wrap_request


''' Helper functions '''


# schema must already be regex compiled
def get_hrefs(text):
    ''' Retrieve any link that appears on the page '''
    log.debug("Getting hrefs for previous url")
    html = bs(text, 'html.parser')
    hrefs = {tag['href'].strip() for tag in html.find_all(href=True)}
    return hrefs


def get_tags(tag, text):
    ''' Retrieve the text from any tag '''
    log.debug("Getting {} for previous url".format(tag))
    html = bs(text, 'html.parser')
    elements = [i.contents[0] for i in html.find_all(tag)]
    return elements


def reg_compiler(string):
    ''' Helper function for cleaning a simple regex string '''
    return re.compile(
        '(' + string.strip("\" ").replace(".", "\.").replace("/", "\/") + ')')


''' Logic and data fetching functions '''


@connection_errors
def goto(url="localhost"):
    ''' Scrape a page with a normal User-Agent '''
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/32.0.1667.0 Safari/537.36'}

    req = requests.get(url, headers=headers)
    return req.text if req.status_code == 200 else None


def match(hrefs, schema):
    '''
        Matches hrefs against a regex -> schema

        Arguments:
            hrefs   :: An iterable of links or a list/set of links
            schema  :: The regex that will match against the hrefs
    '''
    log.debug("Matching {} against {}".format(hrefs, schema))
    retval = set()
    try:
        iter_schema = iter(schema)
    except TypeError:  # Handle an already itered instance
        retval = set(filter(
            lambda x: re.search(schema, x) and x[:7] != "mailto:", hrefs))
    else:
        for i in iter_schema:
            for j in filter(
                    lambda x: re.search(i, x) and x[:7] != "mailto:", hrefs):
                retval.add(j)

    return retval


def sift(html, tag):
    ''' Sift through the html for a specific tag '''
    page = bs(html, 'html.parser')
    tagged = page.find('meta', {'name': tag})
    if not tagged:
        tagged = page.find('meta', {'property': 'og:' + tag})
    return tagged.get('content') if tagged is not None else ("No %s" % tag)


def validate_url(base_url, addendum):
    ''' Fix urls to absolute paths instead of relative paths '''
    ret_url = addendum

    if "http" not in addendum:
        b_split = base_url[:-1] if base_url[-1] == '/' else base_url
        ret_url = '/'.join(b_split.split('/') +
                           addendum.split('/')[1:])
    return ret_url


def on_site_only(base_url, urls):
    '''
        Match urls that are only on the site and do not have
            3 character file extensions. This is incomplete and
            needs to handle files that are longer than 3 chars
    '''
    return set(filter(lambda x: x[:len(base_url)] == base_url,
                      filter(lambda x: "." not in x[-4:], urls)))


# Still in testing
def get_elements(outfile, tag):
    ''' Read all the hrefs from outfile and fetch the contents of those urls '''
    log.debug("Getting {} at urls listed in {}".format(tag, outfile))
    with open(outfile + ".csv", "r", newline='') as href_file:
        href = []
        read_csv = csv.reader(href_file)
        for row in read_csv:
            href.append([i.strip() for i in row])

    # You are guaranteed to get only one href
    for index, urls in enumerate(href):
        href[index] = href[index] + get_tags(tag, goto(urls[0]))

    return href


def robot_read(base_url):
    '''
        Look for time out and disallowed urls on robots.txt
            Defaults to a timeout of 2.5, and everything allowed

        Arguments:
            base_url :: the base url off of which to find robots.txt

        Returns:
            t_out    :: The time out length on which to wait
            disallow :: The urls that are disallowed
    '''
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


def loop(url, find, schema, ignore, test=False):
    '''
        Loop over every url on the site, searching for pages that link
            to the original page. Return a list of urls on which the listed
            urls were found.
        On Ctrl-C (KeyboardInterrupt), pass over the page listed.

        Arguments:
            url     :: The site url to scrape over
            find    :: A list of regex strings of what to search for in the tag
            schema  :: A regex string of what type of pages to scrape
            ignore  :: A list of regex strings of what pages to ignore
            test    :: Runs through once, and quits out. Test the url

        Returns:
            pages   :: The pages on which 'find' showed up
    '''
    pages, gone_to, to_go = [[] for i in range(len(find))], set(), set()
    try:
        base_url = url
        time_out, disallow = robot_read(base_url)

        while True:
            print("\r" + " " * (TERM_ROW - 3), end='')  # Clear terminal
            prnt = "\r:: Scraping {}".format(
                url.encode('ascii', 'ignore').decode('ascii'))

            if len(prnt) > (TERM_ROW - 9):
                prnt = prnt[:(TERM_ROW - 9)] + "..."
            print(prnt, end='')
            sys.stdout.flush()
            html = goto(url=url)

            if html is None:  # Request was bad
                url = to_go.pop()
                gone_to.add(url)
                slp(time_out)
                continue

            hrefs = get_hrefs(html)
            hrefs = hrefs - disallow
            if ignore:  # Ignore based on the schema
                for ign in ignore:
                    hrefs = hrefs - match(hrefs, ign)

            # Match against the hrefs and take only unique hrefs
            matched = set(map(lambda x: validate_url(base_url, x), match(hrefs, schema)))
            for ind, finder in enumerate(find):
                found = match(matched, finder)
                if found:
                    pages[ind].append(url)
                log.info("Found : {}, matched against : {}.".format(
                    len(found), len(matched)))
                log.debug("find : {}, match : {}".format(found, matched))

            # Find the new urls to scrape and cross off those that are gone to
            matched = on_site_only(base_url, matched)
            to_go |= (matched - gone_to)
            log.info("Urls to check : {}, Urls checked : {}".format(
                     len(to_go), len(gone_to)))
            log.debug("to_go : {}, gone_to : {}".format(to_go, gone_to))

            try:
                url = to_go.pop()
                gone_to.add(url)
                slp(time_out)
            except KeyError:  # to_go is empty
                break

            if test:  # On test, print results of first url
                print(find)
                print(gone_to)
                print(to_go)
                break

    except KeyboardInterrupt:  # Pass url on KeyboardInterrupt
        pass
    return pages


def write_to(out, pages):
    ''' Write the found pages to the outfile '''
    print("\n:: Writing to file {}.csv".format(out))

    with open(out + ".csv", 'w', newline="") as sheet:
        log.info("Writing to file {}.csv".format(out))
        writer = csv.writer(sheet)
        for page in pages:
            writer.writerow([page])

    print(":: File closed.")


def read_csv(fname):
    ''' Read a newline seperated list of urls to search through '''
    urls = None
    if os.path.isfile(fname):
        with open(fname, 'r') as getter:
            urls = [line.strip(', \n') for line in getter.readlines()]
        for url in urls:  # Assumes correct url structure
            assert("http" in url)
    else:
        raise FileNotFoundError
    return urls


def main():
    ''' The main function to parse all arguments (through argparse) and control io '''
    options = parse_args()
    log.info("User input :: " + ", ".join(map(" = ".join,
             [[k, str(v)] for k, v in {**vars(options)}.items()])))
    base = options.url[0].strip()

    # Log levels
    if options.debug:
        log.getLogger().setLevel(log.DEBUG)
    else:
        log.getLogger().setLevel(log.INFO)

    # Grab tags, elements, or search for urls
    if options.get_meta[0]:
        pages = [sift(goto(options.url[0].strip()), tag=options.get_meta[0])]
    elif options.getelement[0]:
        href_N_tag = get_elements(options.outfile[0], options.getelement[0])
        write_to(options.outfile[0], href_N_tag)
    else:
        schema = reg_compiler(options.schema[0])

        if options.ignore[0]:  # What to ignore
            ignore = [reg_compiler(ign) for ign in options.ignore]
        else:
            ignore = None

        if options.fname:  # If there is a supplied file: read the urls from it
            urls = list(map(reg_compiler, read_csv(options.fname[0])))
            pages = loop(base, urls, schema, ignore, test=options.test)

            for url, data in zip(urls, pages):  # Build outfiles for each url
                clean_url = url.__repr__().split('\\\\/')
                if clean_url[-1] == ")')":
                    outfile = "{}_results".format(
                        "url_" + clean_url[-2])
                else:
                    outfile = "{}_results".format(
                        "url_" + clean_url[-1].replace(")')", ""))
                write_to(outfile, data)
        else:
            pages = loop(base, [reg_compiler(options.find[0])],
                         schema, ignore, test=options.test)
            write_to(options.outfile[0], pages)

    print(":: Exiting Program.")


def parse_args():
    ''' The argument parser for the module '''
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
