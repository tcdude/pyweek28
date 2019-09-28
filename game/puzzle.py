"""
The 3 ring-puzzle to input the final code.
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

import numpy as np
from panda3d import core

from direct.interval.IntervalGlobal import *
from direct.interval.LerpInterval import *

from . import collision
from . import common
from . import gamedata
from . import modelgen


class Puzzle(gamedata.GameData):
    def __init__(self, symbols, pos, collision_handler, app):
        super().__init__()
        self.__symbols = symbols    # the texture arrays
        self.__pos = pos            # center of the 3 rings
        self.__collision_handler = collision_handler
        self.__app = app
        self.__root = self.render.attach_new_node('Puzzle Root')

        # nodes
        self.__rings = None
        self.__symbol_cards = None
        self.__levers = None

        # states
        self.__found = False
        self.__lever_hint = False
        self.__lever_first_move = False
        self.__setup_rings()
        self.__inner_bounds = False
        self.__active_lever = -1
        self.__ring_offsets = [0, 0, 0]
        self.__time_spent = 0

        # events
        self.accept('raw-e-up', self.__toggle_lever, [-1])
        self.accept('raw-r-up', self.__toggle_lever, [1])
        self.task_mgr.add(self.__update_puzzle)

        # other
        self.__lever_text = common.TXT_LEVER_ACTIVATE.replace(
            '--L--',
            str(self.keyboard_map.get_mapped_button('e')).upper()
        ).replace(
            '--R--',
            str(self.keyboard_map.get_mapped_button('r')).upper()
        )
        self.__combination = []
        for i in self.__app.chosen_symbols:
            self.__combination.append(i % 6)
        # print(self.__combination)
        # for i in range(3):
        #     for _ in range(self.__combination[i]):
        #         self.__toggle_lever(-1, i)

    @property
    def get_puzzle_instance(self):
        return self

    def __update_puzzle(self, task):
        if self.__inner_bounds:
            self.__time_spent += self.global_clock.get_dt()
        else:
            self.__time_spent = 0
        if self.__time_spent > 40:
            self.display_hint(common.TXT_LEVER_LONG_TIME)
            self.__time_spent = 0
        return task.cont

    def __toggle_lever(self, direction, lever=None):
        if lever is not None:
            self.__ring_offsets[lever] -= direction
            self.__ring_offsets[lever] = self.__ring_offsets[lever] % 6
            h = self.__rings[lever].get_h()
            self.__rings[lever].set_h(h + 60 * direction)
            return
        if self.__active_lever == -1:
            return
        if self.__inner_bounds:
            dist = self.__levers[self.__active_lever].get_distance(
                    self.__app.char.node_path
            )
            if dist < 6:
                if not self.__lever_first_move:
                    self.display_hint(common.TXT_LEVER_FIRST_MOVE)
                    self.__lever_first_move = True
                h = self.__rings[self.__active_lever].get_h()
                LerpHprInterval(
                    self.__rings[self.__active_lever],
                    1.2,
                    (h + 60 * direction, 0, 0),
                    blendType='easeInOut'
                ).start()
                Sequence(
                    LerpHprInterval(
                        self.__levers[self.__active_lever],
                        0.6,
                        (-90, 45 * direction, 0),
                        (-90, 0, 0),
                        blendType='easeInOut'
                    ),
                    LerpHprInterval(
                        self.__levers[self.__active_lever],
                        0.6,
                        (-90, 0, 0),
                        (-90, 45 * direction, 0),
                        blendType='easeInOut'
                    ),
                ).start()
                v = self.__ring_offsets[self.__active_lever] - direction
                self.__ring_offsets[self.__active_lever] = v % 6
            if self.__ring_offsets == self.__combination:
                self.__app.winning_screen()

    def __lever_hint_event(self):
        self.__inner_bounds = True
        if self.__lever_hint:
            return
        self.display_hint(common.TXT_LEVER_HINT)
        self.__lever_hint = True

    def __found_event(self):
        self.__inner_bounds = False
        if self.__found:
            return
        self.display_hint(common.TXT_FOUND_RINGS)
        self.__found = True

    def __lever_act_range(self, i):
        self.display_hint(self.__lever_text, 0.5, True)
        self.__active_lever = i

    def __setup_rings(self):
        node_path, self.__rings, self.__symbol_cards = modelgen.three_rings()
        node_path.reparent_to(self.__root)
        node_path.set_pos(self.__pos)
        self.__collision_handler.add(
            collision.CollisionCircle(self.__pos, common.TR_RADII[0])
        )
        self.__collision_handler.add(
            collision.CollisionCircle(
                self.__pos,
                common.TR_RADII[0] * 4,
                (self.__found_event, ()),
                ghost=True
            )
        )
        self.__collision_handler.add(
            collision.CollisionCircle(
                self.__pos,
                common.TR_RADII[0] * 2.2,
                (self.__lever_hint_event, ()),
                ghost=True
            )
        )
        for i, s in enumerate(self.__symbols):
            n = self.__symbol_cards[i // 6][i % 6]
            tex = core.Texture('symbol')
            tex.setup_2d_texture(
                *common.NG_SYM_TEX_SIZE,
                core.Texture.T_unsigned_byte,
                core.Texture.F_rgba
            )
            ta = np.ones(common.NG_SYM_TEX_SIZE + (4,), dtype=np.uint8)
            ta *= 255
            tf = np.array(s) < 255
            ta[tf, 0] = int(common.TR_COLORS[i // 6].x * 255)
            ta[tf, 1] = int(common.TR_COLORS[i // 6].x * 255)
            ta[tf, 2] = int(common.TR_COLORS[i // 6].x * 255)
            ta[:, :, 3] = 255
            # ta = np.flip(ta, 1)
            tex.set_ram_image_as(ta, 'RGBA')
            tex.reload()
            n.set_texture(tex, 1)

        # setup levers
        rot = self.__root.attach_new_node('rot')
        rot.set_pos(node_path.get_pos(self.__root))
        self.__levers = []
        for i in range(3):
            node_path, lever = modelgen.lever(i)
            self.__levers.append(lever)
            node_path.reparent_to(rot)
            node_path.set_y(common.TR_LEVER_Y)
            rot.set_h(i * 90 + 90)
            pos = node_path.get_pos(self.__root)
            hpr = node_path.get_hpr(self.__root)
            node_path.reparent_to(self.__root)
            node_path.set_pos_hpr(pos, hpr)
            node_path.set_z(node_path, 2.5)
            self.__collision_handler.add(
                collision.CollisionCircle(
                    pos,
                    4,
                    (self.__lever_act_range, (i, )),
                    ghost=True
                )
            )
            self.__collision_handler.add(
                collision.CollisionCircle(
                    pos,
                    1
                )
            )

