#!/usr/bin/env -S /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B
"""Frozen BOX dev check. Run with python -I -s -B; all outputs stay in boxdev."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'): os.environ[k]='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
import argparse, ast, inspect, json, platform, re, sys, time, tracemalloc
from pathlib import Path
from collections import Counter
HERE=Path(__file__).resolve().parent
os.chdir(HERE)
if os.getpriority(os.PRIO_PROCESS,0)<10: os.nice(10-os.getpriority(os.PRIO_PROCESS,0))
sys.path.insert(0,str(HERE.parent/'r1'))
import relift as R
import numpy as np
RULE='vote_10_3_best'
VENDOR=HERE.parent/'r2/vendor'

def declarations(path, names, bindings):
    nodes=[n for n in ast.parse(path.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    assert len(nodes)==len(names)
    ns=dict(bindings);exec(compile(ast.Module(nodes,[]),str(path),'exec'),ns)
    return [ns[n] for n in names]

def setup():
    pins=HERE/'SOURCE_PINS.json'
    for path,expected in json.loads(pins.read_text()).items():
        if R.sha(path)!=expected:raise ValueError('source pin changed: '+path)
    R.dependencies()
    global fusion_box,lift_frames,session_distance
    fusion_box,=declarations(VENDOR/'ladder_math_v2.py',['fusion_box'],dict(np=np,Counter=Counter))
    lift_frames,session_distance=declarations(VENDOR/'ladder_pricing.py',['lift_frames','session_distance'],dict(np=np,re=re,fusion_box=fusion_box))

def write(path,obj):
    path=Path(path).resolve()
    if not path.is_relative_to(HERE):raise ValueError('output must stay in boxdev')
    R.dump(path,obj)

def parity_gate(args):
    # Execute rank 1's unmodified run prefix through its registered gate. No
    # funnel, intervention, label score, or vote is read/evaluated in this prefix.
    source=inspect.getsource(R.run).split('    # No intervention is evaluated')[0]
    source=source.replace('def run(args):','def _gate(args):',1)
    source+='    return result, refs, rows, depths, computed\n'
    ns=dict(vars(R));ns['dump']=write
    exec(compile(source,str(Path(R.__file__)),'exec'),ns)
    result=ns['_gate'](args)
    if not isinstance(result,tuple):raise ValueError('rank 1 parity gate did not pass')
    report,refs,rows,depths,computed=result
    if len(refs)!=150 or len(report['parity']['items'])!=150:raise ValueError('expected all 150 dev items')
    return result

def base_objects(names,masks,g):
    values=[];objects={}
    for name in names:
        box,obj=R.fit_lift(name,masks[name],g)
        values.append(box);objects[name]=obj
    return values,objects

def arm(names,masks,g,kind):
    """Same Session guard/renderer and exact cached grid-distance kernel in both arms."""
    from trace_format.ground_v313 import Session
    from student_pilot import ground_lifting
    if kind=='base':values,objects=base_objects(names,masks,g);fitted=dict(zip(names,values))
    else:objects={n:lift_frames(n,masks[n],g,R.grounding) for n in names}
    class Provider:
        provider_id='boxdev_'+kind
        def __call__(self,name,obj,geometry,best):
            if kind=='base':return fitted[name]
            raw=fusion_box(obj['points'],obj['best'],RULE,R.grounding.min_area_box)
            return R.boxes.in_f1(g,raw['centroid'],raw['axesLengths'],raw['normalizedAxes'])
    class S(Session):
        def _instances(self,name):
            obj=objects[name]
            return [dict(obj,instance_id=name,first=min(obj['frames']))] if obj['seen'] else []
    s=S(ground_lifting,g,None,instances=lambda n:(),program_version='3.14',multi_instance=True,geometry_mode='sensor',box_provider=Provider())
    responses={n:s.execute(f'<ground obj="{n}" mode="box">') for n in names}
    # boxes.ground retains the deployed raw-mask frame guard. Reuse rank 1's
    # exact grid-gap acceleration after it has accepted both operands.
    values=[]
    for n in names:
        labels=s.box_registry.bindings.get(n,[])
        values.append(s.box_registry.records[labels[0]]['value'] if s.box_registry.states.get(n)=='ok' and len(labels)==1 else None)
    gap=R.round_gap(R.gap_value(values))
    diag=[]
    for n,obj in objects.items():
        frames=obj['frames'];visible=obj['visible']
        diag.append(dict(name=n,grounded_frames=frames,visible_frames=visible,
          lift_calls=len(visible)+(int(obj['seen']) if kind=='base' else 0),
          retained_point_bytes=sum(np.asarray(p,float).nbytes for p in obj['points'].values())))
    return dict(gap_m=gap,responses=responses,objects=diag)

def timed(names,masks,g,kind):
    start=time.perf_counter();result=arm(names,masks,g,kind);result['seconds']=time.perf_counter()-start
    tracemalloc.start();arm(names,masks,g,kind);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    result['peak_traced_bytes']=peak
    return result

def statistics(rows,refs):
    boot=R.Bootstrap(refs);out=[]
    for dataset in ('all','ARKit','ScanNet','ScanNet++'):
        selected=[r for r in rows if dataset=='all' or r['dataset']==dataset]
        diff=boot.metric(selected,'delta');hi=diff['ci95'][1] if diff['ci95'] else None
        out.append(dict(dataset=dataset,n=len(selected),rooms=len({r['room'] for r in selected}),
          base=boot.metric(selected,'base'),vote=boot.metric(selected,'vote'),paired_difference=diff,
          does_not_lose=None if hi is None else hi>=0))
    return out

def hardware():
    cpu=next((l.split(':',1)[1].strip() for l in Path('/proc/cpuinfo').read_text().splitlines() if l.startswith('model name')),'unknown')
    return dict(host=platform.node(),cpu=cpu,python=sys.version,threads=1,processes=1,nice=os.getpriority(os.PRIO_PROCESS,0))

def execute(args):
    for path in (args.depth,args.receipt,args.capture):
        if not path.resolve().is_relative_to('/scratch'):raise ValueError('inputs must be local /scratch')
    if not args.depth.is_file():raise FileNotFoundError('served depth dump missing: '+str(args.depth))
    setup()
    result,refs,rows,depths,computed=parity_gate(args)
    result.update(status='running',rule=RULE,hardware=hardware(),rows=[])
    for iid,ref in refs.items():
        g=R.restore(depths[ref['capture']]);names=R.names(ref)[0]
        objects={o['name'].strip().lower():o for o in rows[iid]['objects']}
        masks={n:R.masks_array(objects.get(n.strip().lower(),{}).get('selected_masks',{})) for n in names}
        base=timed(names,masks,g,'base')
        if base['gap_m']!=computed[iid]['gap']:raise ValueError('base differs from relift cell (a): '+iid)
        vote=timed(names,masks,g,'vote')
        truth=float(ref['task']['ground_truth']);factor=R.unit_factor(ref['task']['question'])
        scores={k:100*R.official_mra(None if v['gap_m'] is None else v['gap_m']*factor,truth) for k,v in [('base',base),('vote',vote)]}
        ds={'arkitscenes':'ARKit','scannet':'ScanNet','scannetpp':'ScanNet++','scannetppv2':'ScanNet++'}[ref['capture'].split('/')[0]]
        result['rows'].append(dict(item_id=iid,capture=ref['capture'],room=ref['task']['room'],dataset=ds,
          **scores,delta=scores['vote']-scores['base'],measurements=dict(base=base,vote=vote)))
    result.update(status='complete',statistics=statistics(result['rows'],refs),base_equals_relift_a=True,
      measurement_scope='CPU lift + box + served guard/renderer + exact gap; excludes model inference, mask decode, depth restore and input IO. One untraced timing plus separate tracemalloc pass per arm/item; peak includes Python/NumPy tracked allocations, not total process RSS. Retained-point bytes are numeric payload only.',
      reading='Pass iff overall paired 95% room-bootstrap upper bound >= 0; dataset readings are descriptive.')
    result['propose_reader_change']=result['statistics'][0]['does_not_lose']
    for kind in ('base','vote'):
        result.setdefault('cost',{})[kind]={key:dict(mean=float(np.mean([r['measurements'][kind][key] for r in result['rows']])),max=float(max(r['measurements'][kind][key] for r in result['rows']))) for key in ('seconds','peak_traced_bytes')}
    result['cost']['mean_extra_peak_traced_bytes']=result['cost']['vote']['peak_traced_bytes']['mean']-result['cost']['base']['peak_traced_bytes']['mean']
    paths=[Path(R.__file__),Path(R.fmt.__file__),Path(R.grounding.__file__),Path(R.geometry.__file__),Path(R.boxes.__file__),Path(R.pose.__file__),Path(inspect.getfile(R.Bootstrap)),VENDOR/'ladder_math_v2.py',VENDOR/'ladder_pricing.py',args.capture,args.depth,args.receipt,HERE/'run.py']
    result['input_sha256'].update({str(p):R.sha(p) for p in paths})
    write(args.out,result)
    if (args.out.parent/'STOP').exists():
        write(args.out.parent/'STOP',dict(status='CLEARED',output=str(args.out),reason='Current run completed successfully'))
    return 0

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--depth',type=Path,default=HERE.parent/'r1/returned/0.gz')
    p.add_argument('--receipt',type=Path,default=HERE.parent/'r1/returned/4.json')
    p.add_argument('--out',type=Path,default=HERE/'out/BOXDEV.json')
    p.add_argument('--capture',type=Path,default=R.BASE/'cap/t1.gz')
    args=p.parse_args(argv);args.half_only=False
    try:return execute(args)
    except Exception as e:
        # Preserve the rank-1 gate diagnostic when present, but never a stale
        # completed score table after any failure.
        report={}
        if args.out.is_file():
            try:report=json.loads(args.out.read_text())
            except (ValueError,OSError):report={}
            report={k:v for k,v in report.items() if k in ('parity','depth_free_gap_checks','gap_atol_m','required_object_fraction')}
        report.update(status='STOP',reason=type(e).__name__+': '+str(e),rows=[],statistics=[])
        write(args.out,report);write(args.out.parent/'STOP',report)
        print(report['reason'],file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
