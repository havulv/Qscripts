#!/usr/bin/env python3
from os import system,name
from time import sleep
from random import randint
import sys

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

def printer(dancers, wait, clear=True):

    dance_moves = [' `\_(^_^)`\_ ', ' _/`(^_^)_/` ', '  ~~(*_*)~~  ',
            ' `\_(^_^)_/` ', ' _/`(-_^)`\_ ', ' _/`(^_-)`\_ ',
            ' /.(@_@).\ ']
    if clear:
        system('cls' if name == 'nt' else 'clear')
        print('\n'*15)
    while True:
        print(
            *[dance_moves[randint(0,6)] for i in range(dancers)],
            end='\r', flush=True
            )
        sleep(wait)

@ctrl_c
def main(clear=False):
    clear = bool(clear)
    printer(5, .1, clear)

if __name__ == "__main__":
    try:
        main(sys.argv[1])
    except IndexError:
        main()
