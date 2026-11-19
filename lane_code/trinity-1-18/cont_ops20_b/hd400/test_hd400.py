"""Offline step-400 identity, fill and normalized-difference checks (Python 3.6)."""
import argparse
import ast
import copy
import difflib
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
def dump(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def refused(fn):
    try:fn()
    except (ValueError,AssertionError,KeyError,FileNotFoundError):return
    raise AssertionError('Invalid input accepted')

def run(kind,stage400,stage544):
    folder=ROOT/('hcam' if kind=='H' else 'dbuild');sys.path.insert(0,str(folder))
    score=importlib.import_module('score_'+kind.lower())
    place=importlib.import_module('place_fill_'+kind.lower())
    from build_support import read_tar,write_tar,bundle_of
    work=Path(tempfile.mkdtemp(prefix=kind+'400_',dir=str(ROOT/'validation')))
    reports={step:read(stage/'BUILD.json')[kind] for step,stage in [(400,stage400),(544,stage544)]}
    paths={400:stage400/'BUILD.json',544:stage544/'BUILD.json'}
    b=read(folder/('bind_'+kind+'400.json'));origin=read(ROOT/'in/BIND400.json')
    assert all(b[k]==v for k,v in origin.items())
    assert b['parts']==[{k:p[k] for k in ('bytes','sha256')} for p in read(ROOT/'in/A10b_INPUTS.json')['archives'][0]['parts']]
    assert (ROOT/'in/m400.done').read_text().split()==[b['object'],str(b['archive_bytes']),b['archive_sha256']]
    rows={};roots={step:work/str(step) for step in (400,544)}
    if kind=='H':
        fixture=importlib.import_module('test_score_h')
        manifest,twins=score.manifest(folder/'in/HELDOUT_CAMERA_ITEMS.json',folder/'in/HELDOUT_CAMERA_TWINS.json')
        for step in (400,544):fixture.synthetic(roots[step],reports[step],manifest,twins,step==400)
        load=lambda step,package:score.load_return(roots[step],package,manifest)
    else:
        fixture=importlib.import_module('test_score_identity_d')
        items=folder/'evidence/items/dist580.json';manifest=read(items)
        for step in (400,544):
            settings=dict(stage1_select_rule='candidates_argmax',perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False,types=['object_abs_distance'])
            binding=dict(settings,arms=['tower'],modes=[{'name':'none'}],lineage='SFT',fixture=False,items_sha256=score.digest(items),item_set_sha256=manifest['item_set_sha256'],step=step,settings_sha256=score.canonical(settings))
            for k in score.SERVING_KEYS+('export_sha256','artifact_manifest_sha256'):binding[k]='1'*64
            env=roots[step]/'metadata/reads/0/metadata/journals/3/0/environment.json';dump(env,dict(settings=settings,binding=binding))
            item=manifest['items'][0]
            (env.parent/'items.jsonl').write_text(json.dumps(dict(id=item['id'],room_key=item['room_key'],arm='tower',mode='none',type='object_abs_distance',complete=True,output=dict(scores=dict(answer=.5))))+'\n')
            fixture.identity_files(roots[step],reports[step],binding['settings_sha256'])
        load=lambda step,package:score.load_return(roots[step],manifest,items,package)
    for step in (400,544):rows[step]=load(step,paths[step])[0]
    refused(lambda:load(544,paths[400]))
    pin=roots[400]/'metadata/EXPORT_PIN.json';original=pin.read_bytes()
    for key in ('run','step','member_directory','object','archive_sha256','config_sha256'):
        bad=json.loads(original);bad[key]='wrong';dump(pin,bad);refused(lambda:load(400,paths[400]));pin.write_bytes(original)
    bad=json.loads(original);bad['preparation']['config']['sha256']='0'*64;dump(pin,bad);refused(lambda:load(400,paths[400]));pin.write_bytes(original)
    # Check actual generated delivery members and payloads, including embedded batch code.
    deliveries={step:dict((m.name,d) for m,d in read_tar((Path(r['delivery_dir'])/'1.tgz').read_bytes())) for step,r in reports.items()}
    payloads={step:dict((m.name,d) for m,d in read_tar(d['0.tgz'])) for step,d in deliveries.items()}
    assert payloads[400].keys()==payloads[544].keys()
    assert [n for n in payloads[400] if payloads[400][n]!=payloads[544][n]]==['9.json']
    plans={step:json.loads(p['9.json']) for step,p in payloads.items()}
    for step in (400,544):
        assert plans[step]['export_binding']==reports[step]['export_binding']
        assert plans[step]['token']==reports[step]['token']
    normalized=[{k:v for k,v in plans[step].items() if k not in ('token','export_binding')} for step in (400,544)]
    assert normalized[0]==normalized[1]
    changed={n for n in deliveries[400] if deliveries[400][n]!=deliveries[544][n]}
    assert changed=={'0.json','CONFIG.json','PACKAGE.json','0.tgz','BATCH.sh','a/4.py'}
    for step,d in deliveries.items():
        pub=json.loads(d['0.json']);pk=json.loads(d['PACKAGE.json'])
        assert pub['payload_sha256']==sha(d['0.tgz']) and pub['payload_bytes']==len(d['0.tgz'])
        assert pub['plan_sha256']==sha(json.dumps(plans[step],sort_keys=True,separators=(',',':')).encode())
        assert all(sha(d[n])==v for n,v in pk['files'].items())
    def norm_batch(step):
        d=deliveries[step];bundle=dict((m.name,x) for m,x in read_tar(bundle_of(d['BATCH.sh'])[1]))
        assert bundle['0.json']==d['0.json'] and bundle['7.py']==d['a/6.py']
        text=re.sub(b'b=bytes.fromhex[^\n]+',b'b=bytes.fromhex(<verified bundle>)',d['BATCH.sh'])
        return text.replace(reports[step]['token'].encode(),b'<TOKEN>'),{k:v for k,v in bundle.items() if k!='0.json'}
    assert norm_batch(400)==norm_batch(544)
    def norm_fill(step):
        return re.sub(rb'^REVIEWED_(OBJECT|ARCHIVE_SHA256) = .*$',b'<EXPORT PIN>',deliveries[step]['a/4.py'],flags=re.M)
    assert norm_fill(400)==norm_fill(544)
    lines=['PASS: step 400 versus step 544; all package, plan and payload pins verified.\n',
           'Payload members: only 9.json differs (token and export_binding); all other bytes identical.\n',
           'Delivery changes: '+', '.join(sorted(changed))+'\n',
           'BATCH.sh: only token and verified embedded public descriptor differ.\n',
           'a/4.py: only REVIEWED_OBJECT and REVIEWED_ARCHIVE_SHA256 differ.\n',
           'Operator, items, settings, serving code, walltime and CPU/submit helpers unchanged.\n']
    for n in ('9.json',):lines.extend(difflib.unified_diff(json.dumps(plans[544],sort_keys=True,indent=2).splitlines(True),json.dumps(plans[400],sort_keys=True,indent=2).splitlines(True),'544/payload/'+n,'400/payload/'+n,n=2))
    (ROOT/('DIFF_'+kind+'400_VS_'+kind+'544.txt')).write_text(''.join(lines))
    # Execute the actual preflight branch without placing a package or opening Orchard paths.
    tree=ast.parse((folder/('place_fill_'+kind.lower()+'.py')).read_text());body=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run').body
    branch=next(n for n in body if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and isinstance(n.test.left,ast.Subscript))
    module=ast.parse('');module.body=[branch];code=compile(module,'<actual preflight>','exec')
    saved=dict(os.environ);os.environ['REUSE_PARTS_FROM']='synthetic';os.environ.pop('DONE_FROM',None)
    try:
        exec(code,dict(place.__dict__,binding=b))
        for bad in [dict(b,run='469ddece'),dict(b,done='/project/community/jjyeung/okh7/x_07ca49df/o/gcs_469ddece_m544.done')]:refused(lambda:exec(code,dict(place.__dict__,binding=bad)))
        os.environ['DONE_FROM']='wrong';refused(lambda:exec(code,dict(place.__dict__,binding=b)));os.environ.pop('DONE_FROM')
        os.environ.pop('REUSE_PARTS_FROM');refused(lambda:exec(code,dict(place.__dict__,binding=b)))
    finally:os.environ.clear();os.environ.update(saved)
    # CLI comparison exercises authentication on both returns.
    if kind=='H':
        argv=[sys.executable,'-B',str(folder/'score_h.py'),'--return',str(roots[400]),'--package',str(paths[400]),'--other-return',str(roots[544]),'--other-package',str(paths[544]),'--out',str(work/'comparison.json')]
    else:
        src=work/'src'
        for n,d in payloads[400].items():
            p=src/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(d)
        argv=[sys.executable,'-B',str(folder/'score_d.py'),str(items),'--src',str(src),'--return',str(roots[400]),'--package',str(paths[400]),'--compare',str(roots[544]),'--compare-package',str(paths[544]),'--out',str(work/'comparison.json')]
    with (work/'compare.log').open('w') as out:subprocess.run(argv,stdout=out,check=True)
    dump(work/'RESULTS.json',dict(passed=True,kind=kind,accepted400=True,rejected544as400=True,wrong_export_rejected=True,comparison400vs544=True,normalized_diff=True,receipt_path_refusals=True))
    print(str(work/'RESULTS.json'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['H','D']);p.add_argument('stage400',type=Path);p.add_argument('stage544',type=Path);a=p.parse_args();run(a.kind,a.stage400,a.stage544)
