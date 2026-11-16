"""Prepare local tensor stand-ins and the production worker's metadata contract."""
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import sys
import tarfile
B=Path(__file__).resolve().parents[2];W=B.parents[1]/'work';K=B/'out/guard_kit'
sys.path[:0]=[str(K),str(W/'from113/work/np226'),str(W/'from113/work/pyextra')]
from guard_core import read,write,sha,digest
import closure
from transport import regular_tar

def rawjson(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def tiny_export(artifact,dest):
    import torch
    dest=Path(dest);step=artifact['step'];root=dest/('m'+str(step));weights=root/'full_weights';weights.mkdir(parents=True)
    # The CPU model boundary never loads tensors. The unchanged export checker still
    # checks an actual BF16 safetensors shard against a tiny base tensor inventory.
    header=rawjson({'w':{'dtype':'BF16','shape':[1],'data_offsets':[0,2]}})
    raw=struct.pack('<Q',len(header))+header+b'\0\0'
    (weights/'model.safetensors').write_bytes(raw)
    index={'metadata':{'total_size':2},'weight_map':{'w':'model.safetensors'}}
    (weights/'model.safetensors.index.json').write_bytes(rawjson(index))
    manifest=dict(schema='full-ft-export-v1',dtype='bfloat16',tensor_count=1,
        index=dict(name='model.safetensors.index.json',sha256=sha(weights/'model.safetensors.index.json')),
        files=[dict(name='model.safetensors',bytes=len(raw),sha256=sha(weights/'model.safetensors'),tensors=1)])
    (weights/'full_weights.json').write_bytes(rawjson(manifest))
    torch.save({'fixture_tensor':torch.zeros(1)},root/'heads.pt')
    value=deepcopy(artifact)
    value['full_weights']['sha256']=sha(weights/'full_weights.json');value['heads']['sha256']=sha(root/'heads.pt')
    (root/'artifact.json').write_bytes(rawjson(value))
    archive=dest/'export.tar'
    with tarfile.open(archive,'x',dereference=True) as tar:
        for p in sorted(root.rglob('*')):
            if not p.is_file():continue
            m=tarfile.TarInfo(str(p.relative_to(dest)));m.size=p.stat().st_size;m.mode=0o644
            with p.open('rb') as s:tar.addfile(m,s)
    regular_tar(archive)
    base=dest/'base';base.mkdir();(base/'model.safetensors').write_bytes(raw)
    return dict(archive=dict(path=str(archive),bytes=archive.stat().st_size,sha256=sha(archive)),
                artifact=dict(path=str(root/'artifact.json'),sha256=sha(root/'artifact.json')),base=str(base),
                changed_fields=['full_weights.sha256','heads.sha256'],
                original_artifact_sha256=hashlib.sha256(rawjson(artifact)).hexdigest())

def prepare(dest):
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
    originals=closure.members(W/'d0closure/closure_359fcc3c.tar')
    candidate=read(W/'d0closure/x/runs/359fcc3c/m50/artifact.json')
    baseline_path=W/'from113/work/obj/m544_artifact.json';baseline=read(baseline_path)
    exports={name:tiny_export(a,dest/name) for name,a in [('proof',baseline),('candidate',candidate)]}
    files=deepcopy(originals);files['runs/359fcc3c/m50/artifact.json']=Path(exports['candidate']['artifact']['path']).read_bytes()
    metadata=dest/'metadata';metadata.mkdir()
    for name,raw in files.items():
        p=metadata/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    cfg=read(B/'out/inputs/BASELINE_CONFIG.json')
    cfg['worker']['artifact']['sha256']=exports['proof']['artifact']['sha256']
    data=read(metadata/'runs/359fcc3c/inputs/data_receipt.json')
    candidate_pin=dict(path=closure.ROOT+'runs/359fcc3c/m50/artifact.json',sha256=exports['candidate']['artifact']['sha256'])
    contract=dict(baseline=cfg,step=50,candidate=dict(artifact=candidate_pin,config=data['config'],
        data_receipt=dict(path=closure.ROOT+'runs/359fcc3c/inputs/data_receipt.json',sha256=sha(metadata/'runs/359fcc3c/inputs/data_receipt.json'))),
        reference=dict(path=str(B/'out/inputs/reference.json'),sha256=sha(B/'out/inputs/reference.json')),
        items=dict(path=str(B/'out/inputs/items.json'),sha256=sha(B/'out/inputs/items.json')),
        closure_root=str(metadata),closure_names=sorted(files),
        baseline_anchor=dict(path=str(baseline_path),sha256=sha(baseline_path)))
    write(dest/'WORKER.json',contract)
    production=dict(schema='g2-rehearsal-projection-v1',step=50,worker=contract,artifact_sha256=candidate_pin['sha256'],
        publication=dict(kind='gcs',prefix='gs://cmu-gpucloud-jjyeung/q8/8c9d2e74',credentials='/project/community/jjyeung/gcloud'))
    local=deepcopy(production);local['publication']=dict(kind='local',root=str(dest/'store'))
    write(dest/'PRODUCTION_CONFIG.json',production);write(dest/'CONFIG.json',local)
    checks=[]
    for role,original in [('candidate',candidate),('proof',baseline)]:
        actual=read(exports[role]['artifact']['path'])
        stripped=deepcopy(actual)
        for field in ('heads','full_weights'):stripped[field]['sha256']=original[field]['sha256']
        if stripped!=original:raise ValueError('CPU artifact changed a non-tensor field')
        checks.append(dict(role=role,changed_fields=exports[role]['changed_fields'],other_fields_equal=True,
            trained_groups_unchanged=True,original_sha256=sha(baseline_path) if role=='proof' else sha(W/'d0closure/x/runs/359fcc3c/m50/artifact.json')))
    proof=dict(status='PASS',fixture=True,config_differences=['publication'],
        production_config_sha256=sha(dest/'PRODUCTION_CONFIG.json'),local_config_sha256=sha(dest/'CONFIG.json'),
        artifact_boundaries=checks,assets=exports,
        limitations=['Tensor loading, prefill and generation use the C8r CPU boundary.',
                     'The production milestone selector is not exercised by the metadata fixture step.',
                     'Shared production assets use the supplied extracted read-only staging; large archives are not restaged.',
                     'The report must refuse the intentionally incomplete twenty-item result.'])
    write(dest/'PREPARATION.json',proof)
    return proof
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();prepare(Path(a.out).resolve())
