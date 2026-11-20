N=/scratch/jjyeung/orch_n30/n_review; R=$N/r1e; P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%TZ; cd $R || exit 1
cp /scratch/jjyeung/orch_n30/tr19_revC1/work/run_tests.py $R/run_tests.py; sha256sum run_tests.py
[ -d tcpp_t1 ] || cp -a tcpp tcpp_t1; mkdir -p tout
cd tcpp_t1 && timeout 900 nice -n 10 env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 LANE_TEST_OUTPUT=$R/tout $P -s -B $R/run_tests.py $R/tcpp_t1 $R/tests_cpp.json test_r1_processor_compat.py test_host24j.py test_carrier_c1_run.py 2>&1 | tail -20
sha256sum $R/tests_cpp.json
$P -c "import json;d=json.load(open('$R/tests_cpp.json'));[print(k,v['ok'],v.get('run'),[f[0] for f in v.get('failures',[])+v.get('errors',[])],v.get('import_error','')[:300]) for k,v in d.items()]"
