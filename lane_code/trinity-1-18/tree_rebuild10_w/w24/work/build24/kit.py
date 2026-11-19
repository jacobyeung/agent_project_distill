import os
"""Build the two opaque kits from the build-22 VQA bindings."""
from pathlib import Path
import ast,base64,hashlib,json,shutil,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24';T=Path(os.environ.get('R2_TREE',L/'work/tree_r1'));B=L/'work/build22'
sys.path[:0]=[str(D),str(T),str(L/'work/build21')]
import joblib as J
from student_pilot.p3_provenance import digest,file_pin,source_files
from student_pilot.source_seal import inventory,archive,check_archive,create
from launch_r2.build import capsule_json

def cap(k,name,value):(k/name).write_bytes(capsule_json(value))
def retire(path,name):
    target=L/'attic/build24'/name;index=0
    while target.exists():
        index+=1;target=L/'attic/build24'/(name+'_'+str(index))
    path.rename(target)
def reseal(k):
    files={str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json')}
    (k/'SHA256SUMS.txt').write_text(''.join(f'{h}  {n}\n' for n,h in sorted(files.items())))
    record=J.load(k/'BUILD.json');record.update(GO=False,kit_sha256=J.seal(k));cap(k,'BUILD.json',record)
    return J.seal(k)

def main():
    import importlib.util
    path=L/'work/build24b/kit.py'
    spec=importlib.util.spec_from_file_location('kit24b_generator',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.main()
if __name__=='__main__':main()
