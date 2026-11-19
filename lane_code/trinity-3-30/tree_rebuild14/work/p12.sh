T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1; cd $T; date -u +%TZ
sed -n 38,56p student_pilot/carrier_c1_run.py </dev/null | cut -c1-200
sed -n 240,256p launch_r2/build.py </dev/null | cut -c1-200
grep -n "sessions" launch_r2/*.py launch_r2/b/* launch_s1/b/*.sh launch_s1/b/*.py 2>/dev/null </dev/null | head -20 | cut -c1-200
grep -n -E "^def |argv|sessions|token|credential|CLOUDSDK|metadata" launch_s1/b/gcsput.py </dev/null | head -30 | cut -c1-180
