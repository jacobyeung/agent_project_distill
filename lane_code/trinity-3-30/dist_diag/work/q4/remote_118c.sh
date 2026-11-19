#!/bin/bash
# dist_diag coverage rows (read-only): locate N's bound slices, s.json, validators; print one row of each slice.
set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
echo "== host $(hostname -s) $(date -u +%FT%TZ) df $(df -BG --output=avail /scratch | tail -1)"
ls -la $W | head -30
for d in $W/w16b/work/build16 $W/w16b/work/build16/inputs $W/w18/work $W/w19 $W/w19/work; do echo "== ls $d"; ls -la $d 2>&1 | head -40; done
echo "== find slices (maxdepth 7) in w16b/w18"
timeout 60 find $W/w16b $W/w19 -maxdepth 7 \( -name '*units*' -o -name '*recovery*' -o -name '*distance*' -o -name 's.json' \) -type f -printf '%s %p\n' 2>/dev/null | grep -v '/tests/\|\.py$\|/test_' | head -60
echo "== validators in tree (w16b)"
timeout 60 find $W/w16b -maxdepth 6 \( -name 'ground_rows.py' -o -name 's1_pool.py' -o -name 's1_routing.py' -o -name 'trace_grammar.py' -o -name 'carrier_c1_routing.py' \) -printf '%s %p\n' 2>/dev/null | head -20
echo "== done $(date -u +%FT%TZ)"
