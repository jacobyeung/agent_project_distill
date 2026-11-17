"""Build and authenticate the fixed room evaluation set without fitting."""
import hashlib,json,sys,tarfile,io
from pathlib import Path
from PIL import Image
W=Path(__file__).resolve().parents[1];O=W/'out';P=O/'src';B=W.parent/'b1g/out'
sys.path[:0]=[str(P/'tree'),str(P)]
from h1eval.items import digest,canonical,sha
H=Path('/scratch/jjyeung/orch_n30/cont_ops/work/h1read')
qpath=H/'in/out/qsets/R0_QUESTIONS_dev_f32.jsonl';fpath=H/'in/out/FRAMES_MANIFEST.json';tarpath=H/'assets/d81f4a26.tar'
extra=json.loads((H/'kit/launcher/EXTRA.json').read_text())
idmap=json.loads((H/'evidence/ID_MAP.json').read_text())
opaque_rows={idmap[r['id']]['source_line']:r for r in map(json.loads,(H/'assets/e52a690b.jsonl').read_text().splitlines())}
assert sha(H/'assets/e52a690b.jsonl')==extra['files']['e52a690b.jsonl']['sha256']
old=json.loads((B/'src/items/devs1_routed.json').read_text())
dev=[r for r in old['items'] if r['question_type']=='room_size_estimation']
r0=[]
for line,text in enumerate(qpath.read_text().splitlines(),1):
 r=json.loads(text)
 if r['question_type']!='room_size_estimation':continue
 key='scannetpp/'+r['scene']
 r.update(id=r['qid'],room_key=key,room=key,native=key,source_frame_indices=r['frame_indices'],
          ground_truth=r['gt']['area_m2'],scorer='official_vsi_mra',answer_type='numeric',development_only=True,
          label_provenance=dict(source='inputs/r0dev/R0_QUESTIONS_dev_f32.jsonl',source_sha256=sha(qpath),line=line,source_qid=r['qid'],label_field='gt.area_m2'))
 r0.append(r)
assert len(dev)==36 and len(r0)==98
assert not {r['room_key'] for r in dev}&{r['room_key'] for r in r0}
assert not {r['id'] for r in dev}&{r['id'] for r in r0}
items=canonical(dev+r0);frames=json.loads(fpath.read_text());captures={};proof=[]
assert tarpath.stat().st_size==797685760
assert sha(tarpath)=='2ad8c67c111d5f286aa96ea688efd5c88218e116a8c09ae1a9b4bc71be893a21'
with tarfile.open(tarpath,'r:') as tar:
 members=tar.getmembers();names={m.name:m for m in members}
 assert len(names)==len(members)
 print('tar members',len(members),'first',list(names)[:4],flush=True)
 expanded=sum(m.size for m in members if m.isfile())
 for item in r0:
  key=item['native'];scene=frames['scenes'][key]
  mapped=opaque_rows[item['label_provenance']['line']]
  assert mapped['question']==item['question'] and mapped['source_frame_indices']==item['frame_indices']
  assert idmap[mapped['id']]['source_qid']==item['qid'] and idmap[mapped['id']]['room']==key
  assert scene['r0_split']=='R0-dev' and not scene['deferred'] and scene['total_frames']==item['total_num_frames']
  chosen=[]
  for index,path in zip(item['source_frame_indices'],mapped['frame_refs']):
   pin=extra['frames'][path];assert path in names
   raw=tar.extractfile(path).read();assert hashlib.sha256(raw).hexdigest()==pin['sha256'] and len(raw)==pin['bytes']
   with Image.open(io.BytesIO(raw)) as im:assert im.size==(640,480)
   chosen.append(dict(index=index,path=path,sha256=pin['sha256']))
   if item['id']==min(x['id'] for x in r0):
    dest=W/'work/frames'/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
  item['frame_paths']=mapped['frame_refs']
  captures[key]=dict(native=key,frames=chosen,anchor_indices=item['source_frame_indices'],anchor_slots=list(range(32)),fps=item['fps'],total_num_frames=item['total_num_frames'],timestamps=[i/item['fps'] for i in item['source_frame_indices']])
  proof.append(dict(id=item['id'],source_scene_manifest_sha256=scene['manifest_sha256'],frame_manifest_sha256=sha(H/'kit/launcher/EXTRA.json'),frames=32))
items=canonical(dev+r0)
value=dict(schema='h1-items-v1',name='room134',status='ready',items=items,count=134,
 item_set_sha256=digest(items),per_type={'room_size_estimation':134},development_only=True,fitting_permitted=False,
 r0_check=dict(pin=old['r0_check']['pin'],checked=134,found=98),
 source=dict(path='inputs/r0dev/R0_QUESTIONS_dev_f32.jsonl',sha256=sha(qpath)),
 sources=[dict(path='W5/src/items/devs1_routed.json',sha256=sha(B/'src/items/devs1_routed.json')),dict(path='inputs/r0dev/R0_QUESTIONS_dev_f32.jsonl',sha256=sha(qpath))],
 sets={'dev-S1':[r['id'] for r in dev],'R0-dev':[r['id'] for r in r0]},
 frames_manifest_sha256=sha(fpath))
for path,data in [(P/'items/room134.json',value),(P/'inputs/room_captures.json',{'captures':captures}),(O/'FRAME_CHECK.json',dict(passed=True,archive=str(tarpath),sha256=sha(tarpath),bytes=tarpath.stat().st_size,expanded_bytes=expanded,items=98,frames=3136,proof=proof))]:
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
(O/'R0_FRAME_PROVENANCE.json').write_text(json.dumps(dict(layout='opaque 24-hex room/frame names',source_manifest_sha256=sha(fpath),frame_manifest_sha256=sha(H/'kit/launcher/EXTRA.json'),id_map_sha256=sha(H/'evidence/ID_MAP.json'),item_file_sha256=sha(H/'assets/e52a690b.jsonl')),indent=2)+'\n')
(O/'ITEM_KEYS.txt').write_text(''.join(r['id']+'\n' for r in items))
# Authenticate producer metadata in the sealed payload too.
for source,dest in [(qpath,P/'inputs/r0dev/R0_QUESTIONS_dev_f32.jsonl'),(fpath,P/'inputs/r0dev/FRAMES_MANIFEST.json')]:dest.write_bytes(source.read_bytes())
print(json.dumps(dict(items=len(items),item_set_sha256=value['item_set_sha256'],expanded_bytes=expanded)))
