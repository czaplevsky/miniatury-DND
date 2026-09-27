import sys, trimesh, numpy as np
m = trimesh.load(sys.argv[1], force='mesh')
m.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [1,0,0]))  # Y-up -> Z-up
b = m.bounds; h = b[1][2]-b[0][2]
m.apply_translation([-(b[0][0]+b[1][0])/2, -(b[0][1]+b[1][1])/2, -b[0][2]])
m.apply_scale(44.0/h)
print(sys.argv[1], len(m.faces), 'watertight', m.is_watertight, 'extent', np.round(m.extents,1))
m.export(sys.argv[2])
