#!/bin/sh
# quota spend: Kontext back/left/right views from the sculpt front (same image the CPU MV model uses)
S=/tmp/claude-0/-home-user-DASHBOARD/875c84ef-72ed-526b-a1dc-8eb9fffa8e2f/scratchpad
cd $S && FALLBACK=kontext timeout 900 research/hyvenv/bin/python v3/views.py v3/img/front_k21b.png v3/img/kv "$@"
