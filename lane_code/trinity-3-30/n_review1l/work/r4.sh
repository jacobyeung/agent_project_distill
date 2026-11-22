set -e
L=/scratch/jjyeung/orch_n30/n_review1l
O=/scratch/jjyeung/orch_n30/tree_rebuild10_w
mkdir -p $L/w24z14b $L/w24z12b/work
cp -a $O/w24z14/out $L/w24z14b/
mkdir -p $L/w24z14b/work
cp -a $O/w24z14/work/build24m4z14 $L/w24z14b/work/ 2>/dev/null || echo "no build dir copy"
cp -a $O/w24z12/out $L/w24z12b/
mkdir -p $L/w24z12b/work/tree_r1c
tar xf $L/in/t_02fd9a95ebd9719c.tar -C $L/w24z12b/work/tree_r1c 2>/dev/null || tar xzf $L/in/t_02fd9a95ebd9719c.tar -C $L/w24z12b/work/tree_r1c
cd $L/w24z14b/out
sed -i "s|^J = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14')|J = Path('$L/w24z14b')|; s|^BASE = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12')|BASE = Path('$L/w24z12b')|; s|^SEAL = '9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b'|SEAL = '02fd9a95ebd9719c596b39ac80e5247b92c1d6673d6cc2f4956c70b902718041'|" admit_test.py
sed -i "s|^J=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14$|J=$L/w24z14b|" admit_test.sh
sed -n 14,18p admit_test.py; grep -n '^J=' admit_test.sh
cd $L/w24z12b/work/tree_r1c && /scratch/jjyeung/envs/p1cpu/bin/python -I -c "
import sys; sys.path.insert(0,'.')
from student_pilot import p3_provenance as p
from student_pilot.source_seal import inventory
from pathlib import Path
f=inventory(Path('.').resolve()); print('files',len(f),'seal',p.digest(f)); print('r1_training', f['student_pilot/r1_training.py'])"
du -sh $L; df -h /scratch | tail -1
