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
from math import pi

import numpy as np
from panda3d import core

from .shapegen import shape
from . import common


sg = shape.ShapeGen()


# noinspection PyArgumentList
def fir_tree(
        avg_height=50,
        avg_segments=6,
        avg_radius=1.2,
        offset=0.4,
        tex=None
):
    height = random.uniform(
        offset * avg_height,
        (1.0 - offset + 1) * avg_height
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
    node_path = core.NodePath('fir_tree')
    trunk_node_path = node_path.attach_new_node(
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
    trunk_node_path.set_hpr(random.uniform(0, 360), random.uniform(0, 5), 0)
    if tex is not None:
        trunk_node_path.set_texture(tex, 1)
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
        br_node_path = node_path.attach_new_node(
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
        br_node_path.set_z(trunk_node_path, seg_start + seg_height * 0.5 + i * seg_height)
        br_node_path.set_hpr(random.uniform(0, 360), random.uniform(0, 5), 0)

    return node_path, trunk_radius


# noinspection PyArgumentList
def leaf_tree(
        avg_height=25,
        avg_radius=0.8,
        offset=0.6,
        tex=None
):
    height = random.uniform(
        offset * avg_height,
        (1.0 - offset + 1) * avg_height
    )
    trunk_radius = avg_radius / avg_height * height
    trunk_color = common.LEAF_TRUNK_START
    trunk_color += common.LEAF_TRUNK_DELTA * random.random()
    branch_color, branch_delta = random.choice(common.LEAF_BRANCH_COLORS)
    branch_color2 = branch_color * 0.999
    branch_color += common.LEAF_TRUNK_DELTA * random.random()
    branch_color2 += common.LEAF_TRUNK_DELTA * random.random()

    node_path = core.NodePath('leaf_tree')
    trunk_node_path = node_path.attach_new_node(
        sg.cone(
            origin=core.Vec3(0),
            direction=core.Vec3.up(),
            radius=(trunk_radius, 0),
            polygon=12,
            length=height,
            origin_offset=0.05,
            color=trunk_color,
            nac=False,
            name='leaf_tree/trunk'
        )
    )
    trunk_node_path.set_hpr(random.uniform(0, 360), random.uniform(0, 5), 0)
    if tex is not None:
        trunk_node_path.set_texture(tex, 1)

    for i in range(random.randint(1, 3)):
        bb = core.Vec3(
            random.uniform(trunk_radius * 4, height / 4),
            random.uniform(trunk_radius * 4, height / 4),
            random.uniform(height / 3, height * 0.4),
        )

        br_node_path = node_path.attach_new_node(
            sg.blob(
                origin=core.Vec3(0),
                direction=core.Vec3.up(),
                bounds=bb,
                color=branch_color,
                color2=branch_color2,
                name='fir_tree/branch',
                # seed=np.random.randint(0, 2**31, dtype=np.int32),
                noise_radius=12,
                nac=False
            )
        )
        br_node_path.set_z(trunk_node_path, height - bb.z * random.random())
        br_node_path.set_x(trunk_node_path, bb.x * (random.random() - 0.5))
        br_node_path.set_y(trunk_node_path, bb.y * (random.random() - 0.5))
        br_node_path.set_hpr(random.uniform(0, 360), random.uniform(0, 90), 0)
    return node_path, trunk_radius


# noinspection PyArgumentList
def obelisk(r=(2.5, 1.8)):
    node_path = core.NodePath('obelisk')
    base = node_path.attach_new_node(
        sg.cone(
            origin=core.Vec3(0),
            direction=core.Vec3.up(),
            radius=r,
            polygon=4,
            length=15.0,
            smooth=False,
            capsule=False,
            origin_offset=0,
            color=core.Vec4(core.Vec3(0.2), 1),
            nac=False
        )
    )
    top = node_path.attach_new_node(
        sg.cone(
            origin=core.Vec3(0),
            direction=core.Vec3.up(),
            radius=(r[1], 0),
            polygon=4,
            length=1.5,
            smooth=False,
            capsule=False,
            origin_offset=0,
            color=core.Vec4(core.Vec3(0.2), 1),
            nac=False
        )
    )
    top.set_z(15)
    # mat = core.Material()
    # mat.set_emission(core.Vec4(.35, 1.0, 0.52, 0.1))
    # mat.set_shininess(5.0)
    # node_path.set_material(mat)
    return node_path


# noinspection PyArgumentList
def stone(xy):
    node_path = core.NodePath('stone')
    base = common.STONE_START
    color = base + common.STONE_DELTA * random.random()
    color2 = base + common.STONE_DELTA * random.random()
    bb = core.Vec3(
        xy,
        random.uniform(min(xy) * 0.9, min(xy) * 1.1)
    )
    br_node_path = node_path.attach_new_node(
        sg.blob(
            origin=core.Vec3(0),
            direction=core.Vec3.up(),
            bounds=bb,
            color=color,
            color2=color2,
            name='fir_tree/branch',
            # seed=random.randint(0, 2 ** 32 - 1),
            noise_radius=200,
            nac=False
        )
    )
    return br_node_path


# noinspection PyArgumentList
def three_rings():
    node_path = core.NodePath('three_rings')
    o1 = obelisk((1.5, 0.8))
    o2 = obelisk((1.5, 0.8))
    o1.reparent_to(node_path)
    o2.reparent_to(node_path)
    o1.set_pos(common.TR_O1_OFFSET)
    o2.set_pos(common.TR_O2_OFFSET)
    random.shuffle(common.TR_COLORS)
    rings = []
    symbol_cards = []
    for r, h, c in zip(common.TR_RADII, common.TR_HEIGHTS, common.TR_COLORS):
        rings.append(node_path.attach_new_node(
            sg.cone(
                origin=core.Vec3(0),
                direction=core.Vec3.up(),
                radius=r,
                polygon=common.TR_POLYGON,
                length=h,
                color=c,
                nac=False
            )
        )
        )
        symbol_cards.append([])
        for i in range(6):
            r_node = rings[-1].attach_new_node('rot')
            c = core.CardMaker(f'symbol {len(rings)}/{i}')
            c.set_frame(core.Vec4(-1, 1, -1, 1))
            symbol_cards[-1].append(
                r_node.attach_new_node(c.generate())
            )
            r_node.set_h(i * 60)
            r_node.set_transparency(core.TransparencyAttrib.M_alpha)
            r_node.set_alpha_scale(common.TR_SYM_ALPHA)
            symbol_cards[-1][-1].set_y(r - 0.5)
            symbol_cards[-1][-1].set_z(h)
            symbol_cards[-1][-1].set_billboard_axis()

    return node_path, rings, symbol_cards


def lever(i):
    node_path = core.NodePath('lever')
    box = node_path.attach_new_node(
        sg.box(
            origin=core.Vec3(0),
            direction=core.Vec3.up(),
            bounds=common.TR_LEVER_BOX_BB,
            color=common.TR_COLORS[i] * 0.9,
            nac=False,
            name='lever_box'
        )
    )
    box.set_z(box, -common.TR_LEVER_BOX_BB[2])
    lev = node_path.attach_new_node(
        sg.cone(
            origin=core.Vec3(0),
            direction=core.Vec3.up(),
            radius=0.12,
            polygon=12,
            length=1.8,
            origin_offset=0.2,
            color=common.TR_COLORS[i] * 1.1,
            nac=False,
            name='lever'
        )
    )
    lev.set_z(0.15)
    # lev.set_r(90)
    return node_path, lev


def stone_circle(r, num_stones):
    node_path = core.NodePath('stone_circle')
    rot = node_path.attach_new_node('rot')
    d = rot.attach_new_node('d')
    d.set_y(r)
    c = 2 * pi * r / 2 * 3
    length = c / num_stones / 2
    for i in range(num_stones):
        rot.set_h(300 / num_stones * i - 30)
        p = d.get_pos(node_path)
        s = stone(core.Vec2(length / 2, length))
        s.reparent_to(node_path)
        s.set_pos(p)
    return node_path
