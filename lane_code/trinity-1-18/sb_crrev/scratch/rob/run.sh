#!/bin/bash
# Run callrate.py on each robustness fixture; print exit code, status, error and summary head.
S=/scratch/jjyeung/orch_n30/sb_callrate
R=/scratch/jjyeung/orch_n30/sb_crrev/scratch/rob
PY=/scratch/jjyeung/envs/planner_local_v1/bin/python
O=$S/in/cont_ops/work/r1route/out3
P=$S/in/cont_ops16/work/c15/r1route/out3s
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
cd $S
run() {
  name=$1; shift
  $PY -B callrate.py --input-root in --out $R/out/$name --summary "$@" > $R/out_$name.stdout 2> $R/out_$name.stderr
  code=$?
  st=$($PY -B -c "import json;d=json.load(open('$R/out/$name/callrate.json'));print(d['status'],'|',d.get('error'),'|',d.get('population_error'))" 2>&1)
  echo "### $name exit=$code status=$st"
  head -n ${LINES_SHOWN:-8} $R/out_$name.stdout
}
case "${1:-all}" in
all)
run t0  --a in/cont_ops/work/r1route/out3/A4/ret --a-step 200
run t1  --a $R/t1/ret --a-step 200
run t1b --a $R/t1/ret --a-step 400
run t2  --a $R/t2/ret --a-step 200
run t2b --a $R/t2b/ret --a-step 200
run t2c --a $R/t2c/ret --a-step 200
run t2d --a $R/t2d/ret --a-step 200
run t2e --a $R/t2e/ret --a-step 200
run t2f --a $R/t2f/ret --a-step 200
run t3  --a $R/t3/f00dfeed1234/ret --a-step 200
run t3b --a $R/t3b/ret --a-step 200
run t3c --a in/cont_ops/work/r1route/out3/A4/ret --a-step 200 --a-package $P/B
run t4  --a in/cont_ops/work/r1route/out3/A4/ret --a-step 200 --b in/cont_ops/work/r1route/out3/B5/ret --b-step 200
;;
esac
