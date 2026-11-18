"""Pinned evaluator entry point shared by SFT and RL checkpoints."""
import argparse
import importlib
import inspect
import json
from pathlib import Path
if not __package__:
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    __package__='h1eval'
from .items import K, build, load_manifest, sha, digest, pin
from .statistics import aggregate, paired, DRAWS, SEED
from .modes import mode_key, DEFAULT_MODES


def code_hash(root=None):
    root = Path(root or Path(__file__).parent)
    return digest([(str(p.relative_to(root)),sha(p)) for p in sorted(root.rglob('*'))
                   if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'])


def export_hash(root, cache=None, allocation=None):
    root = Path(root).resolve()
    if root.parts[1:2] in [('home',),('data',),('data2',),('data3',)]:
        raise ValueError('Stage the export on /scratch')
    files = sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    if not files:raise ValueError('Export directory is empty')
    if any(not (p.resolve().is_relative_to('/scratch') or p.resolve().is_relative_to('/dev/shm')) for p in files):
        raise ValueError('Export files must resolve to /scratch or /dev/shm')
    def compute():return digest([(str(p.relative_to(root)),sha(p)) for p in files])
    if cache is None:return compute()
    if not allocation:raise ValueError('Export cache requires allocation identity')
    import fcntl
    cache=Path(cache);cache.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    def identity():
        return dict(root=str(root),allocation=allocation,files=[
            [str(p.relative_to(root)),str(p.resolve()),p.stat().st_dev,p.stat().st_ino,
             p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ctime_ns] for p in files])
    with cache.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        before=identity()
        if cache.exists():
            value=json.loads(cache.read_text())
            if value['identity']==before:return value['full_sha256']
        result=compute()
        if identity()!=before:raise ValueError('Export changed while hashing')
        cache.write_text(json.dumps(dict(identity=before,full_sha256=result)))
        return result


def modes(text):
    result=[]
    defaults={'scale_scene':('k',2.),'scale_translation':('k',2.),'rotate_translation':('deg',180.)}
    for part in text.split(','):
        name,_,value=part.strip().partition(':')
        if not name or name=='none':continue
        if name not in (*defaults,'negate_turn','donor','gt'):raise ValueError('Unknown mode '+name)
        mode={'name':name}
        if name in defaults:
            key,default=defaults[name];mode[key]=float(value) if value else default
        elif value:raise ValueError('Unexpected mode parameter')
        result.append(mode)
    if len({mode_key(v) for v in result})!=len(result):raise ValueError('Duplicate modes')
    return result


def gt_pins(directory,items):
    if directory is None:return []
    return [pin(Path(directory)/(digest(item['id'])+'.npz')) for item in items]


def write_curve(out,rows,manifest,export,settings,frames,arms,interventions,gt_files=()):
    curve=dict(schema='h1-curve-v1',lineage=settings['lineage'],step=settings['step'],
               export_sha256=export_hash(export),item_set_sha256=manifest['item_set_sha256'],
               evaluator_code_sha256=code_hash(),frames=frames,arms=arms,
               gt_inputs_sha256=digest([(Path(p['path']).name,p['sha256']) for p in gt_files]),gt_inputs=list(gt_files),
               modes=[{'name':'none'},*interventions],bootstrap=dict(draws=DRAWS,seed=SEED,unit='room',interval=.95),
               per_type=aggregate(rows),item_count=manifest['count'],
               dependencies=dict(expected_calls=pin(K/'rows/expected_calls.py'),
                                 room_exclusions=pin(K/'tree/student_pilot/h1_r0.py'),
                                 loader_sha256=settings.get('loader_sha256')),
               fixture=bool(settings.get('fixture',False)))
    if manifest.get('constants'):
        curve['no_information_f32']=manifest['constants']
        from .runner import table
        Path(out,'report.md').write_text(table(rows,manifest['constants']))
    Path(out,'curve.json').write_text(json.dumps(curve,indent=2,sort_keys=True,allow_nan=False)+'\n')
    return curve


def run(args):
    from .runner import run as evaluate
    manifest=load_manifest(args.items)
    if args.frames!=32:raise ValueError('Only the validated 32-frame contract is supported')
    arms=args.arms.split(',')
    if not arms or len(set(arms))!=len(arms) or any(a not in ('own','tower') for a in arms):raise ValueError('Invalid arms')
    interventions=modes(args.modes)
    from .items import read_contract
    read_contract(manifest,arms,interventions)
    root=Path(args.export).resolve();settings=json.loads((root/'h1eval.json').read_text())
    if settings.get('lineage') not in ('SFT','RL') or type(settings.get('step')) is not int or settings['step']<0:
        raise ValueError('Export binding requires lineage SFT/RL and nonnegative integer step')
    # A pinned loader binds checkpoint/media to the existing reader; it owns no scoring.
    module,name=settings.get('loader','h1eval.native:load').split(':')
    loader=getattr(importlib.import_module(module),name)
    source=Path(inspect.getsourcefile(loader))
    if settings.get('loader_sha256')!=sha(source):raise ValueError('Export loader source pin mismatch')
    out=Path(args.out).resolve()
    if out==root or root in out.parents:raise ValueError('Run output must be outside the export')
    if out.exists() and any(out.iterdir()):raise ValueError('Run output must be fresh')
    before=export_hash(root)
    scorer_before=code_hash()
    gt_files=gt_pins(args.gt,manifest['items'])
    factory=loader(root,settings,frames=args.frames,gt=Path(args.gt) if args.gt else None,items=manifest['items'])
    rows=evaluate([{**r,'item_set':manifest['name']} for r in manifest['items']],factory,arms,interventions,out)
    if export_hash(root)!=before:raise ValueError('Export changed during evaluation')
    if code_hash()!=scorer_before:raise ValueError('Evaluator changed during evaluation')
    if gt_pins(args.gt,manifest['items'])!=gt_files:raise ValueError('GT inputs changed during evaluation')
    for row in rows:row['item_set']=manifest['name']
    curve=write_curve(out,rows,manifest,root,settings,args.frames,arms,interventions,gt_files)
    return dict(output=str(out),items=len(rows),export_sha256=curve['export_sha256'])


def read_run(path):
    root=Path(path);curve=json.loads((root/'curve.json').read_text())
    rows=[json.loads(s) for s in (root/'items.jsonl').read_text().splitlines() if s.strip()]
    return curve,rows


def pair(a,b):
    x,left=read_run(a);y,right=read_run(b)
    if x['item_set_sha256']!=y['item_set_sha256']:raise ValueError('Cannot pair different item-set hashes')
    for field in ('frames','evaluator_code_sha256','dependencies','fixture','gt_inputs_sha256'):
        if x.get(field)!=y.get(field):raise ValueError('Cannot pair different '+field)
    modes_a={v['name']:v for v in x.get('modes',[])}
    modes_b={v['name']:v for v in y.get('modes',[])}
    if any(modes_a[k]!=modes_b[k] for k in modes_a.keys() & modes_b.keys()):
        raise ValueError('Cannot pair different intervention parameters')
    return dict(direction='b_minus_a',item_set_sha256=x['item_set_sha256'],
                bootstrap=dict(draws=DRAWS,seed=SEED,unit='room'),per_type=paired(left,right))


def curve(paths):
    records=[(p,json.loads((Path(p)/'curve.json').read_text())) for p in paths]
    records.sort(key=lambda x:({'SFT':0,'RL':1}.get(x[1]['lineage'],2),x[1]['step'],str(x[0])))
    lines=['| Lineage | Step | Type / arm / mode | M1 calls | M2 | M3 follow / stick | M4 | No-information f32 | Export SHA256 | Item-set SHA256 | Evaluator SHA256 | Run |',
           '|---|---:|---|---:|---|---|---:|---:|---|---|---|---|']
    for p,r in records:
        groups=[(kind,arm,mode,values) for kind,arms in sorted(r.get('per_type',{}).items())
                for arm,modes in sorted(arms.items()) for mode,values in sorted(modes.items())]
        for kind,arm,mode,values in groups or [('', '', '', {})]:
            def metric(m,k):
                v=values.get(m,{}).get(k,{}).get('value')
                return '—' if v is None else f'{v:.4f}'
            m2=', '.join(k+'='+metric('M2',k) for k,v in sorted(values.get('M2',{}).items()) if isinstance(v,dict) and 'value' in v) or '—'
            constant=r.get('no_information_f32',{}).get(kind,{})
            constant=constant.get('dev_mra_f32',constant.get('dev_acc'))
            row=(r['lineage'],r['step'],' / '.join((kind,arm,mode)),metric('M1','call_rate'),m2,
                 metric('M3','follow')+' / '+metric('M3','stick'),metric('M4','score'),
                 '—' if constant is None else f'{constant/100:.4f}',
                 r['export_sha256'],r['item_set_sha256'],r['evaluator_code_sha256'],p)
            lines.append('| '+' | '.join(str(v) for v in row)+' |')
    return '\n'.join(lines)


def main(argv=None):
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('items');s=p.add_subparsers(dest='action',required=True);p=s.add_parser('build')
    p.add_argument('--out',default=str(K/'items'));p.add_argument('--sets',default='revsi999,devs1_routed,devs1_direct_main,devs1_direct,r0dev')
    p.add_argument('--routed-tasks');p.add_argument('--direct-tasks');p.add_argument('--forward-tasks');p.add_argument('--away-tasks');p.add_argument('--r0dev-items')
    p=sub.add_parser('run')
    for key in ('export','items','out'):p.add_argument('--'+key,required=True)
    p.add_argument('--arms',default='own');p.add_argument('--modes',default=DEFAULT_MODES);p.add_argument('--frames',type=int,default=32);p.add_argument('--gt')
    p=sub.add_parser('pair');p.add_argument('--a',required=True);p.add_argument('--b',required=True)
    p=sub.add_parser('curve');p.add_argument('runs',nargs='+')
    args=parser.parse_args(argv)
    try:
        if args.command=='items':
            result=build(args.out,routed=args.routed_tasks,direct_tasks=args.direct_tasks,forward_tasks=args.forward_tasks,away_tasks=args.away_tasks,r0dev=args.r0dev_items,sets=args.sets.split(','))
            print(json.dumps(result,indent=2));return int(any(v['status']!='ready' for v in result.values()))
        if args.command=='run':result=run(args)
        elif args.command=='pair':result=pair(args.a,args.b)
        else:print(curve(args.runs));return 0
        print(json.dumps(result,indent=2,allow_nan=False));return 0
    except (ValueError,FileNotFoundError,KeyError) as error:
        parser.exit(2,str(error)+'\n')


if __name__=='__main__':raise SystemExit(main())
