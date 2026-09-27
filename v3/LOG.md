# v3 LOG (druid mini)

| # | attempt | quota (GPU s) | verdict |
|---|---|---|---|
| 1 | Qwen-Image-Edit-2511-Fast /infer (front bandage exaggeration), 2 tries | ~0 (Space returns bare `RuntimeError` after 5 s) | Space broken → fallback Kontext |
| 2 | Kontext s7 prompt "a" (long), gs 2.5, src edit/kontext_s7.png → img/front_k7.png | ~30 | head became smooth white hood, bandages NOT exaggerated → rejected |
| 3 | Kontext s21 prompt "b" ("sculpt ... like tabletop miniature"), gs 3.5 → img/front_k21b.png | ~33 | turned whole figure into ivory sculpt; bandage strips on legs/belly/arms more layered and readable, pose & branch preserved 1:1; head smooth cap. Useful as geometry input |
| 4 | multiple-angles /infer_camera_edit az180 s7 from front_k21b | ~?? (97 s wall, 'GPU task aborted') | failed, burned the rest of quota |
| 5 | same from kontext_s7 | 0 | `exceeded your free ZeroGPU quota (60s requested vs. 31s left). Try again in 6:40` → **quota for today exhausted** (it was already partly used before this run) |

Quota spent by this run: roughly 65 s successful + an aborted task; the remaining 31 s is below any Space's requested duration → switch to CPU-only for everything else.

## CPU phase (0 GPU quota from here on)
Consistent side/back views could not be generated (quota). Fallbacks from PLAN §2 used:

| # | attempt | time | verdict |
|---|---|---|---|
| 6 | rembg isnet (cutout.py) on kontext_s7 and front_k21b | 20 s | sculpt image lost dark cloak between legs → used k21b RGB + s7 alpha (`img/front_k21b_s7a.png`) |
| 7 | back view composed from the concept sheet back + mirrored new branch ends (back_compose.py) | – | pose/cloak drape of the sheet back differs a lot from the new front, branch ends float → **not used** (would feed inconsistent views to 2mv) |
| 8 | hy_cpu mv 512 front-only, kontext_s7 (hy/mv_s7_front) | 5 min | cloak full of holes, branch ends like bone knobs → rejected |
| 9 | hy_cpu mv 512 front-only, k21b (hy/mv_k21_front) | 5 min | solid cloak, bark on branch, belly wraps; surfaces lumpy/noisy |
| 10 | re-downloaded mini-turbo (4.2 GB) ; hy_cpu mini 512 k21b seed1 (hy/mini_k21) | 9 min | **cleanest**: crisp armor/crossed straps, solid cloak, clean branch through both fists, watertight; smooth (no bandage geometry) → chosen base |
| 11 | hy_cpu mini 512 s7 seed2 (hy/mini_s7) | 5.5 min | floating debris pieces, not watertight → rejected |
| 12 | research cpu_mini_512 (s7, seed1) | – | similar to #10 but chest less defined |
| 13 | Marigold-e2e normals CPU on k21b and s7 (normals.py) | 70 s each | both good; relief = average of both high-passed heights |
| 14 | regfit.py (normal-correlation fit of the image→mesh mapping) | 3 min | optimiser drifted to a wrong minimum → dropped; plain bbox registration verified visually with regview.py (features line up within a few px) |
| 15 | detail d1: image relief + image-seam grooves + hidden-side wraps | 6 min | grooves readable on belly, but wraps leaked onto cloak back; head bands only on front |
| 16 | d2: procedural wraps all around (KD-tree membership) | 6.5 min | leaked onto chest armor → too much |
| 17 | d3/d4: zone z/x limits, normal filter, integer-k helices | 6.5 min each | torso clean again; head selection wrong (half the head bare, disc on back) |
| 18 | d5: head selected by measured 3D ellipsoid | 6.5 min | whole head wrapped, reads as mummy; eye slit too subtle; back of figure plain; 5 % of surface < 0.3 mm thick |
| 19 | d6: fur mantle (back+shoulder tops), cloak folds, thin-wall inflation, deeper eye slit | 7 min | fur = regular corduroy + bare rectangle (neck zone projected to the back), fur on branch end, eye slit at wrong height (image eye row is 0.65 mm off on the mesh) |
| 20 | d7: eye line measured on the mesh (deepest point of face profile, z=36.0), neck/branch excluded from fur, irregular folds | OOM in Blender decimate at FVOX 0.028 (6.4 M quads); fast-simplification fallback left 52 non-manifold edges → FVOX 0.03 in-process | eye slit + sockets now visible; fur looks like curly sheepskin |
| 21 | d8: hanging fur locks, pointed ragged mantle edge | 7 min | fur reads as shaggy fur; branch edge picked up fur teeth (mask misalignment) |
| 22 | d9: +0.17 mm branch thickening (AI branch measured 1.6-3.3 mm wide) | 7 min | step/crease along branch where the image mask ended |
| 23 | d10: branch selected as a 3D tube around the image polyline lifted onto the mesh, smooth distance weight | 7 min | see final |
| 24 | d11: extra thickening next to the fists (branch min Ø 1.56 → ~2 mm) | 7 min | **delivered as v3** (druid_mini_v3.stl/.3mf, 21.9 MB 3MF via compact writer) |

## Round 2 (after coordinator review of d11) — CPU while waiting for the quota reset (~14:05-14:30 UTC)
Critique: fur = corduroy, cloak back flat, head = beehive rings, stray pegs at forearms/shoulders, branch end claw?

| # | attempt | time | verdict |
|---|---|---|---|
| 25 | d12: head = 16 individual crossing strips on the head ellipsoid (layered, bevelled edges); fur = 1385 hanging teardrop locks (KD-tree, random length/angle/priority); cloak folds; peg removal (pegs.py: thin in ≥2 directions → Laplacian collapse, 80 it.) | 8 min | head reads as crossing wraps but strips too thin + crinkle → yarn ball; fur ok from side, fine towel from back; cloak folds = worm squiggles; pegs only partly gone |
| 26 | d13: 11 wider strips (0.5-0.6 mm), less crinkle, wider slit+eyeballs; locks 0.62 spacing, 1.2-2.8 mm; broad fanning cloak folds; pegs TH 0.8, radius 0.32, 160 it.; torn hem = manifold3d V-notches (notch.py) | 9 min | head clearly crossing wraps like the portrait (good); slit still noisy; fur grid-like shingles from the back; cloak folds too shallow to read; only 4 notches |
| 27 | d14: dart-throwing lock seeds + 2-3 strands per lock, cloak folds up to 0.78 mm at the hem (narrow ridges), 6 hem notches, stronger face smoothing | 12 min | **fur now reads as hanging shaggy locks**, cloak back has real folds + torn hem; slit cleaner; but moiré hatch band under the fur (0.3 mm noise) and locks a bit needle-like |
| 28 | d15: no fine noise under the fur, wider/softer locks, deeper eye sockets + bigger eyeballs | 12 min | clean shaggy fur with ragged edge, folds + torn hem; best CPU result so far. Branch lower end checked at 1600 px: blunt bark-wrapped stump, not a claw. A few knobs remain on the right forearm and a thin twig at the knee |
| 29 | d16: + free-standing twig rule (33 clusters collapsed) | 12 min | ≈ d15, slightly fewer twigs; knee twig still partly there. **best CPU-only candidate** |
| 35 | Kontext "rotate the camera 90°: strict side profile … from his left side", seed 5, gs 3 | ~29 | **true profile** (faces image-right, i.e. seen from his right = Hunyuan 'left' slot), branch in front consistent |
| 36 | same prompt "from his right side" | ~29 | Kontext ignored the direction: same facing as #35 → not used |
| 40 | Kontext back seed 11 | ~39 | branch drawn behind the back → rejected |
| 41 | Kontext back seed 21 | 0 | `exceeded your ZeroGPU runs limit` → **quota exhausted (≈4.5 min GPU spent in this window: 9 successful calls)** |
| 42 | d18: detail pass on the hybrid | 12 min | **best so far**: crisp front, volumetric fur collar covered in hanging locks, torn cloak; shoulder thorns collapsed into knobby blobs, small fin behind the head, faint seam on the cloak side |
| 43 | d19: nape box cut in hybrid.py (no fin behind head), peg collapse radius 0.5 / 260 it. | – | OOM-killed in the final remesh (hybrid has more surface: 6.8 M quads at FVOX 0.03) → use FVOX 0.032 for the hybrid |

## Round 3 (coordinator: user likes d18 = v4; CPU-only fixes → v5)
| 46 | d20: depegged hybrid + seam-band smoothing (±0.6 mm around y=-0.5, 25 it.), FVOX 0.032 | 13 min | shoulder knobs + nape fin gone, knee twig gone; cloak side seam still visible, box-side seam at |x|=10.6 on the back |
| 47 | d21: seam band ±1 mm, 60 it., plus bands at the box sides |x|=10.6 | 13 min | side seam fainter but still a line: crease analysis showed it is the front mesh's cloak edge poking through the MV cloak (y 0.5-2.5), not the cut plane |
| 48 | hybrid.py: front mesh trimmed behind y=-0.3 for |x|>7.3 (cloak sides come only from the MV mesh) | 1 min | raw hybrid side views show no seam line |
| 49 | d22: detail on the trimmed hybrid | 13 min | side seam gone at print scale; small ragged bits left at the depeg cut sites on the forearm; **walls < 0.4 mm on 6.6 % of samples (thick2)** – MV cloak is thin and grooves/relief carve into it |
| 50 | d23: + wall protection (negative displacement faded out where the raw wall < 0.85 mm, inflation target 0.64 mm) + smoothing of the 32 depeg cut sites | 14 min | forearm cut sites smoother, no regressions → **v5** |

### v5 validation (druid_mini_v5.stl / .3mf)
- single body, watertight, winding consistent; 1.9 M tris; volume 4150 mm³ (~4.2 ml resin)
- soles→head top 36.03 mm, base Ø25 × 3 mm, total 39.03 mm; max radius above the base 12.25 mm (inside the 12.5 mm footprint)
- 3MF 23.9 MB (reloads as 1 watertight body). **Bug found**: the compact 3MF writer rounded coordinates to 0.1 µm (4 decimals), which on the d18 (v4) mesh produced 3 degenerate 2-face specks (main body still watertight). Now 6 decimals; re-exported v4 as `druid_mini_v4_fixed.3mf` (1 watertight body).
- walls: new `thick3.py` (sheet-scale thickness: inward ray along the 0.45 mm-averaged normal, decimation slivers < 0.08 mm ignored): 0.82 % of surface samples < 0.4 mm (v2: 0.33 %) – torn cloak/fur-lock tips; thick2.py counts relief ridges (fur locks, strips) as walls and reports 8 %, which is not meaningful for relief.
- remaining: faint crease down the back of the right arm (hybrid seam, visible only in close-up), a thin horizontal step under the fur collar on the back-left, a few small ragged bits on the right forearm.
