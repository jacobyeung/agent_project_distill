"""Vehicle N loader audit on the real stores (lane tree_rebuild8): N's own prepare-time filters and native reader
checks over the full v7 store and the vehN routing slices, then N's R1 card allocation and 1000-step plan."""
import json,os,sys,sqlite3,hashlib,collections,copy,tempfile
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/loader_n');K=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/pkg')
T=K/'work/tree_r1';os.environ.update(R2_FIXTURES=str(K/'fixtures'),R2_PROOFS=str(W/'tmp'));(W/'tmp').mkdir(exist_ok=True)
sys.path[:0]=[str(T)]
from student_pilot.p3_provenance import load,pinned,file_pin,digest
from student_pilot import carrier_c1_run as C, carrier_c1_routing as routing
from student_pilot.carrier_c1_run import Rows
from student_pilot.s1_exclusions import Exclusions
from student_pilot.row_removals import Removals
from student_pilot.r1_mix import allocate
from student_pilot.r1_training import STREAMS
from tests.test_r2_build9_recovery import TinyProcessor
CFG=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild_w/w12/work/n1fix2/inputs/config.json'))
CARD=json.load(open(CFG['r1_training']['mix']['path']))
LOC=Path('/scratch/jjyeung/orch_n30/r1_pkt/work/derive_7fh23bg8/b/k')  # P's staged copies; sha checked against N's pins
def local(pin):
    p=pin['path'];q=LOC/Path(p).name if not Path(p).exists() else Path(p)
    v=dict(path=str(q),sha256=pin['sha256']);pinned(v);return v
dev=local(CFG['dev_scene_exclusions']);bench=local(CFG['benchmark_scene_exclusions']);excl=local(CFG['exclusions'])
rep=local(CFG['report_exclusions']) if Path(LOC/Path(CFG['report_exclusions']['path']).name).exists() else None
xq=local(CFG['exclude_qids']);rem=[dict(local(f),**{k:v for k,v in f.items() if k not in('path','sha256')}) for f in CFG['remove_files']]
scene=Exclusions(dev,bench);benchmark=routing.load_exclusions(excl);reported=routing.load_exclusions(rep) if rep else set()
held={k:set(v) for k,v in load(pinned(xq)).items()};removals=Removals(rem)
DIV=load(pinned(dict(path='/scratch/jjyeung/orch_n30/rows_rebuild/work/s0/pull/m3/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/z/4c230a7e.json',sha256='0d28fdd432b02ae96b6ce2aaa840b744005291a540920ce48409f0e8c90276ad')))
train=set(DIV['train_scenes']);heldout=set(DIV['heldout_scenes'])
EXT=CFG['extent_receipt']
reader=Rows({'streams':{},'extent_receipt':EXT,'r1_training':{'schema':'r1-training-v1'}},TinyProcessor())
mem={}
def native(row,stream):
    if stream not in mem:
        c=sqlite3.connect(':memory:');c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)');reader.connections[stream]=c;mem[stream]=c
    mem[stream].execute('INSERT OR REPLACE INTO rows VALUES(0,?,?)',(json.dumps(row),'{}'))
    try:reader.row(stream,0);return None
    except (ValueError,KeyError,TypeError) as e:return type(e).__name__+':'+str(e)[:60]
RELATIVE={'camera_obj_rel_dist_v1':'camera_object_rel_distance_v1','camera_obj_rel_dist_v2':'camera_object_rel_distance_v2','camera_obj_rel_dist_v3':'camera_object_rel_distance_v3',
          'obj_obj_relative_pos_lr':'object_object_left_right','obj_obj_relative_pos_nf':'object_object_near_far','obj_obj_relative_pos_ud':'object_object_up_down'}
def cell(row,stream):
    """P's sealed type_mix.family (snap_fac07052 student_pilot/type_mix.py) renamed to N's R1 card cells."""
    typ=row.get('question_type')
    if stream=='routing':
        q=str(row.get('qid',''));rec=row.get('ground_record',{}) or {}
        if rec.get('not_seen') or 'recovery' in q:return 'recovery'
        if rec.get('unit') or 'units' in q:return 'units'
        return {'camera_displacement':'camera_displacement','camera_movement_direction':'camera_movement_direction','camera_rotation':'camera_rotation',
                'object_abs_distance':'absolute_distance','absolute_distance_object':'absolute_distance'}.get(typ,'excluded_routing_type')
    if typ in RELATIVE:return RELATIVE[typ]
    if typ in ('room_size_estimation','absolute_size_room'):return 'room_size'
    if typ in ('object_size_estimation','absolute_size_object','relative_size_object'):return 'object_size'
    if typ in ('object_rel_direction_easy','object_rel_direction_medium','object_rel_direction_hard','relative_direction_object','absolute_direction_object'):
        return 'facing_pairs' if row.get('facing') in ('toward','away') else 'direction'
    if typ in ('object_counting','absolute_count','relative_count'):return 'totals' if row.get('count_kind')=='total' else 'counting'
    return {'object_rel_distance':'relative_distance','relative_distance_object':'relative_distance','obj_appearance_order':'appearance_order','appearance_order':'appearance_order',
            'first_seen_frame':'first_seen_frame','box_3d':'box_3d','route_planning':'route_planning','camera_obj_abs_dist':'camera_object_abs_distance','camera_obj_rel_dist':'relative_distance'}.get(typ,'unassigned:'+str(typ))
def judge(row,stream,i=None):
    """First refusing filter in N's prepare/read order, or None."""
    if not removals.keep(row):return 'remove_files'
    s=row.get('dataset','')+'/'+row.get('scene','')
    if s in heldout:return 'division_heldout'
    if s not in train:return 'division_outside'
    if C.held_row(row,stream,held,{}):return 'exclude_qids'
    if stream=='vqa' and C.routed_type(row,CFG):return 'routed_type'
    hit,_=C.excluded_row(row,benchmark,reported,stream)
    if hit:return 'benchmark_exclusion'
    if scene.excluded(row):return 'scene_exclusion(dev/benchmark scenes)'
    r=native(row,stream)
    return 'reader:'+r if r else None
out=dict(schema='n-loader-audit-v1',tree_seal='de231562f857f95b26b33d03fe0d21f5958632b0b9e6f95831884cc1783a36ef',config=file_pin(Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/w12/work/n1fix2/inputs/config.json')),card=CFG['r1_training']['mix'],
         inputs=dict(dev=dev,bench=bench,exclusions=excl,report=rep,exclude_qids=xq,remove_files=rem,division='0d28fdd4',extent_receipt=EXT),streams={})
eligible=collections.Counter();examples=collections.defaultdict(list);pairs=collections.defaultdict(set)
# VQA: the full v7 store by receipt
V=load(pinned(CFG['streams']['vqa']));db=V['database'];pinned(db)
con=sqlite3.connect('file:'+db['path']+'?mode=ro',uri=True);refused=collections.Counter();bycell=collections.Counter();n=0
for i,r in con.execute('SELECT i,row FROM rows ORDER BY i'):
    row=json.loads(r);n+=1;why=judge(row,'vqa',i)
    k=cell(row,'vqa')
    if why:refused[why]+=1;continue
    bycell[k]+=1
    if k=='facing_pairs':pairs[row.get('pair_id')].add(row.get('facing'))
    if len(examples[k])<5:examples[k].append(dict(qid=row['qid'],row_sha256=digest(row)))
    if n%20000==0:print('vqa',n,dict(bycell),flush=True)
complete=sum(1 for v in pairs.values() if v=={'toward','away'})
out['streams']['vqa']=dict(database=db,read=n,refused=dict(refused),eligible_by_cell=dict(bycell),facing_complete_pairs=complete,facing_incomplete_pair_ids=sum(1 for v in pairs.values() if v!={'toward','away'}))
print('VQA',json.dumps(out['streams']['vqa'],default=str)[:1500],flush=True)
# Routing slices (row_sources): native intake as in F1 prod, then the same filters
from student_pilot.r2_adapters import normalize
from student_pilot.r2_intake import intake
from tests.test_r2_build9_recovery import envelope
def norm(raw):
    p=raw.get('provenance',{});si=raw.get('student_input',{})
    ind=si.get('frame_indices') or raw.get('frame_indices') or p['frame_indices']
    fr={raw['qid']:dict(fps=si.get('fps') or p.get('fps_source',{}).get('value') or 24.,total_num_frames=ind[-1]+1,frames=[dict(path='/u/'+str(i),sha256='a'*64,source_index=i) for i in ind])}
    return normalize(raw,fr)
RS=json.load(open(CFG['r1_training']['row_sources']['path']))
SRC={'recovery':RS['recovery']['source'],'absolute_distance':RS['absolute_distance']['source'],'units':dict(path='/scratch/jjyeung/orch_n30/rows_r1/out/vehN_units/repaired/rows_slice.jsonl',sha256=None)}
rout={}
for fam,pin in SRC.items():
    path=Path(pin['path']);h=hashlib.sha256(path.read_bytes()).hexdigest()
    if pin['sha256'] and h!=pin['sha256']:raise SystemExit('slice sha differs '+fam)
    lines=path.read_text().splitlines();cnt=collections.Counter();cells=collections.Counter();units=collections.Counter()
    for k0 in range(0,len(lines),400):
        rows=[norm(json.loads(l)) for l in lines[k0:k0+400]]
        for r in rows:r.update(answer_form='routed',response_heads=['pose','depth'])
        d=Path(tempfile.mkdtemp(dir=W/'tmp'));p=envelope(d,copy.deepcopy(rows),'routing',fam);m=json.loads(p.read_text());m['extent_receipt']=EXT;p.write_text(json.dumps(m))
        adm,repo=intake(p);ok={a['row']['qid'] for a in adm}
        for r in rows:
            cnt['read']+=1
            if r['qid'] not in ok:cnt['intake_refused']+=1;continue
            why=judge(r,'routing')
            if why:cnt['refused:'+why[:60]]+=1;continue
            c=cell(r,'routing');cells[c]+=1
            if fam=='units':
                from student_pilot.r2_units import asked_unit
                units[asked_unit(r)]+=1
            if len(examples['routing:'+c])<5:examples['routing:'+c].append(dict(qid=r['qid'],row_sha256=digest(r)))
    rout[fam]=dict(source=dict(path=str(path),sha256=h),counts=dict(cnt),cells=dict(cells),**({'asked_units':dict(units)} if units else {}))
    print('ROUTING',fam,rout[fam],flush=True)
out['streams']['routing_slices']=rout
json.dump(dict(out,examples=examples),open(W/'CENSUS.json','w'),indent=1,default=str)
print('DONE')
