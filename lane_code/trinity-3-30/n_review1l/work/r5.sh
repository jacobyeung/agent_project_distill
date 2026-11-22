set -e
L=/scratch/jjyeung/orch_n30/n_review1l
NEW=db42866fd9e8d0090276686527e8ebd8837ab2a9401609d81039b8784187f034
mkdir -p $L/w24z12b/work/tree_r1c2
tar xf $L/in/t_db42866fd9e8d009.tar -C $L/w24z12b/work/tree_r1c2
cd $L/w24z14b/out
sed -i "s|^TREE = BASE / 'work/tree_r1c'$|TREE = BASE / 'work/tree_r1c2'|; s|^SEAL = '02fd9a95ebd9719c596b39ac80e5247b92c1d6673d6cc2f4956c70b902718041'|SEAL = '$NEW'|" admit_test.py
sed -n 14,18p admit_test.py
printf '{\n  "tree_sha256": "%s",\n  "files": 945\n}\n' $NEW > $L/w24z12b/out/TREE_SEAL.json; cat $L/w24z12b/out/TREE_SEAL.json
cd $L/w24z12b/work/tree_r1c2 && /scratch/jjyeung/envs/p1cpu/bin/python -I -c "
import sys; sys.path.insert(0,'.')
from student_pilot import p3_provenance as p
from student_pilot.source_seal import inventory
from pathlib import Path
f=inventory(Path('.').resolve()); print('files',len(f),'seal',p.digest(f)); print(f['student_pilot/r1_training.py'][:8], f['student_pilot/carrier_c1_run.py'][:8])"
