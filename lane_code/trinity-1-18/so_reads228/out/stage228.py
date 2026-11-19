"""Verify or prepare node-local A10b assets; never transfer data or use a GPU."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parent))
from common228 import *

def archive_map(plan):
    result={}
    for group in plan['input_archives']+plan['runtime_archives']:
        for part in group['parts']:
            if part['path'] in result:raise Refusal('Duplicate source path')
            result[part['path']]=local(part['target'])
    return result

def mapped_part(part, mapping):
    if part['path'] not in mapping:raise Refusal('No local staging map: '+part['path'])
    return local(mapping[part['path']])

class PartStream:
    """Consume an ordered tar stream, authenticating every part and the concatenation."""
    def __init__(self, parts, mapping):
        self.parts=iter(parts);self.mapping=mapping;self.file=None
        self.digest=hashlib.sha256();self.size=0;self.closed=False

    def read(self, size):
        if size<0:raise Refusal('Bounded stream reads required')
        chunks=[]
        while size:
            if self.file is None:
                self.part=next(self.parts,None)
                if self.part is None:break
                self.file=mapped_part(self.part,self.mapping).open('rb')
                self.part_hash=hashlib.sha256();self.part_size=0
            b=self.file.read(size)
            if not b:
                self.file.close();self.file=None
                if self.part_size!=self.part['bytes'] or self.part_hash.hexdigest()!=self.part['sha256']:
                    raise Refusal('Archive part pin differs: '+self.part['path'])
                continue
            self.digest.update(b);self.part_hash.update(b);self.part_size+=len(b)
            if self.part_size>self.part['bytes']:raise Refusal('Archive part oversized')
            self.size+=len(b);size-=len(b);chunks.append(b)
        return b''.join(chunks)

    def close(self):
        if self.file:self.file.close()
        self.closed=True

def extract_group(group, mapping, destination):
    """Never overwrite an existing member; reuse it only when its streamed bytes agree."""
    destination=local(destination);destination.mkdir(parents=True,exist_ok=True)
    stream=PartStream(group['parts'],mapping);inventory={};total=0;seen=set()
    try:
        with tarfile.open(fileobj=stream,mode='r|*') as t:
            for m in t:
                p=Path(m.name)
                if p.is_absolute() or '..' in p.parts or str(p) in seen:raise Refusal('Unsafe/duplicate archive member')
                seen.add(str(p));target=destination/p
                if target.is_symlink() or not beneath(target.resolve(),destination.resolve()):
                    raise Refusal('Archive member crosses a symlink')
                if m.isdir():target.mkdir(parents=True,exist_ok=True);continue
                if not m.isfile():raise Refusal('Input archive links require coordinator inspection: '+m.name)
                total+=m.size
                if total>group['expanded_bytes']:raise Refusal('Archive expansion exceeds its pin')
                target.parent.mkdir(parents=True,exist_ok=True)
                h=hashlib.sha256();n=0
                exists=target.exists()
                existing=target.open('rb') if exists else None
                output=None if exists else target.open('xb')
                try:
                    with t.extractfile(m) as f:
                        for b in iter(lambda:f.read(1024*1024),b''):
                            h.update(b);n+=len(b)
                            if existing is not None:
                                if existing.read(len(b))!=b:raise Refusal('Existing member differs; preserve and ask coordinator: '+str(target))
                            else:output.write(b)
                    if existing is not None and existing.read(1):raise Refusal('Existing member is longer')
                finally:
                    if existing:existing.close()
                    if output:output.close()
                if n!=m.size:raise Refusal('Truncated archive member')
                if not exists:target.chmod(m.mode&0o777)
                inventory[str(target)]=dict(bytes=n,sha256=h.hexdigest())
        while stream.read(1024*1024):pass
        if stream.digest.hexdigest()!=group['sha256'] or total!=group['expanded_bytes']:
            raise Refusal('Whole archive hash/expanded size differs')
    finally:stream.close()
    return inventory

def code_install(root, cfg):
    dest=local(Path(cfg['logical'])/'p')
    pins=read(HERE/'A10b_PINS.json')['source']
    if dest.exists():source_check(dest,pins);return
    dest.mkdir(parents=True,exist_ok=False)
    with tarfile.open(root/'package/0.tgz') as t:
        for m in t:
            if m.name not in pins or not m.isfile():raise Refusal('Unexpected payload member')
            p=dest/m.name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(t.extractfile(m).read());checked(p,pins[m.name])
    source_check(dest,pins)

def versions(python, receipt, env, env_roots=()):
    # The pinned env receipt, not the CPU test environment, selects production versions.
    probe=('import json,sys,sysconfig,torch,torchvision,transformers,scipy;'
           'print(json.dumps(dict(versions={m.__name__:m.__version__ for m in '
           '(torch,torchvision,transformers,scipy)},python=sys.executable,cuda=torch.version.cuda,'
           'prefix=sys.prefix,base_prefix=sys.base_prefix,python_version=list(sys.version_info[:3]),'
           'audit_roots=[sysconfig.get_paths()[k] for k in ("stdlib","platstdlib","purelib","platlib")],'
           'module_paths={m.__name__:m.__file__ for m in (torch,torchvision,transformers,scipy)})))')
    probe_file=local(Path(env['TMPDIR'])/'version_probe.py');probe_file.write_text(probe+'\n')
    result=subprocess.run([str(python),'-B','-I',str(probe_file)],env=env,text=True,capture_output=True,timeout=120)
    if result.returncode:raise Refusal('Environment probe failed: '+result.stderr[-2000:])
    got=json.loads(result.stdout.strip().splitlines()[-1])
    if got['versions']!=receipt.get('versions'):raise Refusal('Environment versions differ from pinned q/env.json')
    if not got['cuda']:raise Refusal('A CUDA-enabled torch build is required; CPU torch cannot run this reader')
    if got['python_version'][:2]!=[3,12]:raise Refusal('Require staged Python 3.12')
    # The sealed reader trusts sysconfig library roots and settings.env_roots.
    trusted=[local(p).resolve() for p in got['audit_roots']]+[local(p).resolve() for p in env_roots]
    for key in ('python','prefix','base_prefix'):local(got[key])
    for path in got['module_paths'].values():
        path=local(path).resolve()
        if not any(beneath(path,r) for r in trusted):raise Refusal('Framework module is outside reader audit roots')
    got['env_roots']=list(env_roots)
    got['audit_coverage_verified']=True
    return got

def local_bytes(roots):
    """Count logical bytes once per inode in the named local trees, without following directory links."""
    unique=sorted({local(p).resolve() for p in roots if Path(p).exists()},key=lambda p:len(p.parts))
    selected=[]
    for p in unique:
        if not any(p==r or beneath(p,r) for r in selected):selected.append(p)
    seen=set();total=0;files=0
    for root in selected:
        for base,dirs,names in os.walk(root,followlinks=False):
            for name in names:
                p=Path(base)/name
                stat=p.stat();key=(stat.st_dev,stat.st_ino)
                if key not in seen:seen.add(key);total+=stat.st_size;files+=1
    return dict(bytes=total,files=files,roots=[str(p) for p in selected],basis='logical bytes, unique file inodes; directory symlinks require their target in the named roots')

def staging_receipts(plan):
    expected=sha(HERE/'STAGE_PLAN.json');extracted={}
    for name in ('INPUT_EXTRACTION.json','RUNTIME_EXTRACTION.json'):
        path=STAGE/name
        if not path.is_file():raise Refusal('Missing completed local extraction receipt: '+str(path))
        receipt=read(path)
        if receipt.get('passed') is not True or receipt.get('plan_sha256')!=expected:
            raise Refusal('Extraction receipt does not authenticate this stage plan')
        extracted.update(receipt['files'])
    path=STAGE/'RUNTIME_RELOCATION.json'
    if not path.is_file():raise Refusal('Run explicit --relocate-runtime before preparation')
    relocation=read(path)
    if relocation.get('enabled') is not True:raise Refusal('Runtime relocation receipt is incomplete')
    wanted={str(Path(plan['logical'])/'d/v/py'),str(Path(plan['logical'])/'d/v/boot.py'),
            str(Path(plan['environment']['local_base_env'])/'pyvenv.cfg')}
    if {row['path'] for row in relocation['files']}!=wanted:raise Refusal('Runtime relocation file set differs')
    for row in relocation['files']:
        if row['before']!=extracted.get(row['path']):raise Refusal('Runtime relocation input pin differs')
        checked(local(row['original']),row['before']);checked(local(row['path']),row['after'])
    return dict(extraction_plan_sha256=expected,relocation_sha256=sha(path))

def stage_check(root, cfg, inputs, export, *, prepare=False, check_env=True):
    plan=read(HERE/'STAGE_PLAN.json');data=Path(cfg['logical'])/'d';p=Path(cfg['logical'])/'p'
    extraction=staging_receipts(plan)
    source_check(p,read(HERE/'A10b_PINS.json')['source'])
    for spec in inputs['files'].values():checked(local(spec['path']),spec)
    for spec in export['preparation'].values():checked(data/spec['path'],spec)
    # Full export shard pins are reached only through the authenticated manifest.
    weights=read(inputs['files']['full_weights']['path'])
    for spec in weights['files']+[weights['index']]:
        path=Path(inputs['files']['full_weights']['path']).parent/spec['name']
        if Path(spec['name']).name!=spec['name']:raise Refusal('Unsafe shard name')
        if 'bytes' in spec:checked(path,spec)
        elif not path.is_file() or sha(path)!=spec['sha256']:raise Refusal('Wrong shard/index sha256')
    for name in ('frames_root','sam_source'):
        if not local(inputs[name]).is_dir():raise Refusal('Missing directory: '+inputs[name])
    python=local(inputs['python'])
    if not python.is_file() or not os.access(python,os.X_OK):raise Refusal('Missing executable '+str(python))
    policy_check()
    env_info=None
    env=clean_environment(STAGE/'prepare')
    if check_env:
        env_info=versions(python,read(inputs['files']['env']['path']),env,inputs['env_roots'])
    if prepare and not (data/'READY.json').exists():
        # The sealed preparation function creates the restore and verifies its tensor mapping.
        # No source patch or unchecked model/config rewrite is involved.
        dispatch=STAGE/'prepare/0.json'
        write(dispatch,dict(action=0,package=str(p),config=cfg,inputs={**inputs,'_export':export}))
        if (data/'e').exists():raise Refusal('Restore already exists; check it instead of rerunning preparation')
        with (STAGE/'prepare/prepare.log').open('xb') as log:
            rc=subprocess.run(['nice','-n','10',str(python),'-B','-I',str(p/'orchard_h10/entry.py'),str(dispatch)],
                              env=env,stdout=log,stderr=subprocess.STDOUT).returncode
        if rc:raise Refusal('Sealed preparation failed; no retry. See '+str(STAGE/'prepare/prepare.log'))
    for name in ('READY.json','binding.json','manifest.json','settings.json','6.json'):
        if not (data/name).is_file():raise Refusal('Run stage228.py --prepare after staging; missing '+str(data/name))
    ready=read(data/'READY.json')
    if ready['settings']!=sha(data/'settings.json') or ready['binding']!=sha(data/'binding.json') or ready['restore']!=sha(data/'e/RESTORE.json'):
        raise Refusal('Prepared restore receipt differs')
    if read(data/'6.json')!=export:raise Refusal('Prepared export identity differs')
    settings=read(data/'settings.json')
    if settings.get('env_roots')!=inputs['env_roots']:raise Refusal('Prepared env_roots differ from package')
    for key in ('stage1_select_rule','perception_memo','perception_memo_modules','perception_memo_verify_ids','save_own_depth'):
        if settings[key]!=cfg[key]:raise Refusal('Prepared settings differ: '+key)
    if any(k.startswith('read_') for k in settings):raise Refusal('OFF settings contain extension switches')
    if shutil.disk_usage(data).free<plan['budget']['free_floor_bytes']:raise Refusal('Less than 200 GiB free on scratch')
    roots=[Path(cfg['logical']),STAGE,root,HERE]
    if env_info:
        roots.extend([env_info['prefix'],env_info['base_prefix']])
    footprint=local_bytes(roots)
    if footprint['bytes']>plan['budget']['limit_bytes']-plan['budget']['code_returns_cache_allowance_bytes']:
        raise Refusal('Staged footprint leaves less than the 5 GB run allowance below 150 GB')
    return dict(passed=True,utc=utc(),mode='OFF',plan_sha256=cfg['plan_sha256'],step=export['step'],
                environment=env_info,ready=ready,source_files=927,footprint=footprint,extraction=extraction)

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('package')
    mode=ap.add_mutually_exclusive_group();mode.add_argument('--install-code',action='store_true')
    mode.add_argument('--extract-inputs',action='store_true');mode.add_argument('--prepare',action='store_true')
    mode.add_argument('--extract-runtime',action='store_true');mode.add_argument('--relocate-runtime',action='store_true')
    ap.add_argument('--out');a=ap.parse_args(argv)
    print(utc(),file=sys.stderr)
    target_host()
    root,cfg,inputs,export=deployment(a.package)
    if a.install_code:
        code_install(root,cfg);result=dict(code_installed=True,logical=cfg['logical'])
    elif a.extract_inputs:
        target_host();plan=read(HERE/'STAGE_PLAN.json');mapping=archive_map(plan)
        need=sum(g['expanded_bytes'] for g in plan['input_archives'])
        if shutil.disk_usage(STAGE).free<need+plan['budget']['free_floor_bytes']:raise Refusal('Insufficient staging space')
        inventory={}
        # Refuse missing local bytes before writing any archive member. Never fetch.
        for group in plan['input_archives']:
            for part in group['parts']:
                path=mapped_part(part,mapping)
                if not path.is_file() or path.stat().st_size!=part['bytes']:raise Refusal('Missing/wrong staged part: '+str(path))
        for group in plan['input_archives']:
            print(utc()+' extracting '+group['id'],file=sys.stderr)
            inventory.update(extract_group(group,mapping,group['destination']))
        result=dict(utc=utc(),passed=True,plan_sha256=sha(HERE/'STAGE_PLAN.json'),files=inventory)
        write(STAGE/'INPUT_EXTRACTION.json',result)
    elif a.extract_runtime:
        from runtime228 import extract_runtime
        plan=read(HERE/'STAGE_PLAN.json');mapping=archive_map(plan)
        for group in plan['runtime_archives']:
            for part in group['parts']:
                path=mapped_part(part,mapping)
                if not path.is_file() or path.stat().st_size!=part['bytes']:
                    raise Refusal('Runtime bytes missing; coordinator must resolve MISSING.json: '+str(path))
        limit=plan['budget']['runtime_expanded_allowance_bytes']
        if shutil.disk_usage(STAGE).free<limit+plan['budget']['free_floor_bytes']:raise Refusal('Insufficient runtime staging space')
        result=dict(files={},groups={});total=0
        for group in plan['runtime_archives']:
            print(utc()+' extracting '+group['id'],file=sys.stderr)
            got=extract_runtime(group,mapping,limit=limit-total);total+=got['expanded_bytes']
            result['files'].update(got['files']);result['groups'][group['id']]=got['archive_sha256']
        result.update(expanded_bytes=total,passed=True,plan_sha256=sha(HERE/'STAGE_PLAN.json'))
        write(STAGE/'RUNTIME_EXTRACTION.json',result)
    elif a.relocate_runtime:
        from runtime228 import relocate_runtime
        result=relocate_runtime(read(HERE/'STAGE_PLAN.json'),enabled=True)
    else:
        target_host();result=stage_check(root,cfg,inputs,export,prepare=a.prepare)
    if a.out:write(local(a.out),result)
    print(json.dumps({k:v for k,v in result.items() if k!='files'},sort_keys=True))
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (Refusal,OSError,ValueError,KeyError) as e:
        print('REFUSED: '+str(e),file=sys.stderr);raise SystemExit(2)
