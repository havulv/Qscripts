#!/usr/bin/python3

'''
    CAVEATS:
        Yes, I know this is a slow way to implement this system. Instead
        of using the oh-so-slow-file-i/o I could do something fancy like
        import the file and inspect the __dict__ for listed functions.
        HOWEVER, that requires that you have a module that follows all
        syntax rules and will not throw any exceptions.
        This way, I cover the edge case of unfinished modules. BUT, it
        is not extended to the truly edge case of modules which do not
        even have complete function declarations.


    Quick Script for adding documentation to files.

    Searches through a directory or file and returns functions that do
    not have a \'\'\' within the first line after "def". Then allows
    the user to write their own documentation for the function and
    inserts this into the file.

    Doc style:
        {Summary}
        --------------------------------
        {Parameters}
        --------------------------------
        {Return Values}


    Also checks for "python3" at the beginning of file
        --And strict PEP-8 line compliance
'''
from pprint import pprint as pp
from classes import Func
import itertools, re
import os

def read_contents(fname):
    '''
        Reads a file and returns it's contents
        ---------------------------------------------------------------
        Parameters:
            fname :: full filename path
        ---------------------------------------------------------------
        Returns:
            list(enumerate(linelist)):: list of lines
    '''
    linelist = []
    with open(fname, "r") as reader:
        for line in reader.readlines():
            linelist.append(line)
    return linelist

def func_find(contents):
    '''
        Takes an enumerated list of a file's lines and returns a list
        of functions: their opening declaration and their return line
        ---------------------------------------------------------------
        Parameters:
            contents :: list of lines
        ---------------------------------------------------------------
        Returns:
            functions :: A list of tuples with the format:
                        [(declaration, return value).. ]
    '''
    functions = []
    contents = list(enumerate(contents))
    for i in contents:
        if "def " in i[1]:
            for j in contents[i[0]:]:
                if "return " in j[1]:
                    functions.append(Func(i,j))
                    break
            else:
                functions.append(Func(i))
    for fun in functions:
        fun.doc = fun.doc_check(contents)
    return functions

def write_contents(fname, contents, functions):
    fileindex = 1
    for func in list(filter(lambda x: not x.doc, functions)):
        func.mk_doc()
        if func.docstring:
            contents.insert(func.location[0]+fileindex, func.docstring)
            fileindex += 1

    with open(fname, 'w') as doc_up:
        for line in contents:
            doc_up.write(line)

def main():
    fname = input("What is the name of the file you wish to add "
            "documentation to?\n\t")
    innards = read_contents(fname)
    funcs = func_find(innards)
    pp(funcs)
    write_contents(fname, innards, funcs)

if __name__ == "__main__":
    main()
