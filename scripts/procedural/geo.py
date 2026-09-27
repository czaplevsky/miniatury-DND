"""Geometry helpers for building the miniature procedurally in Blender (bpy).

All builders work at real-world scale in metres; the figure is scaled to print
size (mm) at the end.
"""
import math
import random

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector, noise

PARTS = {}


def mesh_obj(name, verts, faces, group="detail"):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    PARTS.setdefault(group, []).append(ob)
    return ob


def bm_obj(name, bm, group="detail"):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    PARTS.setdefault(group, []).append(ob)
    return ob


def frames(pts, ref=Vector((0, -1, 0))):
    n = len(pts)
    T = []
    for i in range(n):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        T.append((b - a).normalized())
    r = ref.copy()
    if abs(r.dot(T[0])) > 0.95:
        r = Vector((1, 0, 0)) if abs(T[0].x) < 0.9 else Vector((0, 1, 0))
    cur = (r - r.dot(T[0]) * T[0]).normalized()
    N = []
    for i in range(n):
        cur = (cur - cur.dot(T[i]) * T[i]).normalized()
        N.append(cur.copy())
    B = [T[i].cross(N[i]) for i in range(n)]
    return T, N, B


def tube(name, pts, radii, seg=16, group="detail", ref=Vector((0, -1, 0)), disp=None, caps=True):
    """Sweep an (elliptical) cross-section along a polyline.

    radii: per-point float or (r_along_ref, r_side).
    disp(i, angle, point) -> radius multiplier (bark, gnarls).
    """
    pts = [Vector(p) for p in pts]
    T, N, B = frames(pts, ref)
    verts, faces = [], []
    for i, p in enumerate(pts):
        r = radii[i]
        rx, ry = (r, r) if not isinstance(r, (tuple, list)) else r
        for j in range(seg):
            a = 2 * math.pi * j / seg
            m = disp(i, a, p) if disp else 1.0
            verts.append(p + N[i] * math.cos(a) * rx * m + B[i] * math.sin(a) * ry * m)
    n = len(pts)
    for i in range(n - 1):
        for j in range(seg):
            j2 = (j + 1) % seg
            faces.append((i * seg + j, i * seg + j2, (i + 1) * seg + j2, (i + 1) * seg + j))
    if caps:
        c0 = len(verts)
        verts.append(pts[0])
        c1 = len(verts)
        verts.append(pts[-1])
        for j in range(seg):
            j2 = (j + 1) % seg
            faces.append((c0, j2, j))
            faces.append((c1, (n - 1) * seg + j, (n - 1) * seg + j2))
    return mesh_obj(name, verts, faces, group)


def smooth_path(ctrl, n):
    """Catmull-Rom through control points, n samples."""
    ctrl = [Vector(c) for c in ctrl]
    pts = []
    segs = len(ctrl) - 1
    for k in range(n):
        u = k / (n - 1) * segs
        i = min(int(u), segs - 1)
        t = u - i
        p0 = ctrl[max(i - 1, 0)]
        p1 = ctrl[i]
        p2 = ctrl[i + 1]
        p3 = ctrl[min(i + 2, segs)]
        t2, t3 = t * t, t * t * t
        pts.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return pts


def ellipsoid(name, c, r, rot=(0, 0, 0), seg=24, rings=14, group="detail"):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    M = Matrix.Translation(Vector(c)) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((r[0], r[1], r[2], 1))
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return bm_obj(name, bm, group)


def rbox(name, c, size, rot=(0, 0, 0), bevel=0.3, group="detail", rotm=None):
    """Rounded box. size = full extents; bevel = fraction of smallest half-extent."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    off = min(size) * 0.5 * bevel
    if off > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=off, segments=3, affect="EDGES", profile=0.5)
    R = rotm if rotm is not None else Euler(rot).to_matrix()
    M = Matrix.Translation(Vector(c)) @ R.to_4x4()
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return bm_obj(name, bm, group)


def ribbon(name, pts, normals, width, thick, group="detail", inset=0.4, taper=0.78):
    """Flat strap swept along pts lying on a surface (normals = outward)."""
    n = len(pts)
    if n < 2:
        return None
    verts, faces = [], []
    for i in range(n):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        nn = normals[i]
        w = t.cross(nn)
        if w.length < 1e-6:
            w = nn.orthogonal()
        w.normalize()
        base = pts[i] - nn * thick * inset
        top = pts[i] + nn * thick * (1 - inset)
        hw = width / 2
        verts += [base - w * hw, base + w * hw, top + w * hw * taper, top - w * hw * taper]
    for i in range(n - 1):
        for k in range(4):
            k2 = (k + 1) % 4
            faces.append((4 * i + k, 4 * i + k2, 4 * (i + 1) + k2, 4 * (i + 1) + k))
    faces.append((3, 2, 1, 0))
    faces.append(tuple(4 * (n - 1) + k for k in range(4)))
    return mesh_obj(name, verts, faces, group)


def axis_frame(A, B):
    D = B - A
    L = D.length
    D = D.normalized()
    U = Vector((0, -1, 0))
    if abs(U.dot(D)) > 0.9:
        U = Vector((1, 0, 0))
    U = (U - U.dot(D) * D).normalized()
    V = D.cross(U)
    return D, L, U, V


def wrap(name, A, B, rfun, width=0.034, thick=0.011, pitch=1.0, turns=None, phase=0.0, hand=1,
         t0=0.0, t1=1.0, skip=None, jit=0.25, spt=30, group="detail"):
    """Bandage wound helically around an axis A->B.

    rfun(t) -> (r_front, r_side): surface radii at axis parameter t.
    skip(point, phi) -> True to leave a gap (e.g. eye slit).
    """
    A, B = Vector(A), Vector(B)
    D, L, U, V = axis_frame(A, B)
    if turns is None:
        turns = L * (t1 - t0) / (width * pitch)
    n = int(max(10, turns * spt))
    runs, cur = [], ([], [])
    seed = random.random() * 100
    for i in range(n + 1):
        s = i / n
        t = t0 + (t1 - t0) * s
        phi = phase + hand * 2 * math.pi * turns * s
        ru, rv = rfun(t)
        # per-turn lift so neighbouring turns read as separate layers
        lift = 1.0 + jit * thick / max(ru, 1e-4) * (0.5 + 0.5 * noise.noise(Vector((seed, phi * 0.35, 0.0))))
        c = A + D * (L * t)
        p = c + (U * math.cos(phi) * ru + V * math.sin(phi) * rv) * lift
        nv = (U * math.cos(phi) * rv + V * math.sin(phi) * ru).normalized()
        if skip and skip(p, phi):
            if len(cur[0]) > 2:
                runs.append(cur)
            cur = ([], [])
            continue
        cur[0].append(p)
        cur[1].append(nv)
    if len(cur[0]) > 2:
        runs.append(cur)
    obs = []
    for k, (pp, nn) in enumerate(runs):
        obs.append(ribbon(f"{name}_{k}", pp, nn, width, thick, group=group))
    return obs


def cone_r(ra, rb):
    return lambda t: (ra + (rb - ra) * t, ra + (rb - ra) * t)


def grid_surface(name, cols, rows, fn, group="detail", thick=0.04, offset=1.0):
    """Build a solid sheet from fn(u, v) -> point with thickness along a normal fn."""
    verts = []
    for j in range(rows + 1):
        for i in range(cols + 1):
            verts.append(fn(i / cols, j / rows))
    faces = []
    W = cols + 1
    for j in range(rows):
        for i in range(cols):
            faces.append((j * W + i, j * W + i + 1, (j + 1) * W + i + 1, (j + 1) * W + i))
    ob = mesh_obj(name, verts, faces, group)
    mod = ob.modifiers.new("solid", "SOLIDIFY")
    mod.thickness = thick
    mod.offset = offset
    mod.use_even_offset = True
    mod.use_rim = True
    bake_modifiers(ob)
    return ob


def bake_modifiers(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    bpy.data.meshes.remove(old)
    return ob


def join(objs, name):
    objs = [o for o in objs if o is not None]
    bm = bmesh.new()
    for o in objs:
        me = o.data.copy()
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    for o in objs:
        m = o.data
        bpy.data.objects.remove(o)
        if m.users == 0:
            bpy.data.meshes.remove(m)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def voxel_remesh(ob, size, smooth_iters=0, smooth_factor=0.5):
    mod = ob.modifiers.new("vox", "REMESH")
    mod.mode = "VOXEL"
    mod.voxel_size = size
    mod.adaptivity = 0.0
    mod.use_smooth_shade = True
    if smooth_iters:
        sm = ob.modifiers.new("sm", "SMOOTH")
        sm.factor = smooth_factor
        sm.iterations = smooth_iters
    return bake_modifiers(ob)
