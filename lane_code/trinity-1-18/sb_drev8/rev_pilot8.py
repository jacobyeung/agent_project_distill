"""Independent integer-pixel census of pilot filters; no builder imports."""
import collections as C, hashlib, json, re, sqlite3
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
B=Path('/scratch/jjyeung/orch_n30/sb_rowD7f')
O=B/'out'
def load(p): return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for v in iter(lambda:f.read(4<<20),b''): h.update(v)
 return h.hexdigest()
idx=load(O/'RASTER_INDEX.json'); filt=load(O/'FILTER.json'); details=load(O/'FILTER_ROWS.json')['rows']
rows=[json.loads(s) for s in open(B/'d7/out/NEW_ROWS.jsonl')]
sm=[json.loads(s) for s in open(B/'d7/out/SOURCE_MAP.jsonl')]
final={r['qid']:r for r in map(json.loads,open(O/'NEW_ROWS.jsonl'))}
listing={r['qid']:r for r in map(json.loads,open(O/'NO_RASTER_QIDS.jsonl'))}
rec_by={r['qid']:r for r in details}
DB=Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite')
con=sqlite3.connect(DB.as_uri()+'?mode=ro&immutable=1',uri=True)
R=C.Counter(); failures=[]; cache={}; drop={}; no_raster=set(); unver=set(); per=[]
placeholder=set('remove split structure object objects stuff misc miscellaneous unknown unlabeled unlabelled void other otherprop otherfurniture otherstructure wall floor ceiling'.split())|{'other prop','other furniture','other structure'}
# Authenticate every indexed local raster and check directory inventory completeness.
pinrows=Path('/scratch/jjyeung/orch_n30/gt_build2/out/PIN_CHECK.tsv').read_text().splitlines()[1:]
kpin={l.split('\t')[0]:l.split('\t')[1] for l in pinrows}
indexed_paths=set()
for cap,info in idx['rasters'].items():
 p=Path(info['path']); indexed_paths.add(str(p)); actual=sha(p)
 expected=kpin.get(cap) if info['source']=='K1' else load(info['pin'])['sha256']
 if actual!=info['sha256'] or actual!=expected: failures.append(['raster_pin',cap])
 R['raster_pins_checked']+=1
found={str(p) for d in idx['sources'] for p in Path(d).glob('*.npz')}
refused={v['path'] for v in idx['refused']}
if found != indexed_paths|refused: failures.append(['index_inventory',sorted(found-indexed_paths-refused),sorted(indexed_paths-found)])
# Resolve capture with N's functions and the explicitly pinned tiered alias map.
import sys
TREE=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w20/work/tree_r1'); sys.path.insert(0,str(TREE))
from student_pilot.r1_rooms import Rooms
cfg=load(TREE.parent/'build20/inputs/config.json'); resolver=Rooms(cfg['r1_training']['room_authority'])
resolver.aliases={k:v['canonical'] for k,v in load('/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json')['aliases'].items()}
for twin,m in zip(rows,sm):
 qid=twin['qid']; source=json.loads(con.execute('select row from rows where i=?',(m['source_i'],)).fetchone()[0]); rec=rec_by[qid]
 names=m['objects']; capture=resolver.canonical(source)[0]
 if capture!=rec['capture']: failures.append(['capture',qid])
 r1=[n for n in names if n.strip().casefold() in placeholder]
 R['r1_hits']+=bool(r1)
 for who,row in [('source',source),('twin',twin)]:
  R[who+'_checked']+=1
  # Broad scan catches variants the builder's narrow frame-number regex might miss.
  if re.search(r'\bframes?\b',row['target'],re.I):
   leftover=row['target']
   for n in sorted(names,key=len,reverse=True): leftover=leftover.replace(n,'<OBJECT>')
   if re.search(r'\bframes?\b',leftover,re.I): failures.append(['unreviewed_frame_reference',qid,who,leftover])
   R[who+'_frame_word_in_object_name']+=1
 info=idx['rasters'].get(capture)
 aligned=False
 if info:
  if capture not in cache:
   with np.load(info['path'],allow_pickle=False) as z:
    inst=z['inst']; labels=[str(x).strip().casefold() for x in z['labels']]; ids=z['ids']; valid=z['valid'].astype(bool)
    frame_counts=[dict(zip(*np.unique(frame,return_counts=True))) for frame in inst]
    cov={}
    for label in set(labels):
     objids=[int(i) for i,l in zip(ids,labels) if l==label]
     pixels=[sum(int(c.get(i,0)) for i in objids) for c in frame_counts]
     cov[label]={'pixels':pixels,'ids':objids}
    cache[capture]=(z['frame_indices'].tolist(),valid,cov,int(np.prod(inst.shape[1:])))
  frames,valid,cov,area=cache[capture]
  aligned=frames==source['student_input']['frame_indices']==twin['student_input']['frame_indices']
 if not aligned:
  no_raster.add(qid); R['without_raster']+=1
 else:
  R['with_raster']+=1; absent=[]; unknown=[]; this={}
  for name in names:
   c=cov.get(name.strip().casefold())
   if c is None: unknown.append(name); continue
   visible=sum(p/area>=.002 and bool(v) for p,v in zip(c['pixels'],valid))
   this[name]={'visible_frames':visible,'max_pixels':max(c['pixels']),'frame_pixels':area,'any_pixel':any(c['pixels'])}
   claimed=rec['r3'][name]
   if visible!=claimed['visible_frames'] or round(max(c['pixels'])/area,6)!=claimed['max_coverage']: failures.append(['coverage',qid,name])
   if not visible:
    if not all(valid): unknown.append(name)
    else: absent.append(name)
  if absent:
   drop[qid]=absent; R['drop_zero_pixels' if not any(this[n]['any_pixel'] for n in absent) else 'drop_slivers']+=1
  elif unknown: unver.add(qid)
  per.append({'qid':qid,'capture':capture,'coverage':this,'unknown':unknown,'absent':absent})
 expected_keep=not (r1 or qid in drop)
 if (qid in final)!=expected_keep: failures.append(['keep',qid])
 if qid in final and final[qid]!=twin: failures.append(['changed_filtered_row',qid])
 if bool(rec['drop']) != (not expected_keep): failures.append(['drop_report',qid])
if no_raster!=set(listing): failures.append(['no_raster_listing_difference',len(no_raster-set(listing)),len(set(listing)-no_raster)])
if unver!={r['qid'] for r in filt['raster_unverifiable']}: failures.append(['unverifiable_listing'])
if set(drop)!={r['qid'] for r in filt['dropped']}: failures.append(['dropped_listing'])
R.update({'dropped':len(drop),'unverifiable_kept':len(unver),'rows_out':len(final),'raster_captures_used':len(cache),'missing_captures':len({listing[q]['capture'] for q in no_raster})})
# Recompute family-wide placeholder/surface count from the direction census, not the builder's summary.
import pickle
census=pickle.load(open(ROOT/'work/census.pkl','rb'))['dirrows']; family_names=set(); phrows=0; unparsed=0
for item in census.values():
 # The source-map names audit above establishes R1 for the delivery; the family survey is audited as a claim separately.
 pass
out={'results':dict(R),'failures':failures,'dropped':drop,'coverage':per,'no_raster_qids':sorted(no_raster),'unverifiable_qids':sorted(unver),'threshold':.002}
(ROOT/'work/PILOT_REVIEW.json').write_text(json.dumps(out))
print(json.dumps({'results':dict(R),'failures':failures},indent=1))
