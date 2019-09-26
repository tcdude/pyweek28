"""
A simple 3rd person camera controller that follows the character while trying to
avoid obstacles.
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

from .shapegen import util
from . import common


class FollowCam(object):
    def __init__(self, root, cam, follow, sample_z):
        self.root = root
        self.cam = cam
        self.follow = follow
        self.sample_z = sample_z
        self.dummy = self.root.attach_new_node('cam' + follow.get_name())
        self.z_dummy = self.dummy.attach_new_node('cam_z' + follow.get_name())
        self.z_dummy.set_z(-common.Z_OFFSET)
        self.cam_z = self.follow.get_pos(self.root).z + common.Z_OFFSET

    def update(self, dt):
        f_pos = self.follow.get_pos(self.root)
        z_diff = f_pos.z + common.Z_OFFSET - self.cam_z
        self.dummy.set_pos(f_pos)
        h = util.clamp_angle(self.dummy.get_h())
        t = util.clamp_angle(self.follow.get_h() - h) * dt
        self.dummy.set_h(h + t * common.TURN_RATE)
        x, y, z = self.z_dummy.get_pos(self.root)
        z_diff += self.sample_z(x, y) - z
        if z_diff < 0:
            z_diff = max(common.Z_RATE * -dt, z_diff)
        else:
            z_diff = min(common.Z_RATE * dt, z_diff)
        self.cam_z = common.Z_OFFSET + z_diff
        self.cam.set_pos(self.root, self.dummy.get_pos())
        self.cam.set_y(self.dummy, common.Y_OFFSET)
        self.cam.set_z(self.dummy, self.cam_z)
        self.cam.look_at(f_pos + common.FOCUS_POINT)
