"""
A rudimentary 2D collision system.
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

from math import cos
from math import sin
from math import sqrt
from math import radians
from typing import List
from typing import Union

from panda3d import core

from .shapegen import util


NOP = 0
CIRCLE = 1
ELLIPSE = 2


class CollisionHandler(object):
    def __init__(
            self,
            origin,
            half_bounds,
            max_depth=8,
            max_leafs=16
    ):
        self.qt = util.QuadTree(origin, half_bounds, max_depth, max_leafs)

    def add(self, collision_shape):
        # type: (CollisionShape) -> None
        self.qt.insert(collision_shape.aabb, collision_shape)

    # noinspection DuplicatedCode
    def traverse(self, op, dp, r):
        # type: (core.Vec2, core.Vec2, float) -> (core.Vec2, float)
        """
        Return corrected position and rate change in speed in range [0, -1].

        Args:
            op: origin point
            dp: destination point
            r: collision radius
        """
        aabb = util.AABB(dp, core.Vec2(r))
        chk = self.qt.query(
            aabb
        )  # type: List[Union[CollisionCircle, CollisionEllipse]]
        if not chk:
            return dp, 0.0
        forward = (dp - op).normalized()
        r_sq = r ** 2
        callbacks = []
        checked = {}
        rate = 0
        collisions = 0

        for s in chk:
            if s in checked or not aabb.intersect(s.aabb):
                continue
            checked[s] = core.Vec2(0)
            if s.shape == CIRCLE:
                delta = dp - s.point
                if delta.length_squared() >= r_sq + s.r ** 2:
                    continue
                if s.callback is not None:
                    callbacks.append(s.callback)
                if s.ghost:
                    continue

                collisions += 1
                d_n = delta.normalized()
                rate += forward.dot(d_n) * 0.5 - 0.5
                checked[s] = d_n * (r + s.r - delta.length())
            elif s.shape == ELLIPSE:
                delta = dp - s.point
                sp = core.Vec2(
                    delta.x * s.cos - delta.y * s.sin,
                    delta.y * s.cos + delta.x * s.sin
                )
                if abs(sp.x) - r >= s.a or abs(sp.y) - r >= s.b:
                    continue
                spx_sq = sp.x ** 2
                spy_sq = sp.y ** 2
                if s.a >= s.b:
                    a, b, a_sq, b_sq = s.a, s.b, s.a_sq, s.b_sq
                else:
                    b, a, b_sq, a_sq = s.a, s.b, s.a_sq, s.b_sq

                d = spx_sq / a_sq + spy_sq / b_sq
                if d > 1:
                    continue
                collisions += 1
                p2 = core.Vec2(
                    sp.x,
                    sqrt(b_sq * (1.0 - spx_sq / a_sq))
                )
                p1 = core.Vec2(
                    sqrt(a_sq * (1.0 - spy_sq / b_sq)),
                    sp.y
                )
                intersect = (p1 + p2) / 2
                n = (p2 - p1).normalized()
                mag = (intersect - sp)
                n.xy = -n.y, n.x
                n_mag = n * mag.length()
                rate += forward.dot(n) * 0.5 - 0.5
                n_mag.x, n_mag.y = (
                    n_mag.x * s.inv_cos - n_mag.y * s.inv_sin,
                    n_mag.y * s.inv_cos + n_mag.x * s.inv_sin
                )
                checked[s] = n_mag.normalized()
            else:
                raise ValueError(f'unknown shape {s.shape}')
        for f, a in callbacks:
            f(*a)

        if collisions == 0:
            return dp, 0.0

        d = core.Vec2(0)
        for v in checked.values():
            d += v
        d /= collisions
        return dp + d, rate / collisions


class CollisionShape(object):
    shape = NOP
    point = core.Vec2(0)
    aabb = None
    callback = None
    ghost = None


class CollisionCircle(CollisionShape):
    shape = CIRCLE

    def __init__(self, p, r, callback=None, ghost=False):
        self.point = p
        self.r = r
        self.aabb = util.AABB(p, core.Vec2(r))
        self.callback = callback
        self.ghost = ghost


class CollisionEllipse(CollisionShape):
    shape = ELLIPSE

    def __init__(self, p, a, b, h_offset=0, callback=None, ghost=False):
        self.point = p
        self.a, self.b, self.h_offset = a, b, h_offset
        self.a_sq, self.b_sq = a ** 2, b ** 2
        self.sin = sin(radians(h_offset))
        self.cos = cos(radians(h_offset))
        self.inv_sin = sin(radians(-h_offset))
        self.inv_cos = cos(radians(-h_offset))
        x = a * self.cos - b * self.sin
        y = b * self.cos + a * self.sin
        self.aabb = util.AABB(p, core.Vec2(abs(x), abs(y)))
        self.callback = callback
        self.ghost = ghost
