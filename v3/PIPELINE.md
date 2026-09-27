# v3 pipeline notes (druid mini, 36 mm resin)

All paths relative to `scratchpad/`. Envs: `research/hyvenv` (torch, diffusers, Hunyuan3D-2, rembg, skimage),
`bvenv` (bpy 5.0.1, trimesh+embree, scipy, fast-simplification).

| step | script | env | notes |
|---|---|---|---|
| 1 front edit (GPU) | `v3/edit_front.py {qwen\|kontext} SEED SRC OUT` | any | Qwen-Image-Edit-2511-Fast Space was broken (bare RuntimeError). Kontext prompt "b" (sculpt like a tabletop miniature) gives an ivory sculpt with layered wraps: good geometry input, same pose/branch. |
| 2 views (GPU) | `v3/views.py SRC PREFIX SEED 180 90 270` | any | Qwen multiple-angles (fallback `FALLBACK=kontext`). Not run successfully today: quota ran out. |
| 2' back fallback | `v3/back_compose.py` | any | sheet back + mirrored branch ends. Tried, not used (pose too different). |
| 3 cutout | `v3/cutout.py IN OUT_RGBA` | hyvenv | rembg isnet. For the sculpt image use the colour image's alpha (cloak between legs gets lost). |
| 4 shape (CPU) | `v3/hy_cpu.py {mv\|mini} OUT.glb 512 5 SEED front=... [back=...]` | hyvenv | mini-turbo 512: 5-9 min, 1.25 M tris. mv-turbo 512: 5 min. |
| 4b prep | `v3/prep.py IN.glb OUT.stl` | bvenv | Y-up→Z-up, front −Y, soles z=3, head z=39. |
| 5 normals (CPU) | `v3/normals.py IMG_RGBA PREFIX 1248` | hyvenv | Marigold-e2e, 70 s, + Frankot-Chellappa height. |
| 5b maps | `v3/maps.py` | hyvenv | relief (high-pass height, avg of 2 normal maps), image seams (Sato ridges → skeleton → V profile), bandage zones + branch polyline (hand-placed px boxes for this character). |
| 5c registration | `v3/reg.py` (bbox), check with `v3/regview.py MESH maps/reg_bbox.json OUT.png` | bvenv | `regfit.py` (normal-correlation optimiser) drifted; bbox mapping is good to a few px. |
| 6+8 detail + base | `v3/detail.py BODY.stl OUTPREFIX` | bvenv | 6 min, peak ~13 GB. See docstring. Env knobs: GROOVE, RAISE, IMGSEAM, FUR_Z0, BRTHICK, FVOX (0.03; 0.028 OOMs in decimate), TARGET_TRIS. |
| 8 export | `v3/finalize.py IN.stl OUT` | bvenv | drops specks, prints checks, writes STL + 3MF. `fin/thick.py` for wall thickness. |
| renders | `v3/rend.sh MESH NAME` → `v3/r/NAME_{full,c,h}/sheet.png` | bvenv | full, torso close-up (ortho 17, z 29), head close-up (ortho 7). |
| compare | `v3/compare.py FULL CLOSE OUT` | any | v2 vs v3 image. |

## What the detail pass adds (all in mm, displacement along normals)
- bandage zones (head, neck, belly band, upper arms, fists, thighs, boots): helical V-grooves 0.18 deep / 0.18 wide,
  pitch 0.5-0.66, plus a 0.07 shingle step at every seam (layered look); image-detected seams at 35 % weight on top.
- head: whole head raised 0.12 as crossing strip families (k=3 above the eyes, k=−2 below), grooves 0.16, eye slit
  (±0.24 mm around the measured eye line) left recessed with two 0.2 mm eye sockets; AI face (nose/lips) smoothed first.
- relief from AI normals: ±0.05 general, ±0.17 on bandages, ±0.13 on bark (front-visible surfaces only).
- branch: long bark furrows ±0.1 all around, whole branch thickened +0.17 radially.
- fur mantle: back + top of shoulders raised 0.2 with hanging-lock strands (±0.11) and a pointed ragged lower edge at z≈28.8.
- cloak: irregular vertical fold ridges (≤0.24, only outward).
- thin walls: every vertex whose inward thickness is < 0.52 mm is pushed out by (0.52−t)/2 (≤0.16).
- base: 25 mm × 3 mm with bevels + a few stones; body sunk 0.15 mm into it; union by voxel remesh 0.03 mm, decimate to 1.9 M tris.

## v4/v5 additions (round 2-3)
| step | script | notes |
|---|---|---|
| back view (GPU) | `v3/kviews.sh SEED 180` (views.py FALLBACK=kontext, from the sculpt front) | seed 3 gave a true back view; side views need the "rotate the camera 90°: strict side profile" prompt |
| MV shape | `hy_cpu.py mv hy/mv_fb_s3.glb 512 5 1 front=img/front_k21b_s7a.png back=img/kv_back_s3_rgba.png` | front+back; adding the Kontext profile made it worse |
| hybrid | `v3/hybrid.py hy/mini_k21.stl hy/mv_fb_s3.stl hy/hyb.stl -0.5 37.5 10.6` | crisp single-view front ∪ MV back (y>-0.5), head capsule + ellipsoidal nape dip excluded, front cloak sides trimmed behind the plane |
| depeg | `v3/depeg.py hy/hyb.stl hy/hyb_dp.stl` | cuts shoulder thorns / forearm spikes / knee twigs (hull subtraction), writes `_cuts.npy` |
| detail | `CUTS=hy/hyb_dp_cuts.npy HYB_Y0=-0.5 FVOX=0.032 FUR_Z0=28.6 detail.py hy/hyb_dp.stl out/dN` | head strips, fur locks, cloak folds, seam + cut-site smoothing, wall protection |
| hem | `v3/notch.py IN OUT` | torn hem V-notches (manifold3d) |
| checks | `finalize.py` (3MF 6 decimals), `thick3.py` (sheet thickness) | |
