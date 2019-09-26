"""
Everything related to the game world.
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

import random

import numpy as np
from PIL import Image
from panda3d import core
import pyfastnoisesimd as fns

from . import gamedata
from . import flora
from . import common
from .shapegen import shape
from .shapegen import noise
from .shapegen import util


class World(gamedata.GameData):
    def __init__(self):
        gamedata.GameData.__init__(self)
        self.heightfield = None
        self.terrain = None
        self.terrain_root = None
        self.terrain_offset = core.Vec3(0)
        self.tree_root = self.render.attach_new_node('tree_root')
        self.devils_tower = None
        self.noise = noise.Noise()
        self.setup_terrain()
        # self.place_devils_tower()
        # self.place_trees()

    # noinspection PyArgumentList
    def place_devils_tower(self):
        self.devils_tower = self.render.attach_new_node(
            shape.ShapeGen().elliptic_cone(
                a=(240, 70),
                b=(200, 80),
                h=250,
                max_seg_len=20.0,
                exp=2.5,
                top_xy=(40, -20),
                color=core.Vec4(0.717, 0.635, 0.558, 1),
                nac=False
            )
        )
        self.devils_tower.set_h(random.randint(0, 360))
        z = []
        for x in (-220, 0, 220):
            for y in (-220, 0, 220):
                z.append(self.sample_terrain_z(x, y))
        self.devils_tower.set_z(min(z) - 5)

        self.noise.setup_fns(noise_type=fns.NoiseType.Value, )
        y, x = common.DT_TEX_SHAPE
        c = fns.empty_coords(y * x)
        c[0, :] = np.tile(
            np.cos(
                np.linspace(-np.pi, np.pi, x, False)
            ) * common.DT_XY_RADIUS,
            y
        )
        c[1, :] = np.tile(
            np.sin(
                np.linspace(-np.pi, np.pi, x, False)
            ) * common.DT_XY_RADIUS,
            y
        )
        c[2, :] = np.repeat(
            np.linspace(-np.pi, np.pi, x, False) * common.DT_Z_RADIUS,
            y
        )
        a = self.noise.fns.genFromCoords(c).reshape((y, x))
        normal_map = util.sobel(a, 0.15)
        Image.fromarray(normal_map).show()
        tex = self.loader.load_texture('rock.jpg')
        ts = core.TextureStage('ts')
        tex.set_wrap_u(core.Texture.WM_clamp)
        tex.set_wrap_v(core.Texture.WM_clamp)
        self.devils_tower.set_texture(ts, tex)
        self.devils_tower.set_tex_scale(ts, 1)
        tex = core.Texture('dt_normal_map')
        tex.setup_2d_texture(
            y, x, core.Texture.T_unsigned_byte, core.Texture.F_rgb
        )
        tex.set_ram_image_as(normal_map, 'RGB')
        tex.set_wrap_u(core.Texture.WM_clamp)
        tex.set_wrap_v(core.Texture.WM_clamp)
        ts = core.TextureStage('ts')
        ts.set_mode(core.TextureStage.M_normal)
        tex.reload()
        self.devils_tower.set_texture(ts, tex)

    def place_trees(self):
        woods, bounds = self.noise.woods()
        trees = [
            flora.fir_tree()
            for _ in range(common.W_INDIVIDUAL_TREES)
        ]
        x = 3
        y = 3
        hs = common.T_XY * common.T_XY_SCALE / 2
        while y < woods.shape[0] - 3:
            step = np.random.randint(9, 30)
            x += step
            if x > woods.shape[0] - 3:
                y += np.random.randint(10, 20)
                if y >= woods.shape[0] - 3:
                    break
                x = max(3, x % woods.shape[0])
            if not woods[y, x]:
                continue
            node_path = self.tree_root.attach_new_node('fir_tree')
            random.choice(trees).copy_to(node_path)
            pos = core.Vec3(
                x * common.T_XY_SCALE - hs,
                y * common.T_XY_SCALE - hs,
                0
            )
            pos.z = self.sample_terrain_z(pos.x, pos.y)
            node_path.set_pos(pos)

    # noinspection PyArgumentList
    def setup_terrain(self):
        self.heightfield, f = self.noise.terrain()
        self.terrain = core.GeoMipTerrain('terrain')
        self.terrain.set_heightfield(f.get_filename())
        self.terrain.set_block_size(32)
        self.terrain.set_near(2)
        self.terrain.set_far(100)
        self.terrain.set_focal_point(self.camera)
        self.terrain_root = self.terrain.get_root()
        self.terrain_root.reparent_to(self.render)
        self.terrain_root.set_scale(
            common.T_XY_SCALE, common.T_XY_SCALE, common.T_Z_SCALE
        )
        offset = common.T_XY * common.T_XY_SCALE / 2
        self.terrain_offset = core.Vec3(-offset, -offset, 0)
        self.terrain_root.set_pos(self.terrain_offset)
        tex = self.loader.load_texture('grass.jpg')
        tex.set_minfilter(core.SamplerState.FT_linear_mipmap_linear)
        tex.set_anisotropic_degree(2)
        self.terrain_root.set_texture(tex, 1)
        self.terrain_root.set_tex_scale(core.TextureStage.get_default(), 50)
        self.terrain.generate()
        self.task_mgr.add(self.update_task, 'update_task')
        # self.terrain_root.set_bin('fixed', 1000000)
        # self.terrain_root.set_depth_test(False)
        # self.terrain_root.set_depth_write(False)

    def update_task(self, task):
        self.terrain.update()
        return task.cont

    def sample_terrain_z(self, x, y):
        hs = common.T_XY * common.T_XY_SCALE / 2
        last = common.T_XY - 1
        if not (-hs <= x <= hs and -hs <= y <= hs):
            print(f'x/y not on Terrain ({x}/{y})')
            return 0
        x += hs
        y += hs
        x /= common.T_XY_SCALE
        y /= common.T_XY_SCALE
        sx = max(int(x) - 1, 0)
        ex = min(sx + 2, last)
        sy = min(last - int(y) + 1, last)
        ey = max(sy - 2, 0)
        z = self.heightfield[ey:sy, sx:ex]
        # if not z:
        #     print(x, y, sx, ex, sy, ey)
        #     return 0
        return np.average(z) * common.T_Z_SCALE
