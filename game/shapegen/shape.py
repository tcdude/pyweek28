"""
Provides the ShapeGen class for basic shape generation.
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

from math import ceil
from math import pi
from typing import Union

import numpy as np
from panda3d import core

from . import draw
from . import mesh
from . import util
from .. import common


class ShapeGen(object):
    def __init__(self):
        self._draw = draw.Draw()

    def sphere(
            self,
            origin,
            direction,
            radius,
            polygon,
            h_deg=360.0,
            h_offset=0,
            p_from=-90.0,
            p_to=90.0,
            color=core.Vec4(1),
            nac=common.NAC,
            name=None
    ):
        """
        Returns a parametric sphere. Complete spheres get a cylindrical texture
        mapping, which is otherwise omitted.

        Args:
            origin:
            direction:
            radius:
            polygon: number of vertices to be used per 360° revolution
            h_deg:
            h_offset:
            p_from:
            p_to:
            color:
            nac:
            name:
        """
        h_polygon = max(3, int(ceil(polygon / 360 * h_deg)))
        segments = max(1, int(ceil(polygon / 2) / 180 * (p_to - p_from)))
        wrap = h_deg == 360
        complete = h_deg == 360 and p_to - p_from == 180.0
        self._draw.setup(origin, direction)
        self._draw.set_radius(radius)
        msh = mesh.Mesh(name or 'sphere')
        p_steps = np.linspace(p_from, p_to, segments + 1)
        h_steps = np.linspace(
            h_offset,
            h_deg + h_offset,
            h_polygon,
            endpoint=False
        )
        u_steps = np.linspace(0, 1, h_polygon, endpoint=False)
        v_steps = np.linspace(0, 1, segments + 1)
        last = len(p_steps) - 1
        verts = []
        slice_verts = []
        slice_upper = None  # type: Union[None, core.Point3]
        slice_lower = None  # type: Union[None, core.Point3]
        for i, (p, v) in enumerate(zip(p_steps, v_steps)):
            self._draw.set_hp_r(h_offset, p, radius)
            if i == 0:
                if p == -90.0:
                    if complete:
                        line = [
                            msh.add_vertex(
                                self._draw.point,
                                color,
                                core.Vec2(u, v)
                            )
                            for u in u_steps
                        ]
                    else:
                        line = [msh.add_vertex(self._draw.point, color)]
                else:
                    line = [msh.add_vertex(self._draw.center_point, color)]
                verts.append(line)
                if not wrap:
                    slice_verts.append(line[0])
                    slice_lower = msh[line[0]].point
                if p == -90.0:
                    continue

            if i < last or p < 90:
                line = []
                for j, (h, u) in enumerate(zip(h_steps, u_steps)):
                    self._draw.set_hp_r(h, p)
                    if complete:
                        line.append(
                            msh.add_vertex(
                                self._draw.point,
                                color,
                                core.Vec2(u, v)
                            )
                        )
                    else:
                        line.append(msh.add_vertex(self._draw.point, color))

                    if not wrap:
                        if j == 0:
                            slice_verts.insert(0, line[-1])
                        elif j == h_polygon - 1:
                            slice_verts.append(line[-1])
                if complete:
                    line.append(
                        msh.add_vertex(
                            msh[line[0]].point,
                            color,
                            core.Vec2(1, v)
                        )
                    )
                verts.append(line)

            if i == last:
                self._draw.set_hp_r(h_offset, p, radius)
                if p == 90.0:
                    if complete:
                        line = [
                            msh.add_vertex(
                                self._draw.point,
                                color,
                                core.Vec2(u, v)
                            )
                            for u in u_steps
                        ]
                    else:
                        line = [msh.add_vertex(self._draw.point, color)]
                else:
                    line = [msh.add_vertex(self._draw.center_point, color)]
                verts.append(line)
                if not wrap:
                    slice_verts.append(line[0])
                    slice_upper = msh[line[0]].point

        self._populate_triangles(msh, verts, wrap and not complete)
        if not wrap:
            center = slice_lower + (slice_upper - slice_lower) * 0.5
            verts = [[msh.add_vertex(center, color)], slice_verts]
            self._populate_triangles(msh, verts, True, True)
        return msh.export(
            face_normals=False,
            sharp_angle=80.0,
            nac=nac
        )

    def cone(
            self,
            origin,
            direction,
            radius,
            polygon,
            length,
            smooth=True,
            sharp_angle=80.0,
            capsule=False,
            h_deg=360.0,
            h_offset=0.0,
            origin_offset=0.5,
            top_offset=(0.0, 0.0),
            color=core.Vec4(1),
            nac=common.NAC,
            name=None
    ):
        """
        Returns a parametric cone shape. Serves as basis for prism, cylinder
        and capsule.

        Args:
            origin:
            direction:
            radius: Union[float, Tuple[float, float]]
            polygon: number of vertices to be used per 360° revolution
            length: for capsule needs to be > 2 * radius to account for the
                capsule
            smooth: whether to use smooth of flat shading
            sharp_angle: the angle in degrees at which sharp edges are
                generated.
            capsule: whether to put capsules at ends with radius > 0
            h_deg: non-zero float <= 360.0
            h_offset: defines the offset in degrees of the draw heading.
            origin_offset: float 0..1 indicating how far the origin is from the
                base
            top_offset: Tuple[float, float] x/y offset at the top
            color:
            nac:
            name:
        """
        rd = radius if isinstance(radius, (tuple, list)) else (radius, radius)
        for i, r in enumerate(rd):
            if i > 1:
                raise ValueError('maximum 2 radii allowed')
            if r <= 0:
                raise ValueError('radius/radii have to be positive and '
                                 'non-zero float(s)/int(s)')
        if capsule and length <= sum(rd):
            raise ValueError('length has to be > radius * 2 or sum(radius)')
        if not (0.0 <= origin_offset <= 1.0):
            raise ValueError('origin_offset must be in 0..1 range')

        # draw/mesh/general
        self._draw.setup(origin, direction)
        wrap = h_deg == 360
        msh = mesh.Mesh(name or 'cone')

        # distance and amount computation
        h_polygon = max(3, int(ceil(polygon / 360 * h_deg)))
        circumference = 2 * pi * (sum(rd) * 0.5)
        seg_len = circumference / polygon
        if capsule:
            cap_segments = max(2, int(ceil(sum(rd) / seg_len / 2)))
            bod_segments = int(ceil((length - sum(rd)) / seg_len))
        else:
            cap_segments = 0
            bod_segments = int(ceil(length / seg_len))
        if wrap:
            slice_len = 0.0
        else:
            slice_len = 2 * rd[0]
        u_len = circumference / 360 * h_deg + slice_len
        slice_start_u = 1.0 - slice_len / u_len
        body_len = (length - sum(rd)) if capsule else length
        v_len = sum(rd) * capsule + body_len
        body_start_v = 1.0 / v_len * rd[0] * capsule
        body_end_v = 1.0 - 1.0 / v_len * rd[1] * capsule
        body_base = -origin_offset * length + rd[0] * capsule
        body_top = (1.0 - origin_offset) * length - rd[1] * capsule

        # radii, direction, heading, pitch, uv
        if capsule and rd[0]:
            lcap_r_steps = np.array([rd[0]] * cap_segments, np.float64)
            lcap_dir_steps = np.array([body_base] * cap_segments, np.float64)
            lcap_v_steps = np.linspace(
                0,
                body_start_v,
                cap_segments,
                endpoint=False
            )
            lcap_p_steps = np.linspace(
                -90,
                0,
                cap_segments,
                endpoint=False
            )
        else:
            lcap_r_steps = np.array([0.0])
            lcap_dir_steps = np.array([body_base])
            lcap_v_steps = np.zeros(1)
            lcap_p_steps = np.zeros(1)

        if capsule and rd[1]:
            ucap_r_steps = np.array([rd[1]] * cap_segments, np.float64)
            ucap_dir_steps = np.array([body_top] * cap_segments, np.float64)
            ucap_v_steps = np.linspace(
                1.0,
                body_end_v,
                cap_segments,
                endpoint=False
            )
            ucap_v_steps = ucap_v_steps[::-1]
            ucap_p_steps = np.linspace(
                90,
                0,
                cap_segments,
                endpoint=False
            )[::-1]
        else:
            ucap_r_steps = np.array([0.0])
            ucap_dir_steps = np.array([body_top])
            ucap_v_steps = np.ones(1)
            ucap_p_steps = np.zeros(1)

        body_r_steps_dir = np.linspace(rd[0], rd[1], bod_segments + 1)
        body_dir_steps = np.linspace(
            body_base,
            body_top,
            bod_segments + 1
        )
        body_v_steps = np.linspace(
            body_start_v,
            body_end_v,
            cap_segments * 2 + bod_segments + 1
        )

        dir_steps = np.append(lcap_dir_steps, body_dir_steps)
        dir_steps = np.append(dir_steps, ucap_dir_steps)
        dir_radii = np.append(lcap_r_steps, body_r_steps_dir)
        dir_radii = np.append(dir_radii, ucap_r_steps)
        dir_v_steps = np.append(lcap_v_steps, body_v_steps)
        dir_v_steps = np.append(dir_v_steps, ucap_v_steps)
        p_steps = np.append(lcap_p_steps, np.zeros(bod_segments + 1))
        p_steps = np.append(p_steps, ucap_p_steps)

        if wrap:
            h_steps = np.linspace(h_offset, h_deg + h_offset, h_polygon + 1)
            h_radii = np.ones(h_polygon + 1)
            u_steps = np.linspace(
                0,
                1,
                h_polygon + 1
            )
        else:
            h_steps = np.linspace(h_offset, h_deg + h_offset, h_polygon)
            h_steps = np.append(
                h_steps,
                np.linspace(
                    360.0 + h_offset,
                    h_deg + h_offset,
                    2,
                    endpoint=False
                )[::-1]
            )
            h_radii = np.append(np.ones(h_polygon), [0.0, 1.0])
            u_steps = np.linspace(
                0,
                slice_start_u,
                h_polygon
            )
            u_steps = np.append(
                u_steps,
                np.linspace(
                    1,
                    slice_start_u,
                    2 * (not wrap), endpoint=False
                )[::-1]
            )

        # offset TODO: find out how to modify Draw to allow this
        x_steps = np.linspace(0, top_offset[0], len(dir_steps))
        y_steps = np.linspace(0, top_offset[1], len(dir_steps))

        verts = []
        for d, r, p, v, xo, yo in zip(
                dir_steps, dir_radii, p_steps, dir_v_steps, x_steps, y_steps):
            self._draw.set_dir_offset(d)
            line = []
            for h, hr, u in zip(h_steps, h_radii, u_steps):
                self._draw.set_hp_r(h, p, r * hr if not p else r)
                line.append(msh.add_vertex(
                    self._draw.point if hr else self._draw.center_point,
                    color,
                    core.Vec2(u, v)
                ))
            verts.append(line)
        self._populate_triangles(msh, verts, False, chk_illegal=True)

        if smooth:
            return msh.export(
                face_normals=False,
                sharp_angle=sharp_angle,
                nac=nac
            )
        return msh.export(
            nac=nac
        )

    @staticmethod
    def _populate_triangles(msh, verts, wrap, ccw=True, chk_illegal=False):
        for i in range(len(verts) - 1):
            upper = verts[i + 1]
            lower = verts[i]
            tri_ids = util.triangle_line_connect(
                len(upper),
                len(lower),
                wrap,
                ccw
            )
            for up, lo in tri_ids:
                triangle = [upper[v] for v in up] + [lower[v] for v in lo]
                if chk_illegal:
                    pts = []
                    for v in triangle:
                        point = msh[v].point
                        if point in pts:
                            break
                        pts.append(point)
                    if len(pts) < 3:
                        continue
                msh.add_triangle(*triangle)
