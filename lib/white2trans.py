#!/usr/bin/env python3

'''
    Make all white pixels transparent in an image
'''


import os
import sys
from PIL import Image


def get_hex(fname):
    '''
        Converts the image at fname to a list of triplets (base 10)
        ---------------------------------------------------------------
        Parameters:
            fname :: file name of the image
        ---------------------------------------------------------------
        Returns:
            img :: Image object
            data :: image's data
    '''
    if os.path.isfile(os.path.normpath(fname)):
        img = Image.open(fname)
        img = img.convert("RGBA")
        return img, img.getdata()
    else:
        raise FileNotFoundError


def process(item):
    '''
        Monad for stripping the list of triplets of white 0xffffff
        ---------------------------------------------------------------
        Parameters:
            item :: Pixel data
        ---------------------------------------------------------------
        Returns:
            (ff,ff,ff,0) or item :: sets alpha val to 0
    '''
    if item[0] > 135 and item[1] > 135 and item[2] > 135:
        return (255, 255, 255, 0)
    else:
        return (0, 0, 0, 255)


def save_as(fname, img, data):
    '''
        Saves the data as a png
        ---------------------------------------------------------------
        Paramaters:
            img :: The Image object to save
            data :: The data to write into the image
        ---------------------------------------------------------------
        Returns:
            Void
    '''
    img.putdata(data)
    img.save(fname[:-4] + "_trans" + fname[-4:], "PNG")


if __name__ == "__main__":
    try:
        fname = sys.argv[1]
        img, data = get_hex(fname)
        save_as(fname, img, list(map(process, data)))
    except (IndexError, FileNotFoundError):
        print("Check that the file exists or that you even typed in a "
              "filename")
