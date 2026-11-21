"""Fresh-process import provenance and inherited package admission, CPU only."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE))
import build_depth as BD
import json
import subprocess
import tempfile
sys.path.insert(0,str(BD.GB/'gpkg'))
import import_smoke as S
root=Path(tempfile.mkdtemp(dir=HERE.parent/'r1_fixtures_old',prefix='import_'))
BD.B.extract((HERE/'out/delivery.tgz').read_bytes(),root/'package')
BD.B.extract((root/'package/0.tgz').read_bytes(),root/'p')
results=[]
inventory=r'''
import hashlib
from student_pilot.g3t_online import VENDOR, vendor_digest
from student_pilot.c1r_ref import source_import
from student_pilot.tower_read import SOURCE_SHA256
assert vendor_digest()==SOURCE_SHA256
source_import(VENDOR)
inventory=[]
for file in sorted(VENDOR.rglob('*.py')):
    name=file.relative_to(VENDOR).as_posix()[:-3].replace('/','.')
    if name.endswith('.__init__'):name=name[:-9]
    module=importlib.import_module(name)
    physical=Path(module.__file__)
    assert physical.is_relative_to(p)
    assert physical.read_bytes()==file.read_bytes()
    inventory.append(dict(module=name,path=str(physical.relative_to(p)),sha256=hashlib.sha256(physical.read_bytes()).hexdigest()))
assert len(inventory)==26
for name in ('g.w','g.m','g.t','g.d','orchard_h10.s','orchard_h10.e','orchard_h10.budget',
             'student_pilot._tower_native','student_pilot.carrier_c1_decode'):
    module=importlib.import_module(name);physical=Path(module.__file__)
    assert physical.is_relative_to(p)
    inventory.append(dict(module=name,path=str(physical.relative_to(p)),sha256=hashlib.sha256(physical.read_bytes()).hexdigest()))
print(json.dumps(dict(gpu_path_import_inventory=inventory,vendor_files=26,weights_loaded=False,gpu_executed=False)))
'''
for code,tail in [(S.CHILD,['fixed']),(S.OPERATOR,[])]:
    if tail:
        code=code.replace("import torch", "import l\nl.install(p)\nimport torch")
        code=code.replace("w.assert_reader_root(p/'b')",inventory+"\nw.assert_reader_root(p/'b')")
    p=subprocess.run([sys.executable,'-I','-s','-B','-c',code,str(root/'p'),str(root/'package'),*tail],
        cwd=HERE,env=os.environ.copy(),text=True,capture_output=True,timeout=60)
    results.append(dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
info=json.loads((HERE/'out/BUILD.json').read_text())
assert BD.B.sha((HERE/'out/delivery.tgz').read_bytes())==info['delivery_sha256']
(HERE/'out/IMPORT_CHECK.json').write_text(json.dumps(dict(passed=all(x['returncode']==0 for x in results),checks=results,
    delivery_sha256=info['delivery_sha256'],delivery_bytes=info['delivery_bytes']),indent=2)+'\n')
print(json.dumps(dict(passed=all(x['returncode']==0 for x in results),returncodes=[x['returncode'] for x in results])))
raise SystemExit(any(x['returncode'] for x in results))
