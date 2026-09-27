"""Step 6+8: sculpt printable detail onto the AI body and build the final print mesh (Blender bpy + numpy).

usage: python detail.py BODY.stl OUT_PREFIX            (BODY: mm, Z up, front -Y, soles z=3, head z=39)
env:   VOX=0.03 (detail remesh), FVOX=0.028 (final union remesh), TARGET_TRIS=1900000,
       GROOVE=0.18 (V-groove depth, mm), RAISE=0.12 (head wrap thickness), NOBASE=1 (skip base)

What it does
 1. voxel remesh the AI mesh (VOX) so that 0.1-0.2 mm features can be carried;
 2. registers the front concept (img/front_s7_rgba.png) to the mesh by bounding box (checked with regview.py)
    and ray-casts a front depth map -> which vertices are visible in the image;
 3. displacement along vertex normals, all from maps/front_maps.npz (maps.py):
    - relief: high-passed height integrated from Marigold normals, masked (strong on bandage zones and bark, weak elsewhere)
    - V-grooves 0.18 mm deep along bandage seams detected in the image (front-visible parts)
    - procedural wraps (helical V-grooves + shingle step) on the parts of bandaged limbs the front image cannot see
    - head: raised crossing wrap strips (RAISE) with grooves, eye slit left un-wrapped
    - branch: long bark furrows on the sides/back
 4. body sunk 0.15 mm into a 25 x 3 mm round base (soles at z=3 visually), union by voxel remesh, decimate, export STL/3MF.
"""
import os, sys, math, json, time
import numpy as np
import bpy, bmesh
import trimesh
from scipy.ndimage import map_coordinates

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from reg import Reg
from PIL import Image

src, outp = sys.argv[1], sys.argv[2]
VOX = float(os.environ.get('VOX', '0.03'))
FVOX = float(os.environ.get('FVOX', '0.03'))
TARGET = int(os.environ.get('TARGET_TRIS', '1900000'))
GDEP = float(os.environ.get('GROOVE', '0.18'))
RAISE = float(os.environ.get('RAISE', '0.12'))
T0 = time.time()


def log(*a):
    print(f'[{time.time() - T0:6.0f}s]', *a, flush=True)


# ---------------------------------------------------------------- registration on the original AI mesh
orig = trimesh.load(src)
alpha = np.asarray(Image.open(os.path.join(HERE, 'img/front_s7_rgba.png')))[..., 3] > 128
R = Reg(orig, alpha)
M = np.load(os.path.join(HERE, 'maps/front_maps.npz'))
relief, groove, band, zones, branch = M['relief'], M['groove'], M['band'], M['zones'], M['branch'].astype(np.float32)
BRL = M['branch_line']
yfront = R.yfront.copy()
yf_filled = np.where(np.isnan(yfront), 1e3, yfront)
log('registered sx %.2f sz %.2f' % (R.sx, R.sz))

# ---------------------------------------------------------------- remesh in Blender
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.stl_import(filepath=src)
ob = bpy.context.selected_objects[0]
bpy.context.view_layer.objects.active = ob
ob.data.remesh_voxel_size = VOX
ob.data.use_remesh_fix_poles = False
bpy.ops.object.voxel_remesh()
me = ob.data
nv = len(me.vertices)
V = np.empty(nv * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
Nrm = np.empty(nv * 3); me.vertex_normals.foreach_get('vector', Nrm); Nrm = Nrm.reshape(-1, 3)
log('remeshed', nv, 'verts')


def read_mesh():
    V = np.empty(nv * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    Nrm = np.empty(nv * 3); me.vertex_normals.foreach_get('vector', Nrm)
    return V, Nrm.reshape(-1, 3)


# --- head: find it and smooth away the AI face (nose/lips) so it reads as a wrapped mummy head
EYE_Z = R.world(0, 170)[1]                           # eye row in the front image
CHIN_Z = R.world(0, 242)[1]
hu, hw = R.pix(V[:, 0], V[:, 2])
zl0 = map_coordinates(zones.astype(np.float32), [hw - 0.5, hu - 0.5], order=0, mode='nearest').astype(int)
yf0 = map_coordinates(yf_filled.astype(np.float32), [hw - 0.5, hu - 0.5], order=0, mode='nearest')
# eye line: deepest point of the AI face between brow and cheek, measured on the mesh (image estimate is ~0.6 mm off)
_hx = R.world(415, 0)[0]
_zs = np.arange(EYE_Z - 1.2, EYE_Z + 0.4, 0.05)
_ys = []
for _xo in (_hx - 0.5, _hx, _hx + 0.5):
    _o = np.stack([np.full(len(_zs), _xo), np.full(len(_zs), -30.0), _zs], 1)
    _loc, _ri, _ti = orig.ray.intersects_location(_o, np.tile([0, 1.0, 0], (len(_zs), 1)), multiple_hits=False)
    _y = np.full(len(_zs), -99.0); _y[_ri] = _loc[:, 1]; _ys.append(_y)
_prof = np.mean(_ys, 0)
EYE_Z = float(_zs[np.argmax(_prof)])
log('eye z from mesh %.2f' % EYE_Z)
hs0 = (zl0 == 1) & (np.abs(V[:, 1] - yf0) < 0.3) & (V[:, 2] > EYE_Z - 0.6) & (V[:, 2] < EYE_Z + 1.2)
hcx = np.median(V[hs0, 0])
hr = (np.percentile(V[hs0, 0], 99) - np.percentile(V[hs0, 0], 1)) / 2
ZTOP = V[:, 2].max()
hcy = np.percentile(V[hs0, 1], 2) + hr
# refine centre and half-extents from the mesh cross-section between eyes and crown
sl = (V[:, 2] > EYE_Z) & (V[:, 2] < EYE_Z + 1.2) & (np.hypot(V[:, 0] - hcx, V[:, 1] - hcy) < 3.3)
(x0_, y0_), (x1_, y1_) = V[sl, :2].min(0), V[sl, :2].max(0)
hcx, hcy, hrx, hry = (x0_ + x1_) / 2, (y0_ + y1_) / 2, (x1_ - x0_) / 2, (y1_ - y0_) / 2
hr = hrx
hzc, hza = (ZTOP + CHIN_Z - 0.6) / 2, (ZTOP - CHIN_Z + 0.6) / 2 + 0.05
ell = ((V[:, 0] - hcx) / (hrx + 0.3)) ** 2 + ((V[:, 1] - hcy) / (hry + 0.3)) ** 2 + ((V[:, 2] - hzc) / hza) ** 4
hsel = (ell < 1.0) & (V[:, 2] > CHIN_Z - 0.6)
face = hsel & (V[:, 2] < EYE_Z + 0.6) & (V[:, 1] < hcy)
if face.any() and int(os.environ.get('FACESMOOTH', '12')) > 0:
    vg = ob.vertex_groups.new(name='face')
    wts = np.clip((EYE_Z + 0.5 - V[face, 2]) / 0.4, 0, 1) * np.clip((V[face, 2] - (CHIN_Z - 0.6)) / 0.4, 0, 1)
    for i, ww in zip(np.where(face)[0].tolist(), wts.tolist()):
        vg.add([i], ww, 'REPLACE')
    sm = ob.modifiers.new('sm', 'SMOOTH'); sm.factor = 1.0; sm.iterations = int(os.environ.get('FACESMOOTH', '30')); sm.vertex_group = 'face'
    bpy.ops.object.modifier_apply(modifier='sm')
    me = ob.data
    V, Nrm = read_mesh()
    log('face smoothed', int(face.sum()))

# --- stray thin pegs/twigs (forearm vines, shoulder thorns, knee spikes): collapse them by local smoothing,
#     the final voxel remesh then drops what is left (< voxel size)
if int(os.environ.get('PEGSMOOTH', '260')) > 0:
    from pegs import peg_mask
    from scipy.spatial import cKDTree as _KD
    pm, _t = peg_mask(orig, TH=0.8, CH=0.9)
    sub = orig.submesh([np.where(pm[orig.faces].all(1))[0]], append=True)
    kill = []
    for p_ in sub.split(only_watertight=False):
        e_ = np.sort(p_.extents); c_ = p_.vertices.mean(0)
        if e_[1] > 1.4 or len(p_.faces) > 2500:
            continue
        stick = e_[0] < 0.6 and e_[1] < 0.65 and e_[2] > 0.9 and c_[2] < 33 and c_[1] < 2.5   # free-standing twig
        if stick or (c_[2] > 23.5 and abs(c_[0]) > 7.5) or c_[2] > 34 or (8.0 < c_[2] < 16 and abs(c_[0]) > 5.0 and c_[1] < 1.5):
            kill.append(p_.vertices)
    if kill:
        KV = np.concatenate(kill)
        KR = float(os.environ.get('PEGR', '0.5'))
        dk, _ = _KD(KV).query(V, distance_upper_bound=KR)
        pw = np.clip((KR - dk) / 0.15, 0, 1)
        vg2 = ob.vertex_groups.new(name='pegs')
        for i, ww in zip(np.where(pw > 0)[0].tolist(), pw[pw > 0].tolist()):
            vg2.add([i], ww, 'REPLACE')
        sm2 = ob.modifiers.new('sm2', 'SMOOTH'); sm2.factor = 1.0; sm2.iterations = int(os.environ.get('PEGSMOOTH', '260')); sm2.vertex_group = 'pegs'
        bpy.ops.object.modifier_apply(modifier='sm2')
        me = ob.data
        V, Nrm = read_mesh()
        log('pegs smoothed: clusters', len(kill), 'verts', int((pw > 0).sum()))

# --- depeg cut sites (depeg.py writes their centres): smooth the ragged hollows left by the hull cuts
if os.environ.get('CUTS') and os.path.exists(os.environ['CUTS']):
    CC = np.load(os.environ['CUTS'])
    from scipy.spatial import cKDTree as _KD2
    dc, _ = _KD2(CC).query(V, distance_upper_bound=1.1)
    cw = np.clip((1.1 - dc) / 0.4, 0, 1)
    vg4 = ob.vertex_groups.new(name='cuts')
    for i, ww in zip(np.where(cw > 0)[0].tolist(), cw[cw > 0].tolist()):
        vg4.add([i], ww, 'REPLACE')
    sm4 = ob.modifiers.new('sm4', 'SMOOTH'); sm4.factor = 1.0; sm4.iterations = 40; sm4.vertex_group = 'cuts'
    bpy.ops.object.modifier_apply(modifier='sm4')
    me = ob.data
    V, Nrm = read_mesh()
    log('cut sites smoothed', len(CC), int((cw > 0).sum()))

# --- hybrid seams (hybrid.py: front mesh ∪ MV back cut at y = HYB_Y0): smooth a band around the cut plane
if os.environ.get('HYB_Y0'):
    Y0h = float(os.environ['HYB_Y0']); ZTh = float(os.environ.get('HYB_ZT', '37.5'))
    XHh = float(os.environ.get('HYB_XH', '10.6'))
    band_w = np.clip(1 - np.abs(V[:, 1] - Y0h) / 1.0, 0, 1) * (V[:, 2] < ZTh) * (V[:, 2] > 4)
    band_w *= np.abs(V[:, 0] - hcx) > 2.6            # not through the head/neck
    side_w = np.clip(1 - (np.abs(np.abs(V[:, 0]) - XHh)) / 0.8, 0, 1) * (V[:, 1] > Y0h - 0.3) * (V[:, 2] > 4)
    band_w = np.maximum(band_w, side_w)
    vg3 = ob.vertex_groups.new(name='seam')
    for i, ww in zip(np.where(band_w > 0)[0].tolist(), band_w[band_w > 0].tolist()):
        vg3.add([i], ww, 'REPLACE')
    sm3 = ob.modifiers.new('sm3', 'SMOOTH'); sm3.factor = 1.0; sm3.iterations = 60; sm3.vertex_group = 'seam'
    bpy.ops.object.modifier_apply(modifier='sm3')
    me = ob.data
    V, Nrm = read_mesh()
    log('seam band smoothed', int((band_w > 0).sum()))

x, y, z = V[:, 0], V[:, 1], V[:, 2]
u, w = R.pix(x, z)


def samp(img, order=1):
    return map_coordinates(img.astype(np.float32), [w - 0.5, u - 0.5], order=order, mode='nearest')


yf = samp(yf_filled, 0)
dy = y - yf                                           # 0 on the surface seen in the image, >0 behind it
facing = np.clip((-Nrm[:, 1] - 0.05) / 0.45, 0, 1)
fv = facing * np.clip(1 - (dy - 0.08) / 0.2, 0, 1)    # visible in the front image
zl = samp(zones, 0).astype(int)
bandv = samp(band)
brv = samp(branch)
rel = samp(relief)
grv = samp(groove)


def zone_fade(sel, zid):
    return 1.0


def fract(a):
    return a - np.floor(a)


def vgroove(phase, pitch, half=0.09):
    """V profile: 1 on the seam line, 0 at +-half mm from it."""
    d = np.abs(phase - np.round(phase)) * pitch
    return np.clip(1 - d / half, 0, 1)


rng = np.random.default_rng(3)


def snoise(P, scale, n=6):
    """cheap smooth noise: sum of random plane waves (P: Nx3, scale mm)."""
    out = np.zeros(len(P))
    for _ in range(n):
        k = rng.normal(size=3); k /= np.linalg.norm(k)
        out += np.sin(P @ k / scale * 2 * np.pi + rng.uniform(0, 6.3))
    return out / math.sqrt(n / 2)


disp = np.zeros(nv)
from scipy.spatial import cKDTree
IMGSEAM = float(os.environ.get('IMGSEAM', '0.35'))   # weight of image-detected seams (they are noisy)
# --- 1. image relief (front-visible): strong on bandages and bark, weak elsewhere
amp = 0.05 + 0.12 * bandv + 0.08 * brv
disp += fv * rel * amp
# --- 2. image seams -> V-grooves on bandage zones (head handled below), reduced weight
notHead = (zl != 1)
disp -= IMGSEAM * fv * bandv * grv * GDEP * notHead

# --- 3. procedural wraps all around the bandaged limbs (front included); membership = within RAD mm of the
#        front-visible part of the zone (so the cloak behind is not touched)
ZP = {  # zone id: (pitch mm, k (integer: continuous helix), radius mm, tilt noise)
    2: (0.5, 1, 1.4), 3: (0.62, -2, 2.2), 4: (0.55, 1, 1.5), 5: (0.55, -1, 1.5), 6: (0.5, 1, 1.3),
    7: (0.5, -1, 1.3), 8: (0.66, 2, 2.1), 9: (0.66, -2, 2.1), 10: (0.55, 1, 1.8), 11: (0.55, -1, 1.8)}
isbr3d = (brv > 0.5) & (dy < 2.4)
for zid, (pitch, k, RAD) in ZP.items():
    vis = (zl == zid) & (fv > 0.5) & ~isbr3d
    if vis.sum() < 50:
        continue
    zlo, zhi = np.percentile(z[vis], [2, 98]); xlo, xhi = np.percentile(x[vis], [2, 98])
    xm = 0.3 if zid in (3, 8, 9) else RAD                # torso/thighs: wrap only round the sides seen in the image
    cand = np.where((z > zlo - 0.15) & (z < zhi + 0.15) & (x > xlo - xm) & (x < xhi + xm) & ~isbr3d & (dy < 6))[0]
    tree = cKDTree(V[vis])
    dd, _ = tree.query(V[cand], distance_upper_bound=RAD + 0.4)
    wgt_all = np.clip((RAD + 0.4 - dd) / 0.4, 0, 1)
    ok = wgt_all > 0
    sel = cand[ok]; wgt = wgt_all[ok]
    wgt *= np.clip((0.6 - Nrm[sel, 1]) / 0.3, 0, 1)   # keep off the cloak's back: not on surfaces facing backwards
    wgt *= np.clip((zhi + 0.15 - z[sel]) / 0.3, 0, 1) * np.clip((z[sel] - zlo + 0.15) / 0.3, 0, 1)
    cx, cy = np.median(x[vis]), np.median(y[vis]) + 1.0
    th = np.arctan2(x[sel] - cx, -(y[sel] - cy))
    ph = z[sel] / pitch + k * th / (2 * np.pi) + 0.22 * snoise(V[sel], 3.0) + 0.1 * snoise(V[sel], 1.1)
    d = -GDEP * vgroove(ph, pitch) + 0.07 * (fract(ph) - 0.5)
    disp[sel] += wgt * zone_fade(sel, zid) * d
    log('wrap zone', zid, len(sel))

# --- 4. head: individual crossing wrap strips (like the concept portrait), eye slit with eyes
#        each strip = band |q.n_i - o_i| < w_i on the normalised head ellipsoid; the last strip covering a point wins
#        (drawn on top, higher layer); strip edges drop to the layer below -> overlapping, crossing wraps
if hsel.any():
    hx, hy, hz = x[hsel], y[hsel], z[hsel]
    th = np.arctan2(hx - hcx, -(hy - hcy))            # 0 = facing the viewer
    RZ = max(ZTOP - EYE_Z, 1.5)
    Q = np.stack([(hx - hcx) / (hrx + 0.1), (hy - hcy) / (hry + 0.1), (hz - EYE_Z) / RZ], 1)
    Q /= np.maximum(np.linalg.norm(Q, axis=1, keepdims=True), 1e-6)
    hr_ = np.random.default_rng(int(os.environ.get('HEADSEED', '7')))
    strips = []   # (normal, offset, halfwidth)

    def tilt(deg, az):
        t, a = np.radians(deg), np.radians(az)
        return np.array([np.sin(t) * np.cos(a), np.sin(t) * np.sin(a), np.cos(t)])
    # lower face wraps (below the eyes, around jaw and neck), tilted
    for off in np.linspace(-0.6, -0.26, 3):
        strips.append((tilt(hr_.uniform(12, 28), hr_.uniform(0, 360)), off + hr_.normal(0, 0.03), hr_.uniform(0.12, 0.15)))
    # skull wraps above the eyes, crossing at varied angles
    for off in np.linspace(0.26, 0.82, 4):
        strips.append((tilt(hr_.uniform(10, 34), hr_.uniform(0, 360)), off + hr_.normal(0, 0.04), hr_.uniform(0.12, 0.16)))
    # a few strips over the crown and diagonally across the face/brow (the big crossing wraps of the portrait)
    for az in (25, 150):
        strips.append((tilt(hr_.uniform(62, 78), az + hr_.uniform(-15, 15)), hr_.normal(0, 0.1), hr_.uniform(0.13, 0.16)))
    for deg, az, off in ((26, 90 + 40, 0.14), (28, 90 - 45, -0.07)):   # two diagonals over the brow / cheek
        strips.append((tilt(deg, az), off, 0.12))
    order = hr_.permutation(len(strips))
    top = np.full(len(Q), -1); edge_d = np.zeros(len(Q))
    for rank, i in enumerate(order):
        n_, o_, w_ = strips[i]
        s = Q @ n_ - o_
        inside = np.abs(s) < w_
        top[inside] = rank; edge_d[inside] = (w_ - np.abs(s[inside])) * 1.9   # ~mm to the strip edge
    covered = top >= 0
    layer = np.where(covered, 0.11 + 0.07 * (top / max(1, len(strips) - 1)), 0.0)
    bevel = np.clip(edge_d / 0.07, 0, 1) ** 0.5
    crinkle = 0.012 * snoise(V[hsel], 1.2)
    front = np.clip(1 - (np.abs(th) - 0.85) / 0.25, 0, 1)
    slitz = np.abs(hz - EYE_Z) - 0.27
    slit = front * np.clip(1 - slitz / 0.05, 0, 1)
    neck_fade = np.clip((hz - (CHIN_Z - 0.6)) / 0.5, 0, 1)
    d = (layer * bevel + crinkle * covered) * (1 - slit)
    d = np.where(covered | (slit > 0.5), d, -0.05)                   # gaps between strips read as dark grooves
    # eye slit: recessed band, two sockets with rounded eyeballs
    ex = hx - hcx
    EX = float(os.environ.get('EYE_X', '0.58'))
    for sx_ in (-1, 1):
        r2 = ((ex - sx_ * EX) / 0.34) ** 2 + ((hz - EYE_Z) / 0.22) ** 2
        sock = np.exp(-r2 * 2.0) * front
        ball = np.exp(-(((ex - sx_ * EX) / 0.16) ** 2 + ((hz - EYE_Z) / 0.13) ** 2) * 2.0) * front
        d += slit * (-0.24 * sock + 0.22 * ball)
    d -= 0.09 * slit
    d = d * neck_fade + disp[hsel] * (1 - neck_fade)
    disp[hsel] = d
    log('head verts', int(hsel.sum()), 'strips', len(strips), 'covered %.2f' % covered.mean(),
        'eye z %.2f chin z %.2f hc %.2f %.2f' % (EYE_Z, CHIN_Z, hcx, hcy))

# --- 5. branch: 3D tube around the branch axis (axis = image polyline lifted to the mesh: first hit + 1 mm)
#        -> smooth weight by distance to the axis; long bark furrows + radial thickening (no steps at mask edges)
pts = []
for a_, b_ in zip(BRL[:-1], BRL[1:]):
    n_ = int(np.ceil(np.linalg.norm(b_ - a_) / 3))
    pts += [a_ + (b_ - a_) * t_ for t_ in np.arange(n_) / n_]
pts = np.array(pts + [BRL[-1]])
cx_, cz_ = R.world(pts[:, 0], pts[:, 1])
o_ = np.stack([cx_, np.full(len(pts), -30.0), cz_], 1)
loc_, ri_, ti_ = orig.ray.intersects_location(o_, np.tile([0, 1.0, 0], (len(pts), 1)), multiple_hits=False)
cy_ = np.full(len(pts), np.nan); cy_[ri_] = loc_[:, 1] + 1.0
ok_ = ~np.isnan(cy_)
C3 = np.stack([cx_, cy_, cz_], 1)[ok_]
T3 = np.gradient(C3, axis=0); T3 /= np.linalg.norm(T3, axis=1, keepdims=True)
cand = np.where((x > C3[:, 0].min() - 2) & (x < C3[:, 0].max() + 2) & (z > C3[:, 2].min() - 2) & (z < C3[:, 2].max() + 2))[0]
dist, idx = cKDTree(C3).query(V[cand], distance_upper_bound=2.0)
wb = np.clip((1.6 - dist) / 0.35, 0, 1)
okc = wb > 0
bsel = cand[okc]; wb = wb[okc]; idx = idx[okc]
isbr3d = np.zeros(nv, bool); isbr3d[bsel] = True
if len(bsel):
    A = T3[idx]
    P = V[bsel]
    along = (P * A).sum(1)
    perp = P - along[:, None] * A
    fur = np.zeros(len(P))
    for i in range(7):
        kk = rng.normal(size=3); kk /= np.linalg.norm(kk)
        ph = (perp @ kk) / 0.42 + 0.35 * np.sin(along / 1.7 + i) + 0.2 * np.sin(along / 0.6 + 2 * i)
        fur += np.abs(np.sin(ph * np.pi))
    fur = fur / 7 - 0.64
    handw = 1 - 0.7 * np.isin(zl[bsel], (6, 7))      # fists: only a little bark
    disp[bsel] += wb * handw * (1 - fv[bsel] * 0.5) * 0.34 * fur
    # the AI branch is 1.6-3.3 mm wide: thicken it radially so no part is under ~2 mm
    disp[bsel] += wb * float(os.environ.get('BRTHICK', '0.17')) * (1 + 0.35 * (1 - handw) / 0.7)   # a bit more next to the fists (thinnest there)
    log('branch verts', len(bsel), 'axis pts', len(C3))

# --- 6. fur mantle: hundreds of individual hanging locks (tapering teardrops, random length/angle, overlapping)
#        on the back + shoulder tops; the lower edge is ragged because the lowest locks hang past it.
FUR_Z0 = float(os.environ.get('FUR_Z0', '28.8'))
nothead = ~hsel
backw = np.clip((Nrm[:, 1] - 0.1) / 0.3, 0, 1)
topw = np.clip((Nrm[:, 2] - 0.45) / 0.3, 0, 1) * (z > 31.5) * np.clip((0.3 + Nrm[:, 1]) / 0.3, 0, 1)
neck3d = (zl == 2) & (dy < 2.5)
brwide = np.zeros(nv, bool); brwide[cand[np.isfinite(dist)]] = True      # within 2 mm of the branch axis
furw = np.maximum(backw, topw) * nothead * ~neck3d * ~brwide * (zl != 6) * (zl != 7)
z_edge = FUR_Z0 + 0.7 * snoise(V, 2.2)
core = (furw > 0.3) & (z > z_edge)
fr = np.random.default_rng(11)
ci = np.where(core)[0]
# dart-throwing seeds (min spacing 0.5 mm) instead of one per grid cell -> no grid pattern
perm = fr.permutation(len(ci))[:60000]
cand_s = V[ci[perm]]
keep_s = []
tree_s = None
chosen = np.zeros(0, int)
grid = {}
for j, pnt in enumerate(cand_s):
    g = tuple(np.floor(pnt / 0.5).astype(int))
    okp = True
    for dx_ in (-1, 0, 1):
        for dy_ in (-1, 0, 1):
            for dz_ in (-1, 0, 1):
                for q in grid.get((g[0] + dx_, g[1] + dy_, g[2] + dz_), ()):
                    if np.sum((cand_s[q] - pnt) ** 2) < 0.25:
                        okp = False; break
                if not okp: break
            if not okp: break
        if not okp: break
    if okp:
        grid.setdefault(g, []).append(j); keep_s.append(j)
seeds = ci[perm[np.array(keep_s)]]
S = V[seeds]; SN = Nrm[seeds]
down = np.array([0, 0, -1.0]) + 0.5 * np.stack([np.sign(S[:, 0]) * 0.3, np.ones(len(S)), np.zeros(len(S))], 1) * (SN[:, 2:3] > 0.5)
D = down - (down * SN).sum(1, keepdims=True) * SN
D /= np.maximum(np.linalg.norm(D, axis=1, keepdims=True), 1e-6)
ang = fr.normal(0, 0.45, len(S))                     # random swing of each lock around the normal
B0 = np.cross(SN, D)
D = D * np.cos(ang)[:, None] + B0 * np.sin(ang)[:, None]
B = np.cross(SN, D)
L = fr.uniform(1.0, 2.8, len(S)) * np.where(S[:, 2] < FUR_Z0 + 1.5, fr.uniform(0.8, 1.9, len(S)), 1.0)
W0 = fr.uniform(0.3, 0.5, len(S)); HM = fr.uniform(0.14, 0.28, len(S)); PRI = fr.uniform(0, 0.06, len(S))
reg6 = np.where((furw > 0.2) & (z > z_edge - 4.3))[0]
tree = cKDTree(S)
dd, nn = tree.query(V[reg6], k=12, distance_upper_bound=4.4)
best = np.full(len(reg6), -1.0); besth = np.zeros(len(reg6))
for j in range(12):
    ok = np.isfinite(dd[:, j]); k_ = nn[ok, j]
    rel = V[reg6[ok]] - S[k_]
    a = (rel * D[k_]).sum(1); b = (rel * B[k_]).sum(1)
    tt = np.clip(a / L[k_], 0, 1)
    wa = W0[k_] * np.sqrt(np.clip(1 - tt ** 1.6, 0, 1)) * np.clip((a + 0.35) / 0.35, 0, 1)
    inside = (a > -0.35) & (a < L[k_]) & (np.abs(b) < wa)
    bn = b / np.maximum(wa, 1e-4)
    strands = 0.86 + 0.14 * np.cos(np.pi * bn * (2 + (k_ % 2)) + k_)       # 2-3 hair strands per lock
    hgt = HM[k_] * np.sqrt(np.clip(1 - bn ** 2, 0, 1)) * (1 - 0.35 * tt) * strands
    score = np.where(inside, hgt + PRI[k_] - 0.08 * tt, -1)   # roots of lower locks go under the tips of upper ones
    upd = score > best[ok]
    idx_ = np.where(ok)[0][upd]
    best[idx_] = score[upd]; besth[idx_] = hgt[upd]
under = 0.06 * core[reg6]
furdisp = np.where(best > -1, besth + 0.08, under)
disp[reg6] += furw[reg6] * furdisp
log('fur seeds', len(S), 'fur verts', len(reg6), 'covered %.2f' % (best > -1).mean())

# heavy cloak folds: irregular vertical ridges, deeper toward the hem; also on the cloak sides behind the body
cloakw = np.maximum(backw, np.clip((np.abs(Nrm[:, 0]) - 0.5) / 0.3, 0, 1) * (y > 0.5) * (z < 21)) * nothead * ~brwide
cloakw *= (1 - np.clip((z - z_edge + 0.3) / 0.3, 0, 1)) * (z > 4.5)
fan = 1 + np.clip((FUR_Z0 - z) / 45, 0, 0.5)            # folds widen toward the hem
ph1 = x / (2.9 * fan) + 0.25 * snoise(V * [1, 1, 0.25], 6.0) + 0.1 * snoise(V * [1, 1, 0.3], 2.5)
ph3 = y / (3.0 * fan) + 0.25 * snoise(V * [1, 1, 0.25], 6.0)      # sides: folds wrap around
fold = (0.5 + 0.5 * np.sin(2 * np.pi * ph1)) ** 2.5
fold = np.where(np.abs(Nrm[:, 0]) > 0.6, (0.5 + 0.5 * np.sin(2 * np.pi * ph3)) ** 2.5, fold)
famp = 0.12 + 0.66 * np.clip((FUR_Z0 - z) / (FUR_Z0 - 7), 0, 1)
disp += cloakw * famp * fold
log('cloak verts', int((cloakw > 0.5).sum()))

# --- 7. thin walls (cloak, tabard strips): inflate so they end up >= ~0.5 mm
o = V - Nrm * 0.004
t = np.full(nv, 9.0)
for a in range(0, nv, 600000):
    b = min(nv, a + 600000)
    loc, ri, ti = orig.ray.intersects_location(o[a:b], -Nrm[a:b], multiple_hits=False)
    t[a + ri] = np.linalg.norm(loc - o[a:b][ri], axis=1)
# no carving into thin sheets (grooves/sockets would eat the wall), then inflate to >= ~0.62 mm
thinf = np.clip((t - 0.25) / 0.6, 0, 1)
disp = np.where(disp < 0, disp * thinf, disp)
infl = np.clip((float(os.environ.get('WALL', '0.64')) - t) / 2, 0, 0.24)
disp += infl
log('thin (<0.45 mm) verts inflated', int((t < 0.45).sum()))

disp = np.clip(disp, -0.24, 0.82)
V2 = V + Nrm * disp[:, None]
me.vertices.foreach_set('co', V2.ravel()); me.update()
FEET = V2[V2[:, 2] < 3.8][:, :2].copy()
log('disp pct', np.round(np.percentile(disp, [1, 5, 50, 95, 99]), 3).tolist())

# ---------------------------------------------------------------- sink 0.15 mm into the base, keep 36 mm soles->head
S = 36.15 / 36.0
ob.scale = (S, S, S); ob.location = (0, 0, 3.0 - 3.0 * S - 0.15)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

del R, orig, V, Nrm, V2
import gc; gc.collect()
parts = [ob]
if not os.environ.get('NOBASE'):
    sys.path.insert(0, os.path.join(HERE, '..', 'mini'))
    from geo import PARTS, tube, ellipsoid
    bz = [0.0, 0.35, 2.45, 2.85, 3.0, 3.06]
    brs = [12.25, 12.5, 12.5, 12.3, 11.9, 0.1]
    tube('base', [(0, 0, zz) for zz in bz], brs, seg=128)
    # a few low stones on the rim, away from the feet
    feet = FEET
    rs = np.random.default_rng(5); k = 0
    for i in range(60):
        a = rs.uniform(0, 2 * math.pi); r = rs.uniform(8.3, 10.9)
        c = np.array([r * math.cos(a), r * math.sin(a)])
        if len(feet) and np.min(np.linalg.norm(feet - c, axis=1)) < 2.2:
            continue
        ellipsoid(f'stone{k}', (c[0], c[1], 3.0), (rs.uniform(0.6, 1.3), rs.uniform(0.5, 1.0), rs.uniform(0.3, 0.55)),
                  rot=(0, 0, a), seg=14, rings=8)
        k += 1
        if k >= 7:
            break
    parts += sum(PARTS.values(), [])
bpy.ops.object.select_all(action='DESELECT')
for p in parts:
    p.select_set(True)
bpy.context.view_layer.objects.active = ob
bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
ob.data.remesh_voxel_size = FVOX
bpy.ops.object.voxel_remesh()
log('final remesh', len(ob.data.polygons))
n2 = len(ob.data.vertices); C = np.empty(n2 * 3); ob.data.vertices.foreach_get('co', C); C = C.reshape(-1, 3)
C[:, 2] = np.maximum(C[:, 2], 0); ob.data.vertices.foreach_set('co', C.ravel()); ob.data.update()
tris = 2 * len(ob.data.polygons)          # voxel remesh -> quads
if tris > TARGET:
    dm = ob.modifiers.new('dec', 'DECIMATE'); dm.ratio = TARGET / tris; dm.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier='dec')
bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
bpy.ops.wm.stl_export(filepath=outp + '.stl', export_selected_objects=True)
log('exported', outp + '.stl', len(ob.data.polygons), 'faces')
# note: at FVOX 0.028 (6.4M quads) Blender's decimate is OOM-killed on 15 GB; 0.03 (~5.6M) fits.
# decimate.py (fast-simplification) is a lighter fallback but leaves a few dozen non-manifold edges.
