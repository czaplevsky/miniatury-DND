"""Step 8: drop specks, validate and export STL + 3MF. usage: finalize.py IN.stl OUT_PREFIX"""
import sys, os, zipfile, trimesh, numpy as np


def write_3mf(mesh, path, dec=6):
    """compact 3MF (units mm, coordinates rounded to 0.1 um): trimesh's writer gives ~39 MB for 1.9 M tris."""
    v = mesh.vertices; f = mesh.faces
    vs = '\n'.join(f'<vertex x="{a:.{dec}f}" y="{b:.{dec}f}" z="{c:.{dec}f}"/>' for a, b, c in v)
    ts = '\n'.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in f)
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n<metadata name="Title">druid_mini_v3</metadata>\n'
             '<resources><object id="1" type="model"><mesh><vertices>\n' + vs + '\n</vertices><triangles>\n' + ts +
             '\n</triangles></mesh></object></resources>\n<build><item objectid="1"/></build>\n</model>\n')
    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr('[Content_Types].xml', ct); z.writestr('_rels/.rels', rels); z.writestr('3D/3dmodel.model', model)
if __name__ == '__main__':
    m = trimesh.load(sys.argv[1])
    parts = m.split(only_watertight=False)
    main = max(parts, key=lambda p: len(p.faces))
    print('dropped', len(parts) - 1, 'specks', [len(p.faces) for p in parts if p is not main][:5])
    main.merge_vertices()
    r = np.hypot(main.vertices[:, 0], main.vertices[:, 1])
    body = main.vertices[:, 2] > 3.2
    print('watertight', main.is_watertight, 'winding', main.is_winding_consistent, 'volume', round(main.volume, 1), 'mm3')
    print('bounds', np.round(main.bounds, 2).tolist())
    print('max radius above base %.2f (base r 12.5)' % r[body].max())
    print('soles->top %.2f mm' % (main.vertices[:, 2].max() - 3.0))
    main.export(sys.argv[2] + '.stl')
    write_3mf(main, sys.argv[2] + '.3mf')
    for e in ('.stl', '.3mf'):
        print(e, round(os.path.getsize(sys.argv[2] + e) / 1e6, 1), 'MB')
