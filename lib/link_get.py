#!/usr/bin/env python3

#TODO argparser

import requests, sys, re, time
from bs4 import BeautifulSoup as bs

#FIXME the positional parameters are stupid and useless right now
def retrieve_links(link, tag_all='search-text', href='a'):
    '''
        Summary:
            Retrieve the links on a given page

        ----------------------------------------------------------------
        Parameters:
            link :: The address at which to get the hrefs

             tag_all='search-text' :: The tag under which the hrefs will be found

             href='a' :: The class associated with the href

        ----------------------------------------------------------------
        Return Values:
            links :: A list of href links from the given link

    '''
    page = bs(requests.get(link).text, 'html.parser')
    links = [] # type: list[str]
    for tag in page.find_all(href):
        if tag.get('href'):
            links.append(tag.get('href'))
    return links

def print_q_string(links):
    '''
        Summary:
            Print the query_string

        ----------------------------------------------------------------
        Parameters:
            links :: The links that need to be made into a query

        ----------------------------------------------------------------
        Return Values:
            links :: Returns the links in the query?

    '''
    end = re.compile('.*(.com)')
    print('('+'|'.join([end.split(i)[2][:-1] for i in links])+')')

def iterlink(args):
    '''
        Summary:
            iterate over the links to retrieve new links etc. etc.

        ----------------------------------------------------------------
        Parameters:
            args :: optional arguments for the iteration (see code for dets)

        ----------------------------------------------------------------
        Return Values:
            links :: Returns all of the links from the iterations

    '''
    links = [] # type: list[str]
    for i in args:
        links += retrieve_links(i)
        time.sleep(2)
    return links

def main():
    args = sys.argv[1:]
    if args:
        if args[0] == '-a':
            print_q_string(iterlink(args[1:]))
        else:
            for i in args:
                links = retrieve_links(i)
                print('\n'.join(links))
                print_q_string(links)
                time.sleep(5) #Because fucking requests is blocking

if __name__ == "__main__":
    main()
