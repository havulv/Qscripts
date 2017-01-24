#!/usr/bin/env python3

'''
    A script to hit r/indieheads and then bounce back some urls to
    play on vlc. Not very robust but a decent first attmept at this
    that was done in ~20 minutes. Still figuring out this whole
    'documentation' thing.

    MIT License -- John Andersen

'''

from datetime import datetime as dt
import logging as log
import subprocess as sbp
import requests, sys, os, time
from bs4 import BeautifulSoup as bs

# Logging in case a url isn't gotten got
LOG_DIR = os.path.join(os.getcwd(), os.path.normpath("music/"))

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
logfile = open(os.path.join(LOG_DIR, "music.log"), 'a')
logfile.close()

log.basicConfig(level=log.DEBUG,filename=os.path.join(LOG_DIR, "music.log"),
                format="%(asctime)s [%(levelname)s] --- %(message)s")

# Path for vlc media player. Swap with your favorite shit (ncmpcpp or whatever)
# But don't forget to update the subprocess call
VLC_PATH = os.path.normpath(os.path.expanduser('~')+"\\AppData\\"
                                    "Local\\VLC\\vlc-2.2.4\\vlc.exe")
SAVE_FILE = os.path.join(LOG_DIR, 'music_urls.log')

def write_urls(func):
    def wrapper(*args, **kwargs):
        music_urls = func(*args, **kwargs)
        with open(SAVE_FILE, 'a') as to_file:
            for url in music_urls:
                to_file.write(url+'\n')
        return music_urls
    return wrapper

def key_quit(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt or requests.HTTPError as e:
            log.info("{} Quit Out.".format( "HTTP" if
                e == requests.HTTPError else "Keyboard"))
            print("What the fuck man, I was sleeping: {}".format(
                "HTTP" if e == requests.HTTPError else "Keyboard"))
            os.remove(SAVE_FILE)
            log.info("Cleaning up and deleting file")
            sys.exit(0)
    return wrapper

@write_urls
def music_urls(bs_obj):
    '''
        Grabs urls from the indieheads page
        Cuts up youtube links to get the pure video link

        Parameters
            :bs_obj: = Beautiful soup object
            :music_links: = list of music urls
        Returns
            :music_links: = list of music urls
    '''
    old_links = []
    new_links = []
    tag = {'class' : 'title may-blank outbound'}
    with open(SAVE_FILE, 'r') as get_urls:
        for url in get_urls.readlines():
            old_links.append(url.strip('\n'))
    for link in bs_obj.find_all('a', tag):
        url = link.get('data-href-url')
        if "youtube.com" in url and "&" and url:
            pieces = url.split("?")
            # Saves a little bit of computation by not making it a list
            url = pieces[0] + "?" + filter(lambda x: "v" in x,
                                pieces[1].split("&")).__next__()
        elif "reddit.com" in url:
            continue
        if url not in old_links:
            new_links.append(url)
    return new_links

def get_up(sub="indieheads/new/"):
    '''
        Puts a GET request with a Mozilla 5.0 user-agent
        and my email.

        Parameters -- VOID
        Returns
            :bs_obj: = Beautiful Soup object from r/indieheads
    '''
    log.debug("Querying reddit.com/r/indieheads")
    headers = {'User-agent' : ('Mozilla/5.0; Sea_Wulf:I'
                            ' listen to music every hour'),
                'From' : 'johnandersen185@gmail.com'}
    url = "https://www.reddit.com/r/"+sub
    req = requests.get(url, headers=headers)
    if req.status_code != 200:
        log.warn("Status Code: {} :: Failure to get "
                        "page".format(req.status_code))
        raise requests.HTTPError
    log.debug("Status Code: {} :: Success".format(req.status_code))
    return bs(req.text, 'html.parser')


def get_down(music):
    '''
        Pushes the http stream out to VLC or [insert media
        player here]. #TODO support updated playlist

        Parameters
            :music: = list of urls to send to player
        Returns -- VOID
    '''
    log.debug("Calling to VLC :: BASE URL: {}".format([ i.split('/')[2] for i in music]))
    try:
        sbp.run([VLC_PATH, #"--intf=dummy", #interface choice
            "--no-video" ,
            #"vlc://quit" # quit after song
            ] + list(music))
        time.sleep(.25) #Sleep so that VLC doesn't crash -- bad code practice
    except sbp.CalledProcessError:
        log.debug("TOTAL VLC FAILURE")

def dance_baby(slp=300):
    '''
        Daemon Process to schedule a check for new music on the top of
        the hour, every hour until termination.
        Parameters
            :music: = list of stream urls
        Returns -- VOID
    '''
    current_min = dt.now().minute
    if (current_min+5)%20 <= 10:
        log.debug("LET'S GET THIS PARTY STARTED")
        music = music_urls(get_up())
        get_down(music)
        time.sleep(30)
        log.debug("TIME FOR A FRENCH PARTYYY")
        music = music_urls(get_up(sub="MFPMPPJWFA/new/"))
        get_down(music)

    log.debug("SLEEPING: {}".format(slp))
    time.sleep(slp)
    log.debug("AWAKE")

@key_quit
def main():
    with open(SAVE_FILE, "w") as nothing:
        pass #create a file
    log.debug("Starting daemon process.")
    while True:
        dance_baby()

if __name__ == "__main__":
    main()

