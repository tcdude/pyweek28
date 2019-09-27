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

from typing import Optional
from typing import Union

import numpy as np
from PIL import Image
from PIL import ImageDraw

from panda3d import core


def bw_tex(x, y):
    black = (0, 0, 0, 255)
    white = (255, ) * 4
    im = Image.new('RGBA', (x, y), black)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, x // 8 - 1, y - 1), white, white)
    d.rectangle(((x // 8) * 3 - 1, 0,  (x // 8) * 5 - 1, y - 1), white, white)
    d.rectangle(((x // 8) * 7 - 1, 0,  x - 1, y - 1), white, white)
    d.ellipse(
        (x // 8 * 2 - 1, (y // 8) * 3 - 1, x // 8 * 4 - 1, (y // 8) * 5 - 1),
        white,
        white
    )
    # im.show()
    return np.array(im, dtype=np.float32) / 255


def clamp_angle(deg):
    while deg < -180:
        deg += 360
    while deg > 180:
        deg -= 360
    return deg


def sobel(hf, c):
    # type: (np.ndarray, float) -> np.ndarray
    y, x = hf.shape
    uv = np.empty((y + 2, x + 2), dtype=hf.dtype)
    uv[1:y + 1, 1:x + 1] = hf
    uv[1:-1, 0] = hf[:, -1]
    uv[1:-1, -1] = hf[:, 0]
    uv[0, :] = uv[1, :]
    uv[-1, :] = uv[-2, :]

    norm_x = uv[2:, 2:] - uv[2:, :-2]
    norm_x += 2 * (uv[1:-1, 2:] - uv[1:-1, :-2])
    norm_x += uv[:-2, 2:] - uv[:-2, :-2]
    norm_x *= -c
    norm_y = uv[:-2, :-2] - uv[2:, :-2]
    norm_y += 2 * (uv[:-2, 1:-1] - uv[2:, 1:-1])
    norm_y += uv[:-2, 2:] - uv[2:, 2:]
    norm_y *= -c
    norm_z = norm_x * 0 + 1.0
    lens = np.sqrt(norm_x ** 2 + norm_y ** 2 + norm_z)
    normalized = np.empty((y, x, 3), dtype=hf.dtype)
    normalized[:, :, 0] = norm_x / lens
    normalized[:, :, 1] = norm_y / lens
    normalized[:, :, 2] = norm_z / lens
    normalized = normalized * 0.5 + 0.5
    return (normalized * 255).astype(np.uint8)


def ellipse(a, b, q_points=None, ccw=False):
    # type: (float, float, Optional[None, int], Optional[bool]) -> np.ndarray
    """
    Return an ndarray of ellipse coordinates. If no `q_points` value is
    provided, the ceil of the larger value of a, b will be used

    Args:
        a:
        b:
        q_points: number of points in a quarter section (default None)
        ccw: counter clockwise winding order (default False)
    """
    q_points = q_points or int(np.ceil(max(a, b)))
    if a < b:
        fa, fb = b, a
        xy = (1, 0)
    else:
        fa, fb = a, b
        xy = (0, 1)
    r = np.zeros((q_points * 4, 2))
    af = np.linspace(0, fa, q_points, endpoint=False)
    ab = np.linspace(fa, 0, q_points, endpoint=False)
    r[:, xy[0]] = np.concatenate((af, ab, af, ab))
    r[:, xy[1]] = np.sqrt(fb ** 2 * (1 - (np.power(r[:, xy[0]], 2) / fa ** 2)))
    r[2 * q_points:, xy[0]] *= -1
    r[q_points:3 * q_points, xy[1]] *= -1
    # r[:] = r[:, xy]
    return r[::-1] if ccw else r


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
                    (lower_edges[id1],)
                )
            )
            if l_edge:
                triangles.append(
                    (
                        (upper_edges[id2],),
                        (lower_edges[id2], lower_edges[id1])
                    )
                )
                continue

        if l_edge:
            triangles.append(
                (
                    (upper_edges[id1],),
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
    def __init__(self, name='noname', no_texcoord=False, tangents=True):
        self._name = name
        self._no_texcoord = no_texcoord
        self._tangents = tangents
        if no_texcoord and not tangents:
            self._vdata = core.GeomVertexData(
                self._name,
                core.GeomVertexFormat.get_v3n3c4(),
                core.Geom.UH_static
            )
        elif tangents:
            va_format = core.GeomVertexArrayFormat()
            va_format.add_column(
                'vertex',
                3,
                core.Geom.NT_float32,
                core.Geom.C_point
            )
            va_format.add_column(
                'normal', 3, core.Geom.NT_float32, core.Geom.C_vector
            )
            va_format.add_column(
                'tangent', 3, core.Geom.NT_float32, core.Geom.C_vector
            )
            va_format.add_column(
                'binormal', 3, core.Geom.NT_float32, core.Geom.C_vector
            )
            va_format.add_column(
                'color', 4, core.Geom.NT_float32, core.Geom.C_color
            )
            if not no_texcoord:
                va_format.add_column(
                    'texcoord', 2, core.Geom.NT_float32, core.Geom.C_texcoord
                )
            # noinspection PyCallByClass
            va_format = core.GeomVertexFormat.register_format(va_format)
            self._vdata = core.GeomVertexData(
                self._name,
                va_format,
                core.Geom.UH_static
            )
        else:
            self._vdata = core.GeomVertexData(
                self._name,
                core.GeomVertexFormat.get_v3n3c4t2(),
                core.Geom.UH_static
            )

        self._vwriter = core.GeomVertexWriter(self._vdata, 'vertex')
        self._nwriter = core.GeomVertexWriter(self._vdata, 'normal')
        if tangents:
            self._tawriter = core.GeomVertexWriter(self._vdata, 'tangent')
            self._biwriter = core.GeomVertexWriter(self._vdata, 'binormal')
        self._cwriter = core.GeomVertexWriter(self._vdata, 'color')
        if not no_texcoord:
            self._twriter = core.GeomVertexWriter(self._vdata, 'texcoord')
        else:
            self._twriter = None
        self._prim = core.GeomTriangles(core.Geom.UH_static)

        self._v_id = 0
        self.set_num_rows = self._vdata.set_num_rows

    def add_row(
            self,
            point,
            normal,
            color,
            tex=None,
            tangent=None,
            bitangent=None
    ):
        self._vwriter.add_data3(point)
        self._nwriter.add_data3(normal)
        if self._tangents:
            if tangent is None:
                raise ValueError('tangent and bitangent not provided')
            self._tawriter.add_data3(tangent)
            self._biwriter.add_data3(bitangent)
        self._cwriter.add_data4(color)
        if not self._no_texcoord:
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


UL = 0
UR = 1
DL = 2
DR = 3


class AABB(object):
    def __init__(self, origin, bb):
        # type: (core.Vec2, core.Vec2) -> None
        self.origin = origin
        self.bb = bb

    def intersect(self, other):
        # type: (Union[core.Vec2, core.Point2, AABB]) -> bool
        if isinstance(other, (core.Vec2, core.Point2)):
            d = other - self.origin
            return abs(d.x) <= self.bb.x and abs(d.y) <= self.bb.y
        if isinstance(other, AABB):
            d = other.origin.x - self.origin.x
            p = (other.bb.x + self.bb.x) - abs(d)
            if p <= 0:
                return False
            d = other.origin.y - self.origin.y
            p = (other.bb.y + self.bb.y) - abs(d)
            if p <= 0:
                return False
            return True
        raise TypeError(f'expected either Vec2/Point2 or AABB got '
                        f'"{type(other).__name__}" instead')

    def get_child_id(self, point):
        d = point - self.origin
        if d.x <= 0:
            if d.y <= 0:
                return DL
            return UL
        if d.y <= 0:
            return DR
        return UR

    def get_child_aabb(self):
        hbb = self.bb / 2
        return [
            AABB(self.origin + core.Vec2(-hbb.x, hbb.y), hbb),
            AABB(self.origin + core.Vec2(hbb.x, hbb.y), hbb),
            AABB(self.origin + core.Vec2(-hbb.x, -hbb.y), hbb),
            AABB(self.origin + core.Vec2(hbb.x, -hbb.y), hbb)
        ]

    def __repr__(self):
        return f'{repr(self.origin)}, {repr(self.bb)}'

    def __str__(self):
        return repr(self)


class QuadNode(object):
    def __init__(self, aabb, depth, max_leaf_nodes):
        self.aabb = aabb
        self.children = {i: None for i in range(4)}
        self.leafs = []
        self.depth = depth
        self.max_leaf_nodes = max_leaf_nodes

    def insert_leaf(self, quad_element):
        """Return True on success, otherwise the node has to be split."""
        if len(self.leafs) < self.max_leaf_nodes or self.depth == 0:
            self.leafs.append(QuadTree.insert_node(quad_element))
            return True
        return False

    @property
    def is_leaf_node(self):
        return self.children[0] is None


class QuadElement(object):
    def __init__(self, point, data, aabb=None):
        self.point = point
        self.data = data
        self.aabb = aabb or AABB(point, core.Vec2(0))


class QuadTree(object):
    def __init__(self, origin, bounds, max_depth=8, max_leaf_nodes=4):
        self.aabb = AABB(origin, bounds)
        self.max_depth = max_depth
        self.max_leaf_nodes = max_leaf_nodes
        self.root = QuadTree.insert_node(
            QuadNode(self.aabb, max_depth, max_leaf_nodes)
        )

    def insert(self, point, data):
        if not self.aabb.intersect(point):
            raise ValueError('point is outside the bounding box')
        if not isinstance(point, AABB):
            aabb = AABB(point, core.Vec2(0))
        else:
            aabb = point
        qe = QuadElement(point, data, aabb)
        chk_nodes = [self.root]
        while chk_nodes:
            chk_node = QuadTree.nodes[chk_nodes.pop()]
            if chk_node.aabb.intersect(aabb):
                if chk_node.insert_leaf(qe):
                    continue
                for i, aabb in enumerate(chk_node.aabb.get_child_aabb()):
                    chk_node.children[i] = QuadTree.insert_node(
                        QuadNode(
                            aabb,
                            chk_node.depth - 1,
                            self.max_leaf_nodes
                        )
                    )
                for i in chk_node.leafs:
                    n = QuadTree.nodes[i]
                    child_id = chk_node.aabb.get_child_id(n.point)
                    QuadTree.nodes[chk_node.children[child_id]].leafs.append(i)
                chk_node.leafs = []
                chk_nodes += [nid for nid in chk_node.children.values()]
                # QuadTree.nodes[
                #     chk_node.children[chk_node.aabb.get_child_id(point)]
                # ]

    def query(self, aabb):
        if not self.aabb.intersect(aabb):
            raise ValueError('aabb does not intersect with the QuadTree aabb')
        results = []
        chk_nodes = [self.root]
        while chk_nodes:
            chk_node = QuadTree.nodes[chk_nodes.pop()]
            if chk_node.is_leaf_node:
                for n in chk_node.leafs:
                    el = QuadTree.nodes[n]
                    if aabb.intersect_point(el.point):
                        results.append(el.data)
            else:
                chk_nodes += [nid for nid in chk_node.children.values()]
        return results

    def remove(self, point, data):  # TODO: fix to remove all instances
        chk_node = self._find_leaf_node(point)
        for i in chk_node.leafs:
            el = QuadTree.nodes[i]
            if el.point == point and el.data == data:
                QuadTree.remove_node(i)
                return True
        raise RuntimeError('node could be removed. not found')

    def move(self, from_point, to_point, data):
        self.remove(from_point, data)
        self.insert(to_point, data)

    def _find_leaf_node(self, point):
        if not self.aabb.intersect(point):
            raise ValueError('point is outside the bounding box')
        chk_node = QuadTree.get_node(self.root)
        while True:
            if chk_node.is_leaf_node:
                return chk_node
            else:
                chk_node = QuadTree.get_node(
                    chk_node.children[chk_node.aabb.get_child_id(point)]
                )

    # class attrs and methods

    nodes = {}
    node_id = 0
    free_list = []

    @classmethod
    def insert_node(cls, node):
        nid = cls.free_list.pop() if cls.free_list else cls.node_id
        cls.nodes[nid] = node
        if nid == cls.node_id:
            cls.node_id += 1
        return nid

    @classmethod
    def get_node(cls, node_id):
        return cls.nodes[node_id]

    @classmethod
    def remove_node(cls, node_id):
        cls.free_list.append(node_id)
        cls.nodes[node_id] = None
