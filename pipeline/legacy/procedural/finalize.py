import sys, trimesh
src, dst = sys.argv[1], sys.argv[2]
m = trimesh.load(src)
parts = m.split(only_watertight=False)
main = max(parts, key=lambda p: len(p.faces))
print("dropped", len(parts) - 1, "specks; watertight", main.is_watertight)
main.export(dst + ".stl")
main.export(dst + ".3mf")
