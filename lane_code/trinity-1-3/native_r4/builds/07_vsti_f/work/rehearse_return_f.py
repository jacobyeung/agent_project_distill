"""Measure the real return publisher with 311 production-shape prepare outputs."""
from pathlib import Path
from unittest.mock import patch
import sys,time,uuid,collections
import numpy as np
B=Path(__file__).resolve().parents[1];R=B.parents[1];OLD=B.parent/'03_vsti_c';sys.path.append(str(B/'code'))
from adapter import *
import engine,o
engine.initialize(dict(tree=str(R/'from113/work/tree')))
import geometry as G
from student_pilot.tower_read import TowerState,GRID_UV
root=B/'work'/('return_311_'+uuid.uuid4().hex);run=root/'run';(run/'i').mkdir(parents=True)
for p in (OLD/'work/input_full').glob('*'):
 if p.is_file():(run/'i'/p.name).write_bytes(p.read_bytes())
captures=load(run/'i/FRAMES.json')['captures'];assert len(captures)==311
rawdir=run/'cell/g/raw';scaled=run/'cell/g/scaled';rawdir.mkdir(parents=True);scaled.mkdir()
rng=np.random.default_rng(170228);raw_entries={};records=[];videos={};start=time.monotonic()
for c in captures:
 pose=np.zeros((32,9),dtype=np.float64);pose[:,0]=np.arange(32)*.03;pose[:,6:]=1.
 depth=rng.uniform(1,4,(32,51,51)).astype(np.float32)
 confidence=rng.uniform(1,2,(32,51,51)).astype(np.float32)
 state=TowerState(pose,depth,confidence,np.array(c['anchor_indices']),np.arange(32))
 name=digest(c['native']);p=rawdir/(name+'.npz')
 np.savez(p,raw_pose=state.raw_pose9,depth_grid=state.depth_grid,depth_conf_grid=state.depth_conf_grid,
          frame_indices=state.frame_indices,anchor_slots=state.anchor_slots,grid_uv=state.grid_uv,
          source_hw=[480,640],gravity_up=[0.,-1.,0.])
 raw_entries[c['native']]=pin(p);output=scaled/(name+'.npz');diagnostics=dict(tower_gravity=[0.,-1.,0.])
 value=G.convert(state,depth.astype(np.float64)*1.5,[0.,-1.,0.],[480,640],output,diagnostics=diagnostics)
 videos[name]=pin(output)
 records.append(dict(native=c['native'],group=c['group'],clip=name,raw=pin(p),checkpoint=dict(sha256='a'*64,path='/synthetic/checkpoint'),
                     status='PASS',error=None,diagnostics=diagnostics,output=pin(output),seconds=0.,**value))
dump(rawdir/'RAW.json',dict(captures=raw_entries,synthetic=True,dense_manifest=pin(run/'i/DENSE.json')))
dump(scaled/'GEOMETRY.json',dict(videos=videos,records=records,raw_tower=pin(rawdir/'RAW.json'),synthetic=True))
dump(run/'PHASES.json',[dict(name='stage',seconds=0),dict(name='pose',seconds=0),dict(name='prepare',seconds=time.monotonic()-start)])
dump(run/'RESULT.json',dict(complete=False,missing=load(run/'i/BOUND.json')['keys'],segments=[]))
dump(root/'STAGING.json',dict(synthetic=True,scenes=len(captures)))
(root/'b.log').write_text('Synthetic production-shape prepare arrays; real conversion and return publisher.\n')
(root/'a.log').write_text('No remote staging performed.\n')
module=o.imports()[2];config=dict(token='f17022800000000000000000f',binding='f'*64)
with patch.object(module,'identity',return_value=root/'pool'),patch.object(module,'pool_operation',return_value=dict(verified=True)),patch.object(module,'upload',return_value=dict(verified=True)):
 result=o.finish_return(module,root,run,config,0,None)
source=root/'return';members=o.return_members(source);archive=Path(result['local_return'])/'result.tar.gz'
groups={}
for p in sorted(run.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(run)
 category=('cell/g/raw/*.npz' if rel.parts[:3]==('cell','g','raw') and p.suffix=='.npz' else
           'cell/g/scaled/*.npz' if rel.parts[:3]==('cell','g','scaled') and p.suffix=='.npz' else str(rel))
 row=groups.setdefault(category,dict(count=0,bytes=0,suffix=p.suffix,returned=str(rel) in members))
 row['count']+=1;row['bytes']+=p.stat().st_size
for row in groups.values():row['bytes_per_file']=row['bytes']/row['count']
expanded=sum(p.stat().st_size for p in members.values());compressed=archive.stat().st_size
# The old selection is evaluated on the same files, before the extra inventory receipt.
old_members={str(p.relative_to(run)):p for p in run.rglob('*') if p.is_file() and not o.omitted_prepare(p.relative_to(run))}
old_expanded=sum(p.stat().st_size for p in old_members.values())+sum((root/n).stat().st_size for n in ('a.log','b.log','STAGING.json'))
value=dict(scenes=311,synthetic=True,method='Production NPZ shapes/dtypes, seeded nonconstant float32 depth/confidence; real geometry.convert and orchard_results.publish; remote calls mocked.',
 root=str(root),groups=groups,prepare_run_bytes=sum(p.stat().st_size for p in run.rglob('*') if p.is_file()),
 full_return_expanded_bytes=expanded,full_return_archive_bytes=compressed,full_return_members=len(members),
 expanded_cap_bytes=512*1024**2,member_cap=10000,archive_cap_bytes=300_000_000-module.EXIT_RESERVE,channel_cap_bytes=300_000_000,
 expanded_headroom_bytes=512*1024**2-expanded,archive_headroom_bytes=300_000_000-module.EXIT_RESERVE-compressed,
 v1c_selection_expanded_bytes_before_completion=old_expanded,
 archive=pin(archive),inventory=pin(source/'INVENTORY.json'),passed=expanded<=512*1024**2 and compressed<=300_000_000-module.EXIT_RESERVE and result['returned'],
 limitations=['Prepare-size rehearsal, not a completed 450-item decoded return','Frame pixels are already excluded and were not copied; i/ manifests copied from V1c full adaptation','Manifest sizes use synthetic paths/diagnostics; actual manifest and log lengths vary','Random array compression is measured, not a bound on production compression','No GPU, real weights, Orchard namespace, actual remote IO, or return-deadline timing checked'])
assert value['passed'];dump(B/'out/RETURN_SIZE.json',value)
print(json.dumps({k:value[k] for k in ('scenes','full_return_expanded_bytes','full_return_archive_bytes','full_return_members','passed')}))
