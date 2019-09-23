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
from direct.interval.LerpInterval import LerpHprInterval

from .shapegen import shape


class Character(object):
    def __init__(self, root, wheel_radius=0.35, root_node=None):
        self.root = root
        self.wheel_radius = wheel_radius
        self.wheel_circumference = 2 * pi * wheel_radius
        self.char = root_node or root.render.attach_new_node('Character')
        self.left_wheel = self.char.attach_new_node('lw')
        self.right_wheel = self.char.attach_new_node('rw')
        self.body = self.char.attach_new_node('body')
        self.head = self.char.attach_new_node('head')
        LerpHprInterval(self.left_wheel, 1, (0, -360, 0)).loop()
        LerpHprInterval(self.right_wheel, 1, (0, -360, 0)).loop()
        self.setup_nodes()

    # noinspection PyArgumentList
    def setup_nodes(self):
        sg = shape.ShapeGen()
        lw = self.left_wheel.attach_new_node(
            sg.cone(
                origin=core.Vec3(0),
                direction=core.Vec3.left(),
                radius=self.wheel_radius,
                polygon=18,
                length=0.2,
                origin_offset=0,
                smooth=True,
                color=core.Vec4(0.4, 0.2, 0.05, 1),
                nac=False,
                name='left_wheel'
            )
        )
        self.left_wheel.set_pos(-0.49, 0, self.wheel_radius)
        tex = self.root.loader.load_texture('wood.jpg')
        lw.set_texture(tex, 1)
        rw = self.right_wheel.attach_new_node(
            sg.cone(
                origin=core.Vec3(0),
                direction=core.Vec3.right(),
                radius=self.wheel_radius,
                polygon=18,
                length=0.2,
                origin_offset=0,
                smooth=True,
                color=core.Vec4(0.4, 0.2, 0.05, 1),
                nac=False,
                name='right_wheel'
            )
        )
        self.right_wheel.set_pos(0.49, 0, self.wheel_radius)
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
            sg.box(
                origin=core.Vec3(0),
                direction=core.Vec3.up(),
                bounds=core.Vec3(0.3, 0.25, 0.42),
                max_seg_len=0.1,
                corner_radius=0.1,
                smooth=True,
                color=core.Vec4(1),
                nac=False
            )
        )
        self.head.set_pos(0, 0, 1.7)
        hd.flatten_light()
        hd.set_tex_gen(
            core.TextureStage.get_default(),
            core.TexGenAttrib.M_world_position
        )
        hd.set_tex_projector(
            core.TextureStage.get_default(),
            self.root.render,
            hd
        )
        hd.set_tex_scale(core.TextureStage.get_default(), 1e-8)
        hd.set_texture(tex, 2)
