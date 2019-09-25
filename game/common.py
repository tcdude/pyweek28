"""
Various common constants
"""

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

from panda3d import core
import pyfastnoisesimd as fns



# constants for debugging purposes
NAC = True

# colors
FIR_TRUNK_START = core.Vec3(0.19, 0.11, 0.01)
FIR_TRUNK_DELTA = core.Vec3(0.49, 0.3, 0.05) * 0.2
FIR_BRANCH_START = core.Vec3(0.0, 0.23, 0.05)
FIR_BRANCH_DELTA = core.Vec3(0.09, 0.49, 0.2)

# character constants
MAX_SPEED = 80
ACCELERATION = 50
BREAKING = 8
ROTATION_SPEED = 120
PITCH_SPEED = 15 / MAX_SPEED

# follow-cam constants
TURN_RATE = 2.5
Y_OFFSET = -18
Z_OFFSET = 4
FOCUS_POINT = core.Vec3(0, 0, 4.5)

# terrain constants
T_XY = 1025
T_Z_SCALE = 100
T_XY_SCALE = 2
N_TYPE = fns.NoiseType.Simplex
N_FRACTAL_OCT = 8
N_FRACTAL_GAIN = 0.4
N_FRACTAL_LAC = 1.5
N_FREQ = 0.0001
N_PERT_TYPE = fns.PerturbType.GradientFractal_Normalise
N_PERT_OCT = 5
N_PERT_AMP = 0.5
N_PERT_FREQ = 1.2
N_PERT_LAC = 2.5
N_PERT_GAIN = 0.5

# woods constants
WN_TYPE = fns.NoiseType.Cellular
WN_DIST_FUNC = fns.CellularDistanceFunction.Natural
WN_RET_TYPE = fns.CellularReturnType.CellValue
WN_FRACTAL_OCT = 5
W_CELL_TYPE_COUNT = 12
W_BOUND_CLIP = 0.6
W_WOOD_CELL_COUNT = 1
W_INDIVIDUAL_TREES = 10
