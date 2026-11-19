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
import uuid

sys.path.insert(0,str(Path(__file__).resolve().parent))
from common228 import *
from namespace228 import namespace_command,host_path
from inventory228 import verify_members,unexplained,prepare_products,runtime_requirements

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
    """Authenticate/list first, then GNU tar --skip-old-files, then verify every member."""
    from inventory228 import verify_members
    destination=local(destination);destination.mkdir(parents=True,exist_ok=True)
    stream=PartStream(group['parts'],mapping);inventory={};total=0;seen=set();conflicts=[]
    try:
        with tarfile.open(fileobj=stream,mode='r|*') as archive:
            for member in archive:
                p=Path(member.name)
                if p.is_absolute() or '..' in p.parts or str(p) in seen:raise Refusal('Unsafe/duplicate archive member')
                seen.add(str(p));target=destination/p
                if target.is_symlink() or target.parent.resolve()!=target.parent.absolute() or not beneath(target.resolve(),destination.resolve()):
                    raise Refusal('Archive member crosses a symlink')
                if member.isdir():
                    if target.exists() and not target.is_dir():conflicts.append(str(target))
                    continue
                if not member.isfile():raise Refusal('Input archive links require coordinator inspection: '+member.name)
                total+=member.size
                if total>group['expanded_bytes']:raise Refusal('Archive expansion exceeds its pin')
                digest=hashlib.sha256();size=0
                with archive.extractfile(member) as source:
                    for block in iter(lambda:source.read(1024*1024),b''):digest.update(block);size+=len(block)
                if size!=member.size:raise Refusal('Truncated archive member')
                spec=dict(bytes=size,sha256=digest.hexdigest());inventory[str(target)]=spec
                if target.exists():
                    if not target.is_file() or target.stat().st_size!=size or sha(target)!=spec['sha256']:
                        conflicts.append(str(target))
        while stream.read(1024*1024):pass
        if stream.digest.hexdigest()!=group['sha256'] or total!=group['expanded_bytes']:
            raise Refusal('Whole archive hash/expanded size differs')
    finally:stream.close()
    if conflicts:raise Refusal('Existing archive members differ; all preserved: '+str(sorted(conflicts)))
    # Every member and every part was authenticated before tar can create a file.
    # Existing files/directories retain their contents and metadata.
    command=['tar','--extract','--skip-old-files','--no-same-owner',
             '--no-same-permissions','--file','-','--directory',str(destination)]
    stream=PartStream(group['parts'],mapping)
    log_root=local(destination.parent/'read228_extraction_logs');log_root.mkdir(parents=True,exist_ok=True)
    log=log_root/(uuid.uuid4().hex+'.log')
    try:
        with log.open('xb') as errors, subprocess.Popen(command,stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,stderr=errors) as process:
            try:
                for block in iter(lambda:stream.read(1024*1024),b''):process.stdin.write(block)
            except BrokenPipeError:pass
            finally:process.stdin.close()
            rc=process.wait()
        if rc:raise Refusal('Input extraction failed; no retry. See '+str(log))
        if stream.digest.hexdigest()!=group['sha256']:raise Refusal('Archive changed during extraction')
    finally:stream.close()
    verify_members(inventory)
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

def versions(python, receipt, env, env_roots=(), namespace=(), plan=None):
    # The pinned env receipt, not the CPU test environment, selects production versions.
    probe=('import json,sys,sysconfig,torch,torchvision,transformers,scipy;'
           'print(json.dumps(dict(versions={m.__name__:m.__version__ for m in '
           '(torch,torchvision,transformers,scipy)},python=sys.executable,cuda=torch.version.cuda,'
           'prefix=sys.prefix,base_prefix=sys.base_prefix,python_version=list(sys.version_info[:3]),'
           'audit_roots=[sysconfig.get_paths()[k] for k in ("stdlib","platstdlib","purelib","platlib")],'
           'module_paths={m.__name__:m.__file__ for m in (torch,torchvision,transformers,scipy)})))')
    probe_file=local(Path(env['TMPDIR'])/'version_probe.py');probe_file.write_text(probe+'\n')
    result=subprocess.run(list(namespace)+[str(python),'-B','-I',str(probe_file)],env=env,text=True,capture_output=True,timeout=120)
    if result.returncode:raise Refusal('Environment probe failed: '+result.stderr[-2000:])
    got=json.loads(result.stdout.strip().splitlines()[-1])
    if got['versions']!=receipt.get('versions'):raise Refusal('Environment versions differ from pinned q/env.json')
    if not got['cuda']:raise Refusal('A CUDA-enabled torch build is required; CPU torch cannot run this reader')
    if got['python_version'][:2]!=[3,12]:raise Refusal('Require staged Python 3.12')
    # The sealed reader trusts sysconfig library roots and settings.env_roots.
    physical=(lambda path:host_path(path,plan)) if plan else local
    trusted=[physical(p).resolve() for p in got['audit_roots']]+[physical(p).resolve() for p in env_roots]
    for key in ('python','prefix','base_prefix'):physical(got[key])
    for path in got['module_paths'].values():
        path=physical(path).resolve()
        if not any(beneath(path,r) for r in trusted):raise Refusal('Framework module is outside reader audit roots')
    got['physical_runtime_roots']=[str(physical(got[key])) for key in ('prefix','base_prefix')]
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
                stat=p.lstat();key=(stat.st_dev,stat.st_ino)
                if key not in seen:seen.add(key);total+=stat.st_size;files+=1
    return dict(bytes=total,files=files,roots=[str(p) for p in selected],basis='lstat bytes, unique file inodes, including symlink metadata; directory symlinks require their target in the named roots')

def verify_runtime_pins(plan):
    missing=read(HERE/'MISSING.json')
    listed={p['target']:(p['bytes'],p['sha256']) for p in missing['files']}
    parts=[p for group in plan['runtime_archives'] for p in group['parts']]
    if {p['target']:(p['bytes'],p['sha256']) for p in parts}!=listed:
        raise Refusal('Runtime plan differs from MISSING.json pins')
    files={}
    for part in parts:
        path=local(part['target'])
        if not path.is_file():raise Refusal('MISSING.json runtime target absent: '+str(path))
        checked(path,part);files[str(path)]=dict(bytes=part['bytes'],sha256=part['sha256'])
    result=dict(passed=True,files=files,markers_trusted=False,fetch_allowed=False,utc=utc())
    write(STAGE/'RUNTIME_PINS.json',result);return result

def staging_receipts(plan):
    expected=sha(HERE/'STAGE_PLAN.json');extracted={};receipts={}
    for name in ('INPUT_EXTRACTION.json','RUNTIME_EXTRACTION.json'):
        path=STAGE/name
        if not path.is_file():raise Refusal('Missing completed local extraction receipt: '+str(path))
        receipt=read(path)
        if receipt.get('passed') is not True or receipt.get('plan_sha256')!=expected:
            raise Refusal('Extraction receipt does not authenticate this stage plan')
        overlap=set(extracted)&set(receipt['files'])
        if any(extracted[p]!=receipt['files'][p] for p in overlap):raise Refusal('Conflicting extraction inventories')
        extracted.update(receipt['files']);receipts[name]=receipt
    verify_members(extracted)
    path=STAGE/'NAMESPACE.json'
    if not path.is_file():raise Refusal('Run --check-namespace before preparation')
    namespace=read(path)
    if namespace.get('passed') is not True:raise Refusal('Target namespace probe failed; no retry')
    if namespace_command(plan)!=namespace['argv']:raise Refusal('Namespace command differs')
    return dict(extraction_plan_sha256=expected,files=extracted,namespace=namespace,
                runtime_members=receipts['RUNTIME_EXTRACTION.json']['groups'])

def reconcile(plan,extraction,data):
    files=extraction['files'];roots={g['destination'] for g in plan['input_archives']}
    # Scan only the runtime trees named by archives, never all of /scratch/jjyeung.
    for group in plan['runtime_archives']:
        for name in extraction['runtime_members'][group['id']]['members']:
            parts=Path(name['name']).parts
            if not parts:continue
            if parts[0]=='sj' and len(parts)>=3:
                roots.add(str(Path('/scratch/jjyeung').joinpath(*parts[1:3])))
            elif parts[0]=='fsw':roots.add(str(STAGE/'runtime/fsw'))
            elif parts[:2]==('m','ap'):roots.add(str(STAGE/'runtime/m/ap'))
    products=prepare_products(data) if (data/'READY.json').exists() else set()
    receipt=STAGE/'PREPARE_PRODUCTS.json'
    if receipt.is_file():
        owned=read(receipt)
        if owned.get('plan_sha256')!=sha(HERE/'STAGE_PLAN.json'):raise Refusal('Prepare product plan differs')
        verify_members(owned['files']);products.update(owned['files'])
    return unexplained(roots,files,products)

def record_prepare_products(plan,extraction,data):
    # This runs only after our successful creation of a previously absent restore.
    allowed=prepare_products(data);files={}
    caches=[data/'e'/name for name in ('cache','hf','triton','torch')]
    for base,dirs,names in os.walk(str(data),followlinks=False):
        for name in names:
            path=Path(base)/name
            if str(path) in extraction['files']:continue
            if str(path) not in allowed and not any(beneath(path,root) for root in caches):
                raise Refusal('Unrecognized preparation product: '+str(path))
            files[str(path)]=dict(link=os.readlink(str(path))) if path.is_symlink() else dict(bytes=path.stat().st_size,sha256=sha(path))
    write(STAGE/'PREPARE_PRODUCTS.json',dict(plan_sha256=sha(HERE/'STAGE_PLAN.json'),files=files))

def stage_check(root, cfg, inputs, export, *, prepare=False, check_env=True):
    try:
        result=_stage_check(root,cfg,inputs,export,prepare=prepare,check_env=check_env)
    except (Refusal,OSError,ValueError,KeyError) as error:
        result=dict(passed=False,utc=utc(),error=str(error))
        for name,key in (('RUNTIME_EXTRACTION.json','runtime_extraction'),('INPUT_EXTRACTION.json','input_extraction')):
            if (STAGE/name).is_file():result[key]=read(STAGE/name)
        write(STAGE/'STAGE_CHECK.json',result)
        raise
    write(STAGE/'STAGE_CHECK.json',result)
    return result

def _stage_check(root, cfg, inputs, export, *, prepare=False, check_env=True):
    plan=read(HERE/'STAGE_PLAN.json');data=Path(cfg['logical'])/'d';p=Path(cfg['logical'])/'p'
    extraction=staging_receipts(plan)
    inventory_check=reconcile(plan,extraction,data)
    required=runtime_requirements(plan,extraction['files'],inputs)
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
        env_info=versions(python,read(inputs['files']['env']['path']),env,inputs['env_roots'],namespace_command(plan),plan)
    if prepare and not (data/'READY.json').exists():
        # The sealed preparation function creates the restore and verifies its tensor mapping.
        # No source patch or unchecked model/config rewrite is involved.
        dispatch=STAGE/'prepare/0.json'
        write(dispatch,dict(action=0,package=str(p),config=cfg,inputs={**inputs,'_export':export}))
        if (data/'e').exists():raise Refusal('Restore already exists; check it instead of rerunning preparation')
        with (STAGE/'prepare/prepare.log').open('xb') as log:
            rc=subprocess.run(['nice','-n','10']+namespace_command(plan)+[str(python),'-B','-I',str(p/'orchard_h10/entry.py'),str(dispatch)],
                              env=env,stdout=log,stderr=subprocess.STDOUT).returncode
        if rc:raise Refusal('Sealed preparation failed; no retry. See '+str(STAGE/'prepare/prepare.log'))
        record_prepare_products(plan,extraction,data)
        inventory_check=reconcile(plan,extraction,data)
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
    roots.extend(inventory_check.get('checked_roots',[]))
    if env_info:
        roots.extend(env_info.get('physical_runtime_roots',[env_info['prefix'],env_info['base_prefix']]))
    footprint=local_bytes(roots)
    if footprint['bytes']>plan['budget']['limit_bytes']-plan['budget']['code_returns_cache_allowance_bytes']:
        raise Refusal('Staged footprint leaves less than the 5 GB run allowance below 150 GB')
    return dict(passed=True,utc=utc(),mode='OFF',plan_sha256=cfg['plan_sha256'],step=export['step'],
                environment=env_info,ready=ready,source_files=927,footprint=footprint,extraction=extraction,
                namespace=extraction['namespace'],inventory_check=inventory_check,runtime_requirements=required,
                runtime_members=extraction['runtime_members'])

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('package')
    mode=ap.add_mutually_exclusive_group();mode.add_argument('--install-code',action='store_true')
    mode.add_argument('--extract-inputs',action='store_true');mode.add_argument('--prepare',action='store_true')
    mode.add_argument('--extract-runtime',action='store_true');mode.add_argument('--verify-runtime-pins',action='store_true')
    mode.add_argument('--check-namespace',action='store_true')
    ap.add_argument('--out');a=ap.parse_args(argv)
    print(utc(),file=sys.stderr)
    target_host()
    root,cfg,inputs,export=deployment(a.package)
    if a.verify_runtime_pins:
        result=verify_runtime_pins(read(HERE/'STAGE_PLAN.json'))
    elif a.check_namespace:
        from namespace228 import check_namespace
        result=check_namespace(read(HERE/'STAGE_PLAN.json'),clean_environment(STAGE/'namespace_probe'))
    elif a.install_code:
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
        verify_runtime_pins(plan)
        result=dict(files={},groups={});total=0
        for group in plan['runtime_archives']:
            print(utc()+' extracting '+group['id'],file=sys.stderr)
            got=extract_runtime(group,mapping,limit=limit-total);total+=got['expanded_bytes']
            overlap=set(result['files'])&set(got['files'])
            if any(result['files'][p]!=got['files'][p] for p in overlap):raise Refusal('Runtime groups disagree on a member')
            result['files'].update(got['files']);result['groups'][group['id']]=dict(archive_sha256=got['archive_sha256'],members=got['members'])
        result.update(expanded_bytes=total,passed=True,plan_sha256=sha(HERE/'STAGE_PLAN.json'))
        write(STAGE/'RUNTIME_EXTRACTION.json',result)
    else:
        target_host();result=stage_check(root,cfg,inputs,export,prepare=a.prepare)
    if a.out:write(local(a.out),result)
    print(json.dumps({k:v for k,v in result.items() if k!='files'},sort_keys=True))
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (Refusal,OSError,ValueError,KeyError) as e:
        print('REFUSED: '+str(e),file=sys.stderr);raise SystemExit(2)
