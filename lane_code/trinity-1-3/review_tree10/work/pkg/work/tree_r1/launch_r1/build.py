"""Seal an unsubmitted R1 kit, its input requirements and CPU-host request."""
import base64,hashlib,json
from pathlib import Path
from student_pilot.p3_provenance import digest,load,sha256
from student_pilot.source_seal import inventory,archive,check_archive
from launch_r2.build import capsule_json,scan,relocate

TREE=Path(__file__).resolve().parents[1]


def verify(root):
    root=Path(root)
    expected={name:h for h,name in (line.split('  ',1) for line in (root/'SHA256SUMS.txt').read_text().splitlines())}
    actual={str(p.relative_to(root)):sha256(p) for p in root.rglob('*') if p.is_file()
            and str(p.relative_to(root)) not in ('SHA256SUMS.txt','BUILD.json')}
    if expected!=actual:raise ValueError('R1_KIT_CONTENT_DIFFERS')
    scan(root)
    if (root/'k/8.json').exists():
        cfg=load(root/'k/c.json');evidence=load(root/'k/8.json')
        pin=cfg['r1_training']['mix']
        entry=load(root/'k/s.json')['entries'][pin['path']]
        raw=base64.b64decode(entry['payload'],validate=True)
        if hashlib.sha256(raw).hexdigest()!=pin['sha256'] or evidence['report_sha256']!=pin['sha256']:
            raise ValueError('R1_KIT_MIX_EVIDENCE_DIFFERS')
    return sha256(root/'SHA256SUMS.txt')


def build(cfg, inputs, output):
    output=Path(output)
    if output.exists() and any(output.iterdir()):raise ValueError('R1_KIT_ROOT_NOT_EMPTY')
    output.mkdir(parents=True,mode=0o700,exist_ok=True)
    for name in ('b','k','o'):(output/name).mkdir(mode=0o700)
    files=inventory(TREE);seal=digest(files)
    archive_path=output/'k'/('t_'+seal[:16]+'.tar')
    archive(TREE,archive_path,files,compress=True)
    check_archive(dict(path=str(archive_path),sha256=sha256(archive_path)),files)
    source=dict(path=str(archive_path.relative_to(output)),sha256=sha256(archive_path),tree_sha256=seal)
    cfg=load(cfg)
    # External exclusion records enter only through normal pinned-input staging.
    from student_pilot.p3_provenance import pinned
    staged_records={pin['path']:pinned(pin) for pin in cfg.get('remove_files', [])
                    if Path(pin['path']).is_file()}
    if cfg.get('scene_division'):
        staged_records[cfg['scene_division']['path']]=pinned(cfg['scene_division'])
    cfg.update(output='runs/r',preparation_output='o/p')
    from student_pilot.p3_provenance import source_files
    sources={str(p.relative_to(TREE)):sha256(p) for p in source_files([TREE/'student_pilot/carrier_c1_run.py'])}
    code=dict(schema='c1-sealed-source-v1',commit='sha256:'+seal,tree_sha256=seal,files=files,
              archive={k:source[k] for k in ('path','sha256')},sources=sources,operation_sources=sources)
    (output/'k/7.json').write_bytes(capsule_json(code))
    cfg['code']=dict(path='k/7.json',sha256=sha256(output/'k/7.json'))
    paths={};cfg=relocate(cfg,paths)
    # Receipts remain opaque provenance. A missing deployment source stays required.
    entries={}
    for original,destination in paths.items():
        path=Path(original)
        if original in staged_records or (path.is_file() and inputs in path.parents and path.suffix in ('.json','.md')):
            raw=path.read_bytes();entries[destination]=dict(payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())
        else:entries[destination]=dict(required_parameter='verified_remote_source')
    init=load(inputs/'init.json')
    init_dest=cfg['init_artifact']['artifact']['path']
    artifact_member=next(k for k,v in init['archive']['files'].items() if v==init['artifact_sha256'])
    entries[init_dest]=dict(archive=dict(parts=init['archive']['parts'],sha256=init['archive']['sha256'],
        inventory=init['archive']['files']),member=artifact_member,sha256=init['artifact_sha256'])
    # Carry the already verified source substitutions for the sealed parent inputs.
    known=load(TREE/'launch_r2/staging_sources.json')
    def visit(value):
        if isinstance(value,dict):
            if value.get('path') in entries and value.get('sha256') in known:
                entries[value['path']]=known[value['sha256']]
            for v in value.values():visit(v)
        elif isinstance(value,list):
            for v in value:visit(v)
    visit(cfg)
    staging=dict(entries=entries,unresolved=sorted(k for k,v in entries.items() if 'required_parameter' in v))
    (output/'k/8.json').write_bytes(capsule_json(dict(report_file='out/MIX_R1.json',
        report_sha256=cfg['r1_training']['mix']['sha256'])))
    host=dict(schema='r1-host-request-v1',GO=False,binaries=['python3','bash','bwrap'],
        staging=None,routing_selection=None,
        required_assertions=['disk_plan','routing_selection','empty_root','runtime_binaries','directory_modes','scene_division'],
        missing=['Verified full staging closure and native path namespace','Regenerated routing selection and reviewed pin',
                 'Complete post-filter sampler indices','Real camera/pose/pointing frame-host preparation'])
    for name,value in [('c',cfg),('s',staging),('h',host),('a',dict(GO=False,source=source,config='k/c.json',host='k/h.json'))]:
        (output/'k'/f'{name}.json').write_bytes(capsule_json(value))
    (output/'b/wh.json').write_bytes((TREE/'launch_s1/b/wh.json').read_bytes())
    (output/'b/a.py').write_text('''import base64,hashlib,json,sys,tarfile
from pathlib import Path
def read(p):
 v=json.loads(p.read_text());r=base64.b64decode(v['payload'],validate=True)
 if hashlib.sha256(r).hexdigest()!=v['sha256']:raise ValueError('E01')
 return json.loads(r)
kit=Path(__file__).resolve().parents[1];control=read(kit/'k/a.json')
if len(sys.argv)!=3 or sys.argv[1] not in ('p','t'):raise ValueError('E02')
if sys.argv[1]=='t' and control['GO'] is not True:raise ValueError('E03')
root=Path(sys.argv[2]).resolve()
if root.exists() and any(root.iterdir()):raise ValueError('E04')
root.mkdir(parents=True,mode=0o700,exist_ok=True)
src=control['source'];p=kit/src['path']
if hashlib.sha256(p.read_bytes()).hexdigest()!=src['sha256']:raise ValueError('E05')
with tarfile.open(p) as t:t.extractall(root/'s',filter='data')
sys.path.insert(0,str(root/'s'))
from launch_r1.build import verify
verify(kit)
from launch_r1.entry import frame_host,admit
cfg=read(kit/'k/c.json')
if sys.argv[1]=='p':
 r=frame_host(cfg,root/'p',read(kit/'k/h.json'))
 print(json.dumps({'ok':r['status']=='PASS'}))
 sys.exit(0 if r['status']=='PASS' else 1)
admit(cfg)
from student_pilot.carrier_c1_run import train
train(cfg)
''')
    (output/'job.sh').write_text('#!/bin/bash\nset -eu\numask 077\nexec python3 -I -s -B b/a.py t "$1"\n')
    (output/'b/f.sh').write_text('#!/bin/bash\nset -eu\numask 077\nexport CUDA_VISIBLE_DEVICES=""\nexec python3 -I -s -B b/a.py p "$1"\n')
    manifest={str(p.relative_to(output)):sha256(p) for p in output.rglob('*') if p.is_file()}
    (output/'SHA256SUMS.txt').write_text(''.join(f'{h}  {name}\n' for name,h in sorted(manifest.items())))
    result=dict(GO=False,kit_sha256=verify(output),source_seal=seal,config_sha256=sha256(output/'k/c.json'),
        frame_host_sha256=sha256(output/'k/h.json'),staging_sha256=sha256(output/'k/s.json'),unresolved=len(staging['unresolved']))
    (output/'BUILD.json').write_bytes(capsule_json(result))
    return result
