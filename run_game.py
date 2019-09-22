#! /usr/bin/env python

__copyright__ = """
MIT License

Copyright (c) 2019 tcdude

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import sys

if sys.version_info < (3, 6):
    print('''
===================================================
Sorry, but this game requires Python 3.
It was tested on 3.7, but 3.6 may also work.
===================================================
''')
    sys.exit(1)

try:
    import panda3d
    import pyfastnoisesimd as fns
    import PIL
    import numpy as np
except ImportError as ex:
    print('''
===================================================
This game requires: 
    * Panda3D >= 1.10.4.1
    * Pillow/PIL >= 6.1.0
    * pyfastnoisesimd >= 0.4.1
    * numpy >= 1.17.2
    
Please run the following command to install it:
    pip install -r requirements.txt
===================================================
''')
    print(repr(ex))
    sys.exit(1)


print('Using Panda3D {0}'.format(panda3d.__version__))
print('Using Pillow {0}'.format(PIL.__version__))
print('Using pyfastnoisesimd {0}'.format(fns.__version__))
print('Using numpy {0}'.format(np.__version__))


if __name__ == '__main__':
    import game
    game.main()
