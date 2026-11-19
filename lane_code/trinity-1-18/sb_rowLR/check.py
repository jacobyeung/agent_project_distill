"""Independent geometry, trace, identity, field-diff and native-intake checks."""
import copy,json,hashlib,collections,itertools,re,sqlite3
from pathlib import Path
import numpy as np
from scipy import ndimage
from census import W,BASE,TREE,INPUTS,reg,sha,dump,rules,status
from student_pilot import r2_adapters,r2_contract,trace_grammar
from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity
CELLS={'scannet|10-20':12,'scannetpp|10-20':12,'scannet|20-40':8,'scannetpp|20-40':16,'scannet|40-60':2,'scannetpp|40-60':10,'scannet|60-100':2,'scannetpp|60-100':8,'scannetpp|>=100':2}
ALLOWED={'answer','answer_unit','benchmark_improvement_claim','candidate_id','category','form','head_program','infrastructure_only','pool','provenance','qid','question_type','result_status','target','question','options','type','events','ground_record','tool_output_spans','routing','routing_policy','response_source','head_layout','provisional_diagnostic','benchmark_trained_diagnostic','r2_source_sha256'}
BANNED={'wall','floor','ceiling','door frame','window frame','object','otherfurniture','other','unknown','clutter','remove','split','doorframe','structure','shower walls','shower wall','carpet','rug','mat'}
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def independent_area(z):
 # Independently back-project stride-four sensor pixels in the native world basis.
 clouds=[];frames=[]
 for j,valid in enumerate(z['valid']):
  if not valid:continue
  frames.append(j+1);depth=z['depth'][j];v,u=np.meshgrid(np.arange(0,depth.shape[0],4),np.arange(0,depth.shape[1],4),indexing='ij');d=depth[v,u];keep=d>0
  pixels=np.column_stack((u[keep]+.5,v[keep]+.5,np.ones(keep.sum())))
  xyz=(pixels@np.linalg.inv(z['K_frames'][j]).T)*d[keep,None]
  pose=z['c2w'][j];clouds.append(xyz@pose[:3,:3].T+pose[:3,3])
 points=np.vstack(clouds);cutoff=float(np.percentile(points[:,2],1)-.10);above=points[points[:,2]>cutoff];origin=above[:,:2].min(axis=0)
 indices=((above[:,:2]-origin)/.05).astype(np.int64);shape=indices.max(axis=0)+1;assert shape.prod()<=4000000
 occupied=np.zeros(tuple(shape),dtype=bool);occupied[indices[:,0],indices[:,1]]=True;supported=int(occupied.sum())
 padded=np.pad(occupied,5);disk=np.array([[x*x+y*y<=16 for y in range(-4,5)] for x in range(-4,5)])
 filled=ndimage.binary_fill_holes(ndimage.binary_closing(padded,structure=disk));cells=int(filled.sum())
 return dict(area_m2=cells*.05*.05,floor_cells=cells,supported_cells=supported,floor_height_m=cutoff,frames=frames)
def stems(s):
 result=set()
 for word in re.findall(r'\b\w+\b',s):
  if word.startswith('door'):word='door'
  elif word.endswith('ies'):word=word[:-3]+'y'
  elif word.endswith('s') and not word.endswith('ss'):word=word[:-1]
  result.add(word)
 return result
def independent_trace(z,row):
 names=[' '.join(str(s).lower().split()) for s in z['labels']];freq=collections.Counter(names);candidates=[]
 for j,i in enumerate(z['ids']):
  name=names[j]
  if freq[name]!=1 or name in BANNED or re.search(r'\d',name):continue
  shares=np.mean(z['inst']==i,axis=(1,2));best=int(np.argmax(shares));share=float(shares[best])
  if share<.01:continue
  size=sorted(z['obb_lengths'][j]);candidates.append((float(size[-1]*size[-2]),int(i),name,best+1,share,z['obb_centroid'][j].tolist()))
 picked=[];words=set()
 for item in sorted(candidates,key=lambda t:(-t[0],t[1])):
  ws=stems(item[2])
  if words&ws:continue
  picked.append(item);words.update(ws)
  if len(picked)==3:break
 assert len(picked)>=2
 trace=row['provenance']['room_trace'];assert trace['up_axis']==2
 for a,b in zip(picked,trace['landmarks']):
  assert b==dict(footprint=a[0],instance_id=a[1],label=a[2],best_view=a[3],pixel_share=a[4],centroid=a[5])
 assert len(picked)==len(trace['landmarks'])
 xy=np.array([p[5][:2] for p in picked]);pair=max(itertools.combinations(range(len(picked)),2),key=lambda ij:np.sqrt(np.sum((xy[ij[0]]-xy[ij[1]])**2)))
 assert list(pair)==trace['relate']['pair']
 a,c=pair;v=xy[c]-xy[a];length=np.sqrt(np.dot(v,v));assert abs(length-trace['relate']['segment_length'])<1e-10
 rv=(int(digest(row['qid']),16)//2)%2;an,cn=picked[a][2],picked[c][2]
 rel=[f'Of these, the {an} and the {cn} are farthest apart',f'The {an} and the {cn} are the farthest apart among these landmarks'][rv]
 if len(picked)==3:
  third=({0,1,2}-set(pair)).pop();projection=np.dot(xy[third]-xy[a],v)/np.dot(v,v);perp=np.linalg.norm(xy[third]-xy[a]-projection*v);decision='between' if .25<=projection<=.75 and perp<.35*length else 'side'
  assert trace['relate']['third']==third and trace['relate']['decision']==decision
  assert abs(trace['relate']['projection']-projection)<1e-10 and abs(trace['relate']['perpendicular_distance']-perp)<1e-10
  rel+=f', with the {picked[third][2]} '+('between them' if decision=='between' else ['off to the side','to the side of that pair'][rv])
 expected='<think>\nThe question asks for the combined floor area in square meters.\nSeen: '+'; '.join(f'{p[2]} in frame {p[3]}' for p in picked)+'.\n'+rel+'.\n</think>\n\n'+row['answer']
 assert expected==row['target']

def main():
 build=json.load(open(W/'out/BUILD.json'));INPUTS.update(build['input_sha256'])
 for p in ['check.py','out/BUILD.json','out/CENSUS.json','out/PREPARED.json','out/WORDING.json','out/rows.jsonl','out/SOURCES.jsonl','out/READ30.md']:reg(W/p)
 assert sha(W/'out/rows.jsonl')==build['sha256_rows']
 rows=[json.loads(l) for l in open(W/'out/rows.jsonl')];sources={r['qid']:r for r in map(json.loads,open(W/'out/SOURCES.jsonl'))};rs,extra=rules()
 counts=collections.Counter();uses=collections.Counter();rooms=collections.Counter();captures=collections.Counter();cells=collections.Counter();diffs=collections.Counter();qids=set();cids=set()
 for row in rows:
  p=row['provenance'];src=sources[p['source_qid']];uses[src['qid']]+=1;rooms[p['physical_group']]+=1;captures[p['canonical']]+=1;cells[p['details']['cell']]+=1
  assert p['source_row_sha256']==digest(json.dumps(src,sort_keys=True))
  assert not status(p['canonical'],rs,extra);assert rs.room(p['canonical'])==p['physical_group'];assert rs.canonical(src)[0].replace('scannetppv2/','scannetpp/')==p['canonical']
  assert not trace_grammar.validate_row(row)
  r2_contract.validate(r2_adapters.normalize(src),'vqa');counts['source_native_intake']+=1
  packed=r2_adapters.normalize(row);r2_contract.validate(packed,'vqa');assert packed['target']==row['target'] and packed['candidate_id']==row['candidate_id'];counts['new_native_intake']+=1
  a,b=copy.deepcopy(row),copy.deepcopy(src)
  for key in set(a)|set(b):
   if key not in a or key not in b or a[key]!=b[key]:diffs[key]+=1
  ai=a.pop('student_input');bi=b.pop('student_input')
  for key in ['question','options']:ai.pop(key,None);bi.pop(key,None)
  assert ai==bi,'Frame/clock field changed'
  assert {k:v for k,v in a.items() if k not in ALLOWED}=={k:v for k,v in b.items() if k not in ALLOWED},'Unlisted field changed'
  assert row['student_input']['options']==[]
  for key,val in dict(form='direct',question_type='room_size_estimation',category='room_size_estimation',answer_unit='m2').items():assert row[key]==val
  fields=dict(qid=row['qid'],scene=p['canonical'],frame_indices=row['student_input']['frame_indices'],type='room_size_estimation',question=row['student_input']['question'],options=[],trace_revision='3.14')
  assert p['candidate_identity_fields']==fields and candidate_identity(fields)==row['candidate_id']
  assert row['qid'] not in qids and row['candidate_id'] not in cids;qids.add(row['qid']);cids.add(row['candidate_id'])
  raster=reg(p['room_trace']['raster_path'],p['room_trace']['raster_sha256'])
  with np.load(raster) as z:
   assert z['frame_indices'].tolist()==row['student_input']['frame_indices']
   result=independent_area(z)
   for k in ['floor_cells','supported_cells','frames']:assert result[k]==p['room_measurement'][k]
   for k in ['area_m2','floor_height_m']:assert abs(result[k]-p['room_measurement'][k])<1e-9
   assert f"{result['area_m2']:.2f}"==row['answer']
   independent_trace(z,row)
  counts['independent_area_and_trace']+=1
  if counts['independent_area_and_trace']%12==0:print('checked',counts['independent_area_and_trace'],flush=True)
 assert dict(cells)==CELLS and len(rows)==72 and max(uses.values())==max(captures.values())==max(rooms.values())==2
 # Compare identities and source bytes to the pinned store, not just the selected snapshot.
 db=Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite');assert sha(db)=='210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443'
 con=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True);matched=set()
 for raw, in con.execute('SELECT row FROM rows'):
  r=json.loads(raw);assert r.get('qid') not in qids and r.get('candidate_id') not in cids
  if r['qid'] in sources:assert r==sources[r['qid']];matched.add(r['qid'])
 con.close();assert matched==set(sources)
 # Check the measurement rule against every exact-pin metric room_v4 source.
 originals={r['qid']:r for r in map(json.loads,open('/scratch/jjyeung/n30_mirror/rows_r1/out/room_v4/rows.jsonl'))};agreement=0
 for e in json.load(open(W/'out/CENSUS.json'))['entries']:
  for q in e.get('matching_metric_qids',[]):assert abs(float(originals[q]['answer'])-e['measurement']['area_m2'])<=.0050001;agreement+=1
 # Verify every imported trainer module against the newer tree's seal.
 seal=json.load(open(BASE/'out/TREE_SEAL.json'));sealed=0
 import sys
 for mod in list(sys.modules.values()):
  path=getattr(mod,'__file__',None)
  if not path:continue
  p=Path(path)
  if p.is_relative_to(TREE) and p.suffix=='.py':reg(p,seal['files'][str(p.relative_to(TREE))]);sealed+=1
 wording=json.load(open(W/'out/WORDING.json'));assert wording['removed']==0 and not wording['parse_errors']
 assert all(r['student_input']['question'] in [q['question'] for q in wording['questions'] if q['accepted']] for r in rows)
 checks=dict(status='PASS_LOCAL_CHECKS_TARGET_SHORTFALL',rows=len(rows),requested_large_rows=600,actual_large_rows=24,large_shortfall=576,actual_ge60_rows=12,exact_cells=dict(cells),counts=dict(counts),source_rows=len(sources),physical_rooms=len(rooms),max_source_uses=max(uses.values()),max_capture_uses=max(captures.values()),max_physical_room_uses=max(rooms.values()),unique_qids=len(qids),unique_candidate_ids=len(cids),store_identity_collisions=0,unlisted_field_changes=0,changed_top_level_fields=dict(diffs),unchanged='All fields outside explicit task edits; student_input frames, frame indices, timestamps, fps, and source bounds identical to source.',independent_gt_rows=72,independent_landmark_trace_rows=72,excluded_room_hits=0,room_v4_label_agreement=agreement,sealed_imported_modules=sealed,native_intake=dict(status='PASS',method='N direct branch: r2_adapters.normalize + r2_contract.validate(vqa); trace_grammar.validate_row also passes',ground_rows_pack='NOT_APPLICABLE: ground_rows.pack/validate require a routed room call and reject the required room_v4 direct form'),wording=dict(status='PASS_LOCAL_CORPUS',threshold=wording['threshold'],unique_wordings=wording['unique_corpus_wordings'],removed=wording['removed'],missing=wording['missing']),read30=dict(status='PENDING_HUMAN_STYLE_READ',rows=30,sha256=sha(W/'out/READ30.md')),limitations=['No ARKitScenes GT in discovered local pools.','Local pool census is not a complete dataset scene inventory.','No raw RGB bytes read from NFS: existing store image hashes and exact frame pins are preserved.','Full dev-S1 QIDS file is MISSING; wording screen covers discovered local files.','Requested 600 large rows cannot be reached without more scenes.'])
 dump(W/'out/CHECKS.json',checks)
 (W/'STATUS.md').write_text('Validation: all 72 rows pass independent area and landmark recomputation, exact cell counts, source and physical-room reuse caps, field differences, identity checks, five-way exclusions, and the sealed N direct-row intake. The build is 576 large rows short of the requested target. The 30-row reading and final package remain.\n')
 print('PASS',counts,'reference_labels',agreement,'sealed',sealed)
if __name__=='__main__':main()
