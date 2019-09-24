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
    def __init__(self, name='noname', no_texcoord=False):
        self._name = name
        self._no_texcoord = no_texcoord
        if no_texcoord:
            self._vdata = core.GeomVertexData(
                self._name,
                core.GeomVertexFormat.get_v3n3c4(),
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
        self._cwriter = core.GeomVertexWriter(self._vdata, 'color')
        if not no_texcoord:
            self._twriter = core.GeomVertexWriter(self._vdata, 'texcoord')
        else:
            self._twriter = None
        self._prim = core.GeomTriangles(core.Geom.UH_static)

        self._v_id = 0
        self.set_num_rows = self._vdata.set_num_rows

    def add_row(self, point, normal, color, tex=None):
        self._vwriter.add_data3(point)
        self._nwriter.add_data3(normal)
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

    def intersect_point(self, point):
        d = core.Vec2(*map(abs, point - self.origin))
        return d.x <= self.bb.x and d.y <= self.bb.y

    def intersect_aabb(self, aabb):
        d = aabb.origin.x - self.origin.x
        p = (aabb.bb.x + self.bb.x) - abs(d)
        if p <= 0:
            return False
        d = aabb.origin.y - self.origin.y
        p = (aabb.bb.y + self.bb.y) - abs(d)
        if p <= 0:
            return False
        return True

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


class QuadNode(object):
    def __init__(self, aabb, depth, max_leaf_nodes):
        self.aabb = aabb
        self.children = {i: None for i in range(4)}
        self.leafs = []
        self.depth = depth
        self.max_leaf_nodes = max_leaf_nodes

    def insert_leaf(self, point, data):
        """Return True on success, otherwise the node has to be split."""
        if len(self.leafs) > self.max_leaf_nodes or not self.depth:
            self.leafs.append(QuadTree.insert_node(QuadElement(point, data)))
            return True
        return False

    @property
    def is_leaf_node(self):
        return self.children[0] is None


class QuadElement(object):
    def __init__(self, point, data):
        self.point = point
        self.data = data


class QuadTree(object):
    def __init__(self, origin, bounds, max_depth=8, max_leaf_nodes=4):
        self.aabb = AABB(origin, bounds)
        self.max_depth = max_depth
        self.max_leaf_nodes = max_leaf_nodes
        self.root = QuadTree.insert_node(
            QuadNode(self.aabb, max_depth, max_leaf_nodes)
        )

    def insert(self, point, data):
        if not self.aabb.intersect_point(point):
            raise ValueError('point is outside the bounding box')
        chk_node = QuadTree.get_node(self.root)
        while True:
            if chk_node.insert_leaf(point, data):
                return
            for i, aabb in enumerate(chk_node.aabb.get_child_aabb()):
                chk_node.children[i] = QuadTree.insert_node(
                    QuadNode(
                        aabb,
                        chk_node.depth - 1,
                        self.max_leaf_nodes
                    )
                )
            for i in chk_node.leafs:
                n = QuadTree.get_node(i)
                child_id = chk_node.aabb.get_child_id(n.point)
                QuadTree.get_node(chk_node.children[child_id]).leafs.append(i)
            chk_node.leafs = []
            chk_node = QuadTree.get_node(
                chk_node.children[chk_node.aabb.get_child_id(point)]
            )

    def query(self, aabb):
        if not self.aabb.intersect_aabb(aabb):
            raise ValueError('aabb does not intersect with the QuadTree aabb')
        results = []
        chk_nodes = [self.root]
        while chk_nodes:
            chk_node = QuadTree.get_node(chk_nodes.pop())
            if chk_node.is_leaf_node:
                for n in chk_node.leafs:
                    el = QuadTree.get_node(n)
                    if aabb.intersect_point(el.point):
                        results.append(el.data)
            else:
                chk_nodes += [nid for nid in chk_node.children.values()]
        return results

    def remove(self, point, data):
        chk_node = self._find_leaf_node(point)
        for i in chk_node.leafs:
            el = QuadTree.get_node(i)
            if el.point == point and el.data == data:
                QuadTree.remove_node(i)
                return True
        raise RuntimeError('node could be removed. not found')

    def move(self, from_point, to_point, data):
        self.remove(from_point, data)
        self.insert(to_point, data)

    def _find_leaf_node(self, point):
        if not self.aabb.intersect_point(point):
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