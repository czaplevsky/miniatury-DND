"""Body + plain broken bough + 25 mm base -> one watertight print mesh (mm)."""
import os, sys, math, random
import bpy
from mathutils import Vector, noise
sys.path.insert(0, os.path.abspath('mini'))
from geo import PARTS, tube, smooth_path, ellipsoid, join, voxel_remesh, bake_modifiers

body_src, out = sys.argv[1], sys.argv[2]
VOX = float(sys.argv[3]) if len(sys.argv) > 3 else 0.035
random.seed(11)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.stl_import(filepath=body_src)
body = bpy.context.selected_objects[0]

# --- plain bough through both hands (axis measured from the AI staff) ---
AX = [(10.3, -6.0, 34.4), (8.5, -5.95, 32.3), (6.4, -5.9, 28.9), (5.3, -5.6, 25.9), (3.5, -5.8, 24.6), (1.5, -5.8, 23.6),
      (-0.5, -5.3, 22.8), (-2.5, -4.7, 22.1), (-4.5, -4.2, 21.5), (-6.0, -4.1, 21.0), (-7.3, -3.2, 20.0), (-8.6, -2.3, 18.6),
      (-9.8, -1.4, 17.2), (-10.9, -0.7, 15.9)]
path = smooth_path(AX, 160)
HANDS = [Vector((5.3, -5.5, 25.9)), Vector((-6.0, -4.3, 21.0))]
n = len(path)


def radius(i):
    t = i / (n - 1)
    r = 1.12 + 0.12 * t + 0.05 * math.sin(t * 17)          # a touch thicker toward the lower end
    for h in HANDS:
        d = (path[i] - h).length
        if d < 1.6:
            r -= 0.12 * (1 - d / 1.6)                          # slimmer inside the grips
    return r


def bark(i, a, p):
    ridge = abs(math.sin(a * 5 + i * 0.03 + 1.5 * noise.noise(p * 0.6)))      # long bark furrows
    return 1.0 + 0.09 * noise.noise(Vector((math.cos(a) * 1.3, math.sin(a) * 1.3, i * 0.08))) + 0.07 * (ridge - 0.5)


tube('bough', path, [radius(i) for i in range(n)], seg=40, disp=bark)
# broken ends: ragged rim of short, flattened wood slivers leaning along the bough (no tubes sticking out)
for end, nxt, rr in ((path[0], path[4], radius(0)), (path[-1], path[-5], radius(n - 1))):
    d = (end - nxt).normalized()
    u = d.orthogonal().normalized(); w = d.cross(u)
    for k in range(9):
        a = k * 2 * math.pi / 9 + random.uniform(-0.25, 0.25)
        radial = u * math.cos(a) + w * math.sin(a)
        L = random.uniform(0.2, 0.55)
        c = end + radial * rr * 0.72 + d * (L * 0.35 - 0.15)
        tube(f'sliver{k}', [c - d * 0.5, c + d * L], [(0.28, 0.16), (0.12, 0.08)], seg=8, ref=radial)
    ellipsoid('endcap', end - d * 0.1, (rr * 0.9, rr * 0.9, rr * 0.9), seg=16, rings=10)
# one short snapped side stub (as on the reference photo)
base = path[int(n * 0.14)]
d = Vector((-0.35, 0.1, 1)).normalized()
tube('stub', [base, base + d * 0.9, base + d * 1.6 + Vector((0.2, 0, 0))], [0.5, 0.42, 0.36], seg=12)
tube('stubfork', [base + d * 1.3, base + d * 1.3 + Vector((0.45, 0, 0.5))], [0.3, 0.26], seg=8)
# a knot bulge
k = path[int(n * 0.62)]
ellipsoid('knot', k + Vector((0, -0.9, 0.2)), (0.7, 0.55, 0.8))

# --- base 25 x 3 mm with a little ground detail ---
bz = [0.0, 0.4, 2.3, 2.75, 3.0, 3.08]
brs = [12.35, 12.5, 12.4, 12.15, 11.8, 0.1]
tube('base', [(0, 0, z) for z in bz], brs, seg=96)
random.seed(99)
for i in range(9):
    a = random.uniform(0, 2 * math.pi); r = random.uniform(7.5, 10.8)
    c = Vector((r * math.cos(a), r * math.sin(a), 3.0))
    ellipsoid(f'stone{i}', c, (random.uniform(0.7, 1.5), random.uniform(0.6, 1.2), random.uniform(0.35, 0.65)), rot=(0, 0, a), seg=12, rings=8)
for i in range(45):
    a = random.uniform(0, 2 * math.pi); r = math.sqrt(random.uniform(0.02, 1)) * 11
    ellipsoid(f'moss{i}', (r * math.cos(a), r * math.sin(a), 3.0), (0.5, 0.5, 0.2), seg=8, rings=6)

model = join([body] + sum(PARTS.values(), []), 'druid')
PARTS.clear()
voxel_remesh(model, VOX, smooth_iters=1, smooth_factor=0.4)
for v in model.data.vertices:
    if v.co.z < 0: v.co.z = 0.0
TARGET = int(os.environ.get('TARGET_TRIS', '1200000'))
tris = sum(len(p.vertices) - 2 for p in model.data.polygons)
if tris > TARGET:
    dm = model.modifiers.new('dec', 'DECIMATE'); dm.ratio = TARGET / tris; dm.use_collapse_triangulate = True
    bake_modifiers(model)
print('tris', sum(len(p.vertices) - 2 for p in model.data.polygons))
bpy.ops.object.select_all(action='DESELECT'); model.select_set(True); bpy.context.view_layer.objects.active = model
bpy.ops.wm.stl_export(filepath=out, export_selected_objects=True)
