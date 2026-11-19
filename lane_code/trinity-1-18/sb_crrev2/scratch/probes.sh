#!/bin/bash
# Rerun the first review's probes (fixtures read-only) plus step-400/600 summary probes; outputs stay in this scratch.
S=/scratch/jjyeung/orch_n30/sb_callrate
R=/scratch/jjyeung/orch_n30/sb_crrev/scratch/rob
W=/scratch/jjyeung/orch_n30/sb_crrev2/scratch
X=$W/probes
ST=$W/steps
PY=/scratch/jjyeung/envs/planner_local_v1/bin/python
O=in/cont_ops/work/r1route/out3
P=$S/in/cont_ops16/work/c15/r1route/out3s
BASES=$S/$O/bases
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p $X
cd $S
run() {
  name=$1; shift
  timeout 900 $PY -B callrate.py --input-root in --out $X/$name "$@" > $X/$name.stdout 2> $X/$name.stderr
  code=$?
  st=$($PY -B -c "import json;d=json.load(open('$X/$name/callrate.json'));print(d['status'],'|',d.get('error'),'|',d.get('population_error'))" 2>&1)
  echo "### $name exit=$code status=$st"
  echo "--- stdout ($(wc -l < $X/$name.stdout) lines)"; head -n ${LINES_SHOWN:-6} $X/$name.stdout | cut -c1-260
  echo "--- stderr"; head -n 3 $X/$name.stderr | cut -c1-260
}
A4="--a $O/A4/ret --a-step 200"
# Original probes, unchanged arguments.
run t0  $A4 --summary
run t1  --a $R/t1/ret --a-step 200 --summary
run t1b --a $R/t1/ret --a-step 400 --summary
run t2  --a $R/t2/ret --a-step 200 --summary
run t2b --a $R/t2b/ret --a-step 200 --summary
run t2c --a $R/t2c/ret --a-step 200 --summary
run t2d --a $R/t2d/ret --a-step 200 --summary
run t2e --a $R/t2e/ret --a-step 200 --summary
run t2f --a $R/t2f/ret --a-step 200 --summary
run t3  --a $R/t3/f00dfeed1234/ret --a-step 200 --summary
run t3n --a $R/t3/f00dfeed1234/ret --a-step 200 --summary --original-root /nonexistent_prefix
run t3b --a $R/t3b/ret --a-step 200 --summary
run t3c $A4 --a-package $P/B --summary
run t4  $A4 --b $O/B5/ret --b-step 200 --summary
# Opt-in and B-side variants.
run t2_ap   --a $R/t2/ret --a-step 200 --summary --allow-partial
run t2_both --a $R/t2/ret --a-step 200 --summary --allow-partial --allow-subset
run t2_json --a $R/t2/ret --a-step 200
run t2_json_both --a $R/t2/ret --a-step 200 --allow-partial --allow-subset
run t2b_both --a $R/t2b/ret --a-step 200 --summary --allow-partial --allow-subset
run t4_sub  $A4 --b $O/B5/ret --b-step 200 --summary --allow-subset
run bpart   $A4 --b $R/t2/ret --b-step 200 --summary
run bpart_both $A4 --b $R/t2/ret --b-step 200 --summary --allow-partial --allow-subset
# Synthetic step 400/600 (README commands).
run s400     --a $ST/p400/ret --a-step 400 --a-package $ST/p400 --baseline-root $BASES --summary
run s600     --a $ST/p600/ret --a-step 600 --a-package $ST/p600 --baseline-root $BASES --summary
run s400p    --a $ST/p400partial/ret --a-step 400 --a-package $ST/p400partial --baseline-root $BASES --summary
run s400p_both --a $ST/p400partial/ret --a-step 400 --a-package $ST/p400partial --baseline-root $BASES --summary --allow-partial --allow-subset
run s400as600 --a $ST/p400/ret --a-step 600 --a-package $ST/p400 --baseline-root $BASES --summary
run s400v600 --a $ST/p400/ret --a-step 400 --a-package $ST/p400 --b $ST/p600/ret --b-step 600 --b-package $ST/p600 --baseline-root $BASES --summary
run s400v600p --a $ST/p400/ret --a-step 400 --a-package $ST/p400 --b $ST/p600partial/ret --b-step 600 --b-package $ST/p600partial --baseline-root $BASES --summary
run s400v600p_both --a $ST/p400/ret --a-step 400 --a-package $ST/p400 --b $ST/p600partial/ret --b-step 600 --b-package $ST/p600partial --baseline-root $BASES --summary --allow-partial --allow-subset
run s400vB5 --a $ST/p400/ret --a-step 400 --a-package $ST/p400 --b $O/B5/ret --b-step 200 --baseline-root $BASES --summary
run s400_strata --a $ST/p400/ret --a-step 400 --a-package $ST/p400 --baseline-root $BASES --summary --strata $S/examples/devs1_wording_strata.json
