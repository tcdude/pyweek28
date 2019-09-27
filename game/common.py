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

# general
SCR_RES = 1020, 764

# fog
FOG_COLOR = (0.3, 0.3, 0.3)
FOG_EXP_DENSITY = 0.008

# tree colors
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
CHARACTER_COLLISION_RADIUS = 1.2

# follow-cam constants
TURN_RATE = 2.5
Y_OFFSET = -18
Z_OFFSET = 4
FOCUS_POINT = core.Vec3(0, 0, 5.5)
Z_RATE = 1

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

# devils tower constants
DT_TEX_SHAPE = 512, 2048
DT_XY_RADIUS = 5000
DT_Z_RADIUS = 80

# nonogram constants
NG_RADIUS = 0.7
NG_POLY = 20
NG_PAD = 0.9
NG_TEX = 256, 128
NG_SCALE = 0.8
NG_BG_COLOR = core.Vec4(0.3, 0.3, 0.3, 0.6)
NG_OFFSET = core.Vec3(4, 30, -5.5)
NG_X_RANGE = -0.43, 0.46
NG_Y_OFFSET = 0.15  # accounts for Z displacement
NG_GRID = 12, 12
NG_ANIM_DURATION = 0.15
NG_HOVER_Y_OFFSET = -1.5
NG_SYM_TEX_SIZE = 512, 512
NG_SYM_POLY = 14
NG_SYM_GRID_SIDES = 6
NG_SYM_RAD_DIV = 6, 9
NG_SYM_VAR = 0.1, 0.6
NG_SYM_FREQ = 0.1, 0.6
NG_SYM_COUNT = 18
NG_CIRCLE_RAD = 14, 5
NG_CIRCLE_RANGE = 1, 4
NG_TXT_XX = -0.67
NG_TXT_XXO = -0.07
NG_TXT_XY = 0.542 - 0.12
NG_TXT_XYO = -0.1
NG_TXT_YX = -0.57
NG_TXT_YXO = 0.099
NG_TXT_YY = 0.642 - 0.12
NG_TXT_YYO = 0.04

