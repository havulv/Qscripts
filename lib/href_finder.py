#!/usr/bin/env python3

'''
    A general spider for searching for a specific url within a set of structured urls

    TODO:
        -Introduce logging to handle offsite emails etc.
        -extend to arbitrary element/tag
        -Document
        -Combine this with other requests modules in this directory
'''

from time import sleep as slp
import logging as log
import requests, argparse, re, csv, os, sys
from bs4 import BeautifulSoup as bs
from requests.exceptions import MissingSchema, ConnectionError

TERM_ROW, TERM_COL = os.get_terminal_size()

BAN_FTYPES = [".pdf", ".css", ".mp4", ".jpg", ".png", ".svg", ".ico"]
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

def ctrl_c(func):
    def wrap(*args, **kwargs):
        try:
            func_ret = func(*args, **kwargs)
        except KeyboardInterrupt:
            func_ret = [None]
        return func_ret
    return wrap

def connection_errors(func):
    def wrap_request(*args, **kwargs):
        func_ret = connection_correct(func, *args, **kwargs)
        return func_ret
    return wrap_request

def reg_compiler(string):
    return re.compile('(' + string.strip() + ')')

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

def get_tags(tag, text):
    log.debug("Getting {} for previous url".format(tag))
    html = bs(text, 'html.parser')
    elements = [ i.contents[0] for i in html.find_all(tag)]
    return elements

#TODO Refactor
def match(hrefs, schema):
    log.debug("Matching {} against {}".format(hrefs, schema))
    return set(filter(lambda x: schema.search(x) and x[:7] != "mailto:" \
            and (x[-4:] not in BAN_FTYPES) and (".png" not in x) \
            and (".jpg" not in x) and (".svg" not in x) and \
            (".jpeg" not in x), hrefs))

def sift(html, tag):
    page = bs(html, 'html.parser')
    tagged = page.find('meta', {'name' : tag})
    if not tagged:
        tagged = page.find('meta', {'property' : 'og:' + tag})
    return tagged.get('content') if tagged != None else ("No %s" % tag)


def validate_url(base_url, addendum):
    ret_url = addendum
    if "http" not in addendum:
        b_split = base_url[:-1] if base_url[-1] == '/' else base_url
        ret_url = '/'.join(b_split.split('/') +
                            addendum.split('/')[1:])
    return ret_url

def on_site_only(base_url, urls):
    return set(filter( lambda x: x[:len(base_url)] == base_url, urls))

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
#TODO test run time on standard site with and without broken out

# Consider doing this with coroutines. That is, wait until the request
# comes in and then (while sifting through the response) call next for
# the next request
@ctrl_c
def loop(url, find, schema, ignore, test=False):
    base_url = url
    time_out = robot_read(base_url)
    pages, gone_to, to_go = [], set(), set()
    while True:
        print("\r" + " " * (TERM_ROW-3), end='')
        prnt = "\r:: Scraping {}".format(
                    url.encode('ascii', 'ignore').decode('ascii'))
        if len(prnt) > (TERM_ROW-9):
            prnt = prnt[:(TERM_ROW-9)] + "..."
        print(prnt, end='')
        sys.stdout.flush()
        html = goto(url=url)

        if html == None:
            url = to_go.pop()
            gone_to.add(url)
            slp(time_out)
            continue

        hrefs = get_hrefs(html)
        if ignore:
            for ign in ignore:
                hrefs = hrefs - match(hrefs, ign)
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
            slp(time_out)
        except KeyError:
            break
        if test:
            print(gone_to)
            print(to_go)
            break
    return pages

def robot_read(base_url):
    t_out = 5
    html = goto('/'.join(base_url.split('/') + ["robots.txt"]))
    for line in html.split('\n'):
        if "Crawl-delay:" == line[:12]:
            t_out = int(line[12:])
            break
    log.debug("Setting time out to {}".format(t_out))
    slp(t_out)
    return t_out

def write_to(out, pages):
    print(":: Writing to file")
    sheet = open(out+".csv", 'w', newline="")
    log.debug("Writing to file {}.csv".format(out))
    writer = csv.writer(sheet)
    for page in pages:
        writer.writerow([page])
    sheet.close()
    print(":: File closed.")

def main():
    options = parse_args()
    log.debug("User input :: " + \
        ", ".join(
                map(" = ".join,
                    [[k,str(v)] for k,v in {**vars(options)}.items()]
                    )
                ))
    find = reg_compiler(options.find[0])

    if options.get_meta[0]:
        pages = [sift(goto(options.url[0].strip()), tag=options.get_meta[0])]
    else:
        schema = reg_compiler(options.schema[0])
        if options.ignore[0]:
            ignore = [reg_compiler(ign) for ign in options.ignore]
        else:
            ignore = None
        pages = loop(options.url[0].strip(), find, schema, ignore, test=options.test)

    if options.outfile[0]:
        out = options.outfile[0]

    write_to(out, pages)

    if options.get_element[0]:
        href_N_tag = get_element(out, options.get_element[0])
        write_to(out, href_N_tag)

    print(":: Exiting Program.")


def parse_args():
    parser = argparse.ArgumentParser(
        description=("Crawl a domain for a specific hyperlink. Use the"
            " 'schema' to try and cut down on the run-time"))
    parser.add_argument(
        "url", metavar="url", nargs=1, type=str, help=("The domain "
        "that is to be crawled. Please include 'http' or 'https' and "
        "end with '/'"))
    parser.add_argument(
        "find", metavar="find", nargs=1, type=str, help=("The url or "
        "piece of the url to find. Be careful what you put in because "
        "you can't go back once you put this in."), default=None)
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
        "outputs in the .csv format. Defaults to Href_Finder_Results"
        ".csv"),
        default=["Href_Finder_Results"])
    parser.add_argument(
        "-i", "--ignore", metavar="ignore", nargs='*', type=str,
        help=("Specify parts of the domain to ignore. Please delineate"
        "different sections by enclosing them in '/'. You can think of"
        " ignore as NOT (ignore AND ignore ...) if that makes it "
        "easier."),
        default=[None])
    parser.add_argument(
        "-g", "--get-element", metavar="get", nargs=1, type=str,
        help=("Retrieve the given element of the urls once they have "
            "been found. Useful only when there are a small number of "
            "links and only finds the elements of the resultant pages"),
        default=[None])
    parser.add_argument(
        "-gm", "--get-meta", metavar="tag", nargs=1, type=str,
        help=("Retrieve the given meta element from a SINGLE webpage. "
            "Note that this will not do any crawling of the site. And "
            "will most likely only cooperate for meta tags."),
        default=[None])
    parser.add_argument(
        "-t", "--test", action="store_true", default=False,
        help=("Test the url, schema, etc for one run through the site "
            "to check that you are searching for the correct item."))
    opts = parser.parse_args()
    return opts


if __name__ == "__main__":
    main()
