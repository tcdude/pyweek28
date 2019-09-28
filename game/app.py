"""
Provides the GameApp class.
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
import sys

# # noinspection PyPackageRequirements
# from direct.filter.CommonFilters import CommonFilters
# # noinspection PyPackageRequirements
# from direct.interval.IntervalGlobal import *
from panda3d import core

from .shapegen import shape
from . import character
from . import common
from . import collision
from . import modelgen
from . import world
from . import puzzle
from . import nonogram
from . import followcam


def rand_vec3(vmin, vmax, vec_type=core.Vec3):
    v = vec_type(1)
    v.x = random.uniform(vmin, vmax)
    v.y = random.uniform(vmin, vmax)
    v.z = random.uniform(vmin, vmax)
    return v


def rand_cs():
    origin = rand_vec3(-200, 200)  # core.Vec3(0)
    direction = rand_vec3(-1, 1).normalized()  # core.Vec3(0, 1, 0)
    return direction, origin


# noinspection PyArgumentList
class GameApp(world.World, nonogram.NonogramSolver, puzzle.Puzzle):
    def __init__(self):
        # setup before init of parent classes
        self.__collision = collision.CollisionHandler(
            core.Vec2(0),
            core.Vec2(common.T_XY * common.T_XY_SCALE / 2)
        )

        # init parent classes
        world.World.__init__(self, self.__collision)
        nonogram.NonogramSolver.__init__(self)
        symbols = [s[0] for s in self.symbols]
        puzzle.Puzzle.__init__(
            self,
            symbols,
            core.Vec3(-400, -400, self.sample_terrain_z(-400, -400)),
            self.__collision,
            self
        )
        self.set_external(self.get_nonogram_instance, self.get_puzzle_instance)
        # general scene setup
        self.disable_mouse()
        self._shapegen = shape.ShapeGen()
        self.__really_exit = 0

        # self.accept('n', self.toggle_nonogram)
        self.accept('raw-w', self.update_keymap, ['f', 1])
        self.accept('raw-w-repeat', self.update_keymap, ['f', 1])
        self.accept('raw-w-up', self.update_keymap, ['f', 0])
        self.accept('raw-s', self.update_keymap, ['f', -1])
        self.accept('raw-s-repeat', self.update_keymap, ['f', -1])
        self.accept('raw-s-up', self.update_keymap, ['f', 0])
        self.accept('raw-a', self.update_keymap, ['r', 1])
        self.accept('raw-a-repeat', self.update_keymap, ['r', 1])
        self.accept('raw-a-up', self.update_keymap, ['r', 0])
        self.accept('raw-d', self.update_keymap, ['r', -1])
        self.accept('raw-d-repeat', self.update_keymap, ['r', -1])
        self.accept('raw-d-up', self.update_keymap, ['r', 0])
        self.accept('escape', self.__make_sure)
        self.accept('f1', self.toggle_wireframe)

        # character setup
        self.char = character.Character(self)
        self.char.node_path.set_pos(-300, -300, 0)
        self.char_fw = self.char.node_path.attach_new_node('character_fw')
        self.char_fw.set_y(5)
        self.update_z(self.char.node_path)
        self.keymap = {'f': 0, 'r': 0}
        self.no_movement = False

        # camera, fog, lighting
        self.follow_cam = followcam.FollowCam(
            self.render,
            self.cam,
            self.char.node_path,
            self.sample_terrain_z,
            self.mouseWatcherNode
        )
        self.cam.node().get_lens().set_fov(60)
        exp_fog = core.Fog('exp_fog')
        exp_fog.set_color(*common.FOG_COLOR)
        exp_fog.set_exp_density(common.FOG_EXP_DENSITY)
        self.render.set_fog(exp_fog)
        self.set_background_color(0, 0, 0)

        # dl = core.DirectionalLight('dl')
        # dl.set_color(core.Vec4(0.6, 0.6, 0.6, 1))
        # dl_np = self.render.attach_new_node(dl)
        # Sequence(
        #     LerpHprInterval(dl_np, 60, (0, -90, 0), (-90, -50, 0)),
        #     LerpHprInterval(dl_np, 60, (90, -50, 0), (0, -90, 0)),
        # ).loop()
        #
        # self.render.set_light(dl_np)
        al = core.AmbientLight('al')
        al.set_color(core.Vec4(0.3, 0.3, 0.3, 1))
        al_np = self.render.attach_new_node(al)
        self.render.set_light(al_np)
        self.render.set_shader_auto()

        self.atmo = self.loader.load_sfx('Elegia.ogg')
        # self.atmo = self.loader.load_sfx('atmoseerie04.ogg')
        self.atmo.set_loop(True)
        self.atmo.set_volume(0.2)
        self.atmo.play()
        self.task_mgr.add(self.char_update, 'char_update')
        self.start_messages()
        # self.do_method_later(common.START_DURATION, )

    @property
    def collision(self):
        return self.__collision

    def __make_sure(self):
        ft = self.global_clock.get_frame_time()
        if self.__really_exit > ft:
            sys.exit(0)
        self.display_hint('Press ESC again to quit.', 2)
        self.__really_exit = ft + 3

    def __toggle_wf(self, *_):
        self.toggle_wireframe()

    def start_messages(self):
        self.display_hint('Devils Tower, somewhere in WY...', 4)
        self.display_hint('   ', 1)
        self.display_hint('Nah... just kidding...', 2)
        self.display_hint('This is just a simulation...', 3)
        self.display_hint('Enjoy exploring the not so real world.', 2)
        self.display_hint('   ', 1)
        self.display_hint('Hopefully you do not care too much about \n'
                          'graphical fidelity.. ', 2)
        self.display_hint('   ', 1)
        self.do_method_later(6.5, self.__toggle_wf, 'glitch')
        self.do_method_later(7.1, self.__toggle_wf, 'glitch')
        self.do_method_later(7.8, self.__toggle_wf, 'glitch')
        self.do_method_later(8.1, self.__toggle_wf, 'glitch')
        self.do_method_later(8.12, self.__toggle_wf, 'glitch')
        self.do_method_later(8.16, self.__toggle_wf, 'glitch')
        self.do_method_later(8.18, self.__toggle_wf, 'glitch')
        self.do_method_later(8.21, self.__toggle_wf, 'glitch')
        self.do_method_later(8.23, self.__toggle_wf, 'glitch')
        self.do_method_later(8.4, self.__toggle_wf, 'glitch')
        self.do_method_later(8.9, self.__toggle_wf, 'normal')
        self.do_method_later(9.9, self.__toggle_wf, 'normal')

        ht = '/'.join(
            [
                str(self.keyboard_map.get_mapped_button(c))
                for c in ('w', 'a', 's', 'd')
            ]
        ).upper()
        self.display_hint(
            f'Use the "{ht}" keys to move around'
        )

    def winning_screen(self):
        self.no_movement = True
        for msg in common.TXT_WON:
            self.display_hint(msg)
        self.do_method_later(25, sys.exit, 'die...', extraArgs=[0])

    def char_update(self, task):
        if self.no_movement:
            return task.cont
        self.char.forward = self.keymap['f']
        self.char.rotation = self.keymap['r']
        dt = self.global_clock.get_dt()
        self.char.move(dt)
        self.follow_cam.update(dt)
        return task.cont

    def update_keymap(self, k, v):
        self.keymap[k] = v

    def update_z(self, node_path):
        x, y = node_path.get_pos(self.render).xy
        node_path.set_z(self.render, self.sample_terrain_z(x, y))
