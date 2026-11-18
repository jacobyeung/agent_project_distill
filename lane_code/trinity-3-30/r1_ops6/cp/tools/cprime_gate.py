"""Strict C4-to-Cprime authorization; embedded in the sealed submit gate."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re

BASE = '6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74'
BASE_CONFIG_SHA = '2152828974490944a1713f5a539e87211f80179f0b5f9254ea9966fc65788733'
GO = '1f3dff81041a58c45966e83535ec50182a616de94d036fcfcfa5142141862b7e'
B1 = 'caba6a5695781491036de5b3acdb20db2d42ab581e5775fec3fe07fbd2114aad'
REMOVE_PATH = '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/69d2930d/z.json'
RECEIPT = 'ed9aad679a1d9dd6302970dcb82d02d5b92fd6f3a53aede6bf219fca405f8d21'
LOG = '0658f1614ad94ff6141b66ba1523b37d2ea60d28c074929ac6e6f2307b1d58a3'
ALLOWED = ('/project/community/jjyeung/okh7/x_7f1589c1', '/project/community/jjyeung/okh7/x_7f1589c1.f172180')

def digest(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def identity(cfg):
    value={k:v for k,v in cfg.items() if k not in ('preparation','admission','authorization','milestone_gate')}
    if 'readout' in value:value['readout']={k:v for k,v in value['readout'].items() if k!='contiguous_clips'}
    if value.get('frame_layout')=='spread':value.pop('frame_layout')
    return digest(value)

def require(ok,why):
    if not ok:raise ValueError('canary_delta: '+why)

def pinned(path,expected):
    path=Path(path)
    require(not path.is_symlink(),'linked evidence '+str(path))
    raw=path.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==expected,'evidence SHA '+str(path))
    return raw

def validate_delta(base,cfg,ids):
    require(identity(base)==BASE,'base identity')
    expected=copy.deepcopy(base)
    expected['remove_files'].append(dict(path=REMOVE_PATH,sha256=B1))
    for name,cents in dict(counting=1046,totals=0,direction=3499).items():
        expected['type_mix']['streams']['vqa']['cells'][name]['cents']=cents
    expected['continuation']['rows']='rebind'
    token=digest(dict(base=BASE,remove_sha256=B1,mix=expected['type_mix'],rows='rebind'))[:8]
    run=hashlib.sha256(('run/'+token).encode()).hexdigest()[:8]
    for key in ('output','preparation_output'):
        expected[key]=base[key].replace('05b8ac69',run)
    require(cfg==expected,'config diff outside exact allow-list')
    require(ids['identity']==identity(cfg),'new identity')
    require(ids['run_key']==run and ids['job_name']=='a15_cot_ap'+run,'derived run/job')
    require(ids['bun']=='/project/community/jjyeung/okh7/i_'+token and ids['kh']=='/project/community/jjyeung/okh7/x_'+token,'derived bundle/kit')
    return run,token

def admission(k,b,go,ids):
    require(go.get('canary_delta') is True and go.get('canary') is not True,'mode')
    require(go.get('authority')=='sha256:'+GO,'GO SHA')
    require(os.environ.get('ADMISSION_JOB')=='172180','ADMISSION_JOB')
    evidence=os.environ.get('ADMISSION_KIT',ALLOWED[1])
    require(evidence in ALLOWED,'admission kit')
    old=Path(evidence);require(not old.is_symlink(),'linked admission kit')
    receipt=json.loads(pinned(old/'o/172180.proof.json',RECEIPT))
    log=pinned(old/'o/172180.proof.log',LOG).decode()
    require(receipt.get('job')=='172180' and receipt.get('config_identity')==BASE,'admission identity')
    for name in ('directory_modes','empty_root','resume_pointer','runtime_binaries','temporary_paths'):
        require(receipt.get('checks',{}).get(name,{}).get('status')=='PASS',name)
    pointer=receipt['checks']['resume_pointer']
    require(pointer.get('fixture') is True and pointer.get('step')==200 and pointer.get('run')=='673bc60f','resume pointer')
    require(re.findall(r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ \| exit rc=(\d+)$',log,re.M)==['0'],'admission exit')
    sums={}
    for line in pinned(old/'SHA256SUMS.txt',receipt['manifest_sha256']).decode().splitlines():
        sha,name=line.split('  ',1)
        require(name not in sums and not Path(name).is_absolute() and '..' not in Path(name).parts and re.fullmatch('[0-9a-f]{64}',sha),'manifest')
        sums[name]=sha
    def old_json(name):return json.loads(pinned(old/name,sums[name]))
    pin=receipt['config'];require(sums[pin['file']]==pin['sha256'],'base config pin')
    old_deployed=old_json(pin['file'])
    base=json.loads(pinned(b/'c4.json',BASE_CONFIG_SHA))
    old_expected=copy.deepcopy(base)
    if old_deployed.get('admission')!=base.get('admission'):
        old_json('k/review.json')
        old_expected['admission']=dict(path='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/review.json',sha256=sums['k/review.json'])
    require(old_deployed==old_expected,'base deployed config')
    launch=json.loads((k/'k/launch.json').read_text())
    deployed=json.loads(pinned(k/launch['config']['file'],launch['config']['sha256']))
    cfg=json.loads((b/'config.json').read_text())
    expected_deployed=copy.deepcopy(cfg)
    if deployed.get('admission')!=cfg.get('admission'):
        review=launch['review'];require(review['file']=='k/review.json','review path')
        pinned(k/review['file'],review['sha256'])
        expected_deployed['admission']=dict(path='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/review.json',sha256=review['sha256'])
    require(deployed==expected_deployed,'deployed config differs from sealed bundle')
    run,token=validate_delta(base,cfg,ids)
    old_launch=old_json('k/launch.json')
    require(digest(old_launch['in_job_admission'])==receipt['contract_sha256'],'base contract')
    contract=copy.deepcopy(old_launch['in_job_admission'])
    contract['directory']=cfg['output']+'/inputs'
    require(launch['in_job_admission']==contract and digest(contract)==ids['contract'],'new contract')
    old_cur=old_json('k/0.json')
    current=json.loads((k/'k/0.json').read_text())
    expected=json.loads(json.dumps(old_cur).replace('/i_7f1589c1/','/i_'+token+'/'))
    expected['extra'].append(dict(dest=REMOVE_PATH,parts=[ids['bun']+'/z.json'],sha256=B1))
    # Extra entries are a set of uniquely named staging destinations.
    def normalized(cur):
        cur=copy.deepcopy(cur);entries=cur['extra']
        require(len({e['dest'] for e in entries})==len(entries),'duplicate staging destination')
        cur['extra']=sorted(entries,key=lambda e:e['dest']);return cur
    require(normalized(current)==normalized(expected),'staged input hashes')
    old_stage=pinned(old/'b/c.sh',sums['b/c.sh'])
    require(hashlib.sha256(old_stage).hexdigest()==receipt['runtime_sha256']['b/c.sh'],'admission staging pin')
    require((k/'b/c.sh').read_bytes()==old_stage.replace(b'05b8ac69',run.encode()),'staging implementation')
    require(receipt['selection']==cfg['s1_routing']['selection'],'selection')
    store=json.loads(pinned(b/'d.json',cfg['streams']['vqa']['sha256']))
    extras={e['dest']:e['sha256'] for e in current['extra']}
    require(extras[store['database']['path']]==store['database']['sha256'],'store')
    unit=cfg['type_mix']['unit_rows'];require(extras[unit['path']]==unit['sha256'],'units')
    pinned(b/'z.json',B1)
    removals={}
    for line in log.splitlines():
        if line.startswith('{'):
            row=json.loads(line)
            if 'remove_list' in row:
                pin=row['remove_list']['file'];path=pin['path'];sha=pin['sha256']
                require(path not in removals or removals[path]==sha,'conflicting REMOVE log')
                removals[path]=sha
    require(removals=={p['path']:p['sha256'] for p in base['remove_files']},'base REMOVE hashes')
    return dict(canary_delta=True,authority='sha256:'+GO,admission_job='172180',
        base_config_identity=BASE,config_identity=ids['identity'],contract_sha256=ids['contract'],
        manifest_sha256=go['manifest_sha256'],wrapper_sha256=go['wrapper_sha256'],
        admission_receipt_sha256=RECEIPT,admission_log_sha256=LOG,admission_kit=str(old),
        job_name=ids['job_name'],submission='GATE_ACCEPTED')

def add_delta(submit):
    source=Path(__file__).read_text().split('\ndef add_delta(',1)[0]
    # Keep the existing PASS and canary blocks unchanged, including their predicates.
    start=submit.index("if go.get('canary') is True:")
    branch="if go.get('canary_delta') is True:\n"
    branch+='\n'.join(' '+line for line in source.splitlines())
    branch+="\n delta_record=admission(k,b,go,ids)\nelif go.get('canary') is True:"
    submit=submit[:start]+submit[start:].replace("if go.get('canary') is True:",branch,1)
    anchor="sys.path.insert(0,str(k/'b'));import a;a.main(k)\n"
    record="if go.get('canary_delta') is True:\n with (k/'o'/'canary_delta.json').open('x') as handle:\n  json.dump(delta_record,handle,sort_keys=True);handle.write('\\n')\n"
    return submit.replace(anchor,anchor+record)
