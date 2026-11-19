from pathlib import Path
import sys,os,json,hashlib,unittest,tempfile
ROOT=Path(__file__).resolve().parents[1];tree=ROOT/'work/new';tmp=ROOT/'work/unit_tmp';tmp.mkdir(exist_ok=True)
os.environ['TMPDIR']=str(tmp);tempfile.tempdir=str(tmp);sys.path.insert(0,str(tree))
import torch;torch.set_num_threads(16)
suite=unittest.defaultTestLoader.loadTestsFromNames(['tests.test_r1_camera_trace_form','tests.test_r1_camera_trace_form2','tests.test_r1_subset'])
r=unittest.TextTestRunner(verbosity=2).run(suite)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs={str(p):sha(p) for p in [Path(__file__),ROOT/'out/SETUP.json',*sorted((tree/'student_pilot').glob('*.py')),*sorted((tree/'tests').glob('test_r1_camera_trace_form*.py')),tree/'tests/test_r1_subset.py',tree/'configs/r1_camera_trace_form_v1.json']}
(ROOT/'out/UNIT.json').write_text(json.dumps(dict(input_sha256=inputs,command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/unit.py',tests=r.testsRun,failures=[(t.id(),s) for t,s in r.failures],errors=[(t.id(),s) for t,s in r.errors],success=r.wasSuccessful()),indent=2)+'\n')
raise SystemExit(not r.wasSuccessful())
