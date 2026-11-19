#!/bin/bash
# cont_ops19: post-process routed A at step 400. env: J=<job> [NAME=A10b TOK=dc76460c3a164 SKIPFETCH=1]
# fetch on Orchard, pull package (no a/e), unpack into r1route/out3/$NAME, relink out4s/A, score (score_r5_400), dist_gate (p; sets a, c), callrate, calling/non-calling split, corpus ingest
set -uo pipefail; NAME=${NAME:-A10b}; TOK=${TOK:-dc76460c3a164}; J=${J:?}; PKG=a15_cot_ap$TOK
W=/scratch/jjyeung/orch_n30/cont_ops19/work; R=/scratch/jjyeung/orch_n30/cont_ops/work/r1route; PY=/scratch/jjyeung/envs/p1cpu/bin/python
O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh; D=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/dist_diag
RET=$TOK$(printf '%08x' $J); OUT=$W/post_$NAME; mkdir -p $OUT; export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
if [ -z "${SKIPFETCH:-}" ]; then
  timeout 300 bash $O 'bash -s' < $W/o_fetch_${NAME}.sh > $OUT/fetch.out 2>&1 || { echo FETCH_FAILED; tail $OUT/fetch.out; exit 2; }
  timeout 300 bash $O "tar cf - -C /project/community/jjyeung/okh7 --exclude=$PKG/a/e $PKG" > $W/${NAME}_pkg.tar || { echo PULL_FAILED; exit 2; }
  mkdir $R/out3/$NAME && cd $R/out3/$NAME && tar xf $W/${NAME}_pkg.tar && mv $PKG package && mkdir src && tar xzf package/0.tgz -C src && cp package/a/6.py tower_sequence.py && cp ../A4/unpack_return.py ../A4/fetch_return.py . || exit 3
  cmp tower_sequence.py ../A4/tower_sequence.py || { echo OPERATOR_DIFFERS; exit 3; }
  $PY -B unpack_return.py --archive package/a/f/0.tgz --exit package/a/f/EXIT.json --out ret --return-token $RET > $OUT/unpack.out 2>&1 || { cat $OUT/unpack.out; exit 3; }
fi
cd $R/out4s; ln -sfn ../../out3/$NAME/src A/src; ln -sfn ../../out3/$NAME/package A/package; cp ../out3/$NAME/tower_sequence.py A/
$PY - <<'PYEOF'
import json
r=json.load(open('A/READ_PLAN.json')); pub=json.load(open('A/package/0.json')); r['token']=pub['token']; r['plan_sha256']=pub['plan_sha256']
json.dump(r,open('A/READ_PLAN.json','w'),indent=2,sort_keys=True)
PYEOF
cat $R/out3/$NAME/ret/SUMMARY.json | head -c 300; echo
echo "== score_r5_400 (A + B10)"; $PY -B score_r5_400.py --a ../out3/$NAME/ret --b ../out3/B10/ret --out $OUT/scoresAB 2>&1 | tail -14
echo "== dist_gate (rule p, coverage + split: sets a, c)"; $PY -B $D/dist_gate.py --score-dir . --ret ../out3/$NAME/ret --package A --step 400 --rule p --coverage $D/COVERAGE.json --split $D/SPLIT_V2.json --out $OUT/GATE_A400.json 2>&1 | tail -30
echo "== callrate (sb_callrate_v3)"; (cd /scratch/jjyeung/orch_n30/cont_ops18/callrate && $PY -B callrate.py --a $R/out3/$NAME/ret --a-step 400 --a-package $R/out4s/A --baseline-root $R/out3/bases --out $OUT/callrate --summary ${CRFLAGS:-} 2>&1 | tail -30)
echo "== distance MRA by calling / non-calling"; $PY -B - $R/out3/$NAME/ret <<'PYEOF'
import sys,json; ret=sys.argv[1]; sys.argv=['x']; sys.path.insert(0,'.')
import score_r5_400 as S
from h1eval import scorers
a,items,_,_=S.load(ret,S.O/'A',0,400,'candidates_argmax')
bd,_,_,_=S.load(S.BASE/'b1/work/ret',S.BASE/'b1',1,544,'candidates_argmax')
keys=[k for k in a if items[k]['question_type']=='object_abs_distance']
for name,ks in (('calling',[k for k in keys if scorers.records(a[k]['output'])]),('non-calling',[k for k in keys if not scorers.records(a[k]['output'])])):
    m,_=S.metrics(a,items,ks); mb,_=S.metrics(bd,items,ks); r=S.compare(a,bd,items,ks,'')
    print(name,'n',len(ks),'MRA400 %.2f'%(100*(m['score'] or 0)),'MRA544 same items %.2f'%(100*(mb['score'] or 0)),'paired',r['paired']['value'],r['paired']['ci95'],'capped',m['capped'])
PYEOF
echo "== step 200 reference (A4 + B5, out3s/scoresAB/scores.txt)"; cat $R/out3s/scoresAB/scores.txt | cut -c1-260
echo "== corpus (run after writing nothing else; RESULT path = the event you will post):"
echo "cd /scratch/jjyeung/orch_n30/corpus && timeout 1800 bash tool/add_read.sh $R/out3/$NAME/ret 6ed2c7aa_s400_devS1_routed_$NAME dev-S1-routed routed $J 'R1 C-prime step-400 routed read A (dev-S1 636)' <RESULT path> --inputs $R/out3/$NAME"
