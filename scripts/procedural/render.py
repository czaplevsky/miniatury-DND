"""Render clay previews of the miniature STL: front, side, back, 3/4.

Usage: python render.py model.stl out_dir [res]
"""
import math
import os
import sys

import bpy
from mathutils import Vector

stl, out = sys.argv[1], sys.argv[2]
res = int(sys.argv[3]) if len(sys.argv) > 3 else 900
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.stl_import(filepath=stl)
ob = bpy.context.selected_objects[0]
for p in ob.data.polygons:
    p.use_smooth = True

mat = bpy.data.materials.new("clay")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.62, 0.60, 0.57, 1)
bsdf.inputs["Roughness"].default_value = 0.55
ob.data.materials.append(mat)

sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 48
sc.cycles.use_denoising = True
sc.render.resolution_x = int(res * 0.75)
sc.render.resolution_y = res
sc.world = bpy.data.worlds.new("w")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.16, 0.17, 0.19, 1)
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.6


def light(name, kind, loc, energy, size=20):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    if kind == "AREA":
        ld.size = size
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    lo.rotation_euler = (Vector((0, 0, 22)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(lo)
    return lo


cam_d = bpy.data.cameras.new("cam")
cam_d.type = "ORTHO"
cam_d.ortho_scale = float(sys.argv[4]) if len(sys.argv) > 4 else 50
cam = bpy.data.objects.new("cam", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
center = Vector((0, 0, float(sys.argv[5]) if len(sys.argv) > 5 else 22))
views = {"front": -90, "front34": -55, "side": 180, "back": 90, "side_l": 0}
for name, az in views.items():
    a = math.radians(az)
    d = Vector((math.cos(a), math.sin(a), 0.12)).normalized()
    cam.location = center + d * 120
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    for o in [o for o in sc.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o)
    key = Vector((math.cos(a - 0.7), math.sin(a - 0.7), 0.9)) * 100 + center
    fill = Vector((math.cos(a + 1.0), math.sin(a + 1.0), 0.2)) * 100 + center
    rim = Vector((math.cos(a + math.pi), math.sin(a + math.pi), 0.6)) * 100 + center
    light("key", "AREA", key, 60000, 40)
    light("fill", "AREA", fill, 15000, 60)
    light("rim", "AREA", rim, 30000, 30)
    sc.render.filepath = os.path.join(out, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", name)
