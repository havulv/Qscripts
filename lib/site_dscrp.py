#!/usr/bin/env python3

from bs4 import BeautifulSoup as bs
import requests, sys
from requests.exceptions import MissingSchema, ConnectionError

def connection_errors(func):
    def wrap_request(*args, **kwargs):
        try:
            func_ret = func(*args, **kwargs)
            # I could overload these errors with __repr__, but I would
            # rather just suppress the traceback and give the info needed
        except (MissingSchema, ConnectionError) as e:
            if isinstance(e, ConnectionError):
                print("ConnectionError -- did you use https on a site that"
                    " does not support secure http? Try http instead."
                    "\n\nDetails :: {}".format(e))
            elif isinstance(e, MissingSchema):
                print("MissingSchema -- did you include the type of "
                    "protocol in the input web address?Please try what"
                    " the error suggests."
                    "\n\nDetails :: {}".format(e))
            sys.exit(0)
        return func_ret
    return wrap_request


@connection_errors
def html(sitename):
    req = requests.get(sitename)
    return req.text if req.status_code == 200 else req.status_code

def sift(html):
    page = bs(html, 'html.parser')
    dscrp = page.find('meta', {'name' : 'description'})
    if not dscrp:
        dscrp = page.find('meta', {'property' : 'og:description'})
    return dscrp.get('content') if dscrp != None else "No Description"

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
