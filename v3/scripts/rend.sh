#!/bin/sh
# rend.sh MESH.stl NAME : full sheet (4 views), torso closeup and head closeup
S=/tmp/claude-0/-home-user-DASHBOARD/875c84ef-72ed-526b-a1dc-8eb9fffa8e2f/scratchpad
. $S/bvenv/bin/activate
cd $S
nice python mini/render.py $1 v3/r/$2_full 900 44 20.5 >/dev/null 2>&1; python mini/sheet.py v3/r/$2_full
nice python mini/render.py $1 v3/r/$2_c 900 17 29 >/dev/null 2>&1; python mini/sheet.py v3/r/$2_c front front34 side back
nice python mini/render.py $1 v3/r/$2_h 700 7 35.8 >/dev/null 2>&1; python mini/sheet.py v3/r/$2_h front front34 side back
