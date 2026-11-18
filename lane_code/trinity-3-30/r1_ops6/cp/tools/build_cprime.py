"""Build Cprime from authenticated C4 bytes, without changing the sealed trainer."""
import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
import tarfile
from rebind import ROOT,load,write,sha,enc,diff
from cprime_gate import BASE,B1,REMOVE_PATH,digest,identity,validate_delta,add_delta

SNAP=Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_08f3a7b2')
A=Path('/scratch/jjyeung/orch_n30/r1_ops/work/snap_9dd2fbb7')
SOURCE=Path('/scratch/jjyeung/orch_n30/r1_ops6/cf/final_evidence/COUNT_FIX_REMOVE_B1.jsonl')
ARCHIVE_SHA='08f3a7b2ef2e1923ba77b464afcedbbe668a77a1915b4c32c0a815044ff7d9fd'

def config():
    base=load(SNAP/'out/config.json');assert identity(base)==BASE
    cfg=copy.deepcopy(base)
    cfg['remove_files'].append(dict(path=REMOVE_PATH,sha256=B1))
    for name,cents in dict(counting=1046,totals=0,direction=3499).items():
        cfg['type_mix']['streams']['vqa']['cells'][name]['cents']=cents
    cfg['continuation']['rows']='rebind'
    token=digest(dict(base=BASE,remove_sha256=B1,mix=cfg['type_mix'],rows='rebind'))[:8]
    run=hashlib.sha256(('run/'+token).encode()).hexdigest()[:8]
    for key in ('output','preparation_output'):cfg[key]=cfg[key].replace('05b8ac69',run)
    ids=dict(identity=identity(cfg),run_key=run,job_name='a15_cot_ap'+run,
        bun='/project/community/jjyeung/okh7/i_'+token,kh='/project/community/jjyeung/okh7/x_'+token)
    validate_delta(base,cfg,ids)
    from continuation import policy
    policy(cfg,load(A/'out/config.json'))
    binding=load(SNAP/'out/BINDING.json')
    binding.update(config_identity=ids['identity'],run_key=run,store_key=token,
        job_name=ids['job_name'],mix=cfg['type_mix'],continuation=cfg['continuation'])
    binding['record_files']=sorted(binding['record_files']+['z.json'])
    binding['counting_removal']=dict(rows=17879,sha256=B1)
    write(ROOT/'out/config.json',cfg);write(ROOT/'configs/r1p.json',cfg)
    write(ROOT/'configs/cont1_cells.json',{s:p['cells'] for s,p in cfg['type_mix']['streams'].items()})
    write(ROOT/'out/BINDING.json',binding)
    write(ROOT/'out/CONFIG_DIFF_CPRIME.json',diff(base,cfg))
    write(ROOT/'out/CPRIME_IDENTITIES.json',ids)
    return cfg,binding,ids

def package():
    cfg,binding,ids=config()
    archive=SNAP/'out/p_08f3a7b2.tar';assert sha(archive)==ARCHIVE_SHA
    with tarfile.open(archive) as tf:
        members={}
        for m in tf:
            assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts and m.name not in members
            members[m.name]=tf.extractfile(m).read()
    sums={n:h for h,n in (line.split('  ',1) for line in members['sums.txt'].decode().splitlines())}
    assert set(sums)==set(members)-{'sums.txt'}
    assert all(hashlib.sha256(members[n]).hexdigest()==h for n,h in sums.items())
    from cprime_removal import build
    raw=build();assert hashlib.sha256(raw).hexdigest()==B1 and len(raw.splitlines())==17879
    rows=[json.loads(line) for line in raw.splitlines()]
    assert all(set(r)=={'pool','question_type','reason','row_key','scene'} and r['reason']=='count_diag_first_seen_list_form' for r in rows)
    import re
    policy=re.compile(r'split|revsi|vsibench|vsi|distill|qgen|scannet|arkit|qwen|sft|student|benchmark|eval',re.I)
    hits=policy.findall(raw.decode())
    # Pool-only anonymization preserves matching keys and removes content deny hits.
    assert not hits
    write(ROOT/'out/B1_POLICY.json',dict(sha256=B1,lines=len(rows),reason=rows[0]['reason'],
        content_deny_hits=dict(__import__('collections').Counter(hits)),
        public_name_scan='PASS',private_content_classification='REQUIRED' if hits else 'NO_REGEX_HITS',
        reason_only_rewrite_resolves_hits=False if hits else None))
    out=ROOT/'out';(out/'records/z.json').write_bytes(raw)
    members['z.json']=members['records/z.json']=raw
    members['c4.json']=(SNAP/'out/config.json').read_bytes()
    members['config.json']=(enc(cfg)+'\n').encode();members['BINDING.json']=(enc(binding)+'\n').encode()
    oldrun='05b8ac69';oldtoken='7f1589c1';run=binding['run_key'];token=binding['store_key']
    for name in ('jb.sh','e.txt'):
        members[name]=members[name].decode().replace(oldrun,run).replace(oldtoken,token).encode()
    oldids=json.loads(members['ids.json'])
    # The admission contract differs only in its derived output directory.
    proof=load(SNAP/'out/proof/inputs.json')
    # Read the exact sealed launch contract from the proof source if available.
    from cprime_recovery import launch_contract
    contract=launch_contract();contract['directory']=cfg['output']+'/inputs'
    ids['contract']=digest(contract);members['ids.json']=(enc(ids)+'\n').encode()
    script=members['s.sh'].decode()
    # Derived shell paths change; C4 canary constants stay exact.
    script=script.replace('BUN=/project/community/jjyeung/okh7/i_'+oldtoken,'BUN='+ids['bun'])
    script=script.replace('KH=/project/community/jjyeung/okh7/x_'+oldtoken,'KH='+ids['kh'])
    script=script.replace('sbatch -J a15_cot_ap'+oldrun,'sbatch -J '+ids['job_name'])
    members['s.sh']=add_delta(script).encode()
    # The proof script remains available for unchanged PASS-mode semantics.
    proofname='p_'+run+'.sh'
    members[proofname]=members.pop('p_'+oldrun+'.sh').replace(BASE.encode(),ids['identity'].encode())
    members['sums.txt']=''.join(hashlib.sha256(raw).hexdigest()+'  '+n+'\n' for n,raw in sorted(members.items()) if n!='sums.txt').encode()
    package=out/'operator';package.mkdir(exist_ok=True)
    for n,raw in members.items():
        p=package/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    (out/'r1p_code.tar').write_bytes(members['t.tar'])
    assert sha(out/'r1p_code.tar')==binding['code_archive_sha256']
    for n in binding['record_files']:(out/'records'/n).write_bytes(members['records/'+n])
    payload=io.BytesIO()
    with tarfile.open(fileobj=payload,mode='w') as tf:
        for n,raw in sorted(members.items()):
            m=tarfile.TarInfo(n);m.size=len(raw);m.mode=0o700 if n.endswith('.sh') else 0o600;tf.addfile(m,io.BytesIO(raw))
    raw=payload.getvalue();h=hashlib.sha256(raw).hexdigest();target=out/('p_'+h[:8]+'.tar')
    if target.exists():assert target.read_bytes()==raw
    else:
        with target.open('xb') as f:f.write(raw)
    op=dict(archive=target.name,sha256=h,bundle=ids['bun'],kit=ids['kh'],job_name=ids['job_name'],
        contract=ids['contract'],wrapper_sha256=sha(package/'jb.sh'),proof_script=proofname,
        public_filename_scan='PASS',private_content_scan='REQUIRES_INDEPENDENT_REVIEW',production_authorized=False)
    write(out/'OPERATOR.json',op);write(out/'CPRIME_IDENTITIES.json',ids)
    proof.update(config_identity=ids['identity'],config_sha256=sha(out/'config.json'),run_key=run)
    write(out/'proof/inputs.json',proof)
    print(enc(dict(**ids,archive=str(target),sha256=h)),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config-only',action='store_true');args=p.parse_args()
    if args.config_only:print(enc(config()[2]))
    else:package()
