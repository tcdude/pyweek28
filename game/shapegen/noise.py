"""
Some noise experiments...
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

from typing import Union
import random

import numpy as np
from panda3d import core
import pyfastnoisesimd as fns
from PIL import Image

from .. import common
from . import sdf


class Noise(object):
    def __init__(self, seed=None):
        self.seed = seed
        self.fns = None     # type: Union[fns.Noise, None]
        sl = common.T_XY + common.T_XY % 2
        self.terrain_grid = [1, sl, sl]

    def blob(self, xy, z, dim=1, r=None, seed=None, freq=0.001):
        twopi = np.linspace(-np.pi, np.pi, xy, endpoint=False)
        r = r or np.sqrt(((xy / 2) ** 2) * 2)
        step = 2 * np.pi * r / xy
        x_mesh = np.round(np.cos(twopi) * r)
        y_mesh = np.round(np.sin(twopi) * r)
        z_mesh = np.linspace(0, z * step, z)
        self.setup_fns(
            noise_type=fns.NoiseType.SimplexFractal,
            frequency=freq,
            seed=seed
        )
        coord = fns.empty_coords(dim * z * xy)
        for d in range(dim):
            ds = d * z
            for zi in range(z):
                zs = zi * xy + ds
                ro = d * r * 3
                coord[0, zs:zs + xy] = x_mesh + ro
                coord[1, zs:zs + xy] = y_mesh + ro
                coord[2, zs:zs + xy] = z_mesh[zi]
        a = self.fns.genFromCoords(coord)
        res = []
        for d in range(dim):
            ds = d * z
            res.append([])
            for zi in range(z):
                zs = zi * xy + ds
                res[-1].append(a[zs:zs + xy])
        return res

    def woods(self):
        self.setup_fns(
            noise_type=common.WN_TYPE,
            cell_distance_func=common.WN_DIST_FUNC,
            cell_return_type=common.WN_RET_TYPE,
            fractal_octaves=common.WN_FRACTAL_OCT
        )
        c = self.fns.genAsGrid(self.terrain_grid)[0]
        c = c[:common.T_XY, :common.T_XY]
        c = (common.W_CELL_TYPE_COUNT - 1) / (c.max() - c.min()) * (c - c.min())
        self.fns.cell.returnType = fns.CellularReturnType.Distance2Div
        b = self.fns.genAsGrid(self.terrain_grid)[0]
        b = b[:common.T_XY, :common.T_XY]
        b = 1 / (b.max() - b.min()) * (b - b.min())
        b = b ** 2 > common.W_BOUND_CLIP
        fltr = np.zeros(c.shape)
        wood_cells = random.sample(
            range(common.W_CELL_TYPE_COUNT),
            common.W_WOOD_CELL_COUNT
        )
        for i in wood_cells:
            gt = c >= i
            lt = c < i + 1
            f = gt * lt
            fltr[f] = 1
        fltr[b] = 0
        fltr[sdf.circle(fltr.shape, 120)] = 0
        obelisk_circle = sdf.circle((30, 30), 15)
        obelisk_coordinates = [(825, 825)]
        for i in range(3):
            while True:
                cx, cy = 500, 500
                while 400 < cx < 600 or 400 < cy < 600:
                    cx, cy = np.random.randint(150, 950, 2)
                ok = True
                for x, y in obelisk_coordinates:
                    d = (core.Vec2(x, y) - core.Vec2(cx, cy)).length()
                    if d < 140:
                        ok = False
                if ok:
                    if np.sum(fltr[cy - 15:cy + 15, cx - 15:cx + 15]) > 300:
                        obelisk_coordinates.append((cx, cy))
                        break
        for x, y in obelisk_coordinates:
            fltr[y - 15:y + 15, x - 15:x + 15][obelisk_circle] = 0
        # Image.fromarray((fltr * 255).astype(np.uint8)).show()
        # Image.fromarray((b * 255).astype(np.uint8)).show()
        return fltr, b, obelisk_coordinates[1:]

    # noinspection PyArgumentList
    def terrain(self):
        self.setup_fns(
            noise_type=common.N_TYPE,
            frequency=common.N_FREQ,
            fractal_octaves=common.N_FRACTAL_OCT,
            fractal_gain=common.N_FRACTAL_GAIN,
            fractal_lacunarity=common.N_FRACTAL_LAC,
            perturb_type=common.N_PERT_TYPE,
            perturb_octaves=common.N_PERT_OCT,
            perturb_amp=common.N_PERT_AMP,
            perturb_frequency=common.N_PERT_FREQ,
            perturb_lacunarity=common.N_PERT_LAC,
            perturb_gain=common.N_PERT_GAIN
        )
        hf = self.fns.genAsGrid(self.terrain_grid)[0]
        hf = hf[:common.T_XY, :common.T_XY]
        hf = 1 / (hf.max() - hf.min()) * (hf - hf.min())
        return hf

    # noinspection DuplicatedCode
    def setup_fns(
            self,
            noise_type=fns.NoiseType.Simplex,
            frequency=0.01,
            fractal_type=fns.FractalType.FBM,
            fractal_octaves=3,
            fractal_gain=0.5,
            fractal_lacunarity=2.0,
            perturb_type=fns.PerturbType.NoPerturb,
            perturb_octaves=3,
            perturb_frequency=0.5,
            perturb_amp=1.0,
            perturb_gain=0.5,
            perturb_lacunarity=2.0,
            perturb_normalise_length=1.0,
            cell_distance_func=fns.CellularDistanceFunction.Euclidean,
            cell_distance_indices=(0, 1),
            cell_jitter=0.45,
            cell_lookup_frequency=0.2,
            cell_noise_lookup_type=fns.NoiseType.Simplex,
            cell_return_type=fns.CellularReturnType.Distance,
            seed=None
    ):
        self.fns = fns.Noise(seed or self.seed)
        self.fns.noiseType = noise_type
        self.fns.frequency = frequency
        self.fns.fractal.fractalType = fractal_type
        self.fns.fractal.octaves = fractal_octaves
        self.fns.fractal.gain = fractal_gain
        self.fns.fractal.lacunarity = fractal_lacunarity
        self.fns.perturb.perturbType = perturb_type
        self.fns.perturb.octaves = perturb_octaves
        self.fns.perturb.frequency = perturb_frequency
        self.fns.perturb.amp = perturb_amp
        self.fns.perturb.gain = perturb_gain
        self.fns.perturb.lacunarity = perturb_lacunarity
        self.fns.perturb.normaliseLength = perturb_normalise_length
        self.fns.cell.distanceFunc = cell_distance_func
        self.fns.cell.distanceIndices = cell_distance_indices
        self.fns.cell.jitter = cell_jitter
        self.fns.cell.lookupFrequency = cell_lookup_frequency
        self.fns.cell.noiseLookupType = cell_noise_lookup_type
        self.fns.cell.returnType = cell_return_type


# noinspection PyArgumentList
def noise1d(x, seed=None, octaves=4, d=0.5, normalized=False):
    if not (0 < d < 1):
        raise ValueError('expected 0 < d < 1')
    if seed is not None:
        np.random.seed(seed)
    base = np.random.random(x)
    oct_f = [d ** (i + 1) for i in range(octaves)]
    r = np.zeros(x)
    r += base[0]
    s = 2 ** octaves
    for i, f in enumerate(oct_f):
        r[::s] += f * base[::s]
        s = max(s // 2, 1)
    r /= sum(oct_f) + 1
    if normalized:
        r = 1.0 / (r.max() - r.min()) * (r - r.min())
    return r
