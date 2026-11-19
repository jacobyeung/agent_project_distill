"""Real-store census. Full admitted routing rows live only in memory."""
from pathlib import Path
from collections import Counter,defaultdict
from copy import deepcopy
import json,sys,os,sqlite3,itertools,re,hashlib,importlib.util
L=Path(__file__).resolve().parents[2];B=L/'work/build16';T=L/'work/tree_r1';O=B/'proofs/census'
O.mkdir(parents=True,exist_ok=True);sys.path[:0]=[str(T),str(L/'work/n1fix2')]
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(O))
native_open=Path.open
def opened(p,mode='r',*a,**kw):return native_open(p,mode.replace('x','w') if p.is_relative_to(B) else mode,*a,**kw)
Path.open=opened
from monitor9 import Monitor
m=Monitor(T)
from student_pilot.p3_provenance import load,pinned,file_pin,write,digest
from student_pilot.carrier_c1_run import Rows
from student_pilot import carrier_c1_routing as routing
from student_pilot.r1_population import produce,family,SLICE_CELLS
from student_pilot.r1_routing import Filters
from student_pilot.r1_counting import classify,admit
from student_pilot.r2_adapters import normalize
from student_pilot.r2_intake import intake
from tests.test_r2_build9_recovery import envelope
from tests.test_r2_data_path import fixture
cfg=load(B/'inputs/config.json');filters=Filters(cfg,cfg['scene_division']);audit=load(B/'INPUTS.json')
sources={k:load(pinned(cfg['r1_training']['row_sources']))[k]['source'] for k in SLICE_CELLS}
prior=load(L/'work/build14/proofs/census/PLAN_RUN.json')
counts_prior=prior['allocation']['eligible']
batchdir=O/'chunk';batchdir.mkdir(exist_ok=True)
members=dict(schema='r1-source-membership-v1',sources={k:dict(source=v,rows={}) for k,v in sources.items()})
memory=sqlite3.connect(':memory:');memory.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
reader=Rows(dict(streams={},r1_training=cfg['r1_training'],extent_receipt=cfg['extent_receipt']),None)
reader.connections['routing']=memory;reader.counts['routing']=0
slice_counts={};trace_dir=B/'proofs/traces';trace_dir.mkdir(exist_ok=True);traces=defaultdict(list)
def keep_trace(row,target,cell,source):
    if len(traces[cell])>=20:return
    text=row.get('target',row.get('suffix',''))
    traces[cell].append(dict(cell=cell,source=source,row_key=row['qid'],
        prompt=row.get('student_input',{}).get('question',row.get('question')),
        trace=text.split('<think>',1)[1].split('</think>',1)[0] if '<think>' in text else None,
        target_text=text,native_row=row,native_target=target))
for kind,pin in sources.items():
    counts=Counter();refused=Counter();before_k1=0
    with pinned(pin).open() as handle:
        while lines:=list(itertools.islice(handle,200)):
            rows=[]
            for line in lines:
                raw=json.loads(line);p=raw.get('provenance',{});si=raw.get('student_input',{})
                indices=si.get('frame_indices') or raw.get('frame_indices') or p['frame_indices']
                frames={raw['qid']:dict(fps=si.get('fps') or p.get('fps_source',{}).get('value') or 24.,
                    total_num_frames=indices[-1]+1,frames=[dict(path='/u/'+str(i),sha256='a'*64,source_index=i) for i in indices])}
                row=normalize(raw,frames);row.update(answer_form='routed',response_heads=['pose','depth']);rows.append(row)
            mp=envelope(batchdir,rows,'routing',kind);manifest=load(mp);manifest['extent_receipt']=cfg['extent_receipt'];write(mp,manifest)
            admitted,report=intake(mp);counts['read']+=len(rows);counts['intake_admitted']+=len(admitted)
            refused.update('intake:'+r['reason'] for r in report['refusals'])
            for item in admitted:
                row=dict(item['row'])
                if row.get('events') and not row.get('routing'):
                    si=row['student_input'];rgb=dict(si,frames=[dict(p,source_index=i) for i,p in zip(si['frame_indices'],si['frames'],strict=True)])
                    row=routing.c1_row(row,rgb)
                row['r1_source']=dict(family=kind,sha256=pin['sha256']);why=filters.reason(row,'routing')
                if why:refused['filter:'+why]+=1;continue
                i=reader.counts['routing'];memory.execute('INSERT OR REPLACE INTO rows VALUES(?,?,?)',(i,json.dumps(row),json.dumps(item.get('target',{}))))
                try:bound,target=reader.row('routing',i)
                except (ValueError,KeyError,TypeError) as error:refused['reader:'+str(error)]+=1;continue
                members['sources'][kind]['rows'][row['qid']]=digest(row)
                keep_trace(bound,target,kind,pin);reader.counts['routing']+=1;counts['eligible']+=1
    slice_counts[kind]=dict(counts,refused=dict(refused),source=pin)
    assert counts['read']==counts['eligible']+sum(refused.values())
    print(kind,dict(counts),dict(refused),flush=True)
write(O/'membership.json',members)
# VQA: native read-only connection and every prepare-order filter, followed by
# the actual Rows.row check. The separate room audit never changes VQA admission.
v=load(pinned(cfg['streams']['vqa']));pinned(v['database'])
vreader=Rows(dict(streams={'vqa':v},r1_training=cfg['r1_training'],extent_receipt=cfg['extent_receipt']),None)
zpath=pinned(cfg['remove_files'][-1]);zkeys={json.loads(line)['row_key'] for line in zpath.read_text().splitlines()}
classifier=L.parent/'inputs/count/COUNT_FIX_classify_counting_rows.py'
spec=importlib.util.spec_from_file_location('count_reference',classifier);reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
def reference_form(row):
    t=row.get('target') or ''
    if row['question_type']=='first_seen_frame':return 'first_seen','FIRST_SEEN'
    if 'count_kind' in row:cell,form='totals','TOTALS'
    else:cell,form='counting',('FS_LIST' if reference.LIST_RE.search(t) else ('PROC' if reference.PROC_RE.search(t) else 'OTHER'))
    if form in ('FS_LIST','TOTALS') and reference.REGION_RE.search(t):form+='_REGION'
    return cell,form
known=set(audit['known_k1_rooms'])
def room(s):
    s=s.replace('scannetppv2/','scannetpp/')
    return re.sub(r'_\d\d$','',s) if s.startswith('scannet/') else s
r0={room(s) for s in pinned(audit['r0']).read_text().splitlines() if s}
indices=[];bycell=Counter();refused=Counter();refused_cells=defaultdict(Counter);forms=Counter();zfound=set();zexamples={};scene_hits=Counter()
for i,encoded in vreader.connections['vqa'].execute('SELECT i,row FROM rows ORDER BY i'):
    row=json.loads(encoded);cell=family(row,'vqa');can=row.get('canonical') or row.get('provenance',{}).get('canonical')
    if can:
        if room(can) in known:scene_hits['k1_known_positive']+=1
        if room(can) in r0:scene_hits['r0']+=1
    else:scene_hits['canonical_unknown']+=1
    if row['qid'] in zkeys:
        got=classify(row);assert got==reference_form(row),(row['qid'],got,reference_form(row))
        assert got[1].startswith(('FS_LIST','TOTALS'));forms[got[1]]+=1;zfound.add(row['qid'])
        zexamples.setdefault(got[1],row)
    why=filters.reason(row,'vqa')
    if why is None:
        try:bound,target=vreader.row('vqa',i)
        except (ValueError,KeyError,TypeError) as error:why='reader:'+type(error).__name__+':'+str(error)
    if why:refused[why]+=1;refused_cells[cell][why]+=1
    else:
        admit(bound,cell);indices.append(i);bycell[cell]+=1;keep_trace(bound,target,cell,v['database'])
    if (i+1)%50000==0:print('vqa scanned',i+1,flush=True)
assert zfound==zkeys and len(zkeys)==17879
assert bycell['counting']==2617 and bycell['totals']==0
write(O/'CLASSIFIER.json',dict(reference=file_pin(classifier),list=cfg['remove_files'][-1],found=len(zfound),forms=dict(forms),all_equal=True))
write(O/'z_examples.json',list(zexamples.values()))
write(O/'vqa_indices.json',indices)
vreader.indices['vqa']=indices;vreader.counts['vqa']=len(indices)
census=dict(vqa=dict(read=v['count'],eligible_by_cell=dict(bycell),refused=dict(refused),refused_by_cell={k:dict(v) for k,v in refused_cells.items()},database=v['database'],
                     room_audit=dict(hits=dict(scene_hits),k1_complete=False,alias_map_present=False,scope='Report only; canonical provenance and known K1-positive capture subset. Unknown overlap is not a pass.')),
            slices=slice_counts,scene_audit=file_pin(B/'INPUTS.json'),
            standins='Frame metadata /u and GUESS 24 FPS where absent; published alias/canonical coverage. Routing rows remain only in an in-memory SQLite store. Independent host RGB/coverage unavailable.')
write(O/'CENSUS.json',census)
# Synthetic unavailable host populations preserve the inherited plan arithmetic.
raw=fixture(O,qid='fixture_camera',stream='routing')
scene=next(s for s in sorted(filters.train) if not filters.reason(dict(qid='fixture',dataset=s.split('/')[0],scene=s.split('/')[1]),'routing'))
raw['dataset'],raw['scene']=scene.split('/',1);raw['provenance'].update(alias=scene,canonical='scannet/fixture_clean')
rgb={k:raw['student_input'][k] for k in ('fps','total_num_frames')};rgb['frames']=[dict(p,source_index=i) for p,i in zip(raw['student_input']['frames'],raw['student_input']['frame_indices'])]
camera={}
for kind in ('camera_displacement','camera_movement_direction','camera_rotation'):
    r=deepcopy(raw);r.update(qid='fixture_'+kind,question_type=kind);camera[kind]=routing.c1_row(r,rgb)
virtual=Rows(dict(streams={},r1_training=cfg['r1_training']),None)
vm=sqlite3.connect(':memory:');vm.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
for s in ('pose','pointing','routing'):virtual.connections[s]=vm
sizes={k:counts_prior[k] for k in ('pose','pointing')};cameras={k:counts_prior[k] for k in camera}
class Reader:
    def count(self,s):
        if s in sizes:return sizes[s]
        return vreader.count(s) if s=='vqa' else reader.count(s)+sum(cameras.values())
    def row(self,s,i):
        if s=='vqa':return vreader.row(s,i)
        if s=='routing' and i<reader.count(s):return reader.row(s,i)
        if s in sizes:r=dict(qid='fixture_'+s+'_'+str(i))
        else:
            j=i-reader.count('routing')
            for k,n in cameras.items():
                if j<n:r=deepcopy(camera[k]);r['qid']='fixture_'+k+'_'+str(j);break
                j-=n
        vm.execute('INSERT OR REPLACE INTO rows VALUES(0,?,?)',(json.dumps(r),'{}'));return virtual.row(s,0)
write(O/'host_boundary.json',dict(counts=cameras,pose_pointing=sizes,source=file_pin(L/'work/build14/proofs/census/PLAN_RUN.json'),
    scope='Synthetic native rows/virtual offsets stand in for unavailable camera, pose and pointing stores. This is not a production binding.'))
counts={c['type']:bycell.get(c['type'],0) for c in load(pinned(cfg['r1_training']['mix']))['cells']}
counts.update(cameras);counts.update(sizes);counts.update({k:v['eligible'] for k,v in slice_counts.items()})
card=load(pinned(cfg['r1_training']['mix']));cardpath=B/'inputs/CARD.md'
card['counting_admission']='procedure_only_v1'
lines=['# N training card','','Each ceiling is 4 × eligible / 1,000. Source: work/build16/proofs/census/CENSUS.json. Camera, pose and pointing counts use the labelled host substitute in proofs/census/host_boundary.json. Scale weight: 0.04 (work/build15/inputs/kit_config.json).','','| Cell | Rows per step | Eligible | Ceiling |','|---|---:|---:|---:|']
for c in card['cells']:
    n=counts[c['type']];lines.append(f"| {c['type']} | {c['rows_per_step']} | {n} | {4*n/1000:.3f} |")
    c['ceiling_rows_per_step']=4*n/1000
lines+=['','Counting: floor(4 × 2,617 / 1,000 × 100) / 100 = 10.46. Direction: 32.89 + 10.87 + 3.39 − 10.46 = 36.69. Totals: 0. Absolute distance: 15.6, below 31.22; no camera refill. Other quotas retain the build-15 card. Source: work/n1fix2/inputs/mix.json and the census above.']
cardpath.write_text('\n'.join(lines)+'\n');card['source']=file_pin(cardpath);write(B/'inputs/mix.json',card)
cfg['r1_training']['mix']=file_pin(B/'inputs/mix.json')
for name in ('config.json','kit_config.json'):write(B/'inputs'/name,cfg)
binding=produce(Reader(),cfg['r1_training']['mix'],file_pin(O/'membership.json'),[file_pin(O/'CENSUS.json'),file_pin(O/'host_boundary.json')],O/'population')
from student_pilot.r1_mix import plans,validate_binding
card,idx,allocation=validate_binding(binding);assert allocation['cuts']=={}
owner={(c['stream'],i):c['type'] for c in card['cells'] for i in idx['cells'][c['type']]}
draws=Counter();repeat=Counter();step_counts=defaultdict(list);resume={};quotas=Counter()
for step,plan in enumerate(plans(binding,{s:Reader().count(s) for s in ('pose','vqa','routing','pointing')},1000)):
    cellstep=Counter();streamstep=Counter()
    for s,offsets in plan:
        streamstep[s]+=len(offsets)
        for i in offsets:k=owner[s,i];cellstep[k]+=1;draws[k]+=1;repeat[s,i]+=1
    for c in card['cells']:step_counts[c['type']].append(cellstep[c['type']])
    quotas[json.dumps(streamstep,sort_keys=True)]+=1
    if step in (400,600):resume[str(step)]=dict(absolute_step=step,first_step_draws=dict(cellstep),plan_sha256=digest(plan))
for step in (400,600):
    p=next(plans(binding,{s:Reader().count(s) for s in ('pose','vqa','routing','pointing')},1000,start_step=step))
    assert digest(p)==resume[str(step)]['plan_sha256']
percell={c['type']:dict(quota=c['rows_per_step'],eligible=counts[c['type']],mean=sum(step_counts[c['type']])/1000,min=min(step_counts[c['type']]),max=max(step_counts[c['type']]),total=draws[c['type']],largest_repeat=max((v for (s,i),v in repeat.items() if owner[s,i]==c['type']),default=0)) for c in card['cells']}
write(O/'PLAN_RUN.json',dict(binding=binding,allocation=allocation,cells=percell,per_step_quotas=dict(quotas),draws=dict(draws),largest_repeat=max(repeat.values()),steps=1000,resumed=resume))
for c in card['cells']:
    if c['stream'] not in ('vqa','routing'):continue
    (trace_dir/(c['type']+'.jsonl')).write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in traces[c['type']]))
write(trace_dir/'INDEX.json',{c['type']:dict(rows=len(traces[c['type']]),status='native reader output' if traces[c['type']] else ('no eligible rows' if not counts[c['type']] else 'not rerun: input absent (production camera store)'),eligible=counts[c['type']]) for c in card['cells'] if c['stream'] in ('vqa','routing')})
vreader.close();reader.close();vm.close();m.save(O)
(B/'STATUS.md').write_text('# Build 16 status\n\nSteps 1–3: input binding, counting classifier and native census/plans complete. K1 full membership and production camera/pose/pointing inputs remain absent. GO=false. Production-proof mode and final checks remain.\n')
print('PASS census arithmetic and producer plans',json.dumps(dict(vqa=len(indices),slices={k:v['eligible'] for k,v in slice_counts.items()},largest_repeat=max(repeat.values()))),flush=True)
