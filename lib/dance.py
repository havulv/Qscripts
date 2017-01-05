#!/usr/bin/env python3
from os import system, name, get_terminal_size
from time import sleep
from random import randint
import sys

def move():
    eyes = [ "^", "*", "@", "-", "#" ]
    arms = ["`\_", "_/`", "/.", "\.", "~~"]
    mouth = ["_", "o"]
    return "{: >4}({}{}{}){: <4}".format(
                                arms[randint(0, len(arms)-1)],
                                eyes[randint(0, len(eyes)-1)],
                                mouth[randint(0, len(mouth)-1)],
                                eyes[randint(0, len(eyes)-1)],
                                arms[randint(0, len(arms)-1)])

def ctrl_c(func):
    def wrap(*args, **kwargs):
        try:
            ret = func(*args, **kwargs)
        except KeyboardInterrupt:
            ret = None
            print('\r\n')
            print('\r          /``````\ ')
            print(' *(#_#)* { ByeBye }')
            print('          \______/')
            exit(0)
        return ret
    return wrap

@ctrl_c
def main():
    while True:
        print(
            *[move() for i in range(get_terminal_size()[0]//13)],
            end='\r', flush=True
            )
        sleep(.15)

if __name__ == "__main__":
    main()
