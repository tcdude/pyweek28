"""
Provides a Panda NodePath based drawing rig for general shape generation.
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


class Draw(object):
    # noinspection PyArgumentList
    def __init__(self):
        self._world = core.NodePath('world')
        self._origin = self._world.attach_new_node('origin')
        self._pitch_correction = self._origin.attach_new_node('p')
        self._heading_correction = self._pitch_correction.attach_new_node('h')
        self._orient = self._heading_correction.attach_new_node('orient')
        self._orient_offset = self._orient.attach_new_node('orient_offset')
        self._draw = self._orient_offset.attach_new_node('draw')
        # I want the default orientation (forward 0, 1, 0 and up 0, 0, 1) to
        # result in initial drawing point +distance, 0, 0
        self._pitch_correction.set_p(-90)
        self._heading_correction.set_h(-90)

    @property
    def point(self):
        return self._draw.get_pos(self._world)

    @property
    def local_point(self):
        return self._draw.get_pos(self._origin)

    @property
    def center_point(self):
        pos, hpr = self._orient.get_pos(), self._orient.get_hpr()
        # z value for orientation is y value of draw.
        z = self._draw.get_pos(self._origin).y
        self._orient.set_pos_hpr(core.Vec3(0, 0, z), core.Vec3(0))
        center_point = self._orient.get_pos(self._world)
        self._orient.set_pos_hpr(pos, hpr)
        return center_point

    def setup(self, origin, direction):
        """
        Setup the rigs' origin and direction

        Args:
            origin:
            direction:
        """
        self._origin.set_pos(0, 0, 0)
        self._origin.heads_up(core.Vec3(0, 1, 0), core.Vec3(0, 0, 1))
        self._orient.set_pos_hpr(core.Vec3(0), core.Vec3(0))
        self._orient_offset.set_pos_hpr(core.Vec3(0), core.Vec3(0))
        self._draw.set_pos_hpr(core.Vec3(0), core.Vec3(0))
        self._origin.look_at(direction)
        self._origin.set_pos(origin)

    def set_orientation_offset(self, point=core.Vec3(0), hpr=core.Vec3(0)):
        point.y = -point.y
        self._orient_offset.set_pos_hpr(point, hpr)

    def orientation_offset_look_at(self, direction):
        self._orient_offset.look_at(self._orient_offset.get_pos() + direction)

    def set_pos_hp_r(self, x, y, z, h, p, r):
        """
        Update the entire rig in model space.

        Args:
            x: u-axis
            y: v-axis
            z: direction-axis
            h: heading
            p: pitch
            r: draw radius (distance from orientation)
        """
        # y flipped due to origin pitch/heading corrections
        self._orient.set_pos_hpr(x, -y, z, h, p, 0)
        self._draw.set_y(r)

    def set_hp_r(self, h, p, r=None):
        """
        Update heading and pitch of orientation and optionally draw distance.

        Args:
            h: heading
            p: pitch
            r: draw radius (distance from orientation)
        """
        self._orient.set_hpr(h, p, 0)
        if r is not None:
            self._draw.set_y(r)

    def set_dir_offset(self, o):
        """
        Updates only directional-axis.

        Args:
            o: offset
        """
        self._orient.set_z(o)

    def set_radius(self, r):
        """
        Update the draw distance.

        Args:
            r: draw radius (distance from orientation)
        """
        self._draw.set_y(r)
