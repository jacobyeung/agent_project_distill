"""Review artifacts, published phrase schema, and package without modifying the kit."""
from pathlib import Path
import hashlib, json, gzip, tarfile, sys, datetime
HERE = Path(__file__).resolve().parent
ROOT = Path('/scratch/jjyeung/orch_n30/sb_mask_carry')
OUT = ROOT/'out/v2'
sys.path.insert(0, str(ROOT/'kit_v2'))
import mc_common as C
import mc_phrase as PH
pins = {}
def read(p):
    p = Path(p); b = p.read_bytes(); pins[str(p)] = hashlib.sha256(b).hexdigest(); return b
def j(p):
    b=read(p);return json.loads(gzip.decompress(b) if str(p).endswith('.gz') else b)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20), b''):h.update(b)
    pins[str(p)] = h.hexdigest();return h.hexdigest()
read(__file__)
for p in (ROOT/'kit_v2').glob('*'):
    if p.is_file():read(p)
bars=j(OUT/'BARS_FROZEN.json')
spec=read(ROOT/'in/v2/KIT_SPEC_mask_carry_v2.md').decode()
freeze=dict(sha256=pins[str(OUT/'BARS_FROZEN.json')],frozen_utc=bars['frozen_utc'],spec_matches=bars['spec_sha256']==pins[str(ROOT/'in/v2/KIT_SPEC_mask_carry_v2.md')],verbatim_bars=bars['bars_section']==spec[spec.index('## Bars, written before any score'):spec.index('## CPU dry run')].strip())
priced=list((OUT/'dry/price').glob('*/*.json.gz'))
freeze['freeze_mtime_utc']=datetime.datetime.fromtimestamp((OUT/'BARS_FROZEN.json').stat().st_mtime,datetime.timezone.utc).isoformat()
freeze['earliest_priced_mtime_utc']=datetime.datetime.fromtimestamp(min(p.stat().st_mtime for p in priced),datetime.timezone.utc).isoformat()
manifest=read(OUT/'KIT_MANIFEST.sha256').decode()
manifest_bad=[]
for line in manifest.splitlines():
    expected,path=line.split(maxsplit=1)
    if sha(ROOT/path)!=expected:manifest_bad.append(path)
archive=OUT/'sb_mask_carry.tar'
checksum=read(OUT/'sb_mask_carry.tar.sha256').decode().split()[0]
archive_sha=sha(archive)
tar_bad=[]; superseded=[]; member_count=0
with tarfile.open(archive) as tar:
    for m in tar:
        if not m.isfile():continue
        member_count+=1
        name=m.name.removeprefix('./')
        if name.startswith(('kit/','tests/')) or (name.startswith('out/') and not name.startswith('out/v2/')):superseded.append(name)
        p=ROOT/name
        if not p.is_file():tar_bad.append([name,'missing live file']);continue
        h=hashlib.sha256(tar.extractfile(m).read()).hexdigest()
        if h!=sha(p):tar_bad.append([name,'live bytes differ'])
phrase=j(C.PHRASE_FOLDS)
parsed=PH.parse(phrase)
phrase_bad=[dict(row=r,parsed=list(parsed[r['fold']][r['name']])) for r in phrase['folds'] if list(parsed[r['fold']][r['name']])!=r['phrases']]
track=[]
for p in sorted((OUT/'dry/track_cpu').glob('*/*.json.gz')):
    d=j(p)
    obs=[]
    for o in d['objects']:
        seed=next(a for a in o['anchors'] if a['seed'])
        sm=C.rle_decode(seed['rle'])
        added=[a for a in o['anchors'] if a['carried'] and not a['seed']]
        obs.append(dict(name=o['name'],seed_slot=o['seed_slot'],added=len(added),changed_masks=sum(not (C.rle_decode(a['rle'])==sm).all() for a in added),scores=[a['score'] for a in added]))
    track.append(dict(file=str(p),partial=d['partial'],frames=len(d['dense_slots']),objects=obs,skipped=d['skipped_objects'],seconds=d['seconds'],rss=d['peak_rss_gib']))
staging=j(OUT/'STAGING.json')
dry=j(OUT/'DRYRUN.json')
guard=j(OUT/'GUARD.json')
result=dict(command='bash review_run.sh p1cpu audit_static.py',freeze=freeze,manifest=dict(entries=len(manifest.splitlines()),mismatches=manifest_bad),archive=dict(sha256=archive_sha,checksum_matches=archive_sha==checksum,members=member_count,mismatches=tar_bad,superseded_members=superseded),phrase=dict(rows=len(phrase['folds']),mismatches=len(phrase_bad),examples=phrase_bad[:1]+[r for r in phrase_bad if r['row']['name']=='heater'][:1],top_level_keys=list(phrase)),cpu_track_artifacts=track,staging=dict(total_bytes=staging['total_bytes'],sum_bytes=sum(i['bytes'] for i in staging['items'])),estimate=dry['gpu_estimate'],guard=guard['lists']['withheld_80'],input_sha256=pins)
(HERE/'STATIC_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','cpu_track_artifacts')},indent=2))
(HERE/'STATUS.md').write_text('The package and schema audit is complete. The phrase reader misreads the producer’s policy labels as literal phrases. CPU reproduction continues; the final verdict will distinguish reproduced checks from launch blockers.\n')
