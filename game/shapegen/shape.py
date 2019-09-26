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
from . import noise
from . import util
from .. import common


class ShapeGen(object):
    def __init__(self):
        self._draw = draw.Draw()
        self._noise = noise.Noise()

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
        zc = 0
        for i, r in enumerate(rd):
            if i > 1:
                raise ValueError('maximum 2 radii allowed')
            if r <= 0:
                zc += 1
        if zc == 2:
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

    def box(
            self,
            origin,
            direction,
            bounds,
            max_seg_len=None,
            corner_radius=0.0,
            smooth=False,
            sharp_angle=80.0,
            color=core.Vec4(1),
            nac=common.NAC,
            name=None
    ):
        """
        Returns a parametric cuboid shape.

        Args:
            origin:
            direction:
            bounds: half distance
            max_seg_len: number of vertices per plane (multiple of 4)
            corner_radius: radius at corners and edges
            smooth:
            sharp_angle:
            color:
            nac:
            name:
        """
        if not isinstance(bounds, core.Vec3):
            raise TypeError('bounds needs to be type Vec3')
        if not isinstance(corner_radius, (float, int)) or corner_radius < 0:
            raise ValueError('corner_radius is expected to be a number >= 0')
        if corner_radius >= min(bounds):
            raise ValueError('illegal corner radius')
        if not isinstance(sharp_angle, (int, float)) \
                or not (0 < sharp_angle <= 180):
            raise ValueError('illegal value for sharp_angle')
        if not (isinstance(max_seg_len, (float, int)) or max_seg_len is None):
            raise TypeError('expected float/int/NoneType for arg polygon')
        # if max_seg_len is not None \
        #         and max_seg_len > min(bounds) - corner_radius:
        #     raise ValueError('expected max_seg_len to be larger than the '
        #                      'smallest bounds - corner_radius')

        msh = mesh.Mesh(name or 'box')
        self._draw.setup(core.Vec3(0), core.Vec3.forward())

        max_seg_len = max_seg_len or min(bounds - corner_radius) / 4
        b_seg_count = core.LVecBase3i(
            *map(int, map(
                    ceil, (bounds - corner_radius) / max_seg_len
            ))
        )
        top_seg_count = int(
            ceil(max((bounds.xy - corner_radius) / max_seg_len))
        )
        z_seg_count = int(ceil((bounds.z - corner_radius) / max_seg_len))
        top_x_m = np.linspace(
            0,
            1.0 / bounds.x * (bounds.x - corner_radius),
            top_seg_count,
            endpoint=False
        )
        top_y_m = np.linspace(
            0,
            1.0 / bounds.y * (bounds.y - corner_radius),
            top_seg_count,
            endpoint=False
        )

        if corner_radius:
            c_seg_count = max(
                int(ceil(pi * corner_radius * 0.5 / max_seg_len)),
                3
            )
            hpi = np.linspace(0, np.pi * 0.5, c_seg_count + 1)
            sin_quart = np.sin(hpi)
            cos_quart = np.round(np.cos(hpi), 6)
            x_offsets = np.concatenate((
                np.linspace(
                    0,
                    bounds.x - corner_radius,
                    b_seg_count.x + 1,
                    endpoint=False
                ),
                bounds.x - (1 - sin_quart) * corner_radius,
                np.array([bounds.x] * b_seg_count.y)
            ))
            y_offsets = np.concatenate((
                np.array([bounds.y] * (b_seg_count.x + 1)),
                bounds.y - (1 - cos_quart) * corner_radius,
                np.linspace(
                    0,
                    bounds.y - corner_radius,
                    b_seg_count.y,
                    endpoint=False
                )[::-1]
            ))
            z_offsets = np.concatenate((
                np.ones(top_seg_count) * bounds.z,
                bounds.z - corner_radius + cos_quart * corner_radius,
                np.linspace(
                    0,
                    bounds.z - corner_radius,
                    z_seg_count,
                    endpoint=False
                )[::-1]
            ))
            z_x_m = np.concatenate((
                top_x_m,
                1.0 / bounds.x * (
                        bounds.x - corner_radius + sin_quart * corner_radius),
                np.ones(z_seg_count)
            ))
            z_y_m = np.concatenate((
                top_y_m,
                1.0 / bounds.y * (
                        bounds.y - corner_radius + sin_quart * corner_radius),
                np.ones(z_seg_count)
            ))
        else:
            x_offsets = np.concatenate((
                np.linspace(0, bounds.x, b_seg_count.x, endpoint=False),
                np.ones(b_seg_count.y + 1) * bounds.x
            ))
            y_offsets = np.concatenate((
                np.ones(b_seg_count.x) * bounds.y,
                np.linspace(bounds.y, 0, b_seg_count.y + 1)
            ))
            z_offsets = np.concatenate((
                np.ones(top_seg_count + 1) * bounds.z,
                np.linspace(
                    0,
                    bounds.z,
                    z_seg_count,
                    endpoint=False
                )[::-1]
            ))
            z_x_m = np.concatenate((
                top_x_m,
                np.ones(z_seg_count + 1)
            ))
            z_y_m = np.concatenate((
                top_y_m,
                np.ones(z_seg_count + 1)
            ))

        verts = []
        for z, xm, ym in zip(z_offsets, z_x_m, z_y_m):
            if xm == ym == 0:
                self._draw.set_pos_hp_r(0, 0, z, 0, 0, 0)
                verts.append([msh.add_vertex(self._draw.point, color)])
                continue
            elif not xm or not ym:
                raise RuntimeError('xm and ym must be either both 0 or '
                                   'positive')
            line = []
            for x, y in zip(x_offsets * xm, y_offsets * ym):
                self._draw.set_pos_hp_r(x, y, z, 0, 0, 0)
                line.append(msh.add_vertex(self._draw.point, color))
            verts.append(line)

        self._populate_triangles(msh, verts, wrap=False, ccw=False)
        for i in range(3):
            msh.mirror_extend(i)
        self._draw.setup(origin, direction)
        return msh.export(
            face_normals=not smooth,
            sharp_angle=sharp_angle,
            nac=nac,
            transform=self._draw.transform_mat,
            no_texcoord=True
        )

    def blob(
            self,
            origin,
            direction,
            bounds,
            smooth=True,
            sharp_angle=80.0,
            color=core.Vec4(1),
            color2=None,
            nac=common.NAC,
            seed=None,
            noise_radius=6.0,
            noise_frequency=0.001,
            name=None
    ):
        """
        Return a random blob that fits inside specified bounds.

        Args:
            origin:
            direction:
            bounds:
            smooth:
            sharp_angle:
            color:
            color2: if specified, mixes the two colors by noise
            nac:
            seed:
            noise_radius:
            noise_frequency:
            name:
        """
        msh = mesh.Mesh(name or 'blob')
        self._draw.setup(origin, direction)
        seg_len = min(bounds) / 2
        segments = core.LVecBase3i(*map(int, bounds / seg_len)) + 1
        h_segments = (sum(segments.xy) - 2) * 2
        p_segments = h_segments // 2 + 1
        h_n, p_n, r_n, c_n = self._noise.blob(
            h_segments, p_segments, 4, noise_radius, seed, noise_frequency
        )
        c_n = [1 / (c.max() - c.min()) * (c - c.min()) for c in c_n]
        base_r = np.average(r_n[0])
        top_r = np.average(r_n[-1])
        base_c = np.average(c_n[0])
        top_c = np.average(c_n[-1])
        p_steps = np.linspace(-90, 90, p_segments)
        p_step = (p_steps[1] - p_steps[0]) * 0.9
        h_steps = np.linspace(0, 360, h_segments, endpoint=False)
        h_step = (h_steps[1] - h_steps[0]) * 0.9
        verts = []
        for pid, p in enumerate(p_steps):
            if abs(p) == 90:
                r = base_r if p == -90 else top_r
                r = bounds.z + r * bounds.z
                self._draw.set_hp_r(0, p, r)
                if color2 is None:
                    c = color
                else:
                    f = base_c if p == -90 else top_c
                    c = f * color + (1 - f) * color2
                    c = core.Vec4(*c)
                verts.append([msh.add_vertex(self._draw.point, c)])
                continue
            # af = pid * h_segments
            # at = af + h_segments
            twopi = np.linspace(0, 2 * np.pi, h_segments, endpoint=False)
            zp = (
                h_steps,
                h_n[pid],
                p_n[pid],
                r_n[pid],
                c_n[pid],
                np.abs(np.cos(twopi)),
                np.abs(np.sin(twopi))
            )
            verts.append([])
            sin_p = abs(np.sin(np.radians(p)))
            cos_p = abs(np.cos(np.radians(p)))
            rz = sin_p * bounds.z
            for h, ho, po, ro, c, cos_h, sin_h in zip(*zp):
                rx = cos_h * bounds.x
                ry = sin_h * bounds.y
                r_h = np.sqrt(rx ** 2 + ry ** 2) * cos_p
                r = np.sqrt(r_h ** 2 + rz ** 2)
                self._draw.set_hp_r(
                    h + ho * h_step,
                    p + po * p_step,
                    r + r * ro
                )
                if color2 is None:
                    col = color
                else:
                    col = c * color + (1 - c) * color2
                    col = core.Vec4(*col)
                verts[-1].append(
                    msh.add_vertex(self._draw.point, col)
                )
        self._populate_triangles(msh, verts, wrap=True)
        return msh.export(
            face_normals=not smooth,
            sharp_angle=sharp_angle,
            nac=nac
        )

    def elliptic_cone(
            self,
            a,
            b,
            h,
            max_seg_len=1.0,
            exp=2.0,
            top_xy=(0, 0),
            color=core.Vec4(1),
            nac=common.NAC,
            name=None,
    ):
        """
        Return the shape used for the Devils Tower mountain. Features must be
        put on via normal map.

        Args:
            a: 2-Tuple base and top a for the ellipse
            b: 2-Tuple base and top b for the ellipse
            h: height
            max_seg_len: maximum segment length (approximation)
            exp: exponent used to determine slope from base to top
            top_xy: displacement between base and top on the xy-plane.
            color:
            nac:
            name:
        """
        if a[0] == a[1]:
            a = a[0], a[1] * 1.0001
        if b[0] == b[1]:
            b = b[0], b[1] * 1.0001

        msh = mesh.Mesh(name or 'devils_tower')
        h_seg_len = np.sqrt((max_seg_len ** 2) / 2)
        base_perimeter = 2 * np.pi * np.sqrt((a[0] ** 2 + b[0] ** 2) / 2)
        top_perimeter = 2 * np.pi * np.sqrt((a[1] ** 2 + b[1] ** 2) / 2)
        if base_perimeter >= top_perimeter:
            el_points = int(base_perimeter / h_seg_len) + 1
        else:
            el_points = int(top_perimeter / h_seg_len) + 1
        ellipse = util.ellipse(a[1], b[1], el_points)
        el_points *= 4
        h_st = int(h / max_seg_len) + 1
        z_st = np.linspace(0, h, h_st)
        u_st = np.linspace(1, 0, el_points + 1)
        v_off = 1 / (max(max(a), max(b)) + h) * h
        v_st = np.linspace(0, v_off, h_st)
        slope = np.linspace(1, 0, h_st) ** exp

        a_delta = a[1] - a[0]
        b_delta = b[1] - b[0]
        sl_a = slope * a_delta
        sl_b = slope * b_delta
        sl_x = (1 - slope) * top_xy[0]
        sl_y = (1 - slope) * top_xy[1]

        verts = []
        for sa, sb, sx, sy, z, v in zip(sl_a, sl_b, sl_x, sl_y, z_st, v_st):
            verts.append([])
            el = ellipse * 1
            af = (a[1] - sa) / a[1]
            bf = (b[1] - sb) / b[1]
            el[:, 0] = el[:, 0] * af + sx
            el[:, 1] = el[:, 1] * bf + sy
            for i in range(el_points + 1):
                el_i = i % el_points
                verts[-1].append(
                    msh.add_vertex(
                        core.Vec3(*el[el_i], z),
                        color,
                        core.Vec2(u_st[i], v)
                    )
                )

        verts.append([])
        el = ellipse * 0.5
        for i in range(el_points + 1):
            el_i = i % el_points
            verts[-1].append(
                msh.add_vertex(
                    core.Vec3(*el[el_i], h * 1.005),
                    color,
                    core.Vec2(u_st[i], 1 - (1 - v_off) / 2)
                )
            )
        verts.append([msh.add_vertex(
            core.Vec3(*top_xy, h * 1.012),
            color,
            core.Vec2(1)
        )])
        self._populate_triangles(msh, verts, wrap=False)
        return msh.export(face_normals=False, nac=nac, tangent=True)

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
