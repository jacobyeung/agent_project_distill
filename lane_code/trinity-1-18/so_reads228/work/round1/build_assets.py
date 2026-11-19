"""Build A10b assets only from the named read-only mirror and supplied lists."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

L=Path('/scratch/jjyeung/orch_n30/so_reads228')
A=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3/A10b')
LISTS=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts/r228_lists')
O=L/'work/round1/kit'
STAGE='/scratch/jjyeung/orch_n30/reads228'
DATA='/scratch/jjyeung/b01ec87a6f29b/d'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def copy(p,q):
    q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
def pin(p):return dict(bytes=p.stat().st_size,sha256=sha(p))
def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()

print(subprocess.check_output(['date','-u'],universal_newlines=True).strip())
public=read(A/'package/0.json');inputs=read(A/'package/a/1.json');export=read(A/'package/a/export.json')
assert inputs==read(A/'ret/metadata/INPUTS.json') and export==read(A/'ret/metadata/EXPORT_PIN.json')
assert export['step']==400 and export['run']=='6ed2c7aa'
assert export['artifact']['sha256']=='5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd'
assert sha(A/'package/0.tgz')==public['payload_sha256']
package_names=set(read(A/'package/PACKAGE.json')['files'])|{'PACKAGE.json','0.json','0.tgz','a/0.json','a/1.json','a/export.json','a/6'}
for name in sorted(package_names):copy(A/'package'/name,O/'A10b/package'/name)
operators=('tower_sequence.py','unpack_return.py','fetch_return.py')
for name in operators:copy(A/name,O/'A10b'/name)
source={}
with tarfile.open(A/'package/0.tgz') as t:
    for m in t:
        assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
        p=O/'A10b/src'/m.name;p.parent.mkdir(parents=True,exist_ok=True)
        raw=t.extractfile(m).read();p.write_bytes(raw)
        source[m.name]=pin(p)
        assert raw==(A/'src'/m.name).read_bytes()
cfg=read(O/'A10b/src/9.json');assert canonical(cfg)==public['plan_sha256']
assets=read(O/'A10b/src/orchard_h10/vendor/ORCHARD_ASSETS.json')
policy={name:dict(path='/data3/shared/scripts/vnice/'+name+'.sh',
    bytes=(LISTS/'a3x/q'/str(name+'.sh')).stat().st_size,sha256=assets[name+'_sha256']) for name in ('vnice','terminator')}
for name,spec in policy.items():assert sha(LISTS/'a3x/q'/str(name+'.sh'))==spec['sha256']
write(O/'A10b_PINS.json',dict(public=public,operator_sha256=sha(A/'tower_sequence.py'),
    operators={name:pin(A/name) for name in operators},policy=policy,
    inputs_sha256=sha(A/'package/a/1.json'),export_sha256=sha(A/'package/a/export.json'),
    package={name:pin(O/'A10b/package'/name) for name in sorted(package_names)},source=source))

# Authenticate the small reference against the actual Orchard archive, including all metadata.
receipt=read(A/'package/a/f/EXIT.json');assert receipt['job']=='173060'
assert pin(A/'package/a/f/0.tgz')=={k:receipt['archive'][k] for k in ('bytes','sha256')}
ref=O/'reference';prefix=[];members=[]
with tarfile.open(A/'package/a/f/0.tgz') as t:
    for m in t:
        assert m.isfile()
        raw=t.extractfile(m).read();assert raw==(A/'ret'/m.name).read_bytes()
        members.append(dict(path=m.name,bytes=m.size,sha256=hashlib.sha256(raw).hexdigest()))
    for name in ('INPUTS.json','EXPORT_PIN.json','IDENTITY.json','RETURN_ID.json','CARDS.json'):
        copy(A/'ret/metadata'/name,ref/'metadata'/name)
    for kind in (3,0,1,2,4):
        journal=A/'ret/metadata/reads/0/metadata/journals'/str(kind)/'0'
        rows=[json.loads(x) for x in (journal/'items.jsonl').read_text().splitlines()];prefix+=rows
        if kind==3:
            dst=ref/'metadata/reads/0/metadata/journals/3/0';dst.mkdir(parents=True,exist_ok=True)
            (dst/'items.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows[:50]))
            copy(journal/'environment.json',dst/'environment.json')
items=read(O/'A10b/src/items/devs1_routed.json')['items']
order=[r for k in (3,0,1,2,4) for r in items if r['question_type']==cfg['order'][k]]
assert [r['id'] for r in prefix]==[r['id'] for r in order]
write(O/'FIRST50.json',dict(schema=2,reference_job='173060',source=str(A/'ret'),
    plan_sha256=public['plan_sha256'],orchard_prefix_sha256=canonical(prefix[:50]),export=export,
    items=[dict(id=r['id'],type=r['question_type']) for r in order[:50]],full_order=[r['id'] for r in order],
    item_manifest_sha256=sha(O/'A10b/src/items/devs1_routed.json')))
write(O/'ORCHARD_MEMBERS.json',dict(archive=str(A/'package/a/f/0.tgz'),**pin(A/'package/a/f/0.tgz'),members=members))
write(O/'REFERENCE_PROOF.json',dict(job='173060',archive=pin(A/'package/a/f/0.tgz'),
    all_members_match_mirror=True,member_count=len(members),rows=len(prefix),prefix_rows=50,
    orchard_prefix_sha256=canonical(prefix[:50])))

names=(['s4e0','s4e1','s4e2','s4e3'],['g0'],['a2.tar'],['a4.tar'],['a3.tar'],['package/a/6'])
groups=[]
for i,a in enumerate(inputs['archives']):
    parts=[]
    for part,name in zip(a['parts'],names[i]):
        target=STAGE+'/kit/A10b/'+name if i==5 else STAGE+'/dl/'+name
        parts.append(dict(**part,target=target,source_host='trinity-2-28',
            availability='delivered_with_package' if i==5 else 'staged_by_coordinator',
            sha_marker=None if i==5 else target+'.sha_ok'))
    assert len(parts)==len(a['parts'])
    groups.append(dict(id='a'+str(i),parts=parts,sha256=a['sha256'],expanded_bytes=a['expanded_bytes'],
                       destination=DATA,package_destination=a['destination']))
runtime=[];missing=[]
for i,group in enumerate(assets['groups']):
    parts=[]
    for j,(path,n,h) in enumerate(group):
        target=STAGE+'/dl/r'+str(i)+'_'+str(j)
        row=dict(path=path,host=assets['observed_host'],bytes=n,sha256=h,target=target,
                 role='base_runtime',group='r'+str(i),availability='not_in_supplied_staging_inventory',
                 reason='Package job.py stages this template runtime group before the input archives.')
        missing.append(row);parts.append(dict(path=path,bytes=n,sha256=h,target=target))
    runtime.append(dict(id='r'+str(i),parts=parts,destination=STAGE+'/runtime',
        expanded_bytes_limit=40_000_000_000,sha256=None,
        pin_basis='Every ordered part is SHA256-pinned; package provides no concatenation hash.',
        namespace_map={'sj':'/scratch/jjyeung','m/ap':STAGE+'/runtime/m/ap','fsw':STAGE+'/runtime/fsw'}))
write(O/'MISSING.json',dict(schema=1,files=missing,total_bytes=sum(r['bytes'] for r in missing),
    source_basis='A10b/src/orchard_h10/vendor/ORCHARD_ASSETS.json observed_host and groups',
    fetch_allowed=False,reason='The supplied lists have wrappers and overlay only, no base Python/torch runtime. No runtime archive lists were supplied.'))

member_maps={}
for name in ('a2.tar','a4.tar','a3.tar','g0'):
    entries={}
    for line in (LISTS/(name+'.list')).read_text().splitlines():
        fields=line.split(maxsplit=5)
        if len(fields)==6:entries[fields[5]]=dict(kind=fields[0][0],bytes=int(fields[2]))
    member_maps[name]=entries
    copy(LISTS/(name+'.list'),O/'evidence'/(name+'.list'))
for name in ('env.json','policy.json','vnice.sh','terminator.sh'):
    copy(LISTS/'a3x/q'/name,O/'evidence/q'/name)
for name in ('sam3.sha256','vnice.sha256','sys_python.txt','existing_d.txt','nvidia_smi.txt','envs.txt'):
    copy(LISTS/name,O/'evidence'/name)
expanded=[]
for role,spec in inputs['files'].items():
    rel=str(Path(spec['path']).relative_to(DATA));sources=[]
    for name,entries in member_maps.items():
        if rel in entries:
            assert entries[rel]['bytes']==spec['bytes'];sources.append(name)
    if rel.startswith('m400/'):sources=['s4e0..s4e3']
    if role in ('sam_checkpoint','sam_receipt'):sources+=['existing target d/k; revalidate file pin']
    assert sources,(role,rel)
    expanded.append(dict(role=role,**spec,archive_members=sources))
env=read(LISTS/'a3x/q/env.json');assert pin(LISTS/'a3x/q/env.json')=={k:inputs['files']['env'][k] for k in ('bytes','sha256')}
packed=sum(p['bytes'] for g in groups for p in g['parts']);unpacked=sum(g['expanded_bytes'] for g in groups)
runtime_packed=sum(p['bytes'] for g in runtime for p in g['parts'])
budget=dict(limit_bytes=150_000_000_000,input_archives_bytes=packed,input_expanded_bytes=unpacked,
    runtime_archives_bytes=runtime_packed,runtime_expanded_allowance_bytes=40_000_000_000,
    existing_sam3_bytes=inputs['files']['sam_checkpoint']['bytes'],code_returns_cache_allowance_bytes=5_000_000_000,
    free_floor_bytes=200*1024**3,estimated_peak_bytes=packed+unpacked+runtime_packed+40_000_000_000+5_000_000_000+inputs['files']['sam_checkpoint']['bytes'],
    basis='Pinned archive sizes; estimated 40 GB runtime expansion and 5 GB code/cache/return allowance; includes existing SAM3. No archive deletion.')
write(O/'STAGE_PLAN.json',dict(schema='read228-stage-v2',target_host='trinity-2-28',stage_root=STAGE,logical=cfg['logical'],
    active_export=dict(step=400,run='6ed2c7aa',member_directory='m400',artifact_sha256=export['artifact']['sha256'],reference_job='173060'),
    input_archives=groups,runtime_archives=runtime,expanded_files=expanded,budget=budget,
    code=dict(archive=STAGE+'/kit/A10b/package/0.tgz',destination=cfg['logical']+'/p',files=len(source),
              expanded_bytes=sum(p['bytes'] for p in source.values()),sha256=public['payload_sha256']),
    environment=dict(python=inputs['python'],control_python=inputs['python'],bootstrap_python='/usr/bin/python3',
        bootstrap_version='3.6.8 per sys_python.txt; stdlib extraction only',env_roots=inputs['env_roots'],receipt=inputs['files']['env'],
        versions=env['versions'],receipt_content=env,
        archive_map={'a4.tar':['v/py','v/boot.py','v/site'],'a3.tar':['q/env.json','q/policy.json','q/vnice.sh','q/terminator.sh'],
                     'r0-r2':'Base runtime; all package-pinned parts listed in MISSING.json; member mapping checked at extraction.'},
        local_base_env=STAGE+'/runtime/m/ap/19252904/e',local_base_python='/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12',
        audit='Reader trusts interpreter sysconfig roots plus the pinned v/site env_roots. Probe verifies every framework module against these roots before prepare and before the idle gate.',
        unresolved='Runtime bytes and member lists are absent; import/ABI compatibility must pass on target. No pip, downloads or fallback environment.')))
write(O/'ASSET_BUILD.json',dict(source_files=len(source),source_bytes=sum(p['bytes'] for p in source.values()),
    step=400,baseline_rows=len(prefix),missing_runtime_bytes=runtime_packed,estimated_peak_bytes=budget['estimated_peak_bytes']))
print(json.dumps(read(O/'ASSET_BUILD.json'),sort_keys=True))
