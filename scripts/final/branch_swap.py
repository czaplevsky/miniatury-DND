"""Remove the AI-generated staff and export the cleaned, watertight body (mm)."""
import os, sys, math
import bpy
from mathutils import Vector
sys.path.insert(0, os.path.abspath('mini'))
from geo import PARTS, tube, smooth_path, join, voxel_remesh, bake_modifiers

src, dst = sys.argv[1], sys.argv[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.stl_import(filepath=src)
body = bpy.context.selected_objects[0]
import bmesh
bm = bmesh.new(); bm.from_mesh(body.data)
bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
print('boundary left', sum(1 for e in bm.edges if e.is_boundary)); bm.to_mesh(body.data); bm.free()
print('in', len(body.data.vertices)); voxel_remesh(body, 0.05); print('vox', len(body.data.vertices))

# AI staff axis (mm), measured by ray casting the front depth map
AX = [(10.3, -6.0, 34.4), (9.6, -6.0, 33.6), (8.5, -5.9, 32.3), (7.2, -6.0, 30.5), (6.2, -5.95, 28.8), (5.5, -5.3, 27.2),
      (5.2, -5.6, 25.8), (3.5, -5.8, 24.6), (1.5, -5.9, 23.6), (-0.5, -5.2, 22.8), (-2.5, -4.6, 22.1), (-4.5, -4.0, 21.5),
      (-6.0, -4.3, 21.0), (-7.3, -3.1, 20.0), (-8.6, -2.3, 18.6), (-9.8, -1.3, 17.2), (-10.8, -0.6, 16.0), (-11.5, -0.2, 15.2)]
AX = [Vector(p) for p in AX]
HANDS = [(Vector((5.3, -5.5, 25.9)), 1.25), (Vector((-6.0, -4.3, 21.0)), 1.35)]


def near_hand(p):
    return any((p - c).length < r for c, r in HANDS)


path = smooth_path(AX, 120)
run = []
k = 0
for p in path + [None]:
    if p is None or near_hand(p):
        if len(run) > 2:
            d0 = (run[1] - run[0]).normalized(); d1 = (run[-1] - run[-2]).normalized()
            pts = run
            if (run[0] - AX[0]).length < 0.5:
                pts = [run[0] - d0 * 1.5] + pts
            if (run[-1] - AX[-1]).length < 0.5:
                pts = pts + [run[-1] + d1 * 1.5]
            tube(f'cut{k}', pts, [(2.0, 1.45, 2.4)[min(k, 2)]] * len(pts), seg=20, group='cut'); k += 1
        run = []
    else:
        run.append(p)
cutter = join(PARTS.pop('cut'), 'cutter')
m = body.modifiers.new('b', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = cutter; m.solver = 'MANIFOLD' if hasattr(bpy.types.BooleanModifier, 'solver') else 'EXACT'
try:
    bake_modifiers(body)
except Exception as e:
    print('manifold failed, exact', e); m.solver = 'EXACT'; bake_modifiers(body)
print('bool', len(body.data.vertices)); bpy.data.objects.remove(cutter)
voxel_remesh(body, 0.035)
import bmesh
bm = bmesh.new(); bm.from_mesh(body.data)
islands = []
seen = set()
for v in bm.verts:
    if v.index in seen: continue
    stack = [v]; comp = []
    seen.add(v.index)
    while stack:
        x = stack.pop(); comp.append(x)
        for e in x.link_edges:
            o = e.other_vert(x)
            if o.index not in seen:
                seen.add(o.index); stack.append(o)
    islands.append(comp)
islands.sort(key=len, reverse=True)
print('islands', [len(i) for i in islands[:5]])
bmesh.ops.delete(bm, geom=[v for comp in islands[1:] for v in comp], context='VERTS')
bm.to_mesh(body.data); bm.free()
print('verts', len(body.data.vertices))
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); bpy.context.view_layer.objects.active = body
bpy.ops.wm.stl_export(filepath=dst, export_selected_objects=True)
