"""Reseal an authenticated H parent for its exact unfinished subset; no submission."""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
from build_support import read_tar, write_tar
from build_h_base import make_batch, added, jd
from make_items_remainder_h import select, remaining_ids
from return_tools_h import require, read, TYPES, canonical, package_info

HERE=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()

def timing(rows,m,plan):
    means={};observed={}
    for k in TYPES:
        values=[r['seconds'] for r in rows.values() if r['type']==k]
        require(all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) and x>0 for x in values),'Invalid parent timing')
        if values:means[k]=sum(values)/len(values);observed[k]=len(values)
    require(bool(means),'Parent has no timing observations')
    fallback=max(means.values())
    rates={k:means.get(k,fallback) for k in TYPES}
    expected=sum(m['per_type'].get(k,0)*rates[k] for k in TYPES)
    budget=int(math.ceil(expected*1.25+1800))
    required=budget+plan['stop_margin']
    seconds=min(14400,int(math.ceil(required/300.0))*300)
    return dict(per_type_seconds=rates,observed=observed,unobserved_rule='maximum observed type mean',
        expected_item_seconds=expected,margin=1.25,load_overhead_seconds=1800,
        stop_margin_seconds=plan['stop_margin'],required_seconds=required,budget_gpu_seconds=budget,
        walltime='%02d:%02d:%02d'%(seconds//3600,seconds%3600//60,seconds%60),budget_fits=required<=seconds)

def build(parent,archive,exit_path,receipt,stage,items=None):
    stage=Path(stage);stage.mkdir(parents=True,exist_ok=False)
    spec=dict(package=str(parent),archive=str(archive),exit=str(exit_path),receipt=str(receipt))
    m,rows,meta,info=select(spec,stage/'parent_return')
    if items:require(read(items)==m,'Edited subset differs from authenticated partial')
    saved=stage/'parent_publication';saved.mkdir()
    for key,name in [('archive','0.tgz'),('exit','EXIT.json'),('receipt','RETURN_RECEIPT.json')]:
        (saved/name).write_bytes(Path(spec[key]).read_bytes())
        spec[key]=str((saved/name).resolve())
    from fetch_validation import validate_exit, validate_receipt
    validate_exit(meta['publication'],spec['archive'],info['plan'],meta['publication']['token'])
    validate_receipt(read(spec['receipt']),meta['publication'],spec['exit'],spec['archive'],info['plan'],meta['publication']['token'])
    spec['package']=str(Path(parent).resolve())
    parent=Path(parent);plan=copy.deepcopy(info['plan_value']);pf=dict(info['payload'])
    fullraw=pf['items/HELDOUT_CAMERA_ITEMS.json']
    pf['items/H_FULL.json']=fullraw
    pf['items/HELDOUT_CAMERA_ITEMS.json']=jd(m)
    # The generic manifest validator admits this distinct set name. All evaluator,
    # native tasks, twins, serving code and settings remain byte-identical.
    counts=tuple(m['per_type'].get(k,0) for k in TYPES)+(0,0)
    active=[i for i,n in enumerate(counts) if n];schedule=tuple((0,i) for i in active)
    op=(parent/'a/6.py').read_text()
    for old,new in [('COUNTS=(300,300,300,0,0)','COUNTS='+repr(counts)),
                    ('SCHEDULE=((0,0),(0,1),(0,2))','SCHEDULE='+repr(schedule)),
                    ('types=[0,1,2]','types='+repr(active)),('expected=900','expected='+str(m['count'])),
                    ('((0,900),)',repr(((0,m['count']),)))]:
        require(old in op,'Unrecognized parent operator: '+old);op=op.replace(old,new)
    # Keep the same conservative 52-capture memory bound and CPU guard.
    token='d'+os.urandom(6).hex();plan['token']=token
    tm=timing(rows,m,plan);plan['budget_gpu_seconds']=tm['budget_gpu_seconds']
    plan['remainder']=dict(m['remainder'],counts=counts,schedule=schedule,settings_sha256=canonical(meta['settings']))
    for n,b in pf.items():
        if n!='9.json':plan['payload_pins'][n]=dict(bytes=len(b),sha256=sha(b))
    pf['9.json']=jd(plan)
    names=['0.json','0.tgz','3.py','BATCH.sh','CONFIG.json','INPUTS.example.json','PACKAGE.json','SUBMIT.cmd','a/0.json','a/1.json','a/4.py','a/5.py','a/6.py','a/7.py','a/export.json']
    nf={n:(parent/n).read_bytes() for n in names}
    nf['a/1.json']=jd({'pending':True});nf['a/export.json']=jd({'pending':True})
    nf['a/6.py']=op.encode();nf['0.tgz']=write_tar([added(n,pf[n]) for n in sorted(pf)])
    nf['3.py']=nf['3.py'].replace(b'04:00:00',tm['walltime'].encode())
    nf['SUBMIT.cmd']=nf['SUBMIT.cmd'].replace(b'04:00:00',tm['walltime'].encode())
    pub=read(parent/'0.json');oldpub=(parent/'0.json').read_bytes()
    pub.update(token=token,payload_bytes=len(nf['0.tgz']),payload_sha256=sha(nf['0.tgz']),plan_sha256=canonical(plan))
    nf['0.json']=nf['CONFIG.json']=jd(pub)
    nf['BATCH.sh']=make_batch(nf['BATCH.sh'],info['token'],token,oldpub,nf['0.json'],(parent/'a/6.py').read_bytes(),nf['a/6.py'])
    pk=read(parent/'PACKAGE.json');pk['token']=token;pk['files']={n:sha(nf[n]) for n in pk['files']};nf['PACKAGE.json']=jd(pk)
    delivery=write_tar([added(n,nf[n]) for n in names])
    with (stage/'1.tgz').open('xb') as f:f.write(delivery)
    k=Path(os.environ.get('KROOT','/project/community/jjyeung/okh7'))
    report=dict(token=token,package=str(k/('a15_cot_ap'+token)),parent=str(parent.resolve()),
        delivery_dir=str(stage.resolve()),delivery_sha256=sha(delivery),delivery_bytes=len(delivery),
        payload_sha256=pub['payload_sha256'],plan_sha256=pub['plan_sha256'],items_sha256=sha(jd(m)),
        export_binding=info['export_binding'],serving_pins=plan['serving_pins'],walltime=tm['walltime'],timing=tm,
        counts=counts,schedule=schedule,partial=spec,settings=meta['settings'],
        binding_sha256=sha(jd(info['binding'])),operator_sha256=sha(nf['a/6.py']))
    (stage/'BUILD.json').write_bytes(jd({'H':report}));(stage/'binding.json').write_bytes(jd(info['binding']))
    (stage/'REMAINING_IDS.json').write_bytes(jd(remaining_ids(m)))
    (stage/'items.json').write_bytes(jd(m));(stage/'PARENT_SPEC.json').write_bytes(jd(spec))
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('parent','archive','exit','receipt','stage'):p.add_argument('--'+n,required=True)
    p.add_argument('--items');a=p.parse_args()
    r=build(a.parent,a.archive,a.exit,a.receipt,a.stage,a.items)
    print(json.dumps({k:r[k] for k in ('package','walltime','counts','timing')},sort_keys=True))
if __name__=='__main__':main()
