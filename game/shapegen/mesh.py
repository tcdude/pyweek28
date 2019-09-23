"""
Provides a Mesh class to abstract mesh handling
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
from math import radians
from typing import List
from typing import Dict

from panda3d import core

from . import util
from .. import common


class Mesh(object):
    def __init__(self, name='noname'):
        self._name = name
        self._pts = {}      # type: Dict[core.Point3, Point]
        self._vts = {}      # type: Dict[int, Vertex]
        self._trs = []      # type: List[Triangle]
        self._vid = 0
        self._vertex_normals_computed = -1

    def export(
            self,
            face_normals=True,
            avg_color=True,
            sharp_angle=80.0,
            nac=common.NAC
    ):
        """
        Return a Panda Node of the mesh.

        Args:
            face_normals: whether to use face normals (flat shading) or per
                vertex normals (smooth shading)
            avg_color: when using face_normals, if True assures 1 color per
                triangle
            sharp_angle: when using per vertex normals, defines the angle at
                which sharp edges will be generated
            nac: if True ignores the vertex color and uses the
                normal vector as color (helpful for debugging)
        """
        va = util.VertArray(self._name)

        if face_normals:  # flat shading
            # noinspection PyArgumentList
            va.set_num_rows(len(self._trs) * 3)
            for t in self._trs:
                c = None
                if nac:
                    c = core.Vec4(*tuple(t.normal), 1)
                elif avg_color:
                    c = core.Vec3(0, 0, 0)
                    for v in t:
                        c += v.color
                    c = core.Vec4(*tuple(c / 3), 1)
                triangle = [
                    va.add_row(v.point, t.normal, c or v.color, v.texcoord)
                    for v in t
                ]
                va.add_triangle(*triangle)
        else:  # smooth shading
            self._compute_smooth_normals(sharp_angle)
            # noinspection PyArgumentList
            va.set_num_rows(self._vid)
            mesh2va = {}    # type: Dict[Vertex, int]
            for v in self._vts.values():
                if not v.triangles:
                    continue
                if nac:
                    c = core.Vec4(*tuple(v.normal), 1)
                else:
                    c = v.color
                mesh2va[v] = va.add_row(v.point, v.normal, c, v.texcoord)
            for t in self._trs:
                triangle = [mesh2va[v] for v in t]
                va.add_triangle(*triangle)
        return va.node

    def _compute_smooth_normals(self, sharp_angle):
        """
        Computes per vertex normal and duplicates vertices where sharp edges
        happen. Bails out early if the mesh has already been computed before.

        Args:
            sharp_angle: angle in degrees at which vertices will be duplicated
                for sharp edges.
        """
        if self._vertex_normals_computed == self._vid:
            return
        split_cos = cos(radians(sharp_angle))
        for p in self._pts.values():
            triangles = {
                t: self[vid]
                for vid in p.vertices
                for t in self[vid].triangles
            }

            normal_groups = self._group_triangles(triangles, split_cos)
            self._vertex_duplication(triangles, normal_groups)
        self._vertex_normals_computed = self._vid

    def add_vertex(self, point, color=core.Vec4(1), texcoord=core.Vec2(0)):
        """
        Return unique vertex id, inserting a new one only if necessary.

        Args:
            point:
            color:
            texcoord:
        """
        if point not in self._pts:
            self._pts[point] = Point(point, self)
        return self._pts[point].add_vertex(color, texcoord)

    def add_triangle(self, va, vb, vc):
        self._trs.append(Triangle(self[va], self[vb], self[vc]))

    def insert_vertex(self, point, color, texcoord):
        """
        Return vertex id of a new vertex, not preventing duplication.
        Convenience function for Point, do not use otherwise.

        Args:
            point:
            color:
            texcoord:
        """
        self._vts[self._vid] = Vertex(self._vid, point, color, texcoord)
        self._vid += 1
        return self._vid - 1

    def __getitem__(self, item):
        if 0 <= item < self._vid:
            return self._vts[item]
        raise IndexError

    @staticmethod
    def _group_triangles(triangles, split_cos):
        """
        Return List[List[Triangle]] where every entry of the outer list is a
        set of triangles for vertex normal computation.

        Args:
            triangles: Dict[Triangle, Vertex]
            split_cos: cosine value at which to group
        """
        groups = []
        for t in triangles:
            if not groups:
                groups.append([t])
                continue
            gid = -1
            test_normal = t.normal
            for i, g in enumerate(groups):
                gid = i
                for test_t in g:
                    if test_normal.dot(test_t.normal) < split_cos:  # sharp edge
                        gid = -1
                        break
                if gid == i:
                    break
            if gid != -1:
                groups[gid].append(t)
            else:
                groups.append([t])
        return groups

    def _vertex_duplication(self, triangles, normal_groups):
        """
        Perform vertex duplication where necessary.

        Args:
            triangles: Dict[Triangle, Vertex]
            normal_groups: List[List[Triangle]]
        """
        normals = []
        for g in normal_groups:
            normal = core.Vec3(0)
            for t in g:
                normal += t.normal_mag
            normals.append(normal.normalized())

        vts2normal = {}  # type: Dict[Vertex, Dict[core.Vec3, List[Triangle]]]
        for g, n in zip(normal_groups, normals):
            for t in g:
                if triangles[t] in vts2normal:
                    if n not in vts2normal[triangles[t]]:
                        vts2normal[triangles[t]][n] = []
                    vts2normal[triangles[t]][n].append(t)
                else:
                    vts2normal[triangles[t]] = {n: [t]}

        for v in vts2normal:
            first = True
            for n in vts2normal[v]:
                if first:
                    first = False
                    v.normal = n
                    continue
                new_vid = self.insert_vertex(v.point, v.color, v.texcoord)
                self[new_vid].normal = n
                for t in vts2normal[v][n]:
                    t.repl_vertex(v, self[new_vid])
                    v.remove_triangle(t)


class Point(object):
    def __init__(self, point, mesh):
        self._point = point
        self._m = mesh          # type: Mesh
        self._vts = {}

    def add_vertex(self, color, texcoord):
        k = (color, texcoord)
        if k not in self._vts:
            self._vts[k] = self._m.insert_vertex(
                self._point,
                color,
                texcoord
            )
        return self._vts[k]

    @property
    def vertices(self):
        return [self._m[i].vid for i in self._vts.values()]


class Vertex(object):
    def __init__(self, vid, point, color=core.Vec4(1), texcoord=core.Vec2(0)):
        self._vid = vid
        self._point = point
        self._color = color
        self._texcoord = texcoord
        self._trs = []
        self._normal = None

    def add_triangle(self, triangle):
        self._trs.append(triangle)

    def remove_triangle(self, triangle):
        try:
            self._trs.pop(self._trs.index(triangle))
        except ValueError:
            print('triangle not found')
            raise

    @property
    def vid(self):
        return self._vid

    @property
    def triangles(self):
        return self._trs

    @property
    def normal(self):
        if self._normal is not None:
            return self._normal
        raise ValueError('no normal set')

    @normal.setter
    def normal(self, value):
        self._normal = value

    @property
    def point(self):
        return self._point

    @property
    def color(self):
        return self._color

    @property
    def texcoord(self):
        return self._texcoord


class Triangle(object):
    def __init__(self, va, vb, vc):
        self._va = va
        self._vb = vb
        self._vc = vc
        va.add_triangle(self)
        vb.add_triangle(self)
        vc.add_triangle(self)
        self._normal_mag = util.comp_triangle_normal(
            va.point,
            vb.point,
            vc.point,
            False
        )
        self._normal = self._normal_mag.normalized()

    @property
    def normal(self):
        return self._normal

    @property
    def normal_mag(self):
        return self._normal_mag

    def repl_vertex(self, old, new):
        vid = -1
        for i, v in enumerate(self):
            if v == old:
                vid = i
                break
        if vid > -1:
            self[vid] = new
            new.add_triangle(self)
        else:
            raise ValueError('old Vertex is not a part of this Triangle')

    def __getitem__(self, item):
        # type: (int) -> Vertex
        if item == 0:
            return self._va
        elif item == 1:
            return self._vb
        elif item == 2:
            return self._vc
        else:
            raise IndexError

    def __setitem__(self, key, value):
        if key == 0:
            self._va = value
        elif key == 1:
            self._vb = value
        elif key == 2:
            self._vc = value
        else:
            raise IndexError
