# Qscripts
Quick scripts for productivity, data fetches, and tedious tasks. 

Current Scripts
===============

## 72it.py

An attempt to follow a strict adherence to PEP 8 that cuts every single line in a file into a length of 72 characters. Ignores words, punctuation, or anything that would actually be useful.

TODO: 
  -Cut lines over full words and recognize the syntax of at least python.

## addDoc.py

Looks over a file, pulls out functions and asks the user what they would like to write for documentation. This script runs under the assumption (the lofty assumption) that the user has read and understood the file s/he/it is adding documentation to. Does not support decorators or classes.

TODO: 
  -Add support for decorators and classes.
  -Add a config file for custom definition of function documentation

## cat.py

A short script to print out the contents of a file because I didn't feel like downloading the much better GNU cat. This version of cat is so good though, that it doesn't even use pretty print or anything. It just spits lines at you.

TODO:
  -Download GNU cat

## check_site.py

Querying a site for a specific status code. Not sure why I needed a full fledged module for this, but here it is.

TODO:
  -Add option to pass timeout length
  -Time the amount of time until the status code disappears
    -Give statistics on the timing

## dance.py

Makes some fun little ASCII terminal dancers because everyone needs a pick me up once in a while.

TODO:
  -Make prettier dancers
  -Get the slow hip roll in. They are a bit spastic right now

## music.py

Requires VLC. Looks for new posts on 2 subreddits and then shoves them into VLC which sorts out whether they can actually stream them or not. Keeps a log of which urls were used in the case that you want to look up something you just heard, and for minimal memeory in the long term.

TODO:
  -Do some preprocessing so that VLC doesn't have to deal with trying to figure out if it should play music from an article
  -Add some configuration options to when the script does the querying
  
## sw.py

Kindly asks for some site statistics from similarweb.com for a specific site. Equivalent to visiting the webpage. Please don't abuse this.

TODO:
  -Add a User-Agent (Probably Mozilla)

## white2trans.py

Transform all of the white pixels in an image to transparent (Change the alpha values to 0) in a png. Far better results for larger images. Also uses the magic of PIL

TODO:
  -Evaluate the accuracy with a negative of the image compared to the new image.

Classes
-------

Helper classes that make data easier to handle in some of the scripts. Yay Object-Oriented programming!

Etc.
----

If you have any questions, comments, concerns, clarifications, or need advice on what resin you should use in your carbon fiber hull email <mailto:johnandersen185@gmail.com
