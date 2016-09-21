#!/usr/bin/python

import sys,os

def cat(fpath):
    '''
        Summary:
            Takes in a file path and spits out all of the
                characters in the file path.

        ----------------------------------------------------------------
        Parameters:
            fpath :: A valid filename in the current working
                directory.

        ----------------------------------------------------------------
        Return Values:
            VOID
    '''
    print('\n{:#<15} Beginning File {:#>15}'.format('', ''))
    with open(fpath, 'r') as out:
        stuff = out.readlines()
    for line in stuff:
        print(line, end='')
    print('{:#<15} End of File {:#>15}\n'.format('', ''))

if __name__ == "__main__":
    args = sys.argv[1:]
    for i in args:
        if os.path.isfile(i):
            try:
                cat(i)
            except FileNotFoundError as e:
                print('The file, %s, was not found.' % i)
                sys.exit(1)
        else:
            print('The file, %s, was not found.' % i)
