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
from . import flora
from . import world
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
class GameApp(world.World, nonogram.NonogramSolver):
    def __init__(self):
        self.__collision = collision.CollisionHandler(
            core.Vec2(0),
            core.Vec2(common.T_XY * common.T_XY_SCALE / 2)
        )

        world.World.__init__(self, self.__collision)
        nonogram.NonogramSolver.__init__(self)
        self.disable_mouse()
        self._shapegen = shape.ShapeGen()
        # self.accept('s', self.add_sphere)
        # self.accept('c', self.add_cone)
        self.accept('b', self.add_box)
        self.accept('n', self.toggle_nonogram)
        self.accept('w', self.update_keymap, ['f', 1])
        self.accept('w-repeat', self.update_keymap, ['f', 1])
        self.accept('w-up', self.update_keymap, ['f', 0])
        self.accept('s', self.update_keymap, ['f', -1])
        self.accept('s-repeat', self.update_keymap, ['f', -1])
        self.accept('s-up', self.update_keymap, ['f', 0])
        self.accept('a', self.update_keymap, ['r', 1])
        self.accept('a-repeat', self.update_keymap, ['r', 1])
        self.accept('a-up', self.update_keymap, ['r', 0])
        self.accept('d', self.update_keymap, ['r', -1])
        self.accept('d-repeat', self.update_keymap, ['r', -1])
        self.accept('d-up', self.update_keymap, ['r', 0])
        self.accept('escape', sys.exit, [0])
        self.accept('f1', self.toggle_wireframe)

        self.char = character.Character(self)
        self.char.node_path.set_pos(-300, -300, 0)
        self.char_fw = self.char.node_path.attach_new_node('character_fw')
        self.char_fw.set_y(5)
        self.update_z(self.char.node_path)
        # self.update_z(self.nonogram_node_path)
        # self.nonogram_node_path.set_x(self.char_fw.get_x(self.render))
        # self.nonogram_node_path.set_y(self.char_fw.get_y(self.render))
        self.keymap = {'f': 0, 'r': 0}
        self.follow_cam = followcam.FollowCam(
            self.render, self.cam, self.char.node_path, self.sample_terrain_z)

        self.cam.node().get_lens().set_fov(60)
        exp_fog = core.Fog('exp_fog')
        exp_fog.set_color(*common.FOG_COLOR)
        exp_fog.set_exp_density(common.FOG_EXP_DENSITY)
        self.render.set_fog(exp_fog)
        self.set_background_color(0, 0, 0)

        # tmp_node = core.NodePath(core.PandaNode('temp_node'))
        # tmp_node.setAttrib(core.LightRampAttrib.makeSingleThreshold(0.5, 0.4))
        # tmp_node.setShaderAuto()
        # self.cam.node().setInitialState(tmp_node.getState())
        #
        # self.separation = 1
        # self.filters = CommonFilters(self.win, self.cam)
        # filter_ok = self.filters.setCartoonInk(separation=self.separation)

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
        self.task_mgr.add(self.char_update, 'char_update')

    @property
    def collision(self):
        return self.__collision

    def char_update(self, task):
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

    def add_sphere(self):
        radius = random.uniform(4.0, 40.0)
        direction, origin = rand_cs()
        polygon = int(radius / 2 * 4)
        if random.random() < 0.1:
            h_deg = 360.0
        else:
            h_deg = random.uniform(10.0, 350.0)
        h_offset = random.uniform(0.0, 360.0)
        if random.random() < 0.1:
            p_from = -90.0
        else:
            p_from = random.uniform(-80.0, 60.0)
        if random.random() < 0.1:
            p_to = 90.0
        else:
            p_to = random.uniform(p_from + 10.0, 80.0)
        self.render.attach_new_node(
            self._shapegen.sphere(
                origin,
                direction,
                radius,
                polygon,
                h_deg,
                h_offset,
                p_from,
                p_to
            )
        )

    def add_cone(self):
        radii = (random.uniform(0.0, 40.0), random.uniform(0.0, 40.0))
        direction, origin = rand_cs()
        polygon = int(max(radii) / 2 * 4)
        if random.random() < 0.1:
            h_deg = 360.0
        else:
            h_deg = random.uniform(10.0, 350.0)
        h_offset = random.uniform(0.0, 360.0)
        length = random.uniform(3 * max(radii), 8 * max(radii))
        top_offset = (
            (random.random() - 0.5) * max(radii),
            (random.random() - 0.5) * max(radii)
        )
        self.render.attach_new_node(
            self._shapegen.cone(
                origin,
                direction,
                radii,
                polygon,
                length,
                random.random() > 0.5,
                80.0,
                random.random() > 0.5,
                h_deg,
                h_offset,
                random.random(),
                top_offset
            )
        )

    def add_box(self):
        direction, origin = rand_cs()
        origin *= 0
        bounds = rand_vec3(2, 30)
        bnp = self.render.attach_new_node(
            self._shapegen.blob(
                origin,
                direction,
                bounds,
                smooth=True,
                color=core.Vec4(0.2, 0.2, 0.2, 1),
                color2=core.Vec4(0.4, 0.4, 0.4, 1),
                nac=False
            )
        )
        bnp.set_pos(self.char.node_path.get_pos(self.render))

    def add_tree(self):
        tex = self.loader.load_texture('bark1.jpg')
        tree = flora.fir_tree(tex=tex)
        tree.reparent_to(self.render)
        tree.set_pos(rand_cs()[1])
