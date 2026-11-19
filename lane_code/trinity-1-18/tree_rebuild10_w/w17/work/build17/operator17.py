"""Exact available pins, source-config locations, and unresolved milestone fields."""
from pathlib import Path
import sys,json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build17';E=L.parent;O=B/'proofs/operator';O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.p3_provenance import load,file_pin,sha256
cfg=load(B/'inputs/kit_config.json')
configs={k:E/p for k,p in dict(A='ext/r1_ops/work/snap_fac07052/out/config.json',
 C='ext/r1_ops/work/snap_6a5c7d00/out/config.json',Cprime='inputs/p_configs/cprime_31abe087.json',
 runtime='inputs/p_configs/RUNTIME_CONFIG_171377_673bc60f.json').items()}
records={};locations={};cluster_by_hash={}
def pairs(value):
    if isinstance(value,dict):
        if isinstance(value.get('path'),str) and isinstance(value.get('sha256'),str):yield value
        for k,v in value.items():
            if len(k)==64 and isinstance(v,str) and v.startswith('/'):yield dict(path=v,sha256=k)
            yield from pairs(v)
    elif isinstance(value,list):
        for v in value:yield from pairs(v)
for k,p in configs.items():
    c=load(p);locations[k]=dict(config=file_pin(p),output=c['output'],preparation_output=c['preparation_output'],
                               streams=c['streams'],s1_routing=c['s1_routing'],continuation=c.get('continuation'))
    for pin in pairs(c):cluster_by_hash.setdefault(pin['sha256'],[]).append(dict(path=pin['path'],source_config=str(p)))
prep=E/'ext/r1_ops/work/adm171377/prepare_9b0c4b095487492a80bd5e9030d5bbc0/prepared/receipt.json'
locations['recorded_preparation']=dict(pin=file_pin(prep),model=load(prep)['model'])
seen=set()
def add(pin,depth=0,role=None):
    source=Path(pin['path']);h=pin['sha256'];key=(str(source),h)
    if key in seen:return
    seen.add(key)
    allowed=source.is_relative_to(L) or source.is_relative_to(E/'ext') or source.is_relative_to(E/'inputs') or source.is_relative_to(Path('/scratch/jjyeung/n30_mirror'))
    exists=allowed and source.is_file()
    cluster=cluster_by_hash.get(h,[])
    category='already_on_cluster' if cluster or h=='210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443' else 'upload_from_node' if exists else 'unresolved'
    record=dict(source=str(source),staged_name='u/'+h,bytes=source.stat().st_size if exists else None,
                sha256=h,category=category,cluster_sources=cluster,source_evidence=role,
                status='available' if exists else 'not rerun: input absent ('+str(source)+')')
    if h=='210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443':
        record['cluster_receipt']=locations['A']['streams']['vqa']
        record['cluster_database_path']=None
        record['source_evidence']='P configs bind the source receipt at ap/69d2930d/d.json. Its original database locator is absent from supplied metadata. The packet does not substitute the unverified proposed path in v7_JOB_PATHS.json.'
    records[key]=record
    if exists and depth<8 and source.suffix=='.json' and source.stat().st_size<10_000_000:
        try:child=load(source)
        except (ValueError,UnicodeError):return
        for p in pairs(child):add(p,depth+1,str(source))
for pin in pairs(cfg):add(pin)
add(file_pin(B/'inputs/kit_config.json'))
for role,c in locations.items():
    if role=='recorded_preparation':continue
    for pin in pairs(c['s1_routing']):add(pin,role=str(configs[role]))
    for pin in c['streams'].values():add(pin,role=str(configs[role]))
add(load(prep)['model'],role=str(prep))
for folder in ('kits/r1',):
    for p in (B/folder).rglob('*'):
        if p.is_file():
            pin=file_pin(p);records[(str(p),pin['sha256'])]=dict(source=str(p),staged_name=str(p.relative_to(B/'kits/r1')),
                bytes=p.stat().st_size,sha256=pin['sha256'],category='upload_from_node',status='available',cluster_sources=[])
rows=sorted(records.values(),key=lambda r:(r['category'],r['staged_name']))
unique={r['sha256']:r for r in rows if r['category']=='upload_from_node'}
milestone=[]
for i,(role,locator) in enumerate([
 ('artifact pin list','export/artifact.json'),('runtime config','P persisted runtime config recorded by h.json'),
 ('binding','<runtime output>/binding.json'),('preparation','runtime config preparation pin'),
 ('complete','<runtime output>/checkpoint_000400 or checkpoint_000600[/UUID]/complete.json'),
 ('rng files','complete.json files entries rng*'),('layouts','complete.json layouts and each referenced layout'),
 ('stream receipts','preparation streams/*/receipt'),('stream indices','preparation indices/order closure'),
 ('trusted handover receipt','h.json, SHA-256 obtained independently from the trusted ledger'),
 ('model manifest','preparation/model pin; recorded example in P_LOCATIONS.json'),
 ('tokenizer and configuration metadata','every metadata file named in the pinned model manifest; preserve one opaque parent directory'),
 ('weights archive','one object-storage tar containing heads and full_weights manifest/index/shards')]):
    milestone.append(dict(role=role,source=locator,staged_name=f'u/{i:064x}',bytes=None,sha256=None,
                          category='produced_at_milestone',status='not supplied; operator must resolve from the real export'))
request=dict(config=None,staged_pins=[],room_audit=None,frame_roots=[],weights=True,milestone=400,
             device='cuda:0',memory_gib=180)
summary=dict(known_unique_upload_bytes=sum(r['bytes'] for r in unique.values()),upload_files=len(unique),
             unknown_input_sizes=sum(r['bytes'] is None for r in rows),milestone_fields=len(milestone),
             total_upload_bytes_complete=False,v7_cluster_database_locator_verified=False,
             full_operator_packet_complete=False,kit_GO=False)
for name,value in [('STAGING',rows),('P_LOCATIONS',locations),('MILESTONE_INPUTS',milestone),('REQUEST_TEMPLATE',request),('SUMMARY',summary)]:
    (O/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
old=E/'w16b/work/tree_r1/launch_r1/p_handover_receipt.py';new=L/'work/tree_r1/launch_r1/p_handover_receipt.py'
assert old.read_bytes()==new.read_bytes()
(O/'P_PRODUCER_EQUALITY.json').write_text(json.dumps(dict(byte_equal=True,previous=file_pin(old),current=file_pin(new)),indent=2)+'\n')
lines=['# Mode q operator packet','',
 'GO=false. This is an unsubmitted review packet. The native end-to-end fixture remains blocked; source details with unknown sizes remain unresolved.','',
 '1. Stage the files in STAGING.json under their opaque names. Reuse the cluster data named by P’s own configs in P_LOCATIONS.json. For v7, resolve the database from P’s pinned ap/69d2930d/d.json and require the listed database hash; the exact locator was not supplied here. Do not upload the local v7 database.',
 '2. After P publishes the selected milestone, retain MILESTONE_INPUTS.json’s metadata subset, P’s model manifest and tokenizer/config files, and the one export tar. Obtain the h.json pin from the trusted ledger. No checkpoint state shard is an N input. Verify every staged size and SHA-256, and unpack export members under an opaque root. Keep manifest bytes unchanged; map their hashes in persisted_files. Keep tokenizer/config basenames inside an opaque parent so the native processor can load them.',
 '3. Resolve REQUEST_TEMPLATE.json with a native host runtime configuration, routing manifests, the pinned room audit, frame roots and all staged pins. The real export must replace the parent artifact in init_artifact while r2_identity retains the step-544 lineage. Set routing_opener_init=keep. Mode q creates v.json before preparation. CPU: device=cpu and memory_gib=240, use b/q.sh. GPU: device=cuda:0 and memory_gib=180, use b/q1.sh on a GPU with at least 80 GiB (GUESS sizing). The operator supplies the submission name at submission. This build submits nothing.',
 '4. Read RESULT.json. Require status=ADMIT, the requested absolute milestone, all native stages and every rank’s finite first-batch losses. GO remains false. A metadata-only ADMIT does not qualify a weight-loading proof.','',
 'The room gate certifies K1/R0 removal from the three pinned slices. The v7 census reports resolvable hits and unresolved rows separately; the bound EXCLUSIONS record certifies only its named build population. Neither record establishes overlap-free legacy v7 rows.','',
 'STAGING.json supplies every discovered static pin, category, source, opaque name, size and hash. MILESTONE_INPUTS.json contains unresolved values, not guessed pins. SUMMARY.json gives known unique upload bytes; the full total is not yet knowable. The tree archive is already inside the R1 kit and is counted once. SIZING.json records the unmeasured resource estimates.']
(O/'OPERATOR.md').write_text('\n\n'.join(lines)+'\n')
(B/'STATUS.md').write_text((B/'STATUS.md').read_text()+'\nStep 4 packet staged. Static available inputs and P-config paths are exact. Real milestone pins/sizes and the database locator inside P’s v7 source receipt remain unresolved. Evidence: proofs/operator/.\n')
print(json.dumps(summary))
