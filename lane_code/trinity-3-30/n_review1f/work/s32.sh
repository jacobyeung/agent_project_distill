R=/scratch/jjyeung/orch_n30/n_review/r1f; PY=/scratch/jjyeung/envs/p1cpu/bin/python; date -u +%TZ; cd $R; mkdir -p tmpa tmpb
L="test_r1_build16.py test_r1_build17.py test_r2_build9_cpu.py test_r2_data_path.py test_r2_refusals.py test_r2_build8.py"
cat > runt2.sh <<EOT
cd $R/tcpt_t1 && timeout 1500 nice -n 10 env TMPDIR=$R/tmpa PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 LANE_TEST_OUTPUT=$R/tout $PY -s -B $R/run_tests.py $R/tcpt_t1 $R/tests_tcpt_b.json $L > $R/tests_tcpt_b.log 2>&1
cd $R/tcpp_t2 && timeout 1500 nice -n 10 env TMPDIR=$R/tmpb PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 LANE_TEST_OUTPUT=$R/tout0 $PY -s -B $R/run_tests.py $R/tcpp_t2 $R/tests_tcpp2_b.json $L > $R/tests_tcpp2_b.log 2>&1
echo done > $R/runt2.done
EOT
tmux new-session -d -s nr1f_tests2 "bash $R/runt2.sh"
$PY - <<'PY'
import json
a=json.load(open('/scratch/jjyeung/orch_n30/n_review/r1f/tests_tcpt.json')); b=json.load(open('/scratch/jjyeung/orch_n30/n_review/r1f/tests_tcpp2.json'))
for k in a:
    fa=sorted(f[0] for f in a[k].get('failures',[])+a[k].get('errors',[])); fb=sorted(f[0] for f in b[k].get('failures',[])+b[k].get('errors',[]))
    print(k,'run',a[k].get('run'),b[k].get('run'),'fail',len(fa),len(fb),'same' if fa==fb else 'DIFF')
k='test_r1_build13.py'; print([ (f[0][:60], f[1][-300:]) for f in (a[k].get('failures',[])+a[k].get('errors',[]))[:2]])
k='test_carrier_c1_cp2.py'; print([ (f[0][:60], f[1][-300:]) for f in (a[k].get('failures',[])+a[k].get('errors',[]))[:1]])
PY
