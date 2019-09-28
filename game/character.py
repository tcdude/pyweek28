"""
Provides the controllable character.
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

from math import pi

from panda3d import core
# noinspection PyPackageRequirements
from direct.interval.LerpInterval import *
# noinspection PyPackageRequirements
from direct.interval.IntervalGlobal import *

from .shapegen import shape
from . import common


class Character(object):
    def __init__(self, root, w_radius=0.35, w_offset=0.49, root_node=None):
        self.root = root
        self.wheel_circumference = 2 * pi * w_radius
        self.unit_to_deg = 360 / self.wheel_circumference
        self.turn_distance = 2 * pi * w_offset
        self.turn_to_wheel_deg = self.turn_distance / self.wheel_circumference * 360
        self.char = root_node or root.render.attach_new_node('Character')
        self.fw_pitch = self.char.attach_new_node('fw_pitch')
        self.sw_pitch = self.fw_pitch.attach_new_node('sw_pitch')
        self.sw_pitch.set_h(-90)
        self._body_base = self.sw_pitch.attach_new_node('body_base')
        self._body_base.set_h(90)
        self.left_wheel = self._body_base.attach_new_node('lw')
        self.right_wheel = self._body_base.attach_new_node('rw')
        self.body = self._body_base.attach_new_node('body')
        self.head = self._body_base.attach_new_node('head')
        self.setup_nodes(w_radius, w_offset)
        # self.char.set_h(180)
        self.speed = 0
        self._fw = 0
        self._rot = 0
        self._z = 0
        self.animate()
        self.__sfx = self.root.loader.load_sfx('engine.ogg')
        self.__sfx.set_volume(0.01)
        self.__sfx.set_loop(True)
        self.__sfx.play()

    @property
    def forward(self):
        return self._fw

    @forward.setter
    def forward(self, value):
        self._fw = value

    @property
    def rotation(self):
        return self._rot

    @rotation.setter
    def rotation(self, value):
        self._rot = value

    @property
    def z(self):
        return self._z

    @z.setter
    def z(self, value):
        self._z = value

    @property
    def node_path(self):
        return self.char

    def move(self, dt):
        speed_delta = 0
        if self._fw:
            if self._fw > 0:
                speed_delta = dt * common.ACCELERATION
            else:
                speed_delta = dt * -common.ACCELERATION
        elif not self._fw and self.speed != 0:
            if self.speed > 0:
                speed_delta = dt * -common.BREAKING
            else:
                speed_delta = dt * common.BREAKING

        self.speed = max(
            min(self.speed + speed_delta, common.MAX_SPEED),
            -common.MAX_SPEED
        )

        lw_rot = 0
        rw_rot = 0
        if self._rot:
            if self._rot > 0:
                rotation = dt * common.ROTATION_SPEED
            else:
                rotation = dt * -common.ROTATION_SPEED
            if self.speed >= 0:
                lw_rot += rotation * self.turn_to_wheel_deg
                rw_rot -= rotation * self.turn_to_wheel_deg
            else:
                lw_rot -= rotation * self.turn_to_wheel_deg
                rw_rot += rotation * self.turn_to_wheel_deg
            self.char.set_h(self.char, rotation)

        abs_speed = abs(self.speed)
        playing = False
        if abs_speed < common.CUT_OFF_SPEED:
            self.__sfx.set_volume(0)
        elif abs_speed >= common.CUT_OFF_SPEED:
            self.__sfx.set_play_rate(
                (common.MAX_SFX_SPEED - common.MIN_SFX_SPEED)
                / common.MAX_SPEED
                * abs_speed
                + common.MIN_SFX_SPEED
            )
            self.__sfx.set_volume(common.SFX_VOLUME)
            playing = True
        elif lw_rot or rw_rot:
            self.__sfx.set_play_rate(common.MIN_SFX_SPEED)
            self.__sfx.set_volume(common.SFX_VOLUME)
            playing = True

        if playing and self.__sfx.status() == self.__sfx.READY:
            self.__sfx.play()

        if speed_delta:
            dist = self.speed * dt
            lw_rot -= dist * self.unit_to_deg
            rw_rot -= dist * self.unit_to_deg
            op = self.char.get_pos(self.root.render)
            self.char.set_y(self.char, dist)
            dp = self.char.get_pos(self.root.render)
            self.fw_pitch.set_p(-self.speed * common.PITCH_SPEED)
            cp, rate = self.root.collision.traverse(
                op.xy,
                dp.xy,
                common.CHARACTER_COLLISION_RADIUS
            )
            # TODO: Rethink this to make it work...
            # if self.speed < 0:
            #     self.speed = min(
            #          self.speed - rate * common.MAX_SPEED,
            #          0
            #      )
            # else:
            #     self.speed = max(
            #         self.speed + rate * common.MAX_SPEED,
            #         0
            #     )
            b = (common.T_XY * common.T_XY_SCALE / 2) * 0.9
            if not (-b < dp.x < b) or not (-b < dp.y < b):
                cp.x = max(-b, min(cp.x, b))
                cp.y = max(-b, min(cp.y, b))
            self.char.set_x(cp.x)
            self.char.set_y(cp.y)
            self.root.update_z(self.char)

        if lw_rot or rw_rot:
            self.left_wheel.set_p(self.left_wheel, lw_rot)
            self.right_wheel.set_p(self.right_wheel, rw_rot)

    def animate(self):
        Sequence(
            LerpPosHprInterval(
                self.head, 0.6, (0.03, 0, 0.05), (8, -4, 0),
                blendType='easeInOut'),
            LerpPosHprInterval(
                self.head, 0.6, (0, 0, 0), (0, 0, 0), blendType='easeInOut'),
            LerpPosHprInterval(
                self.head, 0.6, (-0.03, 0, 0.05), (8, -4, 0),
                blendType='easeInOut'),
            LerpPosHprInterval(
                self.head, 0.6, (0, 0, 0), (0, 0, 0), blendType='easeInOut'),
        ).loop()
        Sequence(
            LerpHprInterval(
                self.body, 0.5, (0, -2, 0), blendType='easeInOut'),
            LerpHprInterval(
                self.body, 1, (0, 2, 0), blendType='easeInOut'),
            LerpHprInterval(
                self.body, 0.5, (0, 0, 0), blendType='easeInOut'),
        ).loop()

    # noinspection PyArgumentList
    def setup_nodes(self, w_radius, w_offset):
        sg = shape.ShapeGen()
        lw = self.left_wheel.attach_new_node(
            sg.cone(
                origin=core.Vec3(0),
                direction=core.Vec3.left(),
                radius=w_radius,
                polygon=18,
                length=0.2,
                origin_offset=0,
                smooth=True,
                color=core.Vec4(0.4, 0.2, 0.05, 1),
                nac=False,
                name='left_wheel'
            )
        )
        self.left_wheel.set_pos(-w_offset, 0, w_radius)
        tex = self.root.loader.load_texture('wood.jpg')
        lw.set_texture(tex, 1)
        rw = self.right_wheel.attach_new_node(
            sg.cone(
                origin=core.Vec3(0),
                direction=core.Vec3.right(),
                radius=w_radius,
                polygon=18,
                length=0.2,
                origin_offset=0,
                smooth=True,
                color=core.Vec4(0.4, 0.2, 0.05, 1),
                nac=False,
                name='right_wheel'
            )
        )
        self.right_wheel.set_pos(w_offset, 0, w_radius)
        rw.set_texture(tex, 1)
        self.body.attach_new_node(
            sg.cone(
                origin=core.Vec3(0),
                direction=core.Vec3.up(),
                radius=(0.45, 0.37),
                polygon=40,
                length=1.2,
                capsule=True,
                origin_offset=0,
                name='body',
                color=core.Vec4(1),
                nac=False
            )
        )
        tex = self.root.loader.load_texture('other_wood.jpg')
        self.body.set_pos(0, 0, 0.1)
        self.body.set_texture(tex, 1)
        hd = self.head.attach_new_node(
            sg.cone(
                origin=core.Vec3(0),
                direction=core.Vec3.up(),
                radius=(0.21, 0.2),
                polygon=11,
                length=0.5,
                smooth=False,
                capsule=False,
                name='head',
                color=core.Vec4(1),
                nac=False
            )
        )
        hd.set_pos(0, 0, 1.62)
        hd.set_texture(tex, 2)
        eye = hd.attach_new_node(
            sg.sphere(
                origin=core.Vec3(0),
                direction=core.Vec3.up(),
                radius=0.07,
                polygon=12,
                name='eye',
                color=core.Vec4(0),
                nac=False
            )
        )
        eye.set_pos(-0.15, 0.15, 0)
        eye = hd.attach_new_node(
            sg.sphere(
                origin=core.Vec3(0),
                direction=core.Vec3.up(),
                radius=0.07,
                polygon=12,
                name='eye',
                color=core.Vec4(0),
                nac=False
            )
        )
        eye.set_pos(0.15, 0.15, 0)
