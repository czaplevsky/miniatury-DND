#!/bin/sh
# End-to-end v3 pipeline (steps as in PIPELINE.md). GPU steps are optional; everything after step 2 is CPU-only.
set -e
S=/tmp/claude-0/-home-user-DASHBOARD/875c84ef-72ed-526b-a1dc-8eb9fffa8e2f/scratchpad
cd $S/v3
HY=$S/research/hyvenv/bin/python; BP=$S/bvenv/bin/python
# 1 (GPU, optional): exaggerated-bandage sculpt front from the branch-swapped front
[ -f img/front_k21b.png ] || GS=3.5 $HY edit_front.py kontext 21 ../edit/kontext_s7.png img/front_k21b.png
# 3 cutouts; sculpt RGB + colour alpha
$HY cutout.py ../edit/kontext_s7.png img/front_s7_rgba.png
$HY cutout.py img/front_k21b.png img/front_k21b_rgba.png
$HY -c "from PIL import Image; a=Image.open('img/front_s7_rgba.png').split()[3]; k=Image.open('img/front_k21b.png').convert('RGB'); k.putalpha(a); k.save('img/front_k21b_s7a.png')"
# 4 shape on CPU
$HY hy_cpu.py mini hy/mini_k21.glb 512 5 1 front=img/front_k21b_s7a.png
$BP prep.py hy/mini_k21.glb hy/mini_k21.stl
# 5 normals + maps
$HY normals.py img/front_k21b_s7a.png nrm/k21 1248
$HY normals.py img/front_s7_rgba.png nrm/s7 1248
$HY maps.py
# 6 + 8
$BP detail.py hy/mini_k21.stl out/final
$BP finalize.py out/final.stl druid_mini_v3
./rend.sh v3/druid_mini_v3.stl final
