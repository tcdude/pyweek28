"""
Provides various utility functions and classes.
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

from panda3d import core


def comp_triangle_normal(pa, pb, pc, normalized=True):
    """Return triangle face normal for ccw wound triangle pa, pb, pc"""
    u = pb - pa
    v = pc - pa
    n = u.cross(v)
    if normalized:
        n.normalize()
    return n


def _triangle_line_connect(upper, lower, wrap_around, ccw):
    """Return triangle indices for two lines of vertices"""
    steps = max(upper, lower)
    upper_edges = np.linspace(0, upper, steps, endpoint=False, dtype=np.int32)
    lower_edges = np.linspace(0, lower, steps, endpoint=False, dtype=np.int32)
    if ccw:
        upper_edges = upper_edges[::-1]
        lower_edges = lower_edges[::-1]

    triangles = []
    for i in range(steps - 0 if wrap_around else steps - 1):
        id1 = i
        id2 = (i + 1) % steps
        u_edge = upper_edges[id1] != upper_edges[id2]
        l_edge = lower_edges[id1] != lower_edges[id2]

        if u_edge:
            triangles.append(
                (
                    (upper_edges[id1], upper_edges[id2]),
                    (lower_edges[id1], )
                )
            )
            if l_edge:
                triangles.append(
                    (
                        (upper_edges[id2], ),
                        (lower_edges[id2], lower_edges[id1])
                    )
                )
                continue

        if l_edge:
            triangles.append(
                (
                    (upper_edges[id1], ),
                    (lower_edges[id2], lower_edges[id1])
                )
            )
    return triangles


_tlc_cache = {}


def triangle_line_connect(upper, lower, wrap_around=True, ccw=True):
    """
    Return a list of 2-tuples that make up single triangles from upper, lower.

    Args:
        upper: length of the upper line (num vertices)
        lower: length of the lower line (num vertices)
        wrap_around: whether the last vertex should connect back to the first
        ccw: whether the lines are in ccw order
    """
    k = (upper, lower, wrap_around, ccw)
    if k not in _tlc_cache:
        _tlc_cache[k] = _triangle_line_connect(*k)
    return _tlc_cache[k]


# noinspection PyArgumentList
class VertArray(object):
    def __init__(self, name='noname'):
        self._name = name
        self._vdata = core.GeomVertexData(
            self._name,
            core.GeomVertexFormat.get_v3n3c4t2(),
            core.Geom.UH_static
        )
        self._vwriter = core.GeomVertexWriter(self._vdata, 'vertex')
        self._nwriter = core.GeomVertexWriter(self._vdata, 'normal')
        self._cwriter = core.GeomVertexWriter(self._vdata, 'color')
        self._twriter = core.GeomVertexWriter(self._vdata, 'texcoord')
        self._prim = core.GeomTriangles(core.Geom.UH_static)

        self._v_id = 0
        self.set_num_rows = self._vdata.set_num_rows

    def add_row(self, point, normal, color, tex):
        self._vwriter.add_data3(point)
        self._nwriter.add_data3(normal)
        self._cwriter.add_data4(color)
        self._twriter.add_data2(tex)
        self._v_id += 1
        return self._v_id - 1

    def add_triangle(self, va, vb, vc):
        self._prim.add_vertices(va, vb, vc)

    def transform(self, mat):
        self._vdata.transform_vertices(mat)

    @property
    def node(self):
        geom = core.Geom(self._vdata)
        geom.add_primitive(self._prim)
        node = core.GeomNode(self._name)
        node.add_geom(geom)
        return node
