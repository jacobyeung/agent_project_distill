from pathlib import Path
import sys,json,hashlib,inspect
W=Path(__file__).resolve().parents[1];B=W/'work/base';sys.path.insert(0,str(B))
from student_pilot import tower_read
missing=not (B/'student_pilot/scale_donor.py').exists()
no_binding='scale_donor' not in inspect.signature(tower_read.apply_tower).parameters
assert missing and no_binding
result=dict(input_sha256={str(B/'student_pilot/tower_read.py'):hashlib.sha256((B/'student_pilot/tower_read.py').read_bytes()).hexdigest(),str(W/'out/TREE_FILES.sha256'):hashlib.sha256((W/'out/TREE_FILES.sha256').read_bytes()).hexdigest(),str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},status='NOT_APPLICABLE_ON_BASE',donor_module_absent=missing,tower_donor_argument_absent=no_binding,command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/base_negative.py')
(W/'out/BASE_NEGATIVE.json').write_text(json.dumps(result,indent=2)+'\n')
print(result['status'])
