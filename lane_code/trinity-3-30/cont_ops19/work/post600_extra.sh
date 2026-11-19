#!/bin/bash
# cont_ops19: step-600 direct extras after post400.sh (TOK=a136f924ab1 STEP=600): relative count (139, numeric answers) at 200/400/600, counting split 2/3/4/5+ (both sets) at 400 and 600
W=/scratch/jjyeung/orch_n30/cont_ops19/work; C=/scratch/jjyeung/orch_n30/cont_ops/work; PY=/scratch/jjyeung/envs/p1cpu/bin/python; T=${TOK:-a136f924ab1}; B=$C/h1read7/kit/build/$T
echo "== relative count dev-S1 (200, 400, 600)"; python3 $W/relcount.py $C/h1read/kit/build/a8102c3207b/fetched/x/ITEMS.jsonl $C/h1read7/kit/build/a59a7bff4c4/fetched/x/ITEMS.jsonl $B/fetched/x/ITEMS.jsonl
echo "== counting split 2/3/4/5+ (600)"; cd $C/h1read7 && $PY -B $W/split5.py --x $B/fetched/x --label R1m600 --out $B/SPLIT5_R1m600.json | grep 'counting'
echo "== counting split 2/3/4/5+ (400, reference)"; grep -h 'counting' $W/SPLIT5_R1m400.txt 2>/dev/null || $PY -B $W/split5.py --x $C/h1read7/kit/build/a59a7bff4c4/fetched/x --label R1m400 --out /dev/null | grep counting
echo "== relative size (600; 400 was -4.00 [-9.55,+1.03], 200 -1.33)"; cat $B/RELSIZE_m600.json
