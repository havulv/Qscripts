#!/usr/bin/python3
from os import system,name
from time import sleep
from random import randint
from sys import exit

def printer(dancers, wait, clear=True):
    '''
        Summary:
            Prints out the dancers!

        ----------------------------------------------------------------
        Parameters:
            dancers :: Who do you want to shake their booty?

             wait :: How long should we wait

             clear=True :: Get rid of the beautiful dancers?

        ----------------------------------------------------------------
        Return Values:
            VOID
    '''
    hands_up = ' `\_(^_^)`\_ '
    hands_down = ' _/`(^_^)_/` '
    whats_going_on = '  ~~(*_*)~~  '
    shrug = ' `\_(^_^)_/` '
    l_wink = ' _/`(-_^)`\_ '
    r_wink = ' _/`(^_-)`\_ '
    dance_moves = [
            hands_up, hands_down, whats_going_on,
            shrug, l_wink, r_wink
            ]
    if clear:
        system('cls' if name == 'nt' else 'clear')
        print('\n'*15)
    while True:
        print(
            *[dance_moves[randint(0,5)] for i in range(dancers)],
            end='\r', flush=True
            )
        sleep(wait)

def main():
    try:
        printer(5, .1)
    except KeyboardInterrupt:
        print('\r\n')
        print('\r          /``````\ ')
        print(' *(#_#)* { ByeBye }')
        print('          \______/')
        exit(0)

if __name__ == "__main__":
    main()
