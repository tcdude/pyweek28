"""
Provides trees/bushes/etc.
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
from math import ceil

from panda3d import core

from .shapegen import shape
from . import common


# noinspection PyArgumentList
def fir_tree(
        avg_height=40,
        avg_segments=6,
        avg_radius=1.0,
        offset=0.6,
        tex=None
):
    height = random.uniform(
        (1.0 - offset) * avg_height,
        (1.0 + offset) * avg_height
    )
    segments = int(ceil(avg_segments / avg_height * height))
    trunk_radius = avg_radius / avg_height * height
    trunk_color = common.FIR_TRUNK_START
    trunk_color += common.FIR_TRUNK_DELTA * random.random()
    bbc = common.FIR_BRANCH_START + common.FIR_BRANCH_DELTA * random.random()
    branch_colors = [
        bbc + common.FIR_BRANCH_DELTA * (random.random() - 0.5) * 0.1
        for _ in range(segments)
    ]
    np = core.NodePath('fir_tree')
    sg = shape.ShapeGen()
    trunk_np = np.attach_new_node(
        sg.cone(
            origin=core.Vec3(0),
            direction=core.Vec3.up(),
            radius=(trunk_radius, 0),
            polygon=12,
            length=height,
            origin_offset=0.05,
            color=trunk_color,
            nac=False,
            name='fir_tree/trunk'
        )
    )
    trunk_np.set_hpr(random.uniform(0, 360), random.uniform(0, 5), 0)
    if tex is not None:
        trunk_np.set_texture(tex, 1)
    seg_height = height * 0.8 / segments
    seg_start = height * 0.2
    for i, bc in enumerate(branch_colors):
        radius = (
            random.uniform(
                (segments - i) * trunk_radius * 0.8,
                (segments - i) * trunk_radius * 1.0
            ),
            random.uniform(
                (segments - i - 1) * trunk_radius * 0.6,
                (segments - i - 1) * trunk_radius * 0.8
            ) if i < segments - 1 else 0,
        )
        br_np = np.attach_new_node(
            sg.cone(
                origin=core.Vec3(0),
                direction=core.Vec3.up(),
                radius=radius,
                polygon=16,
                length=seg_height,
                color=bc,
                nac=False,
                name=f'fir_tree/branch{i}'
            )
        )
        br_np.set_z(trunk_np, seg_start + seg_height * 0.5 + i * seg_height)
        br_np.set_hpr(random.uniform(0, 360), random.uniform(0, 5), 0)

    return np
