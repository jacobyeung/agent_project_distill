set -euo pipefail
cd /scratch/jjyeung/orch_n30/cont_ops21_c/hrem
mkdir -p /scratch/jjyeung/orch_n30/cont_ops22_c/pre_fix && cp -p generate_scripts_hrem.py o_*_hrem.sh /scratch/jjyeung/orch_n30/cont_ops22_c/pre_fix/
/usr/bin/python3 - <<'PY'
from pathlib import Path
p=Path('generate_scripts_hrem.py');s=p.read_text()
old='export KROOT OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1\n\'\'\''
new='export KROOT OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1\n/usr/bin/python3 -B -c "import os,sys;s=os.statvfs(\'$KROOT\');f=s.f_bavail*s.f_frsize;print(\'FREE_GIB %.1f\'%(f/1024**3));sys.exit(0 if f>=300*1024**3 else 3)" || { echo "REFUSE: project filesystem under 300 GiB free"; exit 3; }\n\'\'\''
assert s.count(old)==1;p.write_text(s.replace(old,new))
PY
/scratch/jjyeung/envs/p1cpu/bin/python generate_scripts_hrem.py
/usr/bin/python3 -B verify_hrem.py | head -c 400; echo
head -16 o_place_fill_hrem.sh | tail -4
for t in test_hrem.py test_steps_hrem.py test_runtime_hrem.py; do echo "== $t"; head -5 $t | grep -iE 'usage|argv|argparse' ; done
grep -n 'add_argument\|sys.argv' test_*.py | head
