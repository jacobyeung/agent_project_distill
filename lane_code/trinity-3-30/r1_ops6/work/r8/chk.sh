#!/bin/bash
# r1_ops8: local-only check of monitor outputs (no Orchard call)
M=/scratch/jjyeung/orch_n30/r1_ops6/work/mon; R=/scratch/jjyeung/orch_n30/r1_ops6/work/r7/m400
echo "now $(date -u +%T) node_last@$(head -1 $M/node_last.txt) pool@$(sed -n 1p $M/last.txt)"
grep '^STEP' $M/node_last.txt | tail -1 | cut -c1-60
python3 -c "import json;d=json.load(open('$M/node_early.json'));print('early',d['verdict'],'problems',d['problems'][-3:],'warn',d.get('warnings',[])[-3:])"
grep -E 'srun rc|early rc' $M/node_last.txt | tr '\n' ' '; echo
grep -E '^172660' $M/last.txt | head -2
echo "err_last: $(grep '^\[2026' $M/last.txt | tail -1 | cut -c1-40)"
grep -v '"step": 201' $M/node_last.txt | grep -o '"wall": [0-9]*' | awk '{if($2>300)print "SLOW",$0}' | tail -3
ls $R 2>/dev/null | tr '\n' ' '; echo; [ -e $R/alarm ] && tail -2 $R/alarm
df -BG --output=avail /scratch | tail -1
