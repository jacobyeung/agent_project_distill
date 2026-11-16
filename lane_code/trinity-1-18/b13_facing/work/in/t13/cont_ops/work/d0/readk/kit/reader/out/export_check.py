"""Read-only export authentication. Never stages or copies full model weights."""
import argparse
import json
from pathlib import Path
import re
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def member(root,name):
    if not isinstance(name,str) or Path(name).name!=name: raise ValueError('Unsafe member')
    p=local(root/name)
    if p.parent!=root.resolve(): raise ValueError('Member escapes export')
    return p

def headers(path):
    with local(path).open('rb') as f:
        prefix=f.read(8)
        if len(prefix)!=8: raise ValueError('Short safetensors header')
        n=struct.unpack('<Q',prefix)[0]
        if not 2<=n<=16*1024*1024: raise ValueError('Invalid safetensors header length')
        h=json.loads(f.read(n))
    return {k:(v['dtype'],v['shape']) for k,v in h.items() if k!='__metadata__'}

def inventory(root,weight_map):
    result={}
    for name in sorted(set(weight_map.values())):
        for key,value in headers(member(root,name)).items():
            if key in result or weight_map.get(key)!=name: raise ValueError('Misplaced/duplicate tensor')
            result[key]=value
    if set(result)!=set(weight_map): raise ValueError('Index tensor inventory differs')
    return result

def check_export(path,expected_sha,base,step=None,scope='direct',receipt=None,header_only=False):
    path=local(path); base=local(base)
    if path.name!='artifact.json' or not re.fullmatch('[0-9a-f]{64}',expected_sha): raise ValueError('Require artifact.json and sha256')
    if sha(path)!=expected_sha: raise ValueError('Artifact hash differs')
    a=load(path)
    if a.get('schema')!='carrier-c1-artifact-v1': raise ValueError('Artifact schema differs')
    if step is not None and a.get('step')!=step: raise ValueError('Optimizer step differs')
    mp=path.parent/'full_weights/full_weights.json'
    if local(a['full_weights']['path'])!=mp.resolve(): raise ValueError('Full weights path is not local milestone; preserve original absolute mount')
    m=load(checked(a['full_weights']))
    if (m.get('schema'),m.get('dtype'))!=('full-ft-export-v1','bfloat16'): raise ValueError('Require full BF16 export')
    ip=member(mp.parent,m['index']['name'])
    if ip.name!='model.safetensors.index.json' or sha(ip)!=m['index']['sha256']: raise ValueError('Index hash differs')
    files=m['files']; names=[r['name'] for r in files]
    if not names or len(names)!=len(set(names)): raise ValueError('Empty/duplicate shard inventory')
    for r in files:
        p=member(mp.parent,r['name'])
        if p.suffix!='.safetensors' or p.stat().st_size!=r['bytes']: raise ValueError('Missing/wrong-sized shard')
        if not header_only and sha(p)!=r['sha256']: raise ValueError('Shard hash differs')
        if len(headers(p))!=r['tensors']: raise ValueError('Shard tensor count differs')
    wm=load(ip)['weight_map']
    if set(wm.values())!=set(names) or len(wm)!=m['tensor_count']: raise ValueError('Manifest/index disagree')
    actual=inventory(mp.parent,wm)
    bi=base/'model.safetensors.index.json'
    expected=inventory(base,load(bi)['weight_map']) if bi.exists() else headers(base/'model.safetensors')
    if (set(actual)-set(expected) or any(not k.startswith('mtp.') for k in set(expected)-set(actual))
        or any(actual[k][0]!='BF16' or expected[k][0] not in ('BF16','F32') or actual[k][1]!=expected[k][1]
               for k in actual.keys() & expected.keys())):
        raise ValueError('Export/native tensor names, dtypes or shapes differ')
    result=dict(scope=scope,status='HEADER_ONLY_NOT_VERIFIED' if header_only else 'VERIFIED',
                artifact=pin(path),step=a.get('step'),tensor_count=len(actual),bytes=sum(r['bytes'] for r in files))
    if scope=='routed':
        if receipt is None: raise ValueError('Routed read requires the admitted training receipt')
        install_tree()
        from evalpath.runtime import check_init_spec
        result['init_spec']=check_init_spec(load(receipt),pin(path))
        # Loader enforces the trained tensor fingerprint and exact coverage on device.
        if 'heads' not in a: raise ValueError('Routed export lacks heads')
        checked(a['heads'])
        result['first_minute']='runtime.load_model must authenticate and load every trained group'
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('export','sha256','base','output'): p.add_argument('--'+k,required=True)
    p.add_argument('--step',type=int); p.add_argument('--scope',choices=['direct','routed'],default='direct')
    p.add_argument('--receipt'); p.add_argument('--header-only',action='store_true')
    a=p.parse_args(); r=check_export(a.export,a.sha256,a.base,a.step,a.scope,a.receipt,a.header_only)
    dump(a.output,r); print(json.dumps(r))
if __name__=='__main__': main()
