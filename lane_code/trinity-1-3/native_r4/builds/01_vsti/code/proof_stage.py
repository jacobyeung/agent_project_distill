"""Prepare the isolated original-input namespace for the historical equality check."""
import argparse
from pathlib import Path
import sys
from adapter import *
from venue import extract,FSW,AP,SJ

def prepare(root,assets_path,original_family,original_code,objects,reference,request,returned):
    root=Path(root);root.mkdir(parents=True,exist_ok=False);objects=Path(objects)
    family=load(original_family);assets=load(assets_path);used=0;original=load(request)
    for filename in ('code_c8r.tar','metadata_e10fbb95487f3baf.tar','geometry_8c58df1547371bdb.tar','masks_4984fac22d84e8c5.tar','frames.tar'):
        source=Path(original_code) if filename=='code_c8r.tar' else objects/filename
        target=root/'original'
        if filename=='frames.tar':
            target=root/'original/sj'/Path(original['frames_root']).relative_to(SJ)
        used+=extract(source,target,8000000000-used)
    run_root=Path(original['grounding']['geometry_manifest']['path']).parents[2]
    destination=root/'original/sj'/run_root.relative_to(SJ)
    used+=extract(returned,destination,8000000000-used,include=lambda n:n.startswith('native/geometry/'))
    assets['base_bindings']=[(str(root/'original/sj'),SJ),(str(root/'original/fsw'),FSW)]+[v for v in assets.get('base_bindings',[]) if v[1]!=FSW]
    # Restore the large export and base as explicit read-only mounts.
    assets['base_bindings'].append((assets['export_root'],assets['export_logical']))
    inputs=root/'inputs';inputs.mkdir()
    (inputs/'REFERENCE.json').write_bytes(Path(reference).read_bytes())
    (inputs/'REQUEST.json').write_bytes(Path(request).read_bytes())
    original=load(request)
    spec=dict(config=original['config'],artifact=original['artifact'],data_receipt=original['data_receipt'],
              tree=assets['tree_logical'],device='cuda:0',proof_core=SJ+'/orch_cd/evalx/work/milestone')
    dump(inputs/'SPEC.json',spec);assets['inputs']=str(inputs)
    dump(root/'ASSETS.json',assets);return assets

def main():
    p=argparse.ArgumentParser()
    for k in ('root','assets','family','code','objects','reference','request','returned'):p.add_argument('--'+k,required=True)
    a=p.parse_args();prepare(a.root,a.assets,a.family,a.code,a.objects,a.reference,a.request,a.returned)
if __name__=='__main__':main()
