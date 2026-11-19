"""Build the small, authenticated CPU-only delivery from the supplied mirrors."""
from pathlib import Path
import hashlib
import json
import tarfile
import shutil
import subprocess

L = Path('/scratch/jjyeung/orch_n30/so_reads228')
A = Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4')
S = Path('/scratch/jjyeung/orch_n30/so_read/out')
O = L/'out'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')

def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)

def main():
    print(subprocess.check_output(['date','-u'], text=True).strip())
    public=json.loads((A/'package/0.json').read_text())
    assert sha(A/'package/0.tgz') == public['payload_sha256']
    for p in (A/'package').rglob('*'):
        if p.is_file():copy(p, O/'A4/package'/p.relative_to(A/'package'))
    for name in ('tower_sequence.py','unpack_return.py','fetch_return.py'):
        copy(A/name, O/'A4'/name)
    # These two files are operator-fillable and absent from PACKAGE.json's seal.
    copy(A/'ret/metadata/INPUTS.json', O/'A4/package/a/1.json')
    copy(A/'ret/metadata/EXPORT_PIN.json', O/'A4/package/a/export.json')
    inp=json.loads((A/'ret/metadata/INPUTS.json').read_text())
    export=json.loads((A/'ret/metadata/EXPORT_PIN.json').read_text())
    seed=json.loads((A/'package/a/0.json').read_text())
    with tarfile.open(A/'package/0.tgz') as t:
        members=t.getmembers()
        for m in members:
            if not m.isfile() or Path(m.name).is_absolute() or '..' in Path(m.name).parts:
                raise ValueError(m.name)
            dst=O/'A4/src'/m.name;dst.parent.mkdir(parents=True,exist_ok=True)
            dst.write_bytes(t.extractfile(m).read())
        cfg=json.loads(t.extractfile('9.json').read())
    assert cfg['export_binding']['step']==export['step']==200
    assert sha(O/'A4/package/a/export.json')==inp['export_pin']['sha256']
    # Preserve a small real prefix for exact comparator and real-unpacker tests.
    ref=O/'reference'
    for name in ('INPUTS.json','EXPORT_PIN.json','IDENTITY.json','RETURN_ID.json'):
        copy(A/'ret/metadata'/name, ref/'metadata'/name)
    prefix=[];schedule=[3,0,1,2,4]
    for kind in schedule:
        journal=A/'ret/metadata/reads/0/metadata/journals'/str(kind)/'0'
        rows=[json.loads(line) for line in (journal/'items.jsonl').read_text().splitlines()]
        prefix.extend(rows)
        if kind==3:
            target=ref/'metadata/reads/0/metadata/journals/3/0';target.mkdir(parents=True,exist_ok=True)
            (target/'items.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows[:50]))
            copy(journal/'environment.json',target/'environment.json')
    manifest=json.loads((O/'A4/src/items/devs1_routed.json').read_text())
    order=[r for k in schedule for r in manifest['items'] if r['question_type']==cfg['order'][k]]
    assert [r['id'] for r in prefix]==[r['id'] for r in order]
    write(O/'FIRST50.json',dict(schema=1,source=str(A/'ret'),plan_sha256=public['plan_sha256'],
          orchard_prefix_sha256=hashlib.sha256(json.dumps(prefix[:50],sort_keys=True,separators=(',',':')).encode()).hexdigest(),
          export=export,items=[dict(id=r['id'],type=r['question_type']) for r in order[:50]],
          full_order=[r['id'] for r in order],item_manifest_sha256=sha(O/'A4/src/items/devs1_routed.json')))
    write(O/'A4_PINS.json',dict(public=public,operator_sha256=sha(A/'tower_sequence.py'),
        operators={name:dict(bytes=(A/name).stat().st_size,sha256=sha(A/name)) for name in ('tower_sequence.py','unpack_return.py','fetch_return.py')},
        inputs_sha256=sha(A/'ret/metadata/INPUTS.json'),export_sha256=sha(A/'ret/metadata/EXPORT_PIN.json'),
        package={str(p.relative_to(O/'A4/package')):dict(bytes=p.stat().st_size,sha256=sha(p))
                 for p in (O/'A4/package').rglob('*') if p.is_file()},
        source={str(p.relative_to(O/'A4/src')):dict(bytes=p.stat().st_size,sha256=sha(p))
                 for p in (O/'A4/src').rglob('*') if p.is_file()}))
    assets=json.loads((O/'A4/src/orchard_h10/vendor/ORCHARD_ASSETS.json').read_text())
    stage='/scratch/jjyeung/a4228'
    files=[]
    for p in (O/'A4/package').rglob('*'):
        if p.is_file():files.append(dict(role='package',target=stage+'/kit/A4/package/'+str(p.relative_to(O/'A4/package')),
            bytes=p.stat().st_size,sha256=sha(p),pin_basis='package seal or authenticated return fill',
            source=dict(kind='Trinity_delivery',node='trinity-1-18',path=str(p))))
    for name in ('tower_sequence.py','unpack_return.py','fetch_return.py'):
        p=O/'A4'/name
        files.append(dict(role='operator',target=stage+'/kit/A4/'+name,bytes=p.stat().st_size,sha256=sha(p),
            source=dict(kind='Trinity_delivery',node='trinity-1-18',path=str(p))))
    groups=[]
    for i,a in enumerate(inp['archives']):
        parts=[]
        for j,p in enumerate(a['parts']):
            target=f'{stage}/archives/a{i}/{j}'
            row=dict(role='A4_input_archive',group=f'a{i}',**p,target=target,
                     source=dict(kind='Orchard_IO_governor_stream',path=p['path'],
                     register_command=None,launch_command=None,todo='Coordinator must supply commands from IO-governor README; mirror absent. Download once; no agent SSH.'))
            files.append(row);parts.append(dict(**p,target=target))
        groups.append(dict(id=f'a{i}',parts=parts,sha256=a['sha256'],expanded_bytes=a['expanded_bytes'],
                           destination=cfg['logical']+'/d'))
    runtime=[]
    for i,g in enumerate(assets['groups']):
        parts=[]
        for j,(p,n,h) in enumerate(g):
            row=dict(role='template_runtime_archive',group=f'r{i}',path=p,bytes=n,sha256=h,
                     target=f'{stage}/archives/r{i}/{j}',source=dict(kind='Orchard_IO_governor_stream',path=p,
                     register_command=None,launch_command=None,todo='Obtain the registered stream command from the coordinator; do not infer a transport URL.'))
            files.append(row);parts.append({k:row[k] for k in ('path','bytes','sha256','target')})
        runtime.append(dict(id=f'r{i}',parts=parts,destination='/scratch/jjyeung',
                            expanded_bytes=None,todo='Inspect authenticated archive member map; stage only /scratch runtime closure, never /home or /data.'))
    expanded=[]
    for name,p in inp['files'].items():
        source=dict(kind='member_of_authenticated_input_or_runtime_archive',todo='Resolve member-to-archive map on first authorized staging; do not download duplicate loose weights.')
        if name=='sam_checkpoint':source=dict(kind='existing_on_target_user_report',path=p['path'],verified=False,
                todo='Verify full SHA256 locally; matching size alone is insufficient. Archive fallback only if pin differs.')
        expanded.append(dict(role=name,**p,target=p['path'],source=source))
    for name,p in export['preparation'].items():
        expanded.append(dict(role='preparation_'+name,**p,target=cfg['logical']+'/d/'+p['path'],
                source=dict(kind='archive_member',group='a5')))
    packed=sum(p['bytes'] for p in files if p['role']=='A4_input_archive')
    unpacked=sum(a['expanded_bytes'] for a in inp['archives'])
    runtime_packed=sum(p['bytes'] for p in files if p['role']=='template_runtime_archive')
    # Runtime expanded size is unknown in the supplied files, so enforce a bound rather than invent a measurement.
    budget=dict(limit_bytes=150_000_000_000,input_archives_bytes=packed,input_expanded_bytes=unpacked,
                runtime_archives_bytes=runtime_packed,runtime_expanded_allowance_bytes=40_000_000_000,
                code_returns_cache_allowance_bytes=5_000_000_000,free_floor_bytes=200*1024**3,
                estimated_peak_bytes=packed+unpacked+runtime_packed+40_000_000_000+5_000_000_000,
                basis='Input sizes read from pins; runtime expansion and 5 GB operating allowance are estimates, enforced as caps. Retain archives; no deletion needed.')
    assert budget['estimated_peak_bytes']<budget['limit_bytes']
    write(O/'STAGE_PLAN.json',dict(schema='read228-stage-v1',target_host='trinity-2-28',logical=cfg['logical'],
        stage_root=stage,active_export=dict(step=200,member_directory='m200',reason='Sealed A4 plan and Orchard job 172744 require m200; a/0.json is a template.'),
        files=files,input_archives=groups,runtime_archives=runtime,expanded_files=expanded,
        code=dict(archive=stage+'/kit/A4/package/0.tgz',destination=cfg['logical']+'/p',
                  expanded_bytes=sum(m.size for m in members),files=len(members),sha256=public['payload_sha256']),
        environment=dict(python=inp['python'],env_roots=inp['env_roots'],target_env_root='/scratch/jjyeung/envs',
            receipt=inp['files']['env'],versions=None,python_runtime='3.12 (template closure; exact production version checked at staging)',
            constraints=['prepare.py requires transformers >=5.12 and exact receipt versions for torch, torchvision, transformers, scipy',
                         'torch 2.11 + CUDA 12.9 is dispatch information, not a recovered A4 env receipt',
                         'No pip/conda installation or downloads inside run228',
                         'a3.tar contains q/env.json; its bytes are absent from this mirror',
                         'v/py and v/site may alias the staged /scratch/jjyeung/envs closure; resolve targets and preserve pins']),
        requested_m544=dict(eligible_for_A4_parity=False,reason='Contradicts sealed export_binding and returned m200 identity; do not stage both exports for this run.',
            archive=seed['archives'][0],files={n:p for n,p in seed['files'].items() if '/m544/' in p['path']}),
        budget=budget,io=dict(governor_readme_mirrored=False,network_limit_bytes_per_second=8_000_000,
            read_shared_limit_bytes_per_second=8_000_000,write_shared_limit_bytes_per_second=4_000_000,
            total_user_limit_bytes_per_second=18_000_000,streams=1,admin_plan_required_for_more_than_30GB=True,
            todo='Coordinator must authorize heavy IO and read /data3/jjyeung/orch_n13_20261026/io_governor/README.md, register ONE sequential stream, and supply its exact register/launch commands. No transfer is run by this kit.'),
        todos=['Recover and verify q/env.json and runtime member map before selecting an env; refuse CUDA execution until versions agree.',
               'Coordinator supplies authenticated IO-governor register/launch commands and authorizes heavy staging.',
               'Target SAM file is user-reported only; hash on 2-28 before reusing it.',
               'Run first 50 OFF items on 2-28; compare with authenticated Orchard return. No Ada fit/parity has been measured.']))
    # Carry the reviewed extension additions and their original provenance, without importing them in OFF.
    ext=O/'so_read';ext.mkdir(exist_ok=True)
    for name in ('01_bounded_read_caches.diff','02_atomic_scene_shards.diff','03_production_integration.diff','MANIFEST.json'):
        copy(S/'patches'/name,ext/name)
    copy(S/'kit_parity50/EXTENSION_PINS.json',ext/'EXTENSION_PINS.json')
    write(O/'ASSET_BUILD.json',dict(files=927,source_expanded_bytes=sum(m.size for m in members),
        baseline_items=636,first50_matched_orchard_order=True,active_step=200,estimated_peak_bytes=budget['estimated_peak_bytes']))
    print(json.dumps(json.loads((O/'ASSET_BUILD.json').read_text()),sort_keys=True))

if __name__=='__main__':main()
