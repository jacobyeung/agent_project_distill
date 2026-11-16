"""kit_combo2 base manifest (devs1-mask-manifest-v1, baseline density) for the 288 official VSI-Bench scenes.
Frames: the official 32 floor-uniform anchors staged by frame_stage.py (FRAMES_INDEX.jsonl). Phrases: the operands of each
scene's abs-distance items; room-size-only scenes carry no phrases. Tower group g3s64 (G3T over 64 dense frames, 32 anchors)."""
import sys,json,hashlib,collections
from pathlib import Path
KIT,FI,ITEMS,OUT=map(Path,sys.argv[1:5])
sys.path.insert(0,str(KIT/'work'/'vendor'));sys.path.insert(0,str(KIT/'work'))
from phrase import normalize_phrase
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
items=[json.loads(l) for l in ITEMS.open()];frames=[json.loads(l) for l in FI.open()]
need=sorted({q['scene'] for q in items})
by={x['dataset']+'/'+x['scene_name']:x for x in frames}
miss=[s for s in need if s not in by]
if miss:raise SystemExit('scenes without staged frames: %s'%miss)
caps=[]
for s in need:
    x=by[s];names=sorted({n.lower() for q in items if q['scene']==s for n in q['operands']})
    caps.append(dict(native=s,scene=s,group='g3s64',hw=x['hw'],anchor_indices=x['anchor_indices'],frames=x['frames'],names={n:normalize_phrase(n) for n in names},phrases=sorted({normalize_phrase(n) for n in names})))
rec=KIT/'work/vendor/SAM3_RECEIPT.json'
m=dict(schema='devs1-mask-manifest-v1',captures=caps,density=dict(joint_floor=.2,cap=10,prompts='P0 only',mask_threshold=.5,resolution=1008,dtype='bf16',link_instance_floor=.3),plan_sha256=sha(FI),receipt_sha256=sha(rec),checkpoint_sha256=json.loads(rec.read_text())['checkpoint_sha256'],detect_calls=sum(len(c['phrases']) for c in caps),items_sha256=sha(ITEMS))
from kitlib import validate_manifest
validate_manifest(m)
OUT.mkdir(parents=True,exist_ok=True);(OUT/'MANIFEST.json').write_text(json.dumps(m,indent=1))
(OUT/'FRAMES_TAR.txt').write_text(''.join(p+'\n' for p in sorted({f['path'] for c in caps for f in c['frames']})))
st=dict(captures=len(caps),detect_calls=m['detect_calls'],by_dataset={d:dict(captures=sum(c['scene'].startswith(d+'/') for c in caps),mask_captures=sum(bool(c['phrases']) and c['scene'].startswith(d+'/') for c in caps),phrases=sum(len(c['phrases']) for c in caps if c['scene'].startswith(d+'/'))) for d in ('arkitscenes','scannet','scannetpp')},hw=collections.Counter(tuple(c['hw']) for c in caps).most_common(),manifest_sha256=sha(OUT/'MANIFEST.json'))
print(json.dumps(st,default=str))
