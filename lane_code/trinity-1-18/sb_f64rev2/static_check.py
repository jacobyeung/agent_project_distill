"""Verify the fixed archive, installed source delta and honest missing-input claims without Git."""
import hashlib, io, json, re, tarfile, difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parent; FIX=ROOT.parent/'sb_f64fix'; KIT=FIX/'kit'; SRC=ROOT.parent/'sb_f64'
inputs={}
def read(p):
    p=Path(p); b=p.read_bytes(); inputs[str(p)]=hashlib.sha256(b).hexdigest(); return b
def obj(p): return json.loads(read(p))
read(__file__)
archive=FIX/'out/sb_f64fix.tar'; blob=read(archive)
expected='da6405ae0f0095414deecf3727a7aa88937686bfcbfa2dcf09e5aa8b1678a4bb'
archive_mismatches=[]; archived={}
with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
    for m in tar.getmembers():
        if m.isfile() and m.name.startswith('kit/'):
            data=tar.extractfile(m).read(); archived[m.name]=hashlib.sha256(data).hexdigest()
            p=FIX/m.name
            if not p.is_file() or read(p)!=data: archive_mismatches.append(m.name)
sums=[]
for line in read(KIT/'SHA256SUMS').decode().splitlines():
    sha,name=line.split(maxsplit=1); p=KIT/name
    if hashlib.sha256(read(p)).hexdigest()!=sha: sums.append(name)
patch=read(KIT/'patches/tree_r1_to_f64.patch').decode()
changed=re.findall(r'^\+\+\+ tree_f64/(\S+)',patch,re.M)
diffs=[]
for rel in changed:
    a=SRC/'pkg/work/tree_r1'/rel;b=SRC/'pkg/work/tree_f64'/rel
    old=read(a).decode() if a.is_file() else ''; new=read(b).decode()
    diffs.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='tree_r1/'+rel,tofile='tree_f64/'+rel))
# Timestamps and diff invocation lines are not part of the source patch.
def canonical(text):
    return '\n'.join(line.split('\t')[0] if line.startswith(('--- ','+++ ')) else line for line in text.splitlines() if not line.startswith('diff '))
patch_matches=canonical(patch)==canonical(''.join(diffs))
(ROOT/'out/INDEPENDENT_TREE_DIFF.patch').write_text(''.join(diffs))
cfg=obj(KIT/'configs/r1_config_f64.json');rc=obj(KIT/'read/READ_CONFIG_F64.json');plan=obj(KIT/'read/STUDENT_FRAMES_PLAN.json')
missing={}
for key,owner in [('preparation','tree_rebuild (W)'),('code','orchestrator'),('admission','independent reviewer'),('depth_init','P x_ee227714, staged by W')]:
    p=Path(cfg['preparation_output'])/'receipt.json' if key=='preparation' else Path(cfg[key]['path'])
    missing[key]=dict(path=str(p),status='EXISTS' if p.is_file() else 'MISSING',owner=owner)
for key in ['r2_sampling','preparation','r1_training.row_plan_sha256','r1_training.host_receipt','r1_training.review','r1_training.store_hashes.pose','r1_training.store_hashes.routing','r1_training.store_hashes.pointing']:
    v=cfg
    for k in key.split('.'): v=v.get(k) if isinstance(v,dict) else None
    missing['config:'+key]=dict(location=str(KIT/'configs/r1_config_f64.json')+':'+key,status='PRESENT' if v else 'MISSING',value=v,owner='W production binding; host audit; independent review')
missing['student_manifest']=dict(location=str(KIT/'read/READ_CONFIG_F64.json')+':settings_add.student_manifest',status='MISSING',value=rc['settings_add']['student_manifest'],owner='reader lane')
missing['POOL.jsonl']=dict(path='/scratch/jjyeung/orch_cd/derivgen/review_pool/POOL.jsonl',status='EXISTS' if Path('/scratch/jjyeung/orch_cd/derivgen/review_pool/POOL.jsonl').is_file() else 'MISSING',owner='derivgen/review-pool owner (not named in kit)')
refs={}
for key,entry in [('training_config',rc['training_config']),('module',rc['code']['module']),('patch',rc['code']['patch']),('frames_plan',rc['student_frames_plan'])]:
    actual=hashlib.sha256(read(KIT/entry['path'])).hexdigest();refs[key]=dict(matches=actual==entry['sha256'],actual=actual)
head_candidates=[]
folder=ROOT.parent/'tree_rebuild10_w/ext/preceipts'
if folder.is_dir():
    for p in folder.rglob('*.json'):
        h=hashlib.sha256(read(p)).hexdigest();head_candidates.append(dict(path=str(p),sha256=h,matches=h==cfg['depth_init']['sha256']))
for p in [FIX/'out/FIX_REPORT.md',KIT/'F64_REPORT.md',KIT/'DESIGN_F64.md',KIT/'CHANGES.md',KIT/'scripts/mem_pilot.py',KIT/'scripts/token_audit.py',KIT/'scripts/nest_store.py',KIT/'read/f64_read.py']:
    read(p)
for rel in ['student_pilot/carrier_c1_run.py','student_pilot/carrier_c1.py','student_pilot/full_ft.py']:
    read(SRC/'pkg/work/tree_f64'/rel)
prior=obj(ROOT.parent/'sb_f64rev/out/static_review.json')
source_recheck=[]
for name,expected_sha in prior['input_sha256'].items():
    p=Path(name)
    if any(p.is_relative_to(SRC/'pkg/work'/t) for t in ['tree_r1','tree_f64']):
        actual_sha=hashlib.sha256(read(p)).hexdigest() if p.is_file() else None
        source_recheck.append(dict(path=name,matches=actual_sha==expected_sha))
value=dict(prior_review_source_files_checked=len(source_recheck),prior_review_source_mismatches=[r for r in source_recheck if not r['matches']],command='bash run_cpu.sh static_check.py',input_sha256=inputs,archive_sha256=inputs[str(archive)],archive_matches_expected=inputs[str(archive)]==expected,archive_kit_members=len(archived),archive_vs_workspace_mismatches=archive_mismatches,checksum_mismatches=sums,patch_matches_installed_tree=patch_matches,changed_files=changed,read_config_pins=refs,missing_inputs=missing,depth_init_staged_candidates=head_candidates,reader_plan=dict(captures=len(plan['captures']),decode_ordinals=sum(len(v['decode']) for v in plan['captures'].values()),claimed_already_decoded=rc['student_frames_plan']['already_decoded_in_tower_dense_manifest'],claimed_pending=rc['student_frames_plan']['frames_to_decode']-rc['student_frames_plan']['already_decoded_in_tower_dense_manifest']))
(ROOT/'out/static_review.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({k:v for k,v in value.items() if k not in ('input_sha256','missing_inputs')},indent=2))
