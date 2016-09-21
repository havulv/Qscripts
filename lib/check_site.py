#!/usr/bin/python3

'''
    Messy script pulled together in <10 minutes to check the status
    of a specific site. https and GET only
'''

import sys
import requests
import time


def main(uri=None, sco=None):
    '''
        Short script to check for status code on specific website
        arguments:          parameter
            uri     =       str(blank.com)
            sco     =       int(http status_code)
    '''
    if uri:
        url = "https://" + uri
    else:
        url = "https://" + input("Site Check (Only sitename+.com): ")
    if sco:
        code = int(sco)
    else:
        code = int(input("status code you are checking against: "))

    req = requests.get(url)

    while req.status_code == code:
        print("Error still there")
        time.sleep(12)
        req = requests.get(url)
        if req.status_code == 504:
            print("Gateway timeout, refreshing connection?")
            time.sleep(15)
            req = requests.get(url)

    print("Finally a different status code: {}".format(req.status_code))

if __name__ == "__main__":
    try:
        main(sys.argv[1], sys.argv[2])
    except IndexError:
        main()

