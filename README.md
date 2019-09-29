# Devils Tower

This is my entry for [PyWeek 28](https://pyweek.org/28/), with the theme __*Tower*__.

## About

A puzzle / exploration game that heavily relies on procedural generation.
I wasn't too excited about the theme Tower at first and when searching
the web, I stumbled on the ["Devils Tower"](https://en.wikipedia.org/wiki/Devils_Tower) 
in Wyoming, USA, which looked like a shape I could more or less generate 
and thus decided to build a game that takes place around the Devils Tower.

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

## Instructions

I purposely did not add a bunch of text in the game. When you find one of the puzzles 
and solved it, you can just move away. To close the instructions on 
[Nonogram](https://en.wikipedia.org/wiki/Nonogram) either press one of these buttons:
(space, enter, right or middle mouse-button).

You can switch to wireframe view with **F1** inside the game at any time.

**Have fun!!**

## Credits

  * Using **Nonogram** for puzzles was the idea of my good friend Evelyne
  * SFX and the song playing in the background are from my neighbor/friend Joel
  * The [Panda3D](https://www.panda3d.org) community for helping me figure out
  technical problems

## Special Thanks to

  * Kathy for keeping my back free during this jam week
  * Evelyne to help brainstorm ideas and help me keep my motivation 
  when I got frustrated
  * My neighbor joel, both for the music and the regular requests to 
  come outside to let our dogs play in the garden -> the only fresh air I got in 7 days :P
  * rdb for motivating me to take part in this competition in the first place 
