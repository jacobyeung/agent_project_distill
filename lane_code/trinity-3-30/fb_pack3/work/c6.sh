F=/scratch/jjyeung/orch_n30/fb_pack; C=$F/combo; PY=/scratch/jjyeung/envs/p1cpu/bin/python
cd $C && [ -d Rt ] || cp -a R Rt
for t in tests/test_r1_patch_a2.py tests/test_r1_subset.py tests/test_scale_donor.py tests/test_r1_camera_trace_form.py tests/test_r1_camera_trace_form2.py; do cp X/$t Rt/$t; done
cat > $C/seal.py <<'P'
import sys; from pathlib import Path
root=Path(sys.argv[1]); sys.path.insert(0,str(root))
from student_pilot import source_seal, p3_provenance
inv=source_seal.inventory(root); print(sys.argv[1], len(inv), p3_provenance.digest(inv))
P
for d in R X; do (cd $C/$d && $PY -B $C/seal.py $C/$d 2>&1 | tail -1); done
T="tests/test_r1_patch_a2.py tests/test_r1_subset.py tests/test_scale_donor.py tests/test_r1_camera_trace_form.py tests/test_r1_camera_trace_form2.py"
(cd $C/Rt && OMP_NUM_THREADS=8 PYTHONPATH=. timeout 900 nice -n 10 $PY -B -m pytest -q -p no:cacheprovider $T > $C/before.log 2>&1; echo "before rc=$?"; tail -3 $C/before.log)
(cd $C/X && OMP_NUM_THREADS=8 PYTHONPATH=. timeout 900 nice -n 10 $PY -B -m pytest -q -p no:cacheprovider $T tests/test_host24l4t.py tests/test_host24l4s.py > $C/after.log 2>&1; echo "after rc=$?"; tail -3 $C/after.log)
(cd $C/R && OMP_NUM_THREADS=8 PYTHONPATH=. timeout 600 nice -n 10 $PY -B -m pytest -q -p no:cacheprovider tests/test_host24l4t.py tests/test_host24l4s.py > $C/R_host.log 2>&1; echo "R host rc=$?"; tail -2 $C/R_host.log)
