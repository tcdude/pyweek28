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
from . import modelgen
from . import common
from . import collision
from .shapegen import shape
from .shapegen import noise
from .shapegen import util
from .shapegen import sdf


class World(gamedata.GameData):
    def __init__(self, collision_handler):
        gamedata.GameData.__init__(self)
        self.heightfield = None
        self.__collision = collision_handler
        self.terrain = None
        self.terrain_root = None
        self.terrain_offset = core.Vec3(0)
        self.tree_root = self.render.attach_new_node('tree_root')
        self.devils_tower = None
        self.__solved_symbols = None
        self.noise = noise.Noise()
        self.__woods, self.__bounds, self.ob_coords = self.noise.woods()
        # print(self.ob_coords)
        self.setup_terrain()
        self.place_devils_tower()
        self.place_trees()
        self.__setup_solved_symbols()

        self.__first_obelisk = True
        self.__tutorial = True
        self.__tut_np = None

        self.__nonogram = None
        self.__puzzle = None
        self.__ng_last_active = 0
        self.__inner_bounds = False
        self.__outer_bounds = False
        # ob = modelgen.obelisk()
        # ob.reparent_to(self.tree_root)
        # ob.set_pos(-300, -300, self.sample_terrain_z(-300, -300))

    @property
    def collision(self):
        return self.__collision

    def __setup_solved_symbols(self):
        c = core.CardMaker('solved')
        c.set_frame(core.Vec4(0, 0.2, -0.3, 0.3))
        c.set_color(core.Vec4(0))
        node_path = self.a2dLeftCenter.attach_new_node(c.generate())
        node_path.set_transparency(core.TransparencyAttrib.M_alpha)
        self.__solved_symbols = []
        c = core.CardMaker('s0')
        c.set_frame(core.Vec4(0.02, 0.18, -0.3, -0.14))
        self.__solved_symbols.append(node_path.attach_new_node(c.generate()))
        c = core.CardMaker('s1')
        c.set_frame(core.Vec4(0.02, 0.18, -0.08, 0.08))
        self.__solved_symbols.append(node_path.attach_new_node(c.generate()))
        c = core.CardMaker('s2')
        c.set_frame(core.Vec4(0.02, 0.18, 0.14, 0.3))
        self.__solved_symbols.append(node_path.attach_new_node(c.generate()))

    def set_external(self, nonogram, puzzle):
        self.__nonogram = nonogram
        self.__puzzle = puzzle
        for n, s in zip(
                self.__solved_symbols, self.__nonogram.chosen_symbols_img):
            tex = core.Texture('chosen_sym')
            tex.setup_2d_texture(
                *common.NG_SYM_TEX_SIZE,
                core.Texture.T_unsigned_byte,
                core.Texture.F_rgb
            )
            ta = np.ones(common.NG_SYM_TEX_SIZE + (4,), dtype=np.uint8)
            ta *= 255
            tf = np.array(s) < 255
            ta[tf, 0] = 0
            ta[tf, 1] = 0
            ta[tf, 2] = 0
            ta[:, :, 3] = 255
            # ta = np.flip(ta, 1)
            tex.set_ram_image_as(ta, 'RGBA')
            tex.reload()
            n.set_texture(tex, 1)
            n.hide()

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
        h = random.randint(0, 360)
        self.collision.add(
            collision.CollisionCircle(
                core.Vec2(0),
                230,
            )
        )
        self.devils_tower.set_h(h)
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
        # Image.fromarray(normal_map).show()
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
        tex = core.Texture('roads')
        ts = core.TextureStage('ts')
        # noinspection PyArgumentList
        tex.setup_2d_texture(
            1024, 1024, core.Texture.T_float, core.Texture.F_rgb
        )
        bounds_tex = np.zeros((1024, 1024, 3), np.float32)
        bounds_tex[self.__bounds[:1024, :1024], :] = -0.05
        # print(bounds_tex.shape)
        tex.set_ram_image_as(bounds_tex, 'RGB')
        tex.reload()
        ts.set_mode(core.TextureStage.M_add)
        # ts.set_combine_rgb(
        #     core.TextureStage.CM_subtract,
        #     core.TextureStage.CS_texture,
        #     core.TextureStage.CO_src_color,
        #     tex,
        #     core.TextureStage.CO_src_color
        # )
        self.terrain_root.set_texture(ts, tex)
        trees = [
            random.choice((modelgen.fir_tree, modelgen.leaf_tree))()
            for _ in range(common.W_INDIVIDUAL_TREES)
        ]
        x = 3
        y = 3
        hs = common.T_XY * common.T_XY_SCALE / 2
        while y < self.__woods.shape[0] - 3:
            step = np.random.randint(9, 30)
            x += step
            if x > self.__woods.shape[0] - 3:
                y += np.random.randint(10, 20)
                if y >= self.__woods.shape[0] - 3:
                    break
                x = max(3, x % self.__woods.shape[0])
            if not self.__woods[y, x]:
                continue
            node_path = self.tree_root.attach_new_node('fir_tree')
            orig, r = random.choice(trees)
            orig.copy_to(node_path)
            pos = core.Vec3(
                (x + random.random() - 0.5) * common.T_XY_SCALE - hs,
                (y + random.random() - 0.5) * common.T_XY_SCALE - hs,
                0
            )
            self.collision.add(
                collision.CollisionCircle(
                    pos.xy,
                    r
                )
            )
            pos.z = self.sample_terrain_z(pos.x, pos.y)
            node_path.set_pos(pos)

    # noinspection PyArgumentList
    def setup_terrain(self):
        self.heightfield = self.noise.terrain()
        f = sdf.circle((30, 30), 15)
        avg = np.max(self.heightfield[713:743, 713:743])
        self.heightfield[713:743, 713:743][f] = avg

        # self.heightfield[self.__bounds] -= 0.1
        # self.heightfield = np.clip(self.heightfield, 0, 1)
        hf = (self.heightfield * 255).astype(np.uint8)
        f = core.TemporaryFile(core.Filename('assets', 'terrain.png'))
        im = Image.fromarray(hf)
        im.save(f.get_filename().get_fullpath())
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

        # Stones where the tower is...
        rot = self.render.attach_new_node('rot')
        d = rot.attach_new_node('d')
        for i in range(40):
            d.set_y(random.uniform(common.T_ST_Y_MIN, common.T_ST_Y_MAX))
            rot.set_h(360 / 40 * (i + random.random() - 0.5))
            node_path = modelgen.stone(core.Vec2(
                random.uniform(common.T_ST_MIN_SIZE, common.T_ST_MAX_SIZE),
                random.uniform(common.T_ST_MIN_SIZE, common.T_ST_MAX_SIZE)
            ))
            node_path.reparent_to(self.render)
            node_path.set_pos(d.get_pos(self.render))
            node_path.set_hpr(
                random.uniform(0, 360),
                random.uniform(0, 360),
                random.uniform(0, 360)
            )
            node_path.set_z(
                self.sample_terrain_z(*tuple(node_path.get_pos().xy)) - 1
            )

        # Obelisks
        mat = core.Material('mat')
        mat.set_emission(core.Vec4(0.2, 0.4, 0.1, 1))
        for i, (x, y) in enumerate(self.ob_coords):
            node_path = modelgen.obelisk()
            node_path.reparent_to(self.render)
            node_path.set_material(mat)
            hs = common.T_XY * common.T_XY_SCALE / 2
            wx = x * common.T_XY_SCALE - hs
            node_path.set_x(wx)
            wy = y * common.T_XY_SCALE - hs
            node_path.set_y(wy)
            node_path.set_z(self.sample_terrain_z(wx, wy))
            self.collision.add(collision.CollisionCircle(
                core.Vec2(wx, wy),
                2,
            ))
            self.collision.add(collision.CollisionCircle(
                core.Vec2(wx, wy),
                20,
                (self.__obelisk_found_event, (i,)),
                ghost=True
            ))
            self.collision.add(collision.CollisionCircle(
                core.Vec2(wx, wy),
                12,
                (self.__toggle_nonogram, (i,)),
                ghost=True
            ))
        self.task_mgr.add(self.__update_terrain, 'update_task')

    def __solved(self, index):
        self.__solved_symbols[index].show()

    def __remove_tut(self):
        if self.__tut_np is not None:
            self.__tut_np.detach_node()
            self.__tut_np = None

    def __toggle_nonogram(self, index):
        if self.__tutorial:
            self.__tutorial = False
            c = core.CardMaker('tut')
            c.set_frame_fullscreen_quad()
            self.__tut_np = self.aspect2d.attach_new_node(c.generate())
            tex = self.loader.load_texture('nonogram_wikipedia.png')
            self.__tut_np.set_texture(tex, 1)
            self.accept_once('space-up', self.__remove_tut)
            self.accept_once('enter-up', self.__remove_tut)
            self.accept_once('mouse2-up', self.__remove_tut)
            self.accept_once('mouse3-up', self.__remove_tut)
        self.__inner_bounds = True
        self.__ng_last_active = self.global_clock.get_frame_time()
        if index == self.__nonogram.current_nonogram_id:
            return
        if not self.__nonogram.nonogram_loaded:
            self.__nonogram.start_nonogram(index)
            if not self.__nonogram.is_nonogram_solved(index):
                self.__nonogram.set_nonogram_callback(self.__solved, (index, ))

    def __obelisk_found_event(self, i):
        self.__outer_bounds = True
        if not self.__inner_bounds and self.__nonogram.nonogram_loaded:
            self.__nonogram.hide_nonogram()
        if self.__first_obelisk:
            self.display_hint(common.TXT_FIRST_OBELISK)
            self.__first_obelisk = False
            self.__tutorial = True

    def __update_terrain(self, task):
        if self.global_clock.get_frame_time() - self.__ng_last_active > 1:
            self.__inner_bounds = False
            self.__nonogram.hide_nonogram()
        self.terrain.update()
        return task.cont

    def sample_terrain_z(self, x, y):
        hs = common.T_XY * common.T_XY_SCALE / 2
        last = common.T_XY - 1
        if not (-hs <= x <= hs and -hs <= y <= hs):
            # print(f'x/y not on Terrain ({x}/{y})')
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
        return np.average(z) * common.T_Z_SCALE + 0.1
