W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Z=$W/w24z10/out; date -u +%TZ; O=$W/work/tgcs_900004; test -e $O && { echo EXISTS; exit 1; }
sha256sum $Z/tgcs/*.py $Z/tgcs/run_tgcs.sh | cut -c1-90
timeout 500 bash $Z/tgcs/run_tgcs.sh 900004 /scratch/jjyeung/orch_n30/n_ops8_x/sess_900004.json $Z/kit_n $O < /dev/null; echo rc=$?
M='s#https?://[^ "]*#[URL]#g'; cd $O && { ls logs; sed -E "$M" RESULT.json | grep -v '"file"' | head -12; echo ==HTTP; sed -E "$M" logs/http.jsonl | sed -E 's/"time": ?[0-9.]+, ?//' | sort | uniq -c | sort -rn | head; echo ==GCERR; sed -E "$M" logs/gc.stderr | tail -5; echo ==COPERR; sed -E "$M" logs/copier.stderr | tail -5; }
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json;r=json.load(open('$O/RESULT.json'))
for x in r['receipts']: print('REC',x['name'],x['bytes'],x['sha256'],x['md5'],x['generation'])"
