"""Recompute local evidence without cloud calls or historical-pilot assumptions."""
import ast, base64, hashlib, json, sys, tarfile
from pathlib import Path
B=Path(__file__).resolve().parents[1]
W=B.parents[1]/'work'
R=B/'out/c8/sources/sj/orch_cd/evalx/work/milestone'
sys.path[:0]=[str(R/'orchard_native'),str(R)]
import native_common as C
import native_pin_graph as G
import native_local_check as L

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as s:
        for chunk in iter(lambda:s.read(1024**2),b''):h.update(chunk)
    return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())
def dump(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
f=load(B/'out/c8/FAMILY_C8.json');old=load(W/'p9/metadata/FAMILY.json')
objects={};member_bytes={};members={};missing=[]
for part in f['assets']['small_objects']:
    path=B/'out/c8/code_c8.tar' if part['role']=='code' else W/'obj'/Path(part['name']).name
    if not path.is_file() or path.stat().st_size!=part['bytes']:
        missing.append(part['role']);continue
    h=hashlib.sha256();md5=hashlib.md5()
    with path.open('rb') as s:
        for chunk in iter(lambda:s.read(1024**2),b''):h.update(chunk);md5.update(chunk)
    assert h.hexdigest()==part['sha256']
    inventory={}
    with tarfile.open(str(path)) as t:
        for item in t:
            assert item.isfile() and item.name not in inventory and '..' not in Path(item.name).parts
            data=t.extractfile(item).read()
            inventory[item.name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            members[item.name]=dict(inventory[item.name],mode=item.mode,role=part['role'])
            if item.name.endswith(('.json','.py','.sh','.jsonl')) and len(data)<16*1024**2:
                member_bytes[item.name]=data
    assert inventory==part['members']
    assert sum(x['bytes'] for x in inventory.values())==part['expanded_bytes']
    objects[part['role']]=dict(path=str(path),sha256=h.hexdigest(),bytes=path.stat().st_size,
        md5=base64.b64encode(md5.digest()).decode(),members=len(inventory),inventory_verified=True)
    if part['md5']!='PENDING_UPLOAD':assert objects[part['role']]['md5']==part['md5']

logical='/scratch/jjyeung/orch_cd/evalx/work/milestone/'
member_prefix='sj/orch_cd/evalx/work/milestone/'
def member_for(path):
    if path.startswith('/scratch/jjyeung/'):return 'sj/'+path[len('/scratch/jjyeung/'):]
    fsw='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/'
    if path.startswith(fsw):return 'fsw/'+path[len(fsw):]
    raise ValueError(path)
def pin_checked(pin):
    member=member_for(pin['path']);assert members[member]['sha256']==pin['sha256'];return members[member]
for p,digest in f['code_pins'].items():pin_checked(dict(path=p,sha256=digest))
for n,digest in f['bootstrap_pins'].items():assert f['code_pins'][logical+n]==digest
for p,digest in f['worker_contract']['adapter_pins'].items():assert f['code_pins'][p]==digest
for n,digest in f['worker_contract']['kernel_source_pins'].items():assert digest==f['code_pins'][logical+'native/out2/'+n+'.py']
tree={n:sha(W/'tree'/n) for n in f['assets']['tree_sources']}
assert tree==f['assets']['tree_sources']
tree_digest=C.canonical(tree)
tree_manifest=load(R/'native/out2/RUNTIME_TREE.json')
assert tree_manifest['sources_sha256']==tree_digest
assert G.constants(R/'native/out2/runtime_tree.py',{'EXPECTED_SOURCES_SHA'})['EXPECTED_SOURCES_SHA']==tree_digest
import native_bootstrap as bootstrap
assert bootstrap.SOURCE==tree_digest and bootstrap.ARCHIVE==f['assets']['runtime']['sha256']
artifact=load(W/'obj/m544_artifact.json');artifact_sha=sha(W/'obj/m544_artifact.json')
assert artifact_sha==load(W/'p9/metadata/CONFIG.json')['worker']['artifact']['sha256']
assert artifact['step']==544
mask=load(R/'orchard_native/MASK_CACHE_C8_BOUND.json')
oldmask=load(R/'orchard_native/MASK_CACHE_P6_BOUND.json')
assert [k for k in mask if mask[k]!=oldmask[k]]==['producer_sha256']
assert mask['producer_sha256']==f['worker_contract']['kernel_source_pins']['nomdg']
asset_checks={}
for n in ('worker_entrypoint','sitecustomize','vnice','frame_puller','model_manifest'):
    asset_checks[n]=pin_checked(f['assets'][n])
asset_checks['fla.manifest']=pin_checked(f['assets']['fla']['manifest'])
for n in ('vnice.sh','terminator.sh'):
    assert members['sj/orch_cd/evalx/work/camera/vnice/'+n]['mode']==0o755
for pin in f['worker_contract']['inputs'].values():pin_checked(pin)
for n in ('config','data_receipt','raw_tower'):pin_checked(f['worker_contract'][n])

sources={}
for p in sorted(R.rglob('*.py')):
    ast.parse(p.read_text(),filename=str(p));sources[str(p.relative_to(R))]=sha(p)

pin_graph_log=dict(constants_executed=True,static_tree_checks_executed=True,
    complete_graph_executed=False,reason='Historical P5/P3 authority objects and production runtime are not supplied; no earlier-pilot assumption is promoted to a C8 pass.')
local_log={}
try:L.objects(f['assets'])
except Exception as e:local_log['objects']=dict(status='EXPECTED_REFUSAL',error=str(e))
else:raise AssertionError('Placeholder cloud generation unexpectedly admitted')
try:L.scope(f)
except Exception as e:local_log['scope']=dict(status='NOT_EVALUATED',error=str(e))
else:local_log['scope']=dict(status='PASS')
dump(B/'out/NATIVE_PIN_GRAPH.json',pin_graph_log)
dump(B/'out/NATIVE_LOCAL_CHECK.json',local_log)

checks={
9:('Bootstrap copies equal shipped code',str(len(f['bootstrap_pins']))+' bootstrap hashes recomputed'),
15:('Exact member hashes and expanded sizes of available objects',json.dumps({k:v['members'] for k,v in objects.items()},sort_keys=True)+'; absent: '+','.join(missing)),
18:('Every sealed tree source and duplicated tree digest',str(len(tree))+' files; '+tree_digest),
21:('Worker and sitecustomize spec inputs equal exact members',json.dumps({k:asset_checks[k]['sha256'] for k in ('worker_entrypoint','sitecustomize')})),
22:('Model manifest equals exact model-object member',asset_checks['model_manifest']['sha256']),
26:('Frame puller equals exact code member',asset_checks['frame_puller']['sha256']),
30:('Both guard shell scripts have executable archive modes','0o755 for both; source hashes unchanged'),
33:('Sitecustomize equals code member',asset_checks['sitecustomize']['sha256']),
35:('Worker entrypoint equals worker source, code pin and bootstrap pin',asset_checks['worker_entrypoint']['sha256']),
37:('All adapter pins equal exact code members',str(len(f['worker_contract']['adapter_pins']))+' recomputed'),
42:('Mask producer equals nomdg; all other receipt fields unchanged',mask['producer_sha256']+'; scalar binding verified, cache-bind not executed'),
}
reasons={
1:'No C8 allocation or launch packet exists.',2:'No C8 BATCH payload exists.',3:'No C8 BATCH payload exists.',
4:'No C8 runtime configuration or allocation exists.',5:'Orchard environment cannot be tested on this host.',
6:'C8 REVIEW and ORDER are not supplied.',7:'C8 authority and upload are pending.',8:'No C8 launch token or ORDER exists.',
10:'No Orchard private job mount exists.',11:'GPU use is forbidden for this build.',
12:'Declared five-object size fits the cap; masks and geometry bytes are unavailable.',
13:'Code generation and md5 are PENDING_UPLOAD; missing archives are unverified.',
14:'Available code, metadata and model hashes pass; masks/geometry and cloud generation are unavailable.',
15:'Available archive inventories pass; masks and geometry inventories cannot be checked from absent bytes.',
16:'Runtime/overlay/closure archives are unavailable; retained identities alone are insufficient.',
17:'Required Python environment is absent.',19:'Local bwrap smoke succeeded, but the pinned production binary is unavailable.',
20:'FLA manifest pin passes; FLA runtime bytes are unavailable.',23:'Tokenizer/config subset is present; base weights are intentionally absent.',
24:'Depth weights are unavailable.',25:'Artifact metadata hash and step pass; export tensor transport is unavailable.',
27:'Frame inventory is retained, but frames.tar has not arrived.',28:'No C8 authority packet or worker namespace run exists.',
29:'No worker run was started.',31:'Runtime/source constants agree; production bootstrap flags/import path not executed.',
32:'Required interpreter and overlays are unavailable.',34:'Required runtime imports cannot be checked.',
36:'Whole-worker config admission has not executed.',38:'Input pins pass; complete real cohort path requires the missing runtime.',
39:'Kernel source pins agree; AST partition requires a supported Python runtime.',
40:'Tree bytes pass; authenticated model restoration has not executed.',41:'Preparation/source-seal/model authentication has not executed.',
42:'Producer-only draft pin passes static checks; actual cache-bind is blocked by the missing masks and runtime.',
43:'Masks object is incomplete.',44:'Raw G3T and real-frame objects are absent.',
45:'Core test drives real pilot terminal/project; no whole-worker pilot/full evidence exists.',
46:'No rehearsal or production return has been published or verified.'}
rows=[]
for item in G.ROWS[:46]:
    number,site,expected,actual,duplicate,kind=item
    status='PASS' if number in checks and number not in reasons else 'N/E'
    recomputed=checks[number][1] if number in checks else ''
    if number in reasons:recomputed=(recomputed+'; ' if recomputed else '')+reasons[number]
    rows.append(dict(check=number,site=site,expected=checks.get(number,(expected,''))[0],actual=recomputed,status=status))
dump(B/'out/PIN_AUDIT.json',dict(rows=rows,pass_count=sum(r['status']=='PASS' for r in rows),
    not_evaluated=sum(r['status']=='N/E' for r in rows),objects=objects,missing_objects=missing,
    artifact_sha256=artifact_sha,tree_files=len(tree),tree_digest=tree_digest,source_syntax_files=len(sources)))
text='# C8 pin audit\n\nThis table recomputes local evidence. N/E includes partial checks; it is not a pass or permission to launch.\n\n'
text+='| Check | Expected | Actual | Result |\n|---|---|---|---|\n'
for row in rows:text+='| {check} | {expected} | {actual} | {status} |\n'.format(**{k:str(v).replace('|','/') for k,v in row.items()})
text+='\nEvidence: `out/PIN_AUDIT.json`, `out/NATIVE_PIN_GRAPH.json`, and `out/NATIVE_LOCAL_CHECK.json`.\n'
(B/'out/PIN_TABLE.md').write_text(text)
print(json.dumps(dict(pass_count=sum(r['status']=='PASS' for r in rows),not_evaluated=sum(r['status']=='N/E' for r in rows),tree_files=len(tree))))
