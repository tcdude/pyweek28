# Devils Tower

This is my entry for [PyWeek 28](https://pyweek.org/28/), with the theme __*Tower*__.

## About

A puzzle / exploration game that heavily relies on procedural generation.

Most of the time, I spent writing various parts of procedural generators as 
a basis to generate geometry, place objects, etc. Also a notable amount of 
time I invested in things I wasn't even sure whether they would come in 
handy later on...

As a challenge I wrote a veeery basic collision system more or less from the 
ground up. I obviously didn't want to implement linear algebra ops from scratch, 
when I have libraries that do that faster than I could ever optimize a piece of code... 
I did implement a quadtree just because I wanted to, at the beginning, which in the end 
proved very helpful together with the collision system.


## Build / Install

This game need Python 3.6 or higher to run and also, if you're not on 64bit Windows, 
you'll need build tools and the Python headers installed on your system. 

On Ubuntu that would be this command:

`sudo apt-get install build-essential python3-dev`

I'm sure on other operating systems / distributions this is just as easy, I'm just too
lazy to look up the proper command for each.  

Clone/Download this repo and run:

`pip install -r requirements.txt`  (ideally in a virtualenv, but that's just my opinion)

## Run the game

After installing all the requirements simply run: 

`python run_game.py` *(or `python3 run_game.py` when both Python2 and 3 are installed)*
