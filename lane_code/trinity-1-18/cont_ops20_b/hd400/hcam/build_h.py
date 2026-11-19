"""Build H from an authenticated A4 delivery. Python 3.6 stdlib; no placement."""
import argparse
import ast
import difflib
import hashlib
import json
import math
import os
import re
import tarfile
from pathlib import Path
from build_support import read_tar, write_tar, replace_once, bundle_of, wrap_batch, HEAD_OLD

from heldout_h import TYPES, ITEM_NAMES, PINS, SCORER_OLD, SCORER_NEW, validate, digest

HERE = Path(__file__).resolve().parent
KEYS = ('base_identity','config_sha256','frame_layout','lineage','member_directory',
        'object','preparation_sha256','run','step')
sha = lambda b: hashlib.sha256(b).hexdigest()
jd = lambda v: (json.dumps(v, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def change(raw, old, new):
    return replace_once(raw, old.encode(), new.encode(), old)


def operator(raw):
    text = raw.decode()
    for old,new in [('two isolated reads','one camera wording read'),
                    ('COUNTS=(150,150,150,150,36)','COUNTS=(300,300,300,0,0)'),
                    ('SCHEDULE=((0,3),(0,0),(0,1),(0,2),(0,4))','SCHEDULE=((0,0),(0,1),(0,2))'),
                    ('types=[3,0,1,2,4],expected=636','types=[0,1,2],expected=900'),
                    ('expected=636','expected=900'), ('((0,636),)', '((0,900),)')]:
        assert old in text, old
        text = text.replace(old,new)
    text = text.replace('captures=(84,)', 'captures=(52,)')
    text = text.replace(" base=Path(config['output']);settings=", " config['items']=str(Path(config['package'])/'items/HELDOUT_CAMERA_ITEMS.json')\n base=Path(config['output']);settings=")
    return text.encode()


def make_batch(raw, oldtoken, token, oldpub, pub, oldop, op):
    marker = b"/usr/bin/python3 -I -s -B - >>\"$L\" 2>&1 <<'A' &\n"
    if raw.startswith(b'#!/bin/bash\n#SBATCH --exclude=orchard-community-2\n'):
        body = raw.split(marker,1)[1].split(b'\nA\n',1)[0]
        unwrapped = HEAD_OLD.encode()+body+b'\nA\n'
        assert wrap_batch(unwrapped,oldtoken)==raw, 'Unrecognized existing EXIT trap'
        raw = unwrapped
    line,bundle = bundle_of(raw); out=[]
    for m,data in read_tar(bundle):
        if m.name=='0.json': assert data==oldpub;data=pub
        elif m.name=='7.py': assert data==oldop;data=op
        out.append((m,data))
    text=change(raw,line,'b=bytes.fromhex(%r)' % write_tar(out).hex())
    text=replace_once(text,oldtoken.encode(),token.encode(),'batch token')
    return wrap_batch(text,token)


def added(name,data):
    info=tarfile.TarInfo(name);info.mode=0o600;info.size=len(data)
    return info,data


def build(stage, source, source_sha, binding_path, timing_path, walltime):
    raw=source.read_bytes();assert sha(raw)==source_sha,'Source delivery SHA256 differs'
    members=read_tar(raw); files={m.name:d for m,d in members}
    assert len(files)==len(members)
    assert set(files)=={'0.json','0.tgz','3.py','BATCH.sh','CONFIG.json','INPUTS.example.json',
                        'PACKAGE.json','SUBMIT.cmd','a/0.json','a/1.json','a/4.py','a/5.py','a/6.py','a/7.py','a/export.json'}
    pk=json.loads(files['PACKAGE.json']);pub=json.loads(files['0.json'])
    assert files['0.json']==files['CONFIG.json']
    for n,h in pk['files'].items():assert sha(files[n])==h,n
    assert pub['token']==pk['token']=='d60a20ec01296'
    assert sha(files['0.tgz'])==pub['payload_sha256']
    pay=read_tar(files['0.tgz']);pf={m.name:d for m,d in pay};plan=json.loads(pf['9.json'])
    assert sha(json.dumps(plan,sort_keys=True,separators=(',',':')).encode())==pub['plan_sha256']
    for n,pin in plan['payload_pins'].items():assert pin==dict(bytes=len(pf[n]),sha256=sha(pf[n])),n
    for n in ITEM_NAMES:pf['items/'+n]=(HERE/'in'/n).read_bytes()
    itemraw=pf['items/HELDOUT_CAMERA_ITEMS.json']
    validation=validate(pf)
    checks=json.loads((HERE/'in/SCORER_PATCH/CHECKS.json').read_text())['input_sha256']
    assert SCORER_OLD in checks.values() and SCORER_NEW in checks.values()
    assert sha(pf['h1eval/scorers.py'])==SCORER_OLD
    patched=(HERE/'in/SCORER_PATCH/h1eval/scorers.py').read_bytes()
    assert sha(patched)==SCORER_NEW
    assert sha((HERE/'in/SCORER_PATCH/placement.patch').read_bytes())=='dcaffaaf48dc17672c62d0a3c9dceefb450e64a1f40225634b5627644bebf4cf'
    pf['h1eval/scorers.py']=patched
    pf['h1eval/heldout_h.py']=(HERE/'heldout_h.py').read_bytes()
    pf['h1eval/items.py']=change(pf['h1eval/items.py'], '    return m\n', "    if m['name']=='heldout_camera_wording':\n        from .heldout_h import validate_payload\n        validate_payload(m)\n    return m\n")
    pf['h1eval/h10/parity_adapter.py']=change(pf['h1eval/h10/parity_adapter.py'], "    if name=='r0dev_f32':", "    if name=='heldout_camera_wording' and not settings.get('tasks'):\n        raise ValueError('H requires explicit native tasks')\n    if name=='r0dev_f32':")
    pf['orchard_h10/build.py']=change(pf['orchard_h10/build.py'], "    add(K/'items/devs1_routed.json','items/devs1_routed.json')", "    add(K/'items/devs1_routed.json','items/devs1_routed.json')\n"+''.join("    add(K/'items/%s','items/%s')\n"%(n,n) for n in ITEM_NAMES))
    pf['orchard_h10/prepare.py']=change(pf['orchard_h10/prepare.py'], "    write(d/'settings.json',settings)", "    settings['tasks']=[str(p/'items/HELDOUT_NATIVE_TASKS.jsonl')]\n    settings.setdefault('item_sets',{})['heldout_camera_wording']=dict(tasks=settings['tasks'])\n    write(d/'settings.json',settings)")
    # Seal the same digest that h1eval.cli.code_hash() checks at launch and merge.
    evaluator=digest([(n[len('h1eval/'):],sha(pf[n])) for n in sorted(pf) if n.startswith('h1eval/') and '__pycache__' not in n and not n.endswith('.pyc')])
    pf['orchard_h10/prepare.py']=change(pf['orchard_h10/prepare.py'], "    settings['tasks']=", "    from h1eval.cli import code_hash\n    if code_hash()!=config['evaluator_code_sha256']:raise ValueError('H evaluator differs from build')\n    settings['tasks']=")
    binding=json.loads(binding_path.read_text());oldbinding=plan['export_binding']
    assert set(oldbinding)==set(KEYS)
    assert sum(p['bytes'] for p in binding['parts'])==binding['archive_bytes'] and len(binding['parts'])==4
    assert binding['base_identity']==oldbinding['base_identity']=='c202236235762e1c871ad0ccb60c8ee5ba337b9a'
    assert binding==json.loads((HERE/('bind_H%d.json'%binding['step'])).read_text())
    if binding['step']==200:assert {k:binding[k] for k in KEYS}==oldbinding
    else:assert (binding['step'],binding['run']) in ((544,'469ddece'),(400,'6ed2c7aa'))
    assert re.fullmatch(r'[0-9]{2}:[0-5][0-9]:[0-5][0-9]',walltime), 'Invalid WALLTIME'
    timing=json.loads(timing_path.read_text());assert timing['n']==450
    required=int(math.ceil(1.3*timing['mean_seconds']*900+timing['load_overhead_seconds']))
    wallseconds=sum(int(x)*v for x,v in zip(walltime.split(':'),(3600,60,1)))
    assert 0<wallseconds<=14400,'H walltime must be positive and at most 04:00:00'
    k=Path(os.environ.get('KROOT','/project/community/jjyeung/okh7'));k.mkdir(parents=True,exist_ok=True)
    token='d'+os.urandom(6).hex();assert not (k/('a15_cot_ap'+token)).exists()
    plan['token']=token;plan['budget_gpu_seconds']=required
    plan['export_binding']={key:binding[key] for key in KEYS}
    plan['evaluator_code_sha256']=evaluator
    plan['serving_pins']=dict(reader_sha256=digest([(n[len('b/e2e_reader/'):],sha(pf[n])) for n in sorted(pf) if n.startswith('b/e2e_reader/')]),
                  parity_code_sha256=digest([(n[len('b/parity_kit/'):],sha(pf[n])) for n in sorted(pf) if n.startswith('b/parity_kit/') and n.count('/')==2 and n.endswith('.py')]),
                  maker_sha256=sha(pf['h1eval/h10/parity_adapter.py']),evaluator_code_sha256=evaluator,expected_calls_sha256=sha(pf['rows/expected_calls.py']))
    for n in pf:
        if n!='9.json':plan['payload_pins'][n]=dict(bytes=len(pf[n]),sha256=sha(pf[n]))
    pf['9.json']=json.dumps(plan,sort_keys=True).encode()
    newpay=[(m,pf[m.name]) for m,d in pay]
    newpay += [added(n,pf[n]) for n in sorted(set(pf)-{m.name for m,d in pay})]
    nf=dict(files);nf['0.tgz']=write_tar(newpay)
    nf['a/6.py']=operator(files['a/6.py'])
    nf['a/5.py']=change(files['a/5.py'],
        "or settings['perception_memo_modules']!=['g3t']", 
        "or inputs.get('types')!=['camera_displacement', 'camera_rotation', 'camera_movement_direction'] or settings['perception_memo_modules']!=['g3t']")
    base=json.loads(files['a/0.json']);assert base['types']==['camera_displacement','camera_rotation','camera_movement_direction','object_abs_distance','room_size_estimation']
    base['types']=TYPES;nf['a/0.json']=jd(base)
    for name,value in [('REVIEWED_OBJECT',repr(binding['object'])),('REVIEWED_ARCHIVE_BYTES',str(binding['archive_bytes'])),('REVIEWED_ARCHIVE_SHA256',repr(binding['archive_sha256']))]:
        if binding['step']==200:continue
        matches=re.findall(r'^'+name+r' = .*$',nf['a/4.py'].decode(),re.M);assert len(matches)==1
        nf['a/4.py']=change(nf['a/4.py'],matches[0],name+' = '+value)
    # Accept exactly one GPU and the sealed walltime through the public entrypoint.
    guard=("if len(sys.argv)>1 and sys.argv[1] in ('check','submit'):\n"
           "    for flag,value in (('--gpus','1'),('--time',%r)):\n"
           "        matches=[i for i,x in enumerate(sys.argv) if x==flag or x.startswith(flag+'=')]\n"
           "        if not matches:sys.argv.extend([flag,value]);continue\n"
           "        if len(matches)!=1:raise ValueError('Duplicate '+flag)\n"
           "        i=matches[0];got=sys.argv[i].split('=',1)[1] if '=' in sys.argv[i] else sys.argv[i+1]\n"
           "        if got!=value:raise ValueError('H requires '+flag+' '+value)\n") % walltime
    nf['3.py']=change(nf['3.py'],"with tarfile.open(p/'0.tgz') as t:",guard+"with tarfile.open(p/'0.tgz') as t:")
    nf['SUBMIT.cmd']=change(change(nf['SUBMIT.cmd'],'${A_N:?Set 1 to 4}','${A_N:-1}'), '${A_T:?Set HH:MM:SS}', '${A_T:-'+walltime+'}')
    pub.update(token=token,payload_bytes=len(nf['0.tgz']),payload_sha256=sha(nf['0.tgz']),
               plan_sha256=sha(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()))
    nf['0.json']=nf['CONFIG.json']=jd(pub)
    nf['BATCH.sh']=make_batch(files['BATCH.sh'],pk['token'],token,files['0.json'],nf['0.json'],files['a/6.py'],nf['a/6.py'])
    pk['token']=token;pk['files']={n:sha(nf[n]) for n in pk['files']};nf['PACKAGE.json']=jd(pk)
    delivery=write_tar([(m,nf[m.name]) for m,d in members])
    # Verify sealed hashes and all immutable payload members, including the routed manifest.
    assert dict((m.name,d) for m,d in read_tar(delivery))==nf
    bundle=dict((m.name,d) for m,d in read_tar(bundle_of(nf['BATCH.sh'])[1]))
    assert bundle['0.json']==nf['0.json'] and bundle['7.py']==nf['a/6.py']
    assert pf['items/devs1_routed.json']==dict((m.name,d) for m,d in pay)['items/devs1_routed.json']
    for n,d in nf.items():
        if n not in ('0.tgz','BATCH.sh'):assert b'd60a20ec01296' not in d,n
    for n,d in pf.items():assert b'd60a20ec01296' not in d,n
    diff=[];changed={}
    def record(n,before,after):
        if before==after:return
        changed[n]=dict(before=sha(before),after=sha(after))
        if n=='0.tgz':return
        if n.startswith('payload/items/HELDOUT_'):
            diff.append('Added '+n+': sha256 '+sha(after)+'\n');return
        if n.endswith('.json'):
            before=jd(json.loads(before)) if before else b'';after=jd(json.loads(after))
        if n=='BATCH.sh':
            before=re.sub(b'b=bytes.fromhex[^\n]+',b'b=bytes.fromhex(<bundle>)',before)
            after=re.sub(b'b=bytes.fromhex[^\n]+',b'b=bytes.fromhex(<bundle>)',after)
        diff.extend(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),'A4/'+n,'H/'+n,n=2))
    for n in sorted(nf):record(n,files[n],nf[n])
    for n in sorted(pf):
        old=dict((m.name,d) for m,d in pay).get(n,b'')
        record('payload/'+n,old,pf[n])
    for n in ('0.json','7.py'):
        oldbundle=dict((m.name,d) for m,d in read_tar(bundle_of(files['BATCH.sh'])[1]))
        record('BATCH.sh/bundle/'+n,oldbundle[n],bundle[n])
    dest=k/('a15_cot_ap'+os.urandom(8).hex());dest.mkdir(mode=0o700)
    (dest/'1.tgz').write_bytes(delivery)
    report=dict(token=token,package=str(k/('a15_cot_ap'+token)),delivery_dir=str(dest),
                delivery_sha256=sha(delivery),delivery_bytes=len(delivery),payload_sha256=pub['payload_sha256'],
                plan_sha256=pub['plan_sha256'],source_sha256=source_sha,items_sha256=sha(itemraw),
                binding_sha256=sha(binding_path.read_bytes()),validation=validation,evaluator_code_sha256=evaluator,
                serving_pins=plan['serving_pins'],export_binding=plan['export_binding'],
                budget_gpu_seconds=required,walltime=walltime,timing=timing,
                budget_fits=required+plan['stop_margin']<=wallseconds,
                risk=('Conservative budget plus stop margin exceeds WALLTIME; return may be partial.' if required+plan['stop_margin']>wallseconds else None),
                changed_members=changed)
    stage.mkdir(parents=True,exist_ok=True)
    (stage/'BUILD.json').write_bytes(jd({'H':report}));(stage/'DIFF.txt').write_text(''.join(diff))
    print(json.dumps({k:report[k] for k in ('token','delivery_dir','delivery_sha256','walltime','budget_gpu_seconds','budget_fits')},sort_keys=True))
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('stage_dir','source_1tgz','source_sha256','binding_json'):p.add_argument(n)
    p.add_argument('--timing',default=str(HERE/'TIMING_H.json'))
    p.add_argument('--time',default='04:00:00')
    a=p.parse_args()
    build(Path(a.stage_dir),Path(a.source_1tgz),a.source_sha256,Path(a.binding_json),Path(a.timing),a.time)

if __name__=='__main__':main()
