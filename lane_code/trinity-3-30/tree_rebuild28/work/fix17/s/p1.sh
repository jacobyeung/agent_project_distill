set -u; W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; hostname -s; date -u +%FT%TZ; df -h /scratch | tail -1
ls -d $W/w34 2>&1; ls $W/w33n; ls $W/w33n/n_go $W/w33n/n_go/k
cd $W/w33n/n_go && sha256sum k/j.json b/a.py b/pf.py k/t_e047002134f979bd.tar k/c.json k/n.json k/p.json k/y.json SHA256SUMS.txt BUILD.json
S=$W/w24z11b/work/build24m4x2/support.py; ls -l $S; grep -n -E '^def |^class |^    def ' $S | head -60
nice -n 10 timeout 120 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import sys,inspect; sys.path[:0]=['$W/w24z11b/work/build24m4x2','$W/w30f1/tree']
import support; from support import J, cap, reseal
print(inspect.getsource(cap)); print(inspect.getsource(reseal))
for n in ('load','seal','sha'): print(inspect.getsource(getattr(J,n)))
from launch_r1.build import verify; print(inspect.signature(verify))
from pathlib import Path; print('seal w33n', J.seal(Path('$W/w33n/n_go')))
import student_pilot.s1_admission as a; print('admit', inspect.signature(a.admit))
"
T=$W/w30f1/tree; grep -n 'admit(' $T/launch_r1/production_proof.py | head; grep -n 'frame_roots' $T/launch_r1/production_proof.py | head
which bwrap; bwrap --version; mkdir -p /scratch/jjyeung/tmp_f17 && bwrap --dev-bind / / --tmpfs /tmp --bind /scratch/jjyeung/tmp_f17 /tmp/q_t --bind /scratch/jjyeung/tmp_f17 /tmp/jjyeung/q_t stat -c '%d %i %n' /tmp/q_t /tmp/jjyeung/q_t; echo bw_rc=$?
cmp $W/w30f1/tree/launch_r1/build.py <(tar xOf $W/w33n/n_go/k/t_e047002134f979bd.tar launch_r1/build.py 2>/dev/null) && echo tree_build_same; tar tf $W/w33n/n_go/k/t_e047002134f979bd.tar | head -3
