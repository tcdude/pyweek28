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

from panda3d import core
from direct.interval.LerpInterval import *

from . import gamedata
from . import common
from .shapegen import shape
from .shapegen import util


class NonogramGenerator(object):
    def __init__(self):
        pass


class Grid(object):
    def __init__(self, yx):
        self.grid = [[False for _ in range(yx[0])] for _ in range(yx[1])]

    def __getitem__(self, item):
        return self.grid[item[1]][item[0]]

    def toggle(self, x, y):
        self.grid[y][x] = not self.grid[y][x]


# noinspection PyArgumentList
class NonogramSolver(gamedata.GameData):
    def __init__(self, solution):
        super().__init__()
        self.__solution = solution
        self.__base = self.cam.attach_new_node('NonogramRoot')
        self.__base.set_pos(common.NG_OFFSET)
        self.__base.set_scale(common.NG_SCALE)
        al = core.AmbientLight('al_nonogramm')
        al.set_color(core.Vec4(1))
        al_np = self.render.attach_new_node(al)
        self.__base.set_light(al_np)
        self.__root = self.__base.attach_new_node('CellRoot')
        self.__yx = (len(solution), len(solution[0]))
        self.__root.set_pos(
            -(common.NG_RADIUS * 2 + common.NG_PAD) * self.__yx[1] / 2,
            0,
            (common.NG_RADIUS * 2 + common.NG_PAD) * self.__yx[0] / 2
        )
        self.__grid = Grid(self.__yx)
        self.__grid_nodes = []
        self.__sg = shape.ShapeGen()
        self.__hidden = False
        self.__clicked = False
        self.__current_hover = None, None
        self.accept('mouse1-up', self.__click)
        self.__setup()
        self.task_mgr.add(self.mouse_watch, 'nonogram_mouse_watcher')

    def __click(self):
        self.__clicked = True

    def mouse_watch(self, task):
        if not self.__hidden and self.mouseWatcherNode.has_mouse():
            aspect = self.win.get_y_size() / self.win.get_x_size()
            x = self.mouseWatcherNode.get_mouse_x()
            y = self.mouseWatcherNode.get_mouse_y() * aspect
            x_min, x_max = common.NG_X_RANGE
            if x_min <= x <= x_max and x_min <= y <= x_max:
                x = min(int(12 / (x_max - x_min) * (x - x_min)), 11)
                y = min(int(12 - 12 / (x_max - x_min) * (y - x_min)), 11)
                self.toggle_hover(x, y)
                if self.__clicked:
                    self.toggle_cell(x, y)
                    self.__clicked = False
            else:
                self.toggle_hover()
        return task.cont

    def toggle_hover(self, x=None, y=None):
        cx, cy = self.__current_hover
        if self.__current_hover != (x, y):
            if cx is not None:
                np = self.__grid_nodes[cy][cx]
                ps = np.get_pos()
                p = ps + core.Vec3(0, 0, 0)
                p.y = 0
                LerpPosInterval(
                    np,
                    0.15,
                    p,
                    ps,
                    blendType='easeInOut'
                ).start()
            if x is not None:
                np = self.__grid_nodes[y][x]
                ps = np.get_pos()
                p = ps + core.Vec3(0, 0, 0)
                p.y = -1
                LerpPosInterval(
                    np,
                    0.15,
                    p,
                    ps,
                    blendType='easeInOut'
                ).start()
            self.__current_hover = x, y

    def toggle_cell(self, x, y):
        np = self.__grid_nodes[y][x]
        h = util.clamp_angle(np.get_h())
        LerpHprInterval(
            np,
            0.15,
            (h + 180, 0, 0),
            (h, 0, 0),
            blendType='easeInOut'
        ).start()
        if h == 0:
            LerpColorInterval(
                np,
                0.15,
                core.Vec4(0),
                blendType='easeOut'
            ).start()
        else:
            np.set_color(core.Vec4(1))

    def toggle_nonogram(self):
        if self.__hidden:
            self.show_nonogram()
        else:
            self.hide_nonogram()

    def show_nonogram(self):
        self.__base.show()
        self.__hidden = False

    def hide_nonogram(self):
        self.__base.hide()
        self.__hidden = True

    def __setup(self):
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
