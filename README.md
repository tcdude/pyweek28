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

Clone this repo and run:

`pip install -r requirements.txt`  (ideally in a virtualenv, but that's just my opinion)

afterwards simply run `python run_game.py`

This game need Python 3.6 or higher to run

