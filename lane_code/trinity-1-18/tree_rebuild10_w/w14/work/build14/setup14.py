from pathlib import Path
import json,hashlib,shutil
L=Path(__file__).resolve().parents[2];B=L/'work/build14';T=L/'work/tree_r1';I=B/'inputs';I.mkdir(exist_ok=True)
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def local(v):
    if isinstance(v,dict):
        out={k:local(x) for k,x in v.items()}
        if 'path' in out and 'sha256' in out:
            for prefix in ('/scratch/jjyeung/orch_n30/tree_rebuild_w/w13/','/scratch/jjyeung/orch_n30/tree_rebuild_w/w12/'):
                if out['path'].startswith(prefix):
                    p=L/out['path'][len(prefix):]
                    if p.is_file() and sha(p)==out['sha256']:out['path']=str(p)
        return out
    if isinstance(v,list):return [local(x) for x in v]
    return v
card=L/'work/n1fix2/inputs/mix.json';v=json.loads(card.read_text());v['weight_scale']=0.04;save(card,v);save(L/'out/MIX_R1.json',v)
for path in [L/'work/n1fix2/inputs/config.json',I/'kit_config.json']:
    source=path if path.exists() else L/'work/build13/inputs/kit_config.json'
    cfg=local(json.loads(source.read_text()))
    cfg['camera_overrides']={'weight_focal':2.0,'weight_scale':0.04}
    cfg['r1_training'].update(weight_scale=0.04,scale_weight_basis='Bound lineage pose receipt weight_scale=0.04; config and card must agree.',mix={'path':str(card),'sha256':sha(card)})
    save(path,cfg)
for name in ('test13.py','kits13.py','packet13.py','packet_inputs13.py','package13.py','compare13.py','delivery13.py'):
    s=(L/'work/build13'/name).read_text().replace('work/build13','work/build14').replace("f'tree_rebuild_b13_","f'tree_rebuild_b14_")
    if name=='delivery13.py':
        s=s.replace("extra=L/'work/build14'","extra=L/'work/build13'\nfor p in extra.rglob('*'):\n    if p.is_file() and not p.is_symlink() and not set(p.relative_to(extra).parts)&{'mutant','frozen','kits'} and p.suffix in ('.py','.sh','.json','.md') and p.stat().st_size<30_000_000:members.append(p)\nextra=L/'work/build14'")
    (B/name.replace('13','14')).write_text(s)
s=(B/'test14.py').read_text().replace('B13_PROOF','B14_PROOF').replace("['tests.test_r1_build13']","['tests.test_r1_build14']")
(B/'test14.py').write_text(s)
save(B/'INPUTS.json',{'card':sha(card),'config':sha(I/'kit_config.json'),'scale':0.04})
(B/'STATUS.md').write_text('# Build 14 status\n\nScale weight binds 0.04 in config and card. Effective comparison and milestone receipt edits are implemented; tests pending. Opener keep/reset remains a real compared mismatch. GO=false.\n')
