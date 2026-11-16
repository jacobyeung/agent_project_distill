"""Stream pool metadata; inspect local ZIP headers only; never stage media."""
import collections,gzip,json,random,sys,zipfile,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import gate
R=gate.ROOT;OUT=Path(__file__).resolve().parents[1]/'out'
def build():
 caps={};pins={};reg={}
 for rel in ['ground_rows/work/inputs/routing356_scenes.json','dose_pool/out/t1_gt/REGISTRY_H1.json','dose_pool/out/t1_gt/REGISTRY_H2.json']:
  p=R/rel;pins[str(p)]=gate.sha(p)
  for v in json.loads(p.read_text()).values():reg.setdefault(gate.normalize(v['canonical']),[]).append(v)
 for p in sorted((R/'dose_pool/out/POOL_S1').glob('*_admitted.jsonl.gz')):
  pins[str(p)]=gate.sha(p)
  with gzip.open(p,'rt') as f:
   for line in f:
    r=json.loads(line)
    if r.get('type') not in ('object_abs_distance','room_size_estimation'):continue
    canon=gate.normalize(r['canonical']);ds,cap=canon.split('/')
    c=caps.setdefault(canon,dict(canonical=canon,**{k:v for k,v in gate.verdict(ds,cap).items() if k!='capture'},
       rows_by_type={},pool_sources=[],gt_sources=[],anchor_grids=[],aliases=[]))
    c['rows_by_type'][r['type']]=c['rows_by_type'].get(r['type'],0)+1
    if str(p) not in c['pool_sources']:c['pool_sources'].append(str(p))
    g=r.get('gt_authority',{}).get('gt',r.get('gt_input'))
    if g and g not in c['gt_sources']:c['gt_sources'].append(g)
    grid=r['frame_indices']
    if grid not in c['anchor_grids']:c['anchor_grids'].append(grid)
    alias=r.get('scene','')
    if alias.startswith('v') and alias not in c['aliases']:c['aliases'].append(alias)
 for c in caps.values():
  for r in reg.get(c['canonical'],[]):
   if r['gt'] not in c['gt_sources']:c['gt_sources'].append(r['gt'])
  c['gt_local_rasters']=[]
  for g in c['gt_sources']:
   p=Path(g['path'])
   if str(p).startswith('/scratch/') and p.is_file():
    with zipfile.ZipFile(p) as z:
     names=z.namelist()
     if 'inst.npy' in names and 'frame_indices.npy' in names:
      c['gt_local_rasters'].append(dict(path=str(p),bytes=p.stat().st_size,expected_sha256=g['sha256'],verified='ZIP member names only; hash/raster contents require run preflight'))
  c['gt_raster_availability']='local_header_verified' if c['gt_local_rasters'] else 'documented_only_not_accessible'
  ds,cap=c['canonical'].split('/')
  for ns in ([ds,'scannetppv2'] if ds=='scannetpp' else [ds]):
   c['aliases'].append('v'+hashlib.sha256(('rung1 scene '+ns+'/'+cap).encode()).hexdigest()[:12])
  if ds=='arkitscenes':c['aliases'].append('v'+hashlib.sha256((ds+'/'+cap).encode()).hexdigest()[:12])
  c['aliases']=sorted(set(c['aliases']))
 amap={a:c for c in caps.values() for a in c['aliases']};frames=collections.defaultdict(dict)
 p=R/'p1c_build/k6/MAP.jsonl.gz';pins[str(p)]=gate.sha(p)
 with gzip.open(p,'rt') as f:
  for line in f:
   r=json.loads(line)
   if r['s'] in amap:frames[amap[r['s']]['canonical']][r['i']]=r
 for c in caps.values():
  fs=frames[c['canonical']];c['frame_source']='k6tk /data2/k6tk; recorded replica on Orchard; MAP provenance only'
  c['frame_count']=len(fs);c['frame_manifest']=str(OUT/'FRAME_SOURCES.jsonl')
  c['anchor_frames_complete']=all(i in fs for grid in c['anchor_grids'] for i in grid)
  c['dense_frame_sequence_verified']=False
  c['staging_bytes']=None
  c['staging_bytes_reason']='MAP has no member sizes; no shared-storage stat or archive scan authorized'
 with (OUT/'FRAME_SOURCES.jsonl').open('w') as f:
  for canon,fs in sorted(frames.items()):
   for i,r in sorted(fs.items()):f.write(json.dumps(dict(canonical=canon,**r))+'\n')
 population=[c for c in caps.values() if c['eligible']]
 counts=collections.Counter(c['canonical'].split('/')[0] for c in population)
 quotas={k:int(300*v/sum(counts.values())) for k,v in counts.items()}
 for k in sorted(counts,key=lambda k:(-(300*counts[k]/sum(counts.values())-quotas[k]),k))[:300-sum(quotas.values())]:quotas[k]+=1
 rng=random.Random(17);pilot=[];shortfall={}
 for ds,n in sorted(quotas.items()):
  choices=sorted((c for c in population if c['canonical'].startswith(ds+'/') and c['gt_local_rasters'] and c['anchor_frames_complete']),key=lambda c:c['canonical'])
  rng.shuffle(choices);pilot.extend(choices[:n]);shortfall[ds]=max(0,n-len(choices))
 rooms=sorted({c['room'] for c in pilot});rng.shuffle(rooms);held=set(rooms[:round(.2*len(rooms))])
 selection=[dict(canonical=c['canonical'],room=c['room'],split='heldout' if c['room'] in held else 'train',gt=c['gt_local_rasters'][0]) for c in sorted(pilot,key=lambda c:c['canonical'])]
 result=dict(schema='b6-captures-v1',seed=17,inputs=pins,captures=list(sorted(caps.values(),key=lambda c:c['canonical'])),
   pilot=selection,pilot_complete=len(selection)==300,pilot_target=300,eligible_pool_counts=dict(counts),
   pool_proportion_basis='unique eligible captures; no answer values used',quotas=quotas,shortfall=shortfall,
   split_rule='shuffle sorted physical rooms with Random(17), following dataset sample draws; first round(0.2*n) held out',
   exact_staging_bytes=None,heavy_io_approval_required=True)
 (OUT/'CAPTURES.json').write_text(json.dumps(result,indent=2)+'\n')
 (OUT/'GATE_RECEIPT.json').write_text(json.dumps(gate.receipt([c['canonical'] for c in selection]),indent=2)+'\n')
 summary={k:result[k] for k in ('pilot_complete','eligible_pool_counts','quotas','shortfall','exact_staging_bytes')}
 summary.update(captures=len(caps),selected=len(selection),gt_available=sum(bool(c['gt_local_rasters']) for c in caps.values()),split=dict(collections.Counter(c['split'] for c in selection)))
 (OUT/'INVENTORY_RESULT.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':build()
