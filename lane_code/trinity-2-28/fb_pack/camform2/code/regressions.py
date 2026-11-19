from pathlib import Path
import sys, os, json, hashlib, unittest, importlib.util
ROOT=Path(__file__).resolve().parents[1];label=sys.argv[1]
tree=ROOT.parent/'camform/work/new' if label=='before' else ROOT/'work/new'
tmp=ROOT/'work'/('regressions_'+label);tmp.mkdir(exist_ok=True)
os.environ['TMPDIR']=str(tmp)
import tempfile;tempfile.tempdir=str(tmp)
sys.path.insert(0,str(tree));sys.dont_write_bytecode=True
p=ROOT/'work/new/tests/test_r1_camera_trace_form2.py'
spec=importlib.util.spec_from_file_location('camera_review_regressions',p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs={str(x):sha(x) for x in [Path(__file__),p,ROOT/'out/SETUP.json',*sorted((tree/'student_pilot').glob('*.py')),tree/'configs/r1_camera_trace_form_v1.json',tree/'tests/test_r1_camera_trace_form.py']}
(ROOT/'out'/('REGRESSIONS_'+label+'.json')).write_text(json.dumps(dict(command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/regressions.py '+label,input_sha256=inputs,tests=result.testsRun,failures=[(t.id(),s) for t,s in result.failures],errors=[(t.id(),s) for t,s in result.errors],success=result.wasSuccessful()),indent=2)+'\n')
