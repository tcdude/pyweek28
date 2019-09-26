"""
Signed Distance Fields.
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


def circle(shape, r):
    a = np.indices(shape)
    a[0] -= shape[0] // 2
    a[1] -= shape[1] // 2
    length = a[0] ** 2 + a[1] ** 2
    a = length < r ** 2
    return a


def random_polygon(cx, cy, avg_r, variance, frequency, num_verts):
    """
    Return a random polygon.

    Args:
        cx: center x
        cy: center y
        avg_r: average radius
        variance: 0..1
        frequency: 0..1
        num_verts:
    """
    def clip(_x, vmin, vmax):
        if vmin > vmax:
            return _x
        elif _x < vmin:
            return vmin
        elif _x > vmax:
            return vmax
        else:
            return _x

    variance = clip(variance, 0, 1) * 2 * np.pi / num_verts
    frequency = clip(frequency, 0, 1) * avg_r

    angle_steps = []
    lower = (2 * np.pi / num_verts) - variance
    upper = (2 * np.pi / num_verts) + variance
    tot = 0
    for i in range(num_verts):
        tmp = np.random.uniform(lower, upper)
        angle_steps.append(tmp)
        tot = tot + tmp

    k = tot / (2 * np.pi)
    for i in range(num_verts):
        angle_steps[i] = angle_steps[i] / k

    points = []
    angle = np.random.uniform(0, 2 * np.pi)
    for i in range(num_verts):
        r_i = clip(np.random.normal(avg_r, frequency), 0, 2 * avg_r)
        x = cx + r_i * np.cos(angle)
        y = cy + r_i * np.sin(angle)
        points.append((int(x), int(y)))

        angle = angle + angle_steps[i]

    return points
