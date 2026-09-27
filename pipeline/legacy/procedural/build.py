"""Builds the bandaged druid miniature (D&D, 32 mm heroic, 25 mm base).

Usage: python build.py [voxel_mm] [out_dir]
Real-scale modelling in metres (character 1.90 m, heroic proportions),
then scaled so sole->top of head = 36 mm, placed on a 25 x 3 mm base.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Euler, Matrix, Vector, noise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import (PARTS, bake_modifiers, cone_r, ellipsoid, join, mesh_obj, rbox,  # noqa: E402
                 ribbon, smooth_path, tube, voxel_remesh, wrap)

VOXEL_MM = float(sys.argv[1]) if len(sys.argv) > 1 else 0.05
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

random.seed(1907)
bpy.ops.wm.read_factory_settings(use_empty=True)

HEAD_TOP_MM = 36.0
BASE_R, BASE_H = 12.5, 3.0

# ---------------------------------------------------------------- torso
# z, half-width (x), half-depth (y), y offset
TORSO = [
    (0.84, 0.125, 0.095, 0.0),
    (0.91, 0.165, 0.113, 0.005),
    (0.98, 0.172, 0.118, 0.006),
    (1.06, 0.158, 0.106, 0.0),
    (1.14, 0.160, 0.106, -0.005),
    (1.24, 0.180, 0.116, -0.010),
    (1.34, 0.200, 0.125, -0.012),
    (1.43, 0.212, 0.127, -0.010),
    (1.50, 0.205, 0.120, 0.0),
    (1.56, 0.150, 0.100, 0.0),
    (1.61, 0.070, 0.065, 0.0),
]


def torso_r(z):
    if z <= TORSO[0][0]:
        return TORSO[0][1:]
    for a, b in zip(TORSO, TORSO[1:]):
        if a[0] <= z <= b[0]:
            t = (z - a[0]) / (b[0] - a[0])
            return tuple(a[k] + (b[k] - a[k]) * t for k in (1, 2, 3))
    return TORSO[-1][1:]


def torso_pt(z, phi, add=0.0):
    """Point on torso surface; phi measured in XY, front (-Y) = -90deg."""
    rx, ry, yo = torso_r(z)
    p = Vector(((rx + add) * math.cos(phi), yo + (ry + add) * math.sin(phi), z))
    n = Vector((math.cos(phi) / rx, math.sin(phi) / ry, 0)).normalized()
    return p, n


def torso_loop(name, zf, add, width, thick, phis):
    pts, nrm = [], []
    for phi in phis:
        p, n = torso_pt(zf(phi), phi, add)
        pts.append(p)
        nrm.append(n)
    return ribbon(name, pts, nrm, width, thick)


def arange(a, b, n):
    return [a + (b - a) * i / (n - 1) for i in range(n)]


# ================================================================= BODY (smoothed)
tube("torso", [(0, t[3], t[0]) for t in TORSO], [(t[2], t[1]) for t in TORSO], seg=32, group="body")
tube("neck", [(0, 0.0, 1.55), (0, -0.005, 1.70)], [0.058, 0.055], seg=20, group="body")

LEG = {}
for s in (-1, 1):
    hip = Vector((s * 0.095, 0.0, 0.95))
    knee = Vector((s * 0.125, -0.012, 0.52))
    ankle = Vector((s * 0.145, 0.0, 0.10))
    LEG[s] = (hip, knee, ankle)
    tube(f"thigh{s}", smooth_path([hip, (s * 0.112, -0.006, 0.73), knee], 8), [0.100, 0.097, 0.092, 0.086, 0.079, 0.072, 0.066, 0.062], group="body")
    tube(f"shin{s}", smooth_path([knee, (s * 0.136, 0.012, 0.33), ankle], 8), [0.062, 0.063, 0.062, 0.058, 0.053, 0.049, 0.045, 0.043], group="body")
    ellipsoid(f"knee{s}", knee, (0.064, 0.064, 0.066), group="body")
    ellipsoid(f"ankle{s}", ankle, (0.046, 0.046, 0.05), group="body")
    ellipsoid(f"hipj{s}", hip, (0.10, 0.10, 0.10), group="body")

ARM = {
    -1: [Vector((-0.235, 0.0, 1.47)), Vector((-0.315, 0.0, 1.225)), Vector((-0.372, -0.092, 1.075))],
    1: [Vector((0.235, 0.0, 1.47)), Vector((0.305, 0.0, 1.225)), Vector((0.332, -0.04, 1.00))],
}
for s, (sh, el, wr) in ARM.items():
    ellipsoid(f"shoulder{s}", sh, (0.082, 0.082, 0.082), group="body")
    tube(f"uarm{s}", [sh, sh.lerp(el, 0.5), el], [0.066, 0.061, 0.053], group="body")
    ellipsoid(f"elbow{s}", el, (0.054, 0.054, 0.054), group="body")
    tube(f"farm{s}", [el, el.lerp(wr, 0.5), wr], [0.053, 0.049, 0.040], group="body")

body = join(PARTS.pop("body"), "body")
voxel_remesh(body, 0.007, smooth_iters=10, smooth_factor=0.6)
DETAIL = [body]

# ================================================================= HEAD
HC = Vector((0.0, -0.008, 1.785))
HR = (0.092, 0.110, 0.128)  # x, y(depth), z
head = ellipsoid("head", HC, HR, seg=40, rings=28, group="head")
# jaw / chin volume and nose bridge (under bandage)
ellipsoid("jaw", HC + Vector((0, -0.035, -0.07)), (0.07, 0.07, 0.06), group="headx")
ellipsoid("nose", HC + Vector((0, -HR[1] * 0.96, -0.012)), (0.017, 0.022, 0.034), group="headx")
ellipsoid("brow", HC + Vector((0, -HR[1] * 0.8, 0.024)), (0.072, 0.03, 0.02), group="headx")
EYE_Z = HC.z + 0.004
eye_cut = []
for s in (-1, 1):
    eye_cut.append(ellipsoid(f"socket{s}", (s * 0.036, HC.y - HR[1] * 0.96, EYE_Z), (0.024, 0.020, 0.015), group="cut"))
PARTS.pop("head")
head = join([head] + PARTS.pop("headx"), "headfull")
head = voxel_remesh(head, 0.004, smooth_iters=4, smooth_factor=0.5)
cutter = join(PARTS.pop("cut"), "eyecut")
bm = head.modifiers.new("b", "BOOLEAN")
bm.operation = "DIFFERENCE"
bm.object = cutter
bm.solver = "EXACT"
bake_modifiers(head)
bpy.data.objects.remove(cutter)
DETAIL.append(head)
for s in (-1, 1):
    ellipsoid(f"eye{s}", (s * 0.036, HC.y - HR[1] * 0.83, EYE_Z), (0.013, 0.010, 0.0095))
    # heavy upper lid / glare
    ellipsoid(f"lid{s}", (s * 0.036, HC.y - HR[1] * 0.86, EYE_Z + 0.009), (0.019, 0.008, 0.005), rot=(0, 0, 0))


def head_r(t):
    h = (t - 0.5) * 2 * 0.108
    k = math.sqrt(max(0.0, 1 - (h / HR[2]) ** 2))
    # bandage sits on head; slightly fuller at the jaw
    return (HR[1] * k + 0.002, HR[0] * k + 0.002)


def eye_skip(p, phi):
    front = math.cos(phi) > 0.35  # U axis = -Y = face
    return front and abs(p.z - EYE_Z) < 0.017


wrap("headwrap", HC - Vector((0, 0, 0.108)), HC + Vector((0, 0, 0.108)), head_r, width=0.030, thick=0.010,
     pitch=0.95, hand=1, skip=eye_skip, jit=0.6)
# second, crossing layer over mouth/jaw and forehead
wrap("jawwrap", HC - Vector((0, 0, 0.108)), HC + Vector((0, 0, 0.108)), lambda t: tuple(r + 0.008 for r in head_r(t)),
     width=0.028, thick=0.009, turns=1.2, t0=0.02, t1=0.30, phase=0.6, hand=-1, jit=0.3)
wrap("browwrap", HC - Vector((0, 0, 0.108)), HC + Vector((0, 0, 0.108)), lambda t: tuple(r + 0.008 for r in head_r(t)),
     width=0.028, thick=0.009, turns=1.1, t0=0.66, t1=0.95, phase=2.0, hand=-1, jit=0.3)
# crown straps over the top
for k in range(4):
    ang = k * math.pi / 4
    pts, nrm = [], []
    for a in arange(-1.2, 1.2, 40):
        d = Vector((math.sin(a) * math.cos(ang), math.sin(a) * math.sin(ang), math.cos(a)))
        p = HC + Vector((d.x * HR[0], d.y * HR[1], d.z * HR[2])) * 1.02
        n = Vector((d.x / HR[0], d.y / HR[1], d.z / HR[2])).normalized()
        pts.append(p)
        nrm.append(n)
    ribbon(f"crown{k}", pts, nrm, 0.036, 0.010)
wrap("chinwrap", HC + Vector((0, -0.028, -0.135)), HC + Vector((0, -0.012, -0.06)),
     lambda t: (0.062 + 0.036 * t, 0.060 + 0.024 * t), width=0.028, thick=0.010, hand=-1, jit=0.5)
wrap("neckwrap", (0, 0.0, 1.56), (0, -0.005, 1.69), cone_r(0.06, 0.057), width=0.03, thick=0.010, hand=-1)

# ================================================================= TORSO ARMOUR
# leather cuirass shell (chest) with layered lower plates
cuir_z = arange(1.23, 1.53, 12)
tube("cuirass", [(0, torso_r(z)[2] - 0.004, z) for z in cuir_z],
     [(torso_r(z)[1] + 0.022, torso_r(z)[0] + 0.020) for z in cuir_z], seg=40)
for zz in (1.255, 1.31, 1.365):
    torso_loop(f"plate{zz}", lambda phi, zz=zz: zz, 0.026, 0.05, 0.016, arange(math.radians(-170), math.radians(-10), 40))
    torso_loop(f"plateb{zz}", lambda phi, zz=zz: zz, 0.026, 0.05, 0.016, arange(math.radians(10), math.radians(170), 40))
# collar plates / upper chest yoke
torso_loop("yoke", lambda phi: 1.47 + 0.03 * math.sin(phi) ** 2, 0.028, 0.045, 0.018, arange(-math.pi, math.pi, 64))
# crossed leather straps (X across chest)
for k, ph0 in enumerate((0.0, math.pi)):
    torso_loop(f"strap{k}", lambda phi, ph0=ph0: 1.24 + 0.2 * math.cos(phi - ph0), 0.040, 0.042, 0.016,
               arange(-math.pi, math.pi, 90))
    # strap buckle on the front
    p, n = torso_pt(1.24 + 0.2 * math.cos(-math.pi / 2 - ph0 + (0.35 if k else -0.35)), -math.pi / 2 + (0.35 if k else -0.35), 0.058)
    xax = Vector((0, 0, 1)).cross(n).normalized()
    rbox(f"sbuckle{k}", p, (0.034, 0.012, 0.03), rotm=Matrix((xax, n, Vector((0, 0, 1)))).transposed(), bevel=0.3)
# lacing down the chest seam
for i, z in enumerate(arange(1.30, 1.50, 7)):
    p, n = torso_pt(z, -math.pi / 2, 0.026)
    for sgn in (-1, 1):
        a = p + Vector((sgn * 0.018, 0, 0))
        b = p + Vector((-sgn * 0.018, 0, 0.022))
        tube(f"lace{i}{sgn}", [a, b], [0.0065, 0.0065], seg=8)
# vines crawling over the cuirass
for k in range(7):
    phi0 = random.uniform(-math.pi, math.pi)
    z0 = random.uniform(1.25, 1.35)
    z1 = random.uniform(1.44, 1.52)
    pts = []
    for z in arange(z0, z1, 26):
        phi = phi0 + 0.25 * math.sin(z * 30 + k) + (z - z0) * random.uniform(-0.8, 0.8) * 0
        pts.append(torso_pt(z, phi, 0.030)[0])
    tube(f"vine{k}", pts, [0.0085] * len(pts), seg=8)
    for b in range(2):  # little tendrils
        i = random.randint(4, len(pts) - 6)
        p = pts[i]
        n = torso_pt(p.z, math.atan2(p.y, p.x), 0)[1]
        side = n.cross(Vector((0, 0, 1))).normalized() * random.choice((-1, 1))
        tube(f"tendril{k}{b}", smooth_path([p, p + side * 0.025 + Vector((0, 0, 0.012)), p + side * 0.04 - Vector((0, 0, 0.005))], 8),
             [0.007] * 7 + [0.005], seg=6)

# abdomen bandages (between cuirass and belt)
wrap("bellywrap", (0, 0, 1.03), (0, 0, 1.25),
     lambda t: (torso_r(1.03 + 0.22 * t)[1] + 0.004, torso_r(1.03 + 0.22 * t)[0] + 0.004), width=0.036, thick=0.012,
     pitch=0.95, hand=1, jit=0.8)

# belts
torso_loop("belt", lambda phi: 1.035, 0.012, 0.058, 0.022, arange(-math.pi, math.pi, 80))
torso_loop("belt2", lambda phi: 0.965 + 0.035 * math.cos(phi + 0.3), 0.020, 0.040, 0.018, arange(-math.pi, math.pi, 80))
bp, bn = torso_pt(1.035, -math.pi / 2, 0.034)
for d, sz in (((0, 0, 0.022), (0.064, 0.014, 0.012)), ((0, 0, -0.022), (0.064, 0.014, 0.012)),
              ((0.027, 0, 0), (0.012, 0.014, 0.05)), ((-0.027, 0, 0), (0.012, 0.014, 0.05))):
    rbox("buckle", bp + Vector(d), sz, bevel=0.4)
tube("prong", [bp + Vector((-0.02, -0.004, 0)), bp + Vector((0.012, -0.006, 0))], [0.005, 0.005], seg=8)


def pouch(name, phi, z, w, d, h):
    p, n = torso_pt(z, phi, 0.018 + d / 2)
    x = Vector((0, 0, 1)).cross(n).normalized()
    R = Matrix((x, n, Vector((0, 0, 1)))).transposed()
    rbox(name, p, (w, d, h), rotm=R, bevel=0.45)
    rbox(name + "flap", p + n * (d / 2 + 0.002) + Vector((0, 0, h * 0.2)), (w * 1.05, 0.012, h * 0.62), rotm=R, bevel=0.5)
    ellipsoid(name + "stud", p + n * (d / 2 + 0.01) + Vector((0, 0, -0.005)), (0.009, 0.007, 0.009))


pouch("pouchR", math.radians(-140), 0.93, 0.075, 0.05, 0.09)
pouch("pouchRB", math.radians(150), 0.92, 0.07, 0.048, 0.085)
pouch("pouchL", math.radians(-38), 0.935, 0.06, 0.04, 0.07)

# tabard (front and back hanging leather/cloth) with tattered hem


def hanging_panel(name, yfront, x0, x1, ztop, zbot, curve, sign, cols=24, rows=26, thick=0.02):
    teeth = [random.uniform(0, 0.07) for _ in range(cols + 1)]

    def fn(u, v):
        x = x0 + (x1 - x0) * u
        zb = zbot - teeth[int(round(u * cols))] * (1 if int(round(u * cols)) % 3 else 0.3)
        z = ztop + (zb - ztop) * v
        y = yfront + sign * curve * ((x - (x0 + x1) / 2) / ((x1 - x0) / 2)) ** 2 + sign * -0.03 * v
        y += 0.006 * math.sin(u * 17 + v * 3)
        return Vector((x, y, z))
    from geo import grid_surface
    return grid_surface(name, cols, rows, fn, thick=thick, offset=0.0)


hanging_panel("tabardF", -0.128, -0.11, 0.11, 1.00, 0.56, 0.035, -1)
hanging_panel("tabardB", 0.135, -0.12, 0.12, 1.00, 0.62, 0.035, 1)
# hip tassets
for s in (-1, 1):
    ellipsoid(f"tasset{s}", (s * 0.175, -0.02, 0.88), (0.05, 0.09, 0.085), rot=(0, s * 0.35, 0))

# ================================================================= SHOULDERS: pauldrons
for s in (-1, 1):
    for k, (c, r, a) in enumerate((((0.245, 0.0, 1.535), (0.11, 0.128, 0.072), 0.35),
                                   ((0.278, 0.0, 1.465), (0.098, 0.116, 0.058), 0.6),
                                   ((0.302, 0.004, 1.40), (0.083, 0.10, 0.048), 0.85))):
        ellipsoid(f"pauld{s}{k}", (s * c[0], c[1], c[2]), r, rot=(0, s * a, 0))
    # vine across pauldron
    pts = [Vector((s * (0.20 + 0.1 * i / 11), 0.03 * math.sin(i * 0.9), 1.60 - 0.12 * i / 11 - 0.02 * (i / 11) ** 2)) for i in range(12)]
    tube(f"pvine{s}", pts, [0.0085] * 12, seg=8)

# ================================================================= ARMS: bandages, bracers, hands
for s, (sh, el, wr) in ARM.items():
    wrap(f"uwrap{s}", sh, el, cone_r(0.066, 0.053), t0=0.35, t1=1.0, hand=s, jit=0.7)
    wrap(f"ewrap{s}", el, wr, cone_r(0.053, 0.040), t0=0.0, t1=0.2, hand=-s, jit=0.7, phase=1.0)
    # leather bracer with straps and vines
    bra = [el.lerp(wr, t) for t in arange(0.22, 0.88, 6)]
    tube(f"bracer{s}", bra, [0.053 + (0.041 - 0.053) * t + 0.016 for t in arange(0.22, 0.88, 6)], seg=24)
    for t in (0.34, 0.72):
        wrap(f"bstrap{s}{t}", el, wr, lambda tt: (0.053 + (0.040 - 0.053) * tt + 0.03,) * 2, turns=1.05, t0=t - 0.02, t1=t + 0.02,
             width=0.02, thick=0.012, spt=40)
    D = (wr - el).normalized()
    Uv = Vector((0, -1, 0))
    Uv = (Uv - Uv.dot(D) * D).normalized()
    Vv = D.cross(Uv)
    vp = []
    for t in arange(0.22, 0.95, 30):
        ang = t * 7.5 + s
        r = 0.053 + (0.041 - 0.053) * t + 0.024
        vp.append(el.lerp(wr, t) + (Uv * math.cos(ang) + Vv * math.sin(ang)) * r)
    tube(f"bvine{s}", vp, [0.0085] * len(vp), seg=8)
    wrap(f"wwrap{s}", el, wr, cone_r(0.053, 0.040), t0=0.88, t1=1.0, hand=s, jit=0.6)

# branch (heavy broken bough used as a club / staff) ----------------------
TR = [(-0.405, -0.140, -0.02), (-0.385, -0.150, 0.30), (-0.425, -0.118, 0.66), (-0.408, -0.130, 1.05),
      (-0.440, -0.112, 1.40), (-0.405, -0.145, 1.74), (-0.440, -0.125, 2.03)]
trunk = smooth_path(TR, 90)


def trunk_r(i):
    t = i / (len(trunk) - 1)
    return 0.060 + 0.030 * t ** 1.4 + 0.008 * math.sin(t * 19) + 0.006 * math.sin(t * 41)


def bark(i, a, p):
    return 1.0 + 0.13 * noise.noise(Vector((math.cos(a) * 1.6, math.sin(a) * 1.6, p.z * 12))) + 0.05 * math.sin(a * 9 + p.z * 9 + 2 * noise.noise(p * 8))


tube("trunk", trunk, [trunk_r(i) for i in range(len(trunk))], seg=28, disp=bark)
TOP = Vector(TR[-1])


def branch(name, start, d, length, r0, r1, bend=0.25, npts=12, twig=True):
    d = d.normalized()
    side = d.orthogonal().normalized()
    ctrl = [start]
    for k in range(1, 5):
        f = k / 4
        wob = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.3, 0.3))) * 0.025
        ctrl.append(start + d * length * f + side * bend * length * f * f + wob)
    pts = smooth_path(ctrl, npts)
    tube(name, pts, [r0 + (r1 - r0) * (i / (npts - 1)) for i in range(npts)], seg=14,
         disp=lambda i, a, p: 1 + 0.08 * noise.noise(Vector((math.cos(a), math.sin(a), p.z * 20 + p.x * 20))))
    ellipsoid(name + "tip", pts[-1], (r1, r1, r1), seg=10, rings=6)
    if twig:
        i = int(npts * random.uniform(0.45, 0.65))
        td = (pts[i + 1] - pts[i]).normalized() + side * random.choice((-1, 1)) * 0.9 + Vector((0, 0, 0.4))
        branch(name + "t", pts[i], td, length * 0.38, r0 * 0.55, max(r1 * 0.9, 0.0145), bend=0.2, npts=7, twig=False)
    return pts


ellipsoid("crownknot", TOP + Vector((0, 0, -0.02)), (0.11, 0.1, 0.12))
branch("b1", TOP + Vector((-0.03, 0, 0.05)), Vector((-0.6, 0.1, 1)), 0.34, 0.055, 0.021)
branch("b2", TOP + Vector((0.03, 0, 0.05)), Vector((0.5, -0.15, 1)), 0.28, 0.05, 0.02)
branch("b3", TOP + Vector((0, 0.04, 0.03)), Vector((0.05, 0.7, 0.8)), 0.24, 0.045, 0.019)
branch("b4", TOP + Vector((0, -0.04, 0.03)), Vector((-0.15, -0.7, 0.75)), 0.26, 0.045, 0.019)
branch("b5", TOP + Vector((-0.04, 0.03, -0.05)), Vector((-0.45, 0.55, 0.9)), 0.17, 0.042, 0.019)
# broken, splintered stub
tube("stub", [TOP + Vector((0, 0, 0.03)), TOP + Vector((0.01, 0, 0.14))], [0.06, 0.055], seg=14)
for k in range(6):
    a = k * math.pi / 3
    base = TOP + Vector((0.01 + 0.04 * math.cos(a), 0.04 * math.sin(a), 0.13))
    tube(f"splinter{k}", [base, base + Vector((0.004 * math.cos(a), 0.004 * math.sin(a), random.uniform(0.025, 0.05)))], [0.013, 0.006], seg=6)
# side twigs and knots along the trunk
for z, d in ((0.52, Vector((-1, 0.2, 0.9))), (1.52, Vector((-0.8, -0.6, 1))), (1.66, Vector((0.9, 0.3, 1.1)))):
    i = min(range(len(trunk)), key=lambda k: abs(trunk[k].z - z))
    branch(f"side{z}", trunk[i], d, 0.09, 0.024, 0.0145, bend=0.1, npts=6, twig=False)
for z in (0.28, 0.9, 1.25, 1.6):
    i = min(range(len(trunk)), key=lambda k: abs(trunk[k].z - z))
    a = random.uniform(0, 2 * math.pi)
    ellipsoid(f"knot{z}", trunk[i] + Vector((math.cos(a), math.sin(a), 0)) * 0.06, (0.038, 0.038, 0.05))


def trunk_surface(z, ang, extra=0.0):
    i = min(range(len(trunk)), key=lambda k: abs(trunk[k].z - z))
    d = Vector((math.cos(ang), math.sin(ang), 0))
    return trunk[i] + d * (trunk_r(i) + extra), d


# carved eyes: raised ring + pupil
for k, (z, ang) in enumerate(((1.34, math.radians(-120)), (1.60, math.radians(-150)), (1.88, math.radians(-95)), (0.62, math.radians(-110)))):
    c, d = trunk_surface(z, ang, 0.004)
    u = d.cross(Vector((0, 0, 1))).normalized()
    ring = [c + (u * math.cos(t) * 1.3 + Vector((0, 0, math.sin(t)))) * 0.021 for t in arange(0, 2 * math.pi, 25)]
    tube(f"eyering{k}", ring, [0.0065] * len(ring), seg=8, caps=True)
    ellipsoid(f"pupil{k}", c + d * 0.003, (0.011, 0.011, 0.011))
# shelf mushrooms
for k, (z, ang, sc) in enumerate(((1.28, math.radians(170), 1.0), (1.315, math.radians(-165), 0.75), (0.70, math.radians(-80), 0.85),
                                   (1.74, math.radians(95), 0.9), (1.93, math.radians(-160), 0.7), (0.74, math.radians(-50), 0.6))):
    c, d = trunk_surface(z, ang, 0.012 * sc)
    ellipsoid(f"shroom{k}", c, (0.046 * sc, 0.046 * sc, 0.016 + 0.002 * sc), rot=(0, 0, ang), seg=18, rings=10)
    ellipsoid(f"shroomgill{k}", c - Vector((0, 0, 0.008)), (0.036 * sc, 0.036 * sc, 0.012), rot=(0, 0, ang), seg=14, rings=8)

# right hand gripping the branch
HP = Vector((-0.408, -0.130, 1.05))
ellipsoid("palmR", HP + Vector((0.05, 0.025, 0.0)), (0.044, 0.05, 0.062), rot=(0, 0, 0.6))
br = 0.075
for k, dz in enumerate((-0.045, -0.016, 0.013, 0.041)):
    arc = []
    for a in arange(math.radians(70), math.radians(290), 14):
        arc.append(HP + Vector((math.cos(a) * (br + 0.012), math.sin(a) * (br + 0.012), dz + 0.004 * math.cos(a))))
    tube(f"fingerR{k}", arc, [0.0155] * len(arc), seg=10)
tube("thumbR", smooth_path([HP + Vector((0.05, -0.02, 0.03)), HP + Vector((0.02, -0.06, 0.06)), HP + Vector((-0.02, -0.066, 0.065))], 8),
     [0.018] * 8, seg=10)
wrap("handwrapR", ARM[-1][2], HP + Vector((0.02, 0.0, -0.03)), cone_r(0.043, 0.048), hand=1, width=0.028, jit=0.5)

# left fist
LP = Vector((0.336, -0.052, 0.935))
ellipsoid("fistL", LP, (0.042, 0.052, 0.062), rot=(0.15, 0, 0))
for k, dz in enumerate((-0.036, -0.012, 0.012, 0.036)):
    ellipsoid(f"knuckL{k}", LP + Vector((-0.012, -0.045, dz - 0.02)), (0.017, 0.02, 0.013))
ellipsoid("thumbL", LP + Vector((-0.038, -0.028, 0.02)), (0.016, 0.03, 0.016), rot=(0.4, 0, 0.3))
wrap("handwrapL", ARM[1][2], LP + Vector((0, 0, -0.02)), cone_r(0.041, 0.05), hand=-1, width=0.028, jit=0.5)

# ================================================================= LEGS
for s, (hip, knee, ankle) in LEG.items():
    wrap(f"thighwrap{s}", hip + Vector((0, 0, -0.04)), knee, cone_r(0.098, 0.064), hand=s, t0=0.05, jit=0.8)
    wrap(f"thighcross{s}", hip + Vector((0, 0, -0.04)), knee, lambda t: (0.098 + (0.064 - 0.098) * t + 0.01,) * 2,
         turns=1.6, t0=0.25, t1=0.85, hand=-s, phase=s, width=0.032, jit=0.3)
    wrap(f"shinwrap{s}", knee, ankle, cone_r(0.062, 0.044), t0=0.05, t1=0.42, hand=-s, jit=0.8)
    # knee cop
    ellipsoid(f"kneecop{s}", knee + Vector((0, -0.045, 0.0)), (0.062, 0.035, 0.074), rot=(0.15, 0, 0))
    ellipsoid(f"kneecop2{s}", knee + Vector((0, -0.05, -0.055)), (0.05, 0.028, 0.04), rot=(0.2, 0, 0))
    # greave / boot shaft with straps and vines
    shaft = [knee.lerp(ankle, t) for t in arange(0.42, 1.02, 7)]
    tube(f"greave{s}", shaft, [0.062 + (0.044 - 0.062) * t + 0.014 for t in arange(0.42, 1.02, 7)], seg=24)
    for t in (0.55, 0.78, 0.95):
        wrap(f"gstrap{s}{t}", knee, ankle, lambda tt: (0.062 + (0.044 - 0.062) * tt + 0.021,) * 2, turns=1.05,
             t0=t - 0.02, t1=t + 0.02, width=0.019, thick=0.012, spt=40)
    vp = []
    for t in arange(0.45, 0.98, 26):
        ang = t * 9 + s * 2
        r = 0.062 + (0.044 - 0.062) * t + 0.022
        c = knee.lerp(ankle, t)
        vp.append(c + Vector((math.sin(ang) * r, -math.cos(ang) * r, 0)))
    tube(f"gvine{s}", vp, [0.0085] * len(vp), seg=8)
    # wrapped soft boot
    foot_c = Vector((s * 0.152, -0.055, 0.042))
    ellipsoid(f"foot{s}", foot_c, (0.058, 0.135, 0.056), rot=(0, 0, s * 0.12), seg=28, rings=16)
    ellipsoid(f"heel{s}", Vector((s * 0.147, 0.03, 0.05)), (0.05, 0.05, 0.055))
    ellipsoid(f"sole{s}", foot_c + Vector((0, -0.005, -0.03)), (0.062, 0.142, 0.022), rot=(0, 0, s * 0.12))
    fr = (0.058, 0.056)
    wrap(f"footwrap{s}", foot_c + Vector((s * 0.01, 0.07, 0.01)), foot_c + Vector((-s * 0.012, -0.10, 0.0)),
         lambda t: (0.057 * (1 - 0.35 * t * t) + 0.002, 0.061 * (1 - 0.3 * t * t) + 0.002), t0=0.05, t1=0.85, hand=s, jit=0.5)

# ================================================================= FUR MANTLE
FC = Vector((0.0, 0.02, 1.42))
FR = (0.32, 0.24, 0.245)


def fur_mask(p):
    if p.z < 1.43 and not (p.y > 0.04 and p.z > 1.24):
        return False
    if p.y < 0.0 and abs(p.x) < 0.16 and p.z < 1.62:
        return False
    if p.y < 0.03 and abs(p.x) < 0.105 and p.z > 1.5:
        return False
    return True


def dome(u, v):
    th = u * 2 * math.pi
    ph = v * math.radians(115)
    d = Vector((math.sin(ph) * math.cos(th), math.sin(ph) * math.sin(th), math.cos(ph)))
    p = FC + Vector((d.x * FR[0], d.y * FR[1], d.z * FR[2]))
    n = Vector((d.x / FR[0], d.y / FR[1], d.z / FR[2])).normalized()
    return p, n


# solid mantle shell under the fur clumps
cols, rows = 96, 40
verts, keep = [], []
for j in range(rows + 1):
    for i in range(cols + 1):
        p, n = dome(i / cols, j / rows)
        verts.append(p)
        keep.append(fur_mask(p))
faces = []
W = cols + 1
for j in range(rows):
    for i in range(cols):
        q = (j * W + i, j * W + i + 1, (j + 1) * W + i + 1, (j + 1) * W + i)
        if all(keep[x] for x in q):
            faces.append(q)
mant = mesh_obj("mantle", verts, faces)
m = mant.modifiers.new("s", "SOLIDIFY")
m.thickness = 0.05
m.offset = -1
m.use_rim = True
bake_modifiers(mant)
# fur clumps
n_ok = 0
tries = 0
while n_ok < 2300 and tries < 90000:
    tries += 1
    g = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))).normalized()
    ph = math.acos(max(-1, min(1, g.z)))
    if ph > math.radians(115):
        continue
    p, n = dome((math.atan2(g.y, g.x) / (2 * math.pi)) % 1.0, ph / math.radians(115))
    if not fur_mask(p):
        continue
    n_ok += 1
    down = Vector((0, 0, -1))
    tdown = down - down.dot(n) * n
    radial = Vector((p.x - FC.x, p.y - FC.y, 0))
    if tdown.length < 0.35:
        tdown = tdown + radial.normalized() * (0.35 - tdown.length) * 2
    jitter = Vector((random.uniform(-.35, .35), random.uniform(-.35, .35), random.uniform(-.2, .1)))
    d = (tdown.normalized() + n * 0.5 + jitter).normalized()
    L = random.uniform(0.055, 0.10)
    mid = p + d * L * 0.5 + n * (0.018 + 0.01 * random.random())
    tube(f"fur{n_ok}", [p - n * 0.015, mid, p + d * L + n * 0.004], [0.025, 0.02, 0.0105], seg=8)
# collar ring around the neck
coll = []
for a in arange(math.radians(-60), math.radians(240), 50):  # leaves the throat open
    ang = a - math.pi / 2 + math.pi  # start at front-right, go round the back
    coll.append(Vector((0.15 * math.cos(ang), 0.012 + 0.125 * math.sin(ang), 1.60 + 0.03 * math.sin(ang))))
tube("collar", coll, [0.045] * len(coll), seg=14)
for k in range(140):
    i = random.randrange(len(coll))
    c = coll[i]
    out = Vector((c.x, c.y - 0.012, 0)).normalized()
    d = (out * 0.85 + Vector((random.uniform(-.25, .25), random.uniform(-.25, .25), random.uniform(-0.7, 0.15)))).normalized()
    L = random.uniform(0.035, 0.06)
    tube(f"cfur{k}", [c, c + d * (0.045 + L * 0.5), c + d * (0.045 + L)], [0.026, 0.02, 0.01], seg=7)

# ================================================================= CLOAK
CT, CB = 1.50, 0.30
tat = {}


def cloak_fn(u, v):
    th = math.radians(-84 + 168 * u)
    col = int(round(u * 120))
    if col not in tat:
        g = col // 5
        random.seed(g * 7919)
        depth = random.uniform(0.0, 0.11)
        random.seed(col * 31)
        tat[col] = depth * (1 - abs((col % 5) - 2) / 2.5) + random.uniform(0, 0.02)
    zb = CB - tat[col] + 0.07 * (abs(th) / math.radians(84)) ** 2
    z = CT + (zb - CT) * v
    s = (CT - z) / (CT - CB)
    rx = 0.29 + 0.15 * s
    ry = 0.17 + 0.14 * s
    fold = (0.012 + 0.05 * s) * math.sin(th * 7 + 0.7 + 0.4 * s) + 0.018 * s * math.sin(th * 13 + 1.3) + 0.01 * math.sin(th * 23) * s
    return Vector((math.sin(th) * (rx + fold), 0.055 + math.cos(th) * (ry + fold), z))


from geo import grid_surface  # noqa: E402
grid_surface("cloak", 120, 70, cloak_fn, thick=0.045, offset=1.0)
random.seed(4242)

# ================================================================= ASSEMBLE, SCALE
fig = join(DETAIL + sum(PARTS.values(), []), "figure")
PARTS.clear()
zmax = max(v.co.z for v in fig.data.vertices if abs(v.co.x) < 0.2)  # head (branch sits at x=-0.4)
S = HEAD_TOP_MM / zmax
fig.data.transform(Matrix.Translation((0, 0, BASE_H)) @ Matrix.Scale(S, 4))
print("scale mm/m:", round(S, 3), "head top real m:", round(zmax, 3))

# ================================================================= BASE (mm)
bz = [0.0, 0.4, 2.3, 2.75, 3.0, 3.05]
brs = [12.35, 12.5, 12.4, 12.15, 11.8, 0.1]
tube("base", [(0, 0, z) for z in bz], brs, seg=96, group="base")
bx = PARTS["base"]
# ground: small stones, roots from the bough, moss tufts
random.seed(99)
for k in range(9):
    a = random.uniform(0, 2 * math.pi)
    r = random.uniform(6.5, 10.5)
    c = (r * math.cos(a), r * math.sin(a), 3.0)
    if abs(c[0] + 7.6) < 2.5 and abs(c[1] + 2.6) < 2.5:
        continue
    ellipsoid(f"stone{k}", c, (random.uniform(0.7, 1.6), random.uniform(0.6, 1.3), random.uniform(0.35, 0.7)),
              rot=(0, 0, a), group="base", seg=12, rings=8)
bb = Vector((-0.400 * S, -0.140 * S, 3.0))
for k, a in enumerate((2.2, 3.4, 4.3, 0.9)):
    d = Vector((math.cos(a), math.sin(a), 0))
    L = random.uniform(2.2, 3.2)
    pts = smooth_path([bb + Vector((0, 0, 1.2)), bb + d * L * 0.45 + Vector((0, 0, 0.45)), bb + d * L + Vector((0, 0, 0.05))], 10)
    tube(f"root{k}", pts, [0.55 - 0.035 * i for i in range(10)], seg=10, group="base")
for k in range(40):
    a = random.uniform(0, 2 * math.pi)
    r = math.sqrt(random.uniform(0.02, 1)) * 11
    ellipsoid(f"moss{k}", (r * math.cos(a), r * math.sin(a), 3.0), (0.5, 0.5, 0.22), group="base", seg=8, rings=6)

model = join([fig] + PARTS.pop("base"), "druid_mini")
print("joined verts", len(model.data.vertices))
voxel_remesh(model, VOXEL_MM, smooth_iters=2, smooth_factor=0.5)
# keep everything on the plate: flatten anything below z=0
for v in model.data.vertices:
    if v.co.z < 0:
        v.co.z = 0.0
print("remeshed verts", len(model.data.vertices), "faces", len(model.data.polygons))
TARGET_TRIS = int(os.environ.get("TARGET_TRIS", "1400000"))
tris = sum(len(p.vertices) - 2 for p in model.data.polygons)
if tris > TARGET_TRIS:
    dm = model.modifiers.new("dec", "DECIMATE")
    dm.ratio = TARGET_TRIS / tris
    dm.use_collapse_triangulate = True
    bake_modifiers(model)
print("final tris", sum(len(p.vertices) - 2 for p in model.data.polygons))

bpy.ops.object.select_all(action="DESELECT")
model.select_set(True)
bpy.context.view_layer.objects.active = model
bpy.ops.wm.stl_export(filepath=os.path.join(OUT, "druid_mini_raw.stl"), export_selected_objects=True, apply_modifiers=True)
print("done")
