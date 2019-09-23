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

# noinspection PyPackageRequirements
from direct.showbase.ShowBase import ShowBase
from panda3d import core

from .shapegen import shape


def rand_vec3(vmin, vmax, vec_type=core.Vec3):
    v = vec_type(1)
    v.x = random.uniform(vmin, vmax)
    v.y = random.uniform(vmin, vmax)
    v.z = random.uniform(vmin, vmax)
    return v


def rand_cs():
    origin = rand_vec3(-1000, 1000)  # core.Vec3(0)
    direction = rand_vec3(-1, 1).normalized()  # core.Vec3(0, 1, 0)
    return direction, origin


class GameApp(ShowBase):
    def __init__(self):
        # noinspection PyCallByClass,PyArgumentList
        self.settings = core.load_prc_file(
            core.Filename.expand_from('$MAIN_DIR/settings.prc')
        )
        super().__init__()
        self._shapegen = shape.ShapeGen()
        self.accept('s', self.add_sphere)
        self.accept('c', self.add_cone)
        self.accept('escape', sys.exit, [0])
        self.accept('f1', self.toggle_wireframe)

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
