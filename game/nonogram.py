"""
Everything nonogram related.
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

from itertools import combinations
import random
from typing import List
from typing import Union

import numpy as np
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFilter

from panda3d import core
from direct.interval.LerpInterval import *

from . import gamedata
from . import common
from .shapegen import sdf
from .shapegen import shape
from .shapegen import util


class NonogramGenerator(object):
    def __init__(self):
        self.grid_shape = common.NG_GRID
        self.symbols = []
        self.chosen_symbols = []
        self.generate()

    def generate(self):
        cs = [
            list(combinations(range(common.NG_SYM_GRID_SIDES ** 2), i))
            for i in range(2, 6)
        ]
        f = [int(len(cs[-1]) / len(cs[i])) + 1 for i in range(3)] + [1]
        comb = []
        for c, m in zip(cs, f):
            comb += c * m
        h = True
        while h:
            s = random.sample(comb, common.NG_SYM_COUNT)
            self.symbols = [self.generate_image(c) for c in s]
            t = np.zeros(self.symbols[0][1].shape)
            for _, a in self.symbols:
                t[a == 255] += 1
            e = t < 4
            t = np.zeros(t.shape)
            t[e] = 1
            e = np.sum(t)
            if e > 45:
                h = False
        self.chosen_symbols = []
        for i in range(3):
            self.chosen_symbols.append(random.randint(0, 5) + i * 6)

    def build_number_hints(self, symbol):
        horizontal = []
        vertical = []
        _, s = self.symbols[symbol]
        for row in s:
            horizontal.append([])
            col_block = 0
            for col, rv in enumerate(reversed(row)):
                if rv:
                    col_block += 1
                else:
                    if col_block > 0:
                        horizontal[-1].append(col_block)
                        col_block = 0
            if col_block > 0:
                horizontal[-1].append(col_block)
        for col in range(len(s[0])):
            vertical.append([])
            row_block = 0
            for cv in reversed(s[:, col]):
                if cv:
                    row_block += 1
                else:
                    if row_block > 0:
                        vertical[-1].append(row_block)
                        row_block = 0
            if row_block > 0:
                vertical[-1].append(row_block)
        return horizontal, vertical

    def show_all(self, ch=False):
        # Debug
        sx, sy = common.NG_SYM_TEX_SIZE
        full = Image.new(
            'L',
            (
                (3 if ch else common.NG_SYM_COUNT) * (sx + 20),
                sy * 2 + 40
            ),
            127
        )
        if ch:
            s = [self.symbols[i] for i in self.chosen_symbols]
        else:
            s = self.symbols
        for i, (tex, a) in enumerate(s):
            im = Image.fromarray(a).resize((sx, sy))
            x = i * sx + i * 20
            full.paste(tex, (x, 10))
            full.paste(im, (x, sy + 30))
        full.show()

    def generate_image(self, quadrants):
        """
        Return a Tuple[ndarray, ndarray] containing image and nonogram.

        Args:
            quadrants: list of quadrants to draw random polygons in.
        """
        sx, sy = common.NG_SYM_TEX_SIZE
        im = Image.new('L', (sx, sy))
        d = ImageDraw.Draw(im)
        sl = common.NG_SYM_GRID_SIDES
        two_sl = sl * 2
        seg_x = sx // sl
        seg_y = sy // sl
        half_seg_x = sx // two_sl
        half_seg_y = sy // two_sl
        for q in quadrants:
            ax, ay = q % sl, q // sl
            ax = ax * seg_x + half_seg_x
            ay = ay * seg_y + half_seg_y
            poly = sdf.random_polygon(
                ax,
                ay,
                sx / np.random.randint(*common.NG_SYM_RAD_DIV),
                np.random.uniform(*common.NG_SYM_VAR),
                np.random.uniform(*common.NG_SYM_FREQ),
                common.NG_SYM_POLY
            )
            d.polygon(tuple(map(tuple, poly)), 255, 255)
        a = np.array(im)
        for _ in range(np.random.randint(*common.NG_CIRCLE_RANGE)):
            circle = sdf.circle(
                (sx, sy),
                np.random.randint(
                    sx // common.NG_CIRCLE_RAD[0],
                    sx // common.NG_CIRCLE_RAD[1]
                )
            )
            circle = np.roll(circle, np.random.randint(0, sx), 0)
            a[circle] = 0 if np.random.random() < 0.5 else 255
        im = Image.fromarray(a)
        tex = im.filter(ImageFilter.GaussianBlur())
        im = im.resize((self.grid_shape[0] - 2, self.grid_shape[1] - 2))
        a = np.array(im)
        f = a > 127
        # noinspection PyArgumentList
        a[f] = a.max()
        tex = tex.transpose(Image.ROTATE_180)
        tex = tex.transpose(Image.FLIP_TOP_BOTTOM)
        tex = tex.transpose(Image.ROTATE_90)
        tex = tex.transpose(Image.FLIP_TOP_BOTTOM)
        return tex, f


class Grid(object):
    def __init__(self, yx):
        self.__grid = [[[]]]
        self.yx = yx
        self.__active = -1
        self.hard_reset()

    @property
    def ready(self):
        return self.__active > -1

    def __getitem__(self, item):
        if self.__active < 0:
            raise ValueError('You first need to activate a grid')
        return self.__grid[self.__active][item[1]][item[0]]

    def set_active(self, index):
        if index not in range(3):
            raise ValueError('needs to be in range(3)')
        # print(f'switched to puzzle no {index}')
        self.__active = index

    def toggle(self, x, y):
        if self.__active < 0:
            raise ValueError('You first need to activate a grid')
        self.__grid[self.__active][y][x] = not self.__grid[self.__active][y][x]

    def hard_reset(self):
        self.__grid = [
            [
                [False for _ in range(self.yx[0])]
                for _ in range(self.yx[1])
            ]
            for _ in range(3)
        ]
        self.__active = -1

    def check(self, ref):
        # print(self.ar_str(ref), str(self))
        if self.__active < 0:
            raise ValueError('You first need to activate a grid')
        for y in range(1, self.yx[0] - 1):
            for x in range(1, self.yx[1] - 1):
                ry = y - 1
                rx = x - 1
                if self.__grid[self.__active][y][x] != ref[ry, rx]:
                    return False
        return True

    def __repr__(self):
        return f'Grid-{self.__active}, ({self.yx})'

    def __str__(self):
        return self.ar_str()

    def ar_str(self, nda=None):
        if nda is not None:
            s = f'Solution {self.__active} = \n'
            s += ' '.join(['0' for _ in range(self.yx[1])])
            s += '\n'
            for r in nda:
                ts = ' 0 '
                for v in r:
                    ts += '1 ' if v else '0 '
                ts += '0 \n'
                s += ts
        else:
            s = f'Grid {self.__active} = \n'
            for r in self.__grid[self.__active]:
                ts = ' '
                for v in r:
                    ts += '1 ' if v else '0 '
                ts += '\n'
                s += ts
        return s


# noinspection PyArgumentList
class NonogramSolver(gamedata.GameData):
    def __init__(self):
        gamedata.GameData.__init__(self)
        # self.__solution = solution
        self.__nonogram_gen = NonogramGenerator()
        self.__current_symbol_id = None
        self.__solved = [False, False, False]
        self.__yx = tuple(reversed(common.NG_GRID))
        self.__grid = Grid(self.__yx)
        self.__solution = [None, None, None]

        self.__base = self.cam.attach_new_node('NonogramRoot')
        self.__text = self.aspect2d.attach_new_node(
            'NonogrammTextRoot'
        )  # type: core.NodePath
        self.__base.set_pos(common.NG_OFFSET)
        self.__base.set_scale(common.NG_SCALE)
        al = core.AmbientLight('al_nonogramm')
        al.set_color(core.Vec4(0.8))
        al_np = self.render.attach_new_node(al)
        self.__base.set_light(al_np)
        self.__root = None
        self.__grid_nodes = []
        self.__h_txt_grid = [
            [] for _ in range(self.__yx[0])
        ]  # type: List[List[core.NodePath]]
        self.__h_txt_values = [
            [
                '' for _ in range(5)
            ] for _ in range(self.__yx[0])
        ]  # type: List[List[str]]
        for h in self.__h_txt_values:
            h[0] = '0'
        self.__v_txt_grid = [
            [] for _ in range(self.__yx[1])
        ]  # type: List[List[core.NodePath]]
        self.__v_txt_values = [
            [
                '' for _ in range(5)
            ] for _ in range(self.__yx[0])
        ]  # type: List[List[str]]
        for v in self.__v_txt_values:
            v[0] = '0'
        self.__sg = shape.ShapeGen()
        self.__hidden = False
        self.__clicked = False
        self.__current_hover = None, None
        self.accept('mouse1-up', self.__click)
        self.accept('m', self.__nonogram_gen.show_all, [True])
        # self.accept('u', self.__update_cells)
        self.__aspect = self.win.get_y_size() / self.win.get_x_size()
        self.__setup()
        self.task_mgr.add(self.mouse_watch, 'nonogram_mouse_watcher')
        self.hide_nonogram()

        self.__nonogram_loaded = False
        self.__nonogram_solved = False

        self.__callback = None
        self.__cbargs = ()

    def set_nonogram_callback(self, callback, args=()):
        self.__callback = callback
        self.__cbargs = args

    def is_nonogram_solved(self, index):
        return self.__solved[index]

    @property
    def symbols(self):
        return self.__nonogram_gen.symbols

    @property
    def nonogram_loaded(self):
        return self.__nonogram_loaded

    @property
    def nonogram_solved(self):
        return self.__nonogram_solved

    @property
    def current_nonogram_id(self):
        return self.__current_symbol_id

    @property
    def get_nonogram_instance(self):
        return self

    @property
    def chosen_symbols_img(self):
        symbols = []
        for i in self.__nonogram_gen.chosen_symbols:
            symbols.append(self.__nonogram_gen.symbols[i][0])
        return symbols

    @property
    def chosen_symbols(self):
        return self.__nonogram_gen.chosen_symbols

    def __click(self):
        if not self.__hidden:
            self.__clicked = True

    def mouse_watch(self, task):
        if self.__hidden:
            return task.cont
        aspect = self.win.get_y_size() / self.win.get_x_size()
        if aspect != self.__aspect:
            self.__update_text()
            self.__aspect = aspect
        if not self.__hidden and self.mouseWatcherNode.has_mouse():
            x = self.mouseWatcherNode.get_mouse_x()
            y = self.mouseWatcherNode.get_mouse_y() + common.NG_Y_OFFSET
            y = y * self.__aspect
            x_min, x_max = common.NG_X_RANGE
            if x_min <= x <= x_max and x_min <= y <= x_max:
                num_x, num_y = common.NG_GRID
                x = min(int(num_x / (x_max - x_min) * (x - x_min)), num_x - 1)
                y = min(
                    int(num_y - num_y / (x_max - x_min) * (y - x_min)),
                    num_y - 1
                )
                self.toggle_hover(x, y)
                if self.__clicked:
                    if not self.__nonogram_solved:
                        self.toggle_cell(x, y)
                    self.__clicked = False
            else:
                self.toggle_hover()
        return task.cont

    def toggle_hover(self, x=None, y=None):
        cx, cy = self.__current_hover
        if self.__current_hover != (x, y):
            if cx is not None:
                node_path = self.__grid_nodes[cy][cx]
                ps = node_path.get_pos()
                p = ps + core.Vec3(0, 0, 0)
                p.y = 0
                LerpPosInterval(
                    node_path,
                    common.NG_ANIM_DURATION,
                    p,
                    ps,
                    blendType='easeInOut'
                ).start()
                for n in self.__h_txt_grid[cy]:
                    n.set_color(core.Vec4(1))
                for n in self.__v_txt_grid[cx]:
                    n.set_color(core.Vec4(1))
            if x is not None:
                node_path = self.__grid_nodes[y][x]
                ps = node_path.get_pos()
                p = ps + core.Vec3(0, 0, 0)
                p.y = common.NG_HOVER_Y_OFFSET
                LerpPosInterval(
                    node_path,
                    common.NG_ANIM_DURATION,
                    p,
                    ps,
                    blendType='easeInOut'
                ).start()
                for n in self.__h_txt_grid[y]:
                    n.set_color(core.Vec4(0.7, 0.3, 0.3, 1.0))
                for n in self.__v_txt_grid[x]:
                    n.set_color(core.Vec4(0.3, 0.7, 0.3, 1.0))
            self.__current_hover = x, y

    def toggle_cell(self, x, y):
        if self.__nonogram_solved:
            return
        self.__grid.toggle(x, y)
        node_path = self.__grid_nodes[y][x]
        h = util.clamp_angle(node_path.get_h())
        if h > 0:
            h = 180
        else:
            h = 0
        LerpHprInterval(
            node_path,
            common.NG_ANIM_DURATION,
            (h + 180, 0, 0),
            (h, 0, 0),
            blendType='easeInOut'
        ).start()
        if h == 0:
            LerpColorInterval(
                node_path,
                common.NG_ANIM_DURATION,
                core.Vec4(0),
                blendType='easeOut'
            ).start()
        else:
            node_path.set_color(core.Vec4(1))
        self.__check_solved()

    def __check_solved(self):
        if not self.nonogram_loaded:
            print('Warning: tried to check when no nonogram is loaded')
            return
        if self.__nonogram_solved:
            print('Warning: tried to check already solved nonogram')
            return
        if self.current_nonogram_id is None:
            print('Warning: tried to check when no nonogram is active')
            return
        if self.__grid.check(
                self.symbols[
                    self.__nonogram_gen.chosen_symbols[self.current_nonogram_id]
                ][1]):
            self.__show_solution(self.current_nonogram_id)
            self.__solved[self.current_nonogram_id] = True
            self.__current_symbol_id = None
            self.reset_grid()
            if self.__callback is not None:
                self.__callback(*self.__cbargs)
            self.__nonogram_solved = True
            self.__nonogram_loaded = False
            self.__callback = None

    def show_nonogram(self):
        self.__base.show()
        self.__text.show()
        # self.__nonogram_loaded = False
        self.__hidden = False

    def hide_nonogram(self):
        self.__base.hide()
        self.__text.hide()
        for n in self.__solution:
            n.hide()
        # self.__nonogram_loaded = False
        # self.__current_symbol_id = None
        self.__hidden = True

    def __add_number_node(self, row=None, col=None):
        base_aspect = common.SCR_RES[0] / common.SCR_RES[1]
        aspect = self.win.get_x_size() / self.win.get_y_size()
        aspect = 1 / base_aspect * aspect
        if row is not None and col is None:
            a = self.__h_txt_grid
            ai = row
            nm = 'row'
            i = len(a[ai])
            v = self.__h_txt_values[ai][i]
            x = (common.NG_TXT_XX + i * common.NG_TXT_XXO) * aspect
            y = (common.NG_TXT_XY + row * common.NG_TXT_XYO) * aspect
        elif col is not None and row is None:
            a = self.__v_txt_grid
            ai = col
            nm = 'col'
            i = len(a[ai])
            v = self.__v_txt_values[ai][i]
            x = (common.NG_TXT_YX + col * common.NG_TXT_YXO) * aspect
            y = (common.NG_TXT_YY + i * common.NG_TXT_YYO) * aspect
        else:
            raise ValueError('expected either row or col')
        tn = core.TextNode(f'nonogramm_{nm}{ai}/{i}')
        tnp = self.__text.attach_new_node(tn)
        tn.set_text(v)
        tnp.set_scale(0.05)
        tnp.set_pos(
            x,
            0,
            y
        )
        a[ai].append(tnp)

    def __show_solution(self, symbol):
        self.__solution[symbol].show()

    def start_nonogram(self, symbol_id):
        # print(repr(self.__grid))
        if symbol_id not in range(3):
            raise ValueError('expected value in range(3)')
        self.__nonogram_solved = False
        if self.__solved[symbol_id]:
            self.__show_solution(symbol_id)
            self.__nonogram_solved = True
            # print('was solved...')
            return
        self.__grid.set_active(symbol_id)
        sm = self.__nonogram_gen.chosen_symbols[symbol_id]
        if self.__hidden:
            self.show_nonogram()
        self.__setup()
        rv, cv = self.__nonogram_gen.build_number_hints(sm)
        # print(rv, cv)
        for i, r in enumerate(rv):
            if not r:
                self.__h_txt_values[i + 1][0] = '0'
                continue
            for j, v in enumerate(r):
                self.__h_txt_values[i + 1][j] = str(v)
        for i, c in enumerate(cv):
            if not c:
                self.__v_txt_values[i + 1][0] = '0'
                continue
            for j, v in enumerate(c):
                self.__v_txt_values[i + 1][j] = str(v)
        self.__update_text()
        self.__update_cells()
        self.__nonogram_loaded = True
        self.__current_symbol_id = symbol_id

    def __update_cells(self):
        if not self.__grid.ready:
            print('warning: tried to update the grid before the grid was '
                  'populated')
            return
        self.reset_grid()
        # print(repr(self.__grid))
        # print(str(self.__grid))

    def reset_grid(self):
        for y in range(self.__grid.yx[0]):
            for x in range(self.__grid.yx[1]):
                if self.__grid[x, y]:
                    self.toggle_cell(x, y)

    def __update_text(self):
        self.__h_txt_grid = [
            [] for _ in range(self.__yx[0])
        ]  # type: List[List[core.NodePath]]
        self.__v_txt_grid = [
            [] for _ in range(self.__yx[1])
        ]  # type: List[List[core.NodePath]]
        self.__text.get_children().detach()
        for i in range(12):
            for _ in range(5):
                self.__add_number_node(col=i)
                self.__add_number_node(i)

    def __setup(self):
        # self.start_nonogram(0)
        if None in self.__solution:
            self.__generate_solution_cards()

        self.__root = None
        self.__base.get_children().detach()
        self.__root = self.__base.attach_new_node('CellRoot')
        self.__root.set_pos(
            -(common.NG_RADIUS * 2 + common.NG_PAD) * self.__yx[1] / 2,
            0,
            (common.NG_RADIUS * 2 + common.NG_PAD) * self.__yx[0] / 2
        )

        c = core.CardMaker('nbg')
        c.set_frame(core.Vec4(-100, 100, -100, 100))
        self.__card = self.__base.attach_new_node(c.generate())
        self.__card.set_color(common.NG_BG_COLOR)
        self.__card.set_transparency(core.TransparencyAttrib.M_alpha)
        o = core.Vec3(0)
        o.xz = common.NG_OFFSET.xz
        self.__card.set_pos(o)
        self.__card.set_bin('fixed', 0)
        self.__card.set_depth_test(False)
        self.__card.set_depth_write(False)

        self.__h_txt_grid = [
            [] for _ in range(self.__yx[0])
        ]  # type: List[List[core.NodePath]]
        self.__h_txt_values = [
            [
                '' for _ in range(5)
            ] for _ in range(self.__yx[0])
        ]  # type: List[List[str]]
        for h in self.__h_txt_values:
            h[0] = '0'

        self.__v_txt_grid = [
            [] for _ in range(self.__yx[1])
        ]  # type: List[List[core.NodePath]]
        self.__v_txt_values = [
            [
                '' for _ in range(5)
            ] for _ in range(self.__yx[0])
        ]  # type: List[List[str]]
        for v in self.__v_txt_values:
            v[0] = '0'

        tex = core.Texture('cell_tex')
        tex.setup_2d_texture(
            *tuple(reversed(common.NG_TEX)),
            core.Texture.T_float,
            core.Texture.F_rgba
        )
        tex.set_ram_image_as(util.bw_tex(*common.NG_TEX), 'RGBA')
        tex.set_wrap_u(core.Texture.WM_clamp)
        tex.set_wrap_v(core.Texture.WM_clamp)
        tex.reload()
        if self.__grid_nodes:
            self.__grid_nodes = []
            self.__root.get_children().detach()

        cell_np = self.__root.attach_new_node(
            self.__sg.sphere(
                core.Vec3(0),
                core.Vec3.up(),
                common.NG_RADIUS,
                common.NG_POLY,
                name='cell 0/0',
                nac=False
            )
        )
        ts = core.TextureStage('ts')
        cell_np.set_texture(ts, tex, 1)
        cell_np.set_tex_offset(ts, 0.25, 0)
        cell_np.set_bin('fixed', 0)
        cell_np.set_depth_test(False)
        cell_np.set_depth_write(False)

        for y in range(self.__yx[0]):
            self.__grid_nodes.append([])
            for x in range(self.__yx[1]):
                if x or y:
                    node_path = self.__root.attach_new_node(f'cell {x}/{y}')
                    cell_np.copy_to(node_path)
                    node_path.set_pos(
                        x * (common.NG_RADIUS + common.NG_PAD),
                        0,
                        -y * (common.NG_RADIUS + common.NG_PAD)
                    )
                    self.__grid_nodes[-1].append(node_path)
                else:
                    self.__grid_nodes[-1].append(cell_np)

    def __generate_solution_cards(self):
        for i in range(3):
            c = core.CardMaker('nbg')
            c.set_frame(core.Vec4(-0.5, 0.5, -0.5, 0.5))
            self.__solution[i] = self.aspect2d.attach_new_node(c.generate())
            im = self.symbols[self.__nonogram_gen.chosen_symbols[i]][0]
            a = np.zeros(im.size + (3,), dtype=np.uint8)
            a[:, :, 0] = np.array(im)
            a[:, :, 1] = np.array(im)
            a[:, :, 2] = np.array(im)
            tex = core.Texture(f'solution{i}')
            tex.setup_2d_texture(
                *a.shape[:2],
                core.Texture.T_unsigned_byte,
                core.Texture.F_rgb
            )
            tex.set_ram_image_as(a, 'RGB')
            tex.reload()
            self.__solution[i].set_texture(tex, 1)
            self.__solution[i].hide()
