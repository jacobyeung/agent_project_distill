import copy, hashlib, json, sys, types, tarfile, tempfile
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1eval_repin'); R=Path('/scratch/jjyeung/orch_n30/review_h1eval/work')
sys.path.insert(0,str(R/'new'))
from orchard_h10.job import check_inputs, verify_config
cfg={**json.loads((R/'new/9.json').read_text()),**json.loads((W/'out/package/0.json').read_text())}; verify_config(cfg)
assert cfg['logical']=='/scratch/jjyeung/b01ec87a6f29b'
base=json.loads((W/'in/prod_pkg/a/1.json').read_text())
E=json.loads((W/'out/export_544.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
def run(name, inp_mut=None, exp_mut=None, expect=None, raw_override=None):
    pkg=Path(tempfile.mkdtemp(dir=R/'t')); (pkg/'a').mkdir()
    e=copy.deepcopy(E)
    if exp_mut: exp_mut(e)
    raw=json.dumps(e).encode(); (pkg/'a/export.json').write_bytes(raw)
    inp=copy.deepcopy(base); inp['export_pin']=dict(path='a/export.json',sha256=sha(raw),bytes=len(raw))
    if raw_override is not None: (pkg/'a/export.json').write_bytes(raw_override)
    if inp_mut: inp_mut(inp)
    try: check_inputs(inp,cfg,package=pkg); msg='ADMITTED'
    except Exception as x: msg=f'{type(x).__name__}: {x}'
    ok=expect in msg; print('PASS' if ok else 'FAIL',name,'->',msg[:120]); return ok
f=lambda k,key,val:(lambda i:i['files'][k].update({key:val}))
r=[]
r.append(run('544 pins admit production a/1.json + export_pin',expect='ADMITTED'))
for k in ('artifact','heads','full_weights'):
    r.append(run(f'{k} declared sha differs',f(k,'sha256','a'*64),expect='Export pin differs: '+k))
    r.append(run(f'{k} declared bytes differs',f(k,'bytes',base['files'][k]['bytes']+1),expect='Export pin differs: '+k))
    r.append(run(f'{k} pin sha differs',exp_mut=lambda e,k=k:e[k].update(sha256='b'*64),expect='Export pin differs: '+k))
    r.append(run(f'{k} pin bytes differs',exp_mut=lambda e,k=k:e[k].update(bytes=e[k]['bytes']+1),expect='Export pin differs: '+k))
r.append(run('member directory differs',exp_mut=lambda e:e.update(member_directory='m100'),expect='Export member path differs'))
r.append(run('member dir traversal',exp_mut=lambda e:e.update(member_directory='../m544'),expect='canonical'))
r.append(run('missing export_pin',lambda i:i.pop('export_pin'),expect='KeyError'))
r.append(run('pin file tampered',raw_override=b'{}',expect='Export pin file differs'))
r.append(run('pin path not a/export.json',lambda i:i['export_pin'].update(path='a/x.json'),expect='Require a/export.json'))
r.append(run('step bool',exp_mut=lambda e:e.update(step=True),expect='nonnegative integer step'))
r.append(run('step missing',exp_mut=lambda e:e.pop('step'),expect='nonnegative integer step'))
r.append(run('lineage missing',exp_mut=lambda e:e.pop('lineage'),expect='SFT/RL'))
r.append(run('prep receipt missing',exp_mut=lambda e:e['preparation'].pop('receipt'),expect='Preparation keys differ'))
r.append(run('prep sha malformed',exp_mut=lambda e:e['preparation']['config'].update(sha256='x'),expect='Invalid export pin'))
r.append(run('prep paths collide',exp_mut=lambda e:e['preparation']['config'].update(path='p0/receipt.json'),expect='distinct'))
r.append(run('prep relative source_path',exp_mut=lambda e:e['preparation']['config'].update(source_path='rel/c.json'),expect='source path'))
r.append(run('camera types admit',lambda i:i.update(types=['camera_displacement','camera_rotation','camera_movement_direction']),expect='ADMITTED'))
r.append(run('logical root destination changed',lambda i:i['archives'][0].update(destination='sj/bf94a7976a7e9/d'),expect='stable data root'))
print('ALL PASS' if all(r) else 'SOME FAIL',sum(r),'/',len(r))
