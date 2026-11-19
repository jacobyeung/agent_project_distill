"""Authenticate H packages and published returns with Python 3.6 stdlib."""
import copy
import hashlib
import json
import re
import tarfile
from pathlib import Path, PurePosixPath
import score_base_h as base
from heldout_h import TYPES, PINS, ITEM_NAMES, digest as canonical, validate_payload
from fetch_validation import digest, validate_exit, validate_receipt

HERE = Path(__file__).resolve().parent

def read(p):
    return json.loads(Path(p).read_text())

def require(ok, message):
    if not ok:
        raise ValueError(message)

def binding_for(step):
    return read(HERE/('bind_H%d.json' % step))

def package_info(package):
    p=Path(package); pub=read(p/'0.json'); pk=read(p/'PACKAGE.json')
    require(pub==read(p/'CONFIG.json') and pk['token']==pub['token'], 'Package token/config differs')
    # Filled a/1.json and a/export.json are mutable protocol outputs.
    for n,h in pk['files'].items():
        if n not in ('a/1.json','a/export.json'):
            require(digest(p/n)==h, 'Delivery differs: '+n)
    require(digest(p/'0.tgz')==pub['payload_sha256'] and (p/'0.tgz').stat().st_size==pub['payload_bytes'],'Payload differs')
    with tarfile.open(str(p/'0.tgz')) as t:
        ms=t.getmembers(); require(len(ms)==len(set(m.name for m in ms)), 'Duplicate payload member')
        pf={m.name:t.extractfile(m).read() for m in ms if m.isfile()}
    plan=json.loads(pf['9.json'])
    require(canonical(plan)==pub['plan_sha256'] and plan['token']==pub['token'],'Plan differs')
    for n,pin in plan['payload_pins'].items():
        require(pin==dict(bytes=len(pf[n]),sha256=hashlib.sha256(pf[n]).hexdigest()),'Payload pin differs: '+n)
    binding=binding_for(plan['export_binding']['step'])
    require(all(binding[k]==v for k,v in plan['export_binding'].items()),'Export binding differs')
    base.EXPORTS[binding['step']]={k:binding[k] for k in ('run','step','member_directory','object','lineage','archive_sha256')}
    expected=base.package_identity(p)
    evaluator=canonical([(n[7:],hashlib.sha256(pf[n]).hexdigest()) for n in sorted(pf) if n.startswith('h1eval/') and '__pycache__' not in n and not n.endswith('.pyc')])
    require(evaluator==plan['serving_pins']['evaluator_code_sha256'],'Evaluator pin differs')
    for n in ITEM_NAMES[1:]:require(hashlib.sha256(pf['items/'+n]).hexdigest()==PINS[n], 'Frozen twins/tasks differ')
    raw=pf['items/'+ITEM_NAMES[0]];m=json.loads(raw)
    if 'remainder' not in m:
        require(hashlib.sha256(raw).hexdigest()==PINS[ITEM_NAMES[0]],'Full H manifest differs')
        validate_payload(m)
    else:
        full=json.loads(pf['items/H_FULL.json']);validate_payload(full)
        require(hashlib.sha256(pf['items/H_FULL.json']).hexdigest()==PINS[ITEM_NAMES[0]],'Full H pin differs')
        validate_subset(m,full)
    expected.update(token=pub['token'],manifest=m,items_sha256=hashlib.sha256(raw).hexdigest(),plan_value=plan,binding=binding,payload=pf)
    return expected

def subset(full, completed, provenance):
    require(len(completed)==len(set(completed)),'Duplicate completed IDs')
    require(set(completed)<=set(i['id'] for i in full['items']),'Unknown completed IDs')
    m=copy.deepcopy(full);m['name']='heldout_camera_remainder'
    m['items']=[i for i in full['items'] if i['id'] not in set(completed)]
    m['count']=len(m['items']);m['item_set_sha256']=canonical(m['items'])
    m['per_type']={k:sum(i['question_type']==k for i in m['items']) for k in TYPES if any(i['question_type']==k for i in m['items'])}
    m['r0_check']['checked']=m['count']
    m['remainder']=dict(provenance,completed_ids=completed)
    return m

def validate_subset(m,full):
    provenance=dict(m['remainder']);done=provenance.pop('completed_ids')
    require(m==subset(full,done,provenance) and 0<m['count']<900,'Edited remainder subset')

def unpack(archive, exit_path, receipt, package, dest, info=None):
    info=info or package_info(package);ex=read(exit_path);token=ex.get('token','')
    require(re.fullmatch(re.escape(info['token'])+'[0-9a-f]{8}',token) is not None,'Return token differs')
    require(str(ex.get('job'))==str(int(token[-8:],16)),'Return job differs')
    validate_exit(ex,archive,info['plan'],token)
    validate_receipt(read(receipt),ex,exit_path,archive,info['plan'],token)
    require(ex.get('archive_complete') is True and ex.get('conflicting_terminal_markers') is False,'Incomplete publication')
    dest=Path(dest)
    with tarfile.open(str(archive)) as t:
        members=t.getmembers();seen=set();total=0
        for m in members:
            n=PurePosixPath(m.name);total+=m.size
            require(m.isfile() and not n.is_absolute() and '..' not in n.parts and str(n)==m.name and m.name not in seen and total<512*1024**2,'Unsafe return member')
            seen.add(m.name)
        dest.mkdir(parents=True,exist_ok=False)
        for m in members:
            target=dest/m.name;target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as f:f.write(t.extractfile(m).read())
    rid=read(dest/'metadata/RETURN_ID.json')
    require(rid.get('token')==token and str(rid.get('job'))==str(ex['job']),'Inner return identity differs')
    return ex

def load(root,package,info=None):
    info=info or package_info(package);m=dict(info['manifest'],sealed_sha256=info['items_sha256'])
    rows,meta=base.load_return(root,package,m);root=Path(root)
    inputs=read(root/'metadata/INPUTS.json');outer=read(root/'metadata/IDENTITY.json')
    require(inputs==read(Path(package)/'a/1.json'),'Return inputs differ from package')
    require(outer['inputs']==canonical({k:v for k,v in inputs.items() if k!='resume'}),'Input identity differs')
    pin=root/'metadata/EXPORT_PIN.json'
    require(digest(pin)==inputs['export_pin']['sha256'] and pin.stat().st_size==inputs['export_pin']['bytes'],'Export pin input differs')
    require(read(pin)==read(Path(package)/'a/export.json'),'Export pin differs from package')
    journals=list((root/'metadata/reads').glob('*/metadata/journals/*/*/items.jsonl*'))
    active=[t for t,k in enumerate(TYPES) if any(i['question_type']==k for i in m['items'])]
    allowed={'metadata/reads/0/metadata/journals/%d/0/items.jsonl%s'%(t,s) for t in active for s in ('','.gz')}
    require(all(p.relative_to(root).as_posix() in allowed for p in journals),'Unexpected journal layout')
    summary=read(root/'SUMMARY.json')
    require(summary['expected']==m['count'] and summary['completed']==len(rows) and summary['complete']==(len(rows)==m['count']),'Summary differs from journals')
    settings=[]
    for p in journals:
        env=read(p.parent/'environment.json');settings.append(env['settings'])
        for key in ('export_sha256','artifact_manifest_sha256'):
            require(env['binding'][key]==meta['binding'][key],'Mixed serving identity')
    require(settings and all(v==settings[0] for v in settings),'Mixed settings')
    meta['settings']=settings[0];meta['export_binding']=info['export_binding']
    return rows,meta

def segment(spec,work):
    info=package_info(spec['package'])
    ex=unpack(spec['archive'],spec['exit'],spec['receipt'],spec['package'],work,info)
    rows,meta=load(work,spec['package'],info)
    require(ex['complete']==(len(rows)==info['manifest']['count']),'EXIT completion differs')
    meta['publication']=ex
    return rows,meta,info
