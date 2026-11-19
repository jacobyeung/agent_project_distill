"""Verify and reconstruct H entirely from reviewer-visible evidence in memory."""
import ast
import base64
import gzip
import hashlib
import json
import math
from pathlib import Path
from build_support import read_tar,write_tar,bundle_of
from heldout_h import validate,digest,SCORER_NEW
HERE=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()

def reconstruct(step):
    ev=HERE/'evidence';source=b''.join((ev/'A4'/('1.tgz.part%d'%i)).read_bytes() for i in range(2))
    assert sha(source)=='dcff106800e96e871a57a58dbb33fe9923beefa575ac668ac1c8e66fd7113459'
    members=read_tar(source);old=dict((m.name,d) for m,d in members);pay=read_tar(old['0.tgz']);pf={m.name:d for m,d in pay}
    delta=read_tar((ev/('H%d/payload_delta.tgz'%step)).read_bytes());changed={m.name:d for m,d in delta};pf.update(changed)
    newpay=[(m,pf[m.name]) for m,d in pay]+[(m,d) for m,d in delta if m.name not in {n.name for n,_ in pay}]
    nf=dict(old);nf.update({m.name:d for m,d in read_tar((ev/('H%d/delivery_delta.tgz'%step)).read_bytes())});nf['0.tgz']=write_tar(newpay)
    report=json.loads((ev/('H%d/BUILD.json'%step)).read_text())['H'];delivery=write_tar([(m,nf[m.name]) for m,d in members])
    assert sha(delivery)==report['delivery_sha256']
    return old,nf,pf,report,delivery

def main():
    ev=HERE/'evidence';count=0
    for line in (ev/'INDEX.md').read_text().splitlines():
        if not line.startswith('| `'):continue
        f=line.split('|');p=ev/f[1].strip().strip('`')
        assert p.stat().st_size==int(f[2]) and sha(p.read_bytes())==f[3].strip().strip('`'),str(p)
        assert p.stat().st_size<5000000;count+=1
    results={}
    for step in (200,544):
        old,nf,pf,r,delivery=reconstruct(step);pub=json.loads(nf['0.json']);plan=json.loads(pf['9.json']);pk=json.loads(nf['PACKAGE.json'])
        assert sha(nf['0.tgz'])==r['payload_sha256']==pub['payload_sha256']
        assert sha(json.dumps(plan,sort_keys=True,separators=(',',':')).encode())==r['plan_sha256']==pub['plan_sha256']
        assert pk['token']==pub['token']==r['token']==plan['token']
        for n,h in pk['files'].items():assert sha(nf[n])==h,n
        for n,pin in plan['payload_pins'].items():assert pin==dict(bytes=len(pf[n]),sha256=sha(pf[n])),n
        assert validate(pf)==r['validation']
        assert sha(pf['h1eval/scorers.py'])==SCORER_NEW
        evaluator=digest([(n[len('h1eval/'):],sha(pf[n])) for n in sorted(pf) if n.startswith('h1eval/') and '__pycache__' not in n and not n.endswith('.pyc')])
        assert evaluator==plan['evaluator_code_sha256']==r['evaluator_code_sha256']
        assert plan['serving_pins']==r['serving_pins']
        original_pf={m.name:d for m,d in read_tar(old['0.tgz'])}
        for n,d in original_pf.items():
            if n.startswith(('b/','tree/','rows/','auth/')):assert pf[n]==d,n
        allowed={'9.json','h1eval/scorers.py','h1eval/items.py','h1eval/h10/parity_adapter.py','orchard_h10/build.py','orchard_h10/prepare.py'}
        assert {n for n in original_pf if original_pf[n]!=pf[n]}==allowed
        assert set(pf)-set(original_pf)=={'h1eval/heldout_h.py','items/HELDOUT_CAMERA_ITEMS.json','items/HELDOUT_CAMERA_TWINS.json','items/HELDOUT_NATIVE_TASKS.jsonl'}
        if step==200:
            assert nf['a/4.py']==old['a/4.py'] and plan['export_binding']==json.loads(original_pf['9.json'])['export_binding']
        bind=json.loads((HERE/('bind_H%d.json'%step)).read_text());assert sha((HERE/('bind_H%d.json'%step)).read_bytes())==r['binding_sha256']
        assert all(bind[k]==v for k,v in plan['export_binding'].items())
        assert (HERE/('bind_H%d.json'%step)).read_bytes()==(ev/('reference/bind_D%d.json'%step)).read_bytes()
        if step==544:
            prep=json.loads((ev/'reference/export_544.json').read_text())['preparation']
            assert bind['preparation_sha256']=={k:v['sha256'] for k,v in prep.items()}
        bundle={m.name:d for m,d in read_tar(bundle_of(nf['BATCH.sh'])[1])}
        assert bundle['0.json']==nf['0.json'] and bundle['7.py']==nf['a/6.py']
        assert nf['BATCH.sh'].count(b'trap fin EXIT')==1
        results[str(step)]=dict(delivery_sha256=sha(delivery),delivery_bytes=len(delivery),token=r['token'],evaluator_code_sha256=evaluator)
    timings=[]
    for spec in json.loads((ev/'SOURCES.json').read_text()):
        raw=gzip.decompress((ev/spec['evidence']).read_bytes());assert sha(raw)==spec['sha256'] and len(raw)==spec['source_bytes']
        timings.extend(json.loads(line)['seconds'] for line in raw.splitlines())
    timing=json.loads((HERE/'TIMING_H.json').read_text());assert len(timings)==450 and sum(timings)/450==timing['mean_seconds']
    assert math.ceil(1.3*sum(timings)/450*900+timing['load_overhead_seconds'])==11038
    assets=ast.literal_eval(next(l for l in (HERE/'o_build_H.sh').read_text().splitlines() if l.startswith('assets = ')).split('=',1)[1].strip())
    for n,spec in assets.items():
        raw=gzip.decompress(base64.b64decode(spec['data']));assert sha(raw)==spec['sha256']
        assert raw==(HERE/('build_h.py' if n=='b.py' else n)).read_bytes(),n
    old=ast.parse((ev/'reference/build_r10.py').read_text());new=ast.parse((HERE/'build_support.py').read_text())
    for name in ('read_tar','write_tar','replace_once','bundle_of','wrap_batch'):
        a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name==name);b=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name==name)
        assert ast.dump(a)==ast.dump(b),name
    for n in ('SCRIPT_RESULTS.json','SCORE_RESULTS.json','PLACE_RESULTS.json'):assert json.loads((ev/n).read_text())['passed'] is True
    print(json.dumps(dict(passed=True,evidence_self_contained=True,indexed_files=count,builds=results,budget_gpu_seconds=11038,with_stop_margin_seconds=12838),sort_keys=True,indent=2))
if __name__=='__main__':main()
