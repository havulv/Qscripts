#!/usr/bin/env python3

'''
    Literally just cuts all lines to 72 characters.
    Restrict all lines to a length of 72

    #TODO split over words
    #TODO preserve indentations

    --John Andersen
'''

import time
import sys, re, math

def reg_div(line):
    ''' Make sure it doesn't give a weird word on endline '''
    pass #Bad form on the func: pass

def restrict(lines):
    '''
        Takes in a list of lines and cuts them to 72 characters
        Parameters
            :lines: list of strings
        Returns
            :ret_list: list of strings all less than 72 chars
    '''
    ret_list = []
    for line in lines:
        if len(line) > 72:
            splits = math.ceil(len(line)/72)
            for i in range(splits):
                ret_list.append(line[(i*72):((i+1)*72)])
        else:
            ret_list.append(line)

    return ret_list

def read(fname):
    '''
        Read a file and return a list of lines
        Paramters
            :fname: file path
        Returns
            :lin_list: list of lines in the file as strings
    '''
    lin_list = []
    with open(fname, 'r') as get:
        for line in get.readlines():
            lin_list.append(line)
    return lin_list

def write(gname, lines):
    '''
        Writes lines to gname
        Parameters
            :gname: file path
        Returns :: VOID
    '''
    with open(gname, 'w') as setter:
        for line in lines:
            setter.write(line+"\n")

def main(filename):
    '''
        Times the formatting, reads the file, cuts the lines, and writes
        it all back to the same file
        Parameters
            :filename: file path of the file to be chopped
        Returns :: VOID
    '''
    start = time.time()
    print("STARTING")
    write(filename, restrict(read(filename)))
    end = time.time()
    print("DONE :: time: {0} seconds".format(end-start))



if __name__ == "__main__":
    try:
        fname = sys.argv[1]
    except IndexError:
        raise Exception("Filename, fuckhead")

    main(fname)
