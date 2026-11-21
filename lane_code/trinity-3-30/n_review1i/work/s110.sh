T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx; W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
date -u +%TZ
n=$(grep -n 'def host_environment' $T/launch_r1/entry.py < /dev/null | cut -d: -f1); sed -n "$((n-2)),$((n+45))p" $T/launch_r1/entry.py < /dev/null
echo "== r1_persisted scope/_paths/_proof"; grep -n "_paths\|_proof\|ContextVar\|def scope\|def proof_scope" $T/student_pilot/r1_persisted.py < /dev/null | head -20
echo "== kit"; cd $W/w26fix2/n_go 2>/dev/null && sha256sum SHA256SUMS.txt b/a.py b/fw.py BUILD.json < /dev/null; (cd $T && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import sys; sys.path.insert(0,'.'); from launch_r1.build import verify; print('verify',verify('$W/w26fix2/n_go'))" < /dev/null 2>&1 | tail -1)
diff -rq $W/w26fix/n_go $W/w26fix2/n_go < /dev/null
