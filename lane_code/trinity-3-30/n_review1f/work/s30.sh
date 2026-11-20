N=/scratch/jjyeung/orch_n30/n_review; R=$N/r1f; PY=/scratch/jjyeung/envs/p1cpu/bin/python; date -u +%TZ; cd $R || exit 1
cp $N/r1e/run_tests.py $R/run_tests.py; sha256sum run_tests.py; mkdir -p tout tout0
[ -d tcpt_t1 ] || cp -a tcpt tcpt_t1; [ -d tcpp_t2 ] || cp -a $N/r1e/tcpp tcpp_t2
L="test_r1_processor_compat.py test_host24j.py test_carrier_c1_run.py test_r1_build13.py test_r1_build16.py test_r1_build17.py test_r2_build9_cpu.py test_r2_data_path.py test_r2_refusals.py test_carrier_c1_cp2.py test_r2_build8.py"
cat > runt.sh <<EOT
cd $R/tcpt_t1 && timeout 1500 nice -n 10 env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 LANE_TEST_OUTPUT=$R/tout $PY -s -B $R/run_tests.py $R/tcpt_t1 $R/tests_tcpt.json $L > $R/tests_tcpt.log 2>&1
cd $R/tcpp_t2 && timeout 1500 nice -n 10 env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 LANE_TEST_OUTPUT=$R/tout0 $PY -s -B $R/run_tests.py $R/tcpp_t2 $R/tests_tcpp2.json $L > $R/tests_tcpp2.log 2>&1
echo done > $R/runt.done
EOT
tmux new-session -d -s nr1f_tests "bash $R/runt.sh"; sleep 2; tmux ls | grep nr1f
