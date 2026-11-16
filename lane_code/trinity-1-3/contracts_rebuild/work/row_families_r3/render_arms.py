"""CPU production-renderer samples. Run in a fresh interpreter for each arm."""
import argparse, copy, hashlib, json, math, sys, traceback
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np

L = Path(__file__).resolve().parents[2]
W = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument('--arm', choices=['base','off','on'], required=True)
ap.add_argument('--output', required=True)
ap.add_argument('--family',action='append',help='Restrict a reproduction to these exact family IDs.')
args = ap.parse_args()
tree = L/'work/trees'/('r6_base' if args.arm == 'base' else 'r6_r3')
sys.path[:0] = [str(tree), str(tree/'generator/derivgen_v7'), str(tree/'generator/ground_rows_out'), str(L/'work/tests_r3')]
if args.arm != 'base':
    from trace_format.contracts import contract_epoch
    epoch = contract_epoch(args.arm == 'on'); epoch.__enter__()
from fixtures_contracts import fixture, masks, own_geometry
from student_pilot import ground_lifting as backend
from derivgen import programs_v314 as P, ground_v313 as I, box_v313 as B, ground_v312 as G
from derivgen import ground_v313_distance as D
import render_gaps_v314 as gaps

results=[]
seen=set()
def profile(frame,event,arg):
    if event=='call':
        p=frame.f_code.co_filename
        prefix=str(tree)+'/'
        if p.startswith(prefix): seen.add(p[len(prefix):])

def clean(x):
    if isinstance(x,np.ndarray): return x.tolist()
    if isinstance(x,np.generic): return x.item()
    if isinstance(x,dict): return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)): return [clean(v) for v in x]
    return x

def capture(family,variant,entry,fn):
    if args.family and family not in args.family:return
    seen.clear();sys.setprofile(profile)
    try:
        row=fn()
        if not isinstance(row,dict): row={'target':row}
        result=dict(family=family,variant=variant,entry_point=entry,status='rendered',row=clean(row))
    except Exception as e:
        result=dict(family=family,variant=variant,entry_point=entry,status='refused',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
    finally: sys.setprofile(None)
    result['executed_source_paths']=sorted(seen)
    results.append(result)

def clip_for(kind,index):
    geo=fixture(kind)[1]()
    # Keep the GT sensor adapter, calibration and trajectory from the r3 fixture.
    # Disjoint instance rasters and depth bands provide three non-collinear centres.
    geo.depth_grid=np.full((32,33,33),2.0+index*.05)
    geo.depth_grid[:,:,12:20]=4.5+index*.05
    geo.depth_grid[:,:,23:]=2.7+index*.05
    geo.grid_uv=np.linspace(0,1000,33)
    geo.ids=np.array([1,2,3]);geo.labels=['chair','table','plant']
    geo.inst=np.zeros((32,24,32),int)
    for iid,x,start in [(1,3,1),(2,24,2),(3,13,3)]: geo.inst[start:start+4,8:16,x:x+5]=iid
    def mask(name):
        norm=name.lower().strip().rstrip('s')
        ids=[i for i,n in zip(geo.ids,geo.labels) if n==norm]
        return np.isin(geo.inst,ids),np.ones(32)
    return NS(geo=geo,masks=mask,programs=NS(T=NS(match_labels=lambda name,labels:[n for n in labels if n==name])))

def make_session(clip,typ):
    if typ in ('object_counting','relative_count'): return gaps.session(backend,clip,typ)
    return D.make_session(backend,clip,[],B.FusedBoxProvider(),multi_instance=True)

def item_for(typ,clip,qid):
    item=dict(qid=qid,type=typ,question='Compare the chair, table and plant.',options=[],roles={},gt_authority='synthetic CPU geometry; parity only',gt_answer='0',target_distance_rule=B.RULE_GRID)
    probe=make_session(clip,typ)
    if typ=='object_counting': item.update(roles={'obj':'chair'},question='How many chairs are in this room?',gt_answer='1')
    elif typ=='relative_count': item.update(roles={'a':'chair','b':'table'},question='Are there more chairs than tables?',options=['A. more','B. fewer','C. equal number'],gt_answer='C')
    elif typ=='object_appearance_order': item.update(roles={'cands':['chair','table']},question='Which appears first, chair or table?',options=['A. chair','B. table'],gt_answer='A')
    elif typ=='object_size_estimation':
        probe.execute('<ground obj="chair" mode="box">')
        value=probe.box_registry.records[probe.box_registry.bindings['chair'][0]]['value']
        item.update(roles={'a':'chair'},question='What is the longest side of the chair in centimeters?',gt_answer=str(round(100*max(value['lengths']))))
    elif typ in ('object_abs_distance','object_rel_distance') or typ.startswith('camera_obj_'):
        names=['chair','table','plant'] if typ=='object_rel_distance' else ['chair','table'] if 'rel_dist' in typ else ['chair'] if typ.startswith('camera') else ['chair','table']
        for n in names: probe.execute(f'<ground obj="{n}" mode="box">')
        if typ.startswith('camera'):
            item['roles']=dict(frame=4,names=names)
            call='<gap camera="4"'+''.join(f' b="{n}"' for n in names)+' rule="box_grid_5cm">'
        else:
            item['roles']=dict(target='chair',cands=names[1:]) if typ=='object_rel_distance' else dict(a='chair',b='table')
            call='<gap a="chair"'+''.join(f' b="{n}"' for n in names[1:])+' rule="box_grid_5cm">'
        probe.execute(call);values=B.replay_audit(probe.events)
        if 'rel_dist' in typ:
            candidates=names if typ.startswith('camera') else names[1:]
            item['options']=[f'{chr(65+i)}. {n}' for i,n in enumerate(candidates)]
            item['gt_answer']=chr(65+int(np.argmin(values)))
        else:item['gt_answer']=B.number(values[0],2)
    elif 'direction' in typ:
        item.update(roles=dict(stand='chair',face='table',query='plant',ccw=True),question='At the chair facing the table, how many degrees counterclockwise to face the plant?')
        for n in ('chair','table','plant'): probe.execute(f'<ground obj="{n}">')
        s,f,q=[probe.objects[n]['f1'] for n in ('chair','table','plant')]
        u,v=[np.asarray(p)[[0,2]]-np.asarray(s)[[0,2]] for p in (f,q)]
        theta=math.degrees(math.atan2(u[0]*v[1]-u[1]*v[0],u@v))
        if typ=='absolute_direction_object': item['gt_answer']=str(round(theta)%360)
        else:
            options=['left','right'] if typ.endswith('easy') else ['left','right','back'] if typ.endswith('medium') else ['front-left','front-right','back-left','back-right']
            item['options']=[f'{chr(65+i)}. {n}' for i,n in enumerate(options)]
            item['gt_answer']='A'
    return item

families=list(dict.fromkeys(P.TYPES))
families=[t for t in families if t!='room_size_estimation']
specs={}
spec_path=W/'items.json'
if args.arm!='base':specs=json.loads(spec_path.read_text())
for typ in families:
    for kind in ('landscape','nadir_positive'):
        for index in range(3):
            key=f'{typ}/{kind}/{index}'
            def run(typ=typ,kind=kind,index=index,key=key):
                clip=clip_for(kind,index)
                # Freeze baseline labels and inputs across arms. These are parity fixtures,
                # not independent benchmark truth or evidence for answer accuracy.
                if args.arm=='base':specs[key]=item_for(typ,clip,key)
                return P.render(copy.deepcopy(specs[key]),make_session(clip,typ),lambda s:len(s.split()))
            capture('ground/'+typ,f'{kind}/{index}','derivgen.programs_v314.render',run)
if args.arm=='base' and not args.family:spec_path.write_text(json.dumps(specs,indent=2))

# Production room preparation includes the render, sensor replay, packing and validation.
def room(index,prepared):
    from derivgen import room_v314 as R
    from derivgen.room_rows_v314 import QUESTION
    from tokenizers import Tokenizer, AddedToken
    from tokenizers.models import WordLevel
    from tokenizers.pre_tokenizers import Whitespace
    import render_room_v314
    class Sensor:
        kind='gt'
        depth=np.full((32,24,32),2.+index*.1,dtype=np.float32)
        K=np.array([[20.,0.,16.],[0.,20.,12.],[0.,0.,1.]])
        def cam(self,k):return np.diag([1.,-1.,-1.]),np.zeros(3)
        def has(self,k):return True
        def frame_of(self,k):return k
    geo=Sensor(); frames=list(range(32)); canonical='scannet/fixture_00'
    pin=dict(path='synthetic-room-sensor',sha256=hashlib.sha256(geo.depth.tobytes()).hexdigest())
    it=dict(qid=f'room/{index}',type='room_size_estimation',roles={},question=QUESTION,options=[],gt_answer=R.measure(geo)['area_m2'],gt_authority=dict(gt=pin,frame_indices=frames,canonical=canonical))
    if not prepared:return P.render(it,I.Session(backend,geo,None,multi_instance=True,geometry_mode='sensor'),lambda s:len(s.split()))
    tok=Tokenizer(WordLevel({'[UNK]':0},unk_token='[UNK]'));tok.pre_tokenizer=Whitespace();tok.add_tokens([AddedToken('<ground',normalized=False)])
    raw,packed=render_room_v314.prepare(it,NS(geo=geo,masks=None),backend,tok,canonical=canonical,pin=pin,frames=frames,dev=set())
    return dict(raw=raw,packed=packed,target=packed['target'],events=packed['events'])
for prepared in (False,True):
    for i in range(3):capture('room/prepared' if prepared else 'ground/room_size_estimation',f'sensor/{i}','render_room_v314.prepare' if prepared else 'derivgen.programs_v314.render',lambda i=i,p=prepared:room(i,p))

# Adapters run on actual generated rows; do not manufacture response text.
ground_results=list(results)
for family,entry in [('adapter/native','student_pilot.e2e_routing_rows.adapt_generated'),('adapter/ground','student_pilot.ground_rows.render_ground')]:
    selected=[r for r in ground_results if r['family']=='ground/object_abs_distance' and r['status']=='rendered']
    for source in selected:
        def adapt(source=source,family=family):
            row=copy.deepcopy(source['row'])
            if family=='adapter/native':
                from student_pilot.e2e_routing_rows import adapt_generated
                return adapt_generated(row,dict(question=row['question'],options=row['options']),dataset='synthetic',scene='fixture')
            from student_pilot.ground_rows import render_ground
            events=[dict(kind='ground_trace_start',trace_revision='3.14')];cursor=0
            for k,e in enumerate(row['events']):
                block=e['call']+'\n'+e['response'];start=row['suffix'].index(block,cursor)
                if start>cursor:events.append(dict(kind='canonical_text',text=row['suffix'][cursor:start]))
                events.extend([dict(kind='ground_call',token=e['call']+'\n',call_id=str(k)),dict(kind='ground_response',text=e['response'],call_id=str(k))]);cursor=start+len(block)
            events.append(dict(kind='canonical_text',text=row['suffix'][cursor:]))
            target,spans,segments=render_ground(events,row['answer'])
            return dict(target=target,events=events,spans=spans,segments=segments,question=row['question'])
        capture(family,source['variant'],entry,adapt)

# The scheduled-sampling renderer is the production path for pose, depth, move and turn.
for name in ('pose','depth_at','move','turn'):
    for kind in ('landscape','nadir_positive'):
        for i in range(3):
            def routing(name=name,kind=kind,i=i):
                from student_pilot import carrier_c1_routing as C
                geo=own_geometry(fixture(kind)[1]())
                arguments={'frame':i+1} if name=='pose' else {'from':1,'to':i+2} if name in ('move','turn') else {'frame':i+2,'pts':[[300+i*50,500]]}
                token=f'<pose frame={i+1}>' if name=='pose' else f'<{name} from=1 to={i+2}>' if name in ('move','turn') else f'<depth_at frame={i+2} pts=[({300+i*50},500)]>'
                event=dict(kind='tool_response',call_id='c1',name=name,text='fixture placeholder')
                if name=='depth_at':event['points']=[dict(label='P1',requested_frame=i+2,actual_frame=i+2)]
                events=[dict(kind='plan',text='Read the requested geometry.'),dict(kind='tool_call',call_id='c1',name=name,arguments=arguments,token=token),event]
                target,spans,segments=C.rerender(dict(events=events,answer='<answer>observed</answer>',trace_revision='3.14'),geo)
                # Preserve the actual returned response bytes in audit events.
                body=target[spans[0]['start']:spans[0]['end']]
                return dict(target=target,events=[dict(call=token,response=body)],spans=spans,segments=segments)
            capture('routing/'+name,f'{kind}/{i}','student_pilot.carrier_c1_routing.rerender',routing)

# An untouched native serializer provides a control for route-plan prose and events.
for i in range(3):
    def canonical(i=i):
        from derivgen.canon_render import render
        events=[dict(kind='plan',text='Walk from the chair toward the table.'),dict(kind='canonical_text',text='Turn left toward the plant.'),dict(kind='decision',result='left')]
        return dict(render(events,chr(65+i)),events=events)
    capture('control/canonical_route',f'route/{i}','derivgen.canon_render.render',canonical)

for kind in ('landscape','nadir_positive'):
    for i in range(3):
        def pose_row(kind=kind,i=i):
            from student_pilot.pose_samples import build_row
            contract,_=fixture(kind)
            source=dict(scene='fixture',dataset='synthetic',student_input=dict(frames=[f'frame{k}.png' for k in range(32)],frame_indices=list(range(32)),timestamps=list(range(32)),fps=1,total_num_frames=32))
            return build_row(source,dict(c2w=contract.camera_to_world,intrinsics=contract.K,raster_hw=[480,640]),i,17)
        capture('control/pose_only',f'{kind}/{i}','student_pilot.pose_samples.build_row',pose_row)

exec(compile((W/'extra_families.py').read_text(),str(W/'extra_families.py'),'exec'))
exec(compile((W/'program_families.py').read_text(),str(W/'program_families.py'),'exec'))
Path(args.output).write_text(json.dumps(dict(arm=args.arm,tree=str(tree),fixture_source=__file__,results=results),indent=2,allow_nan=False))
print(json.dumps(dict(arm=args.arm,rendered=sum(r['status']=='rendered' for r in results),refused=[(r['family'],r['variant'],r.get('error')) for r in results if r['status']!='rendered'])))
