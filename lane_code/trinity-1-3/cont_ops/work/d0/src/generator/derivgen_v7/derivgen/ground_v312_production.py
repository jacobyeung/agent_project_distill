"""Resumable per-scene build. Execute in the approved host shell, not a private /dev/shm."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
import hashlib
import json
import os
from pathlib import Path
import signal
import time

from .ground_v312 import TYPES, RowRefusal, histogram, select_balanced
from .ground_v312_input import normalize
from .ground_v312_io import build, reference, sha
from .ground_v312_pack import training_row
from .ground_v312_quality import deduplicate, set_report


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def pin(path):
    return dict(path=str(Path(path).resolve()), sha256=sha(path))


def read(path):
    return json.loads(Path(path).read_text())


def next_dir(root, prefix):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    index=1
    while (root/f'{prefix}_{index:04d}').exists():index+=1
    path=root/f'{prefix}_{index:04d}';path.mkdir()
    return path


def completed(path, fingerprint):
    marker=Path(path)/'COMPLETE.json'
    if not marker.is_file():return None
    try:receipt=read(marker)
    except (ValueError,OSError):return None
    if receipt['fingerprint']!=fingerprint:raise ValueError('completed scene belongs to another input/code pin')
    for item in receipt['outputs']:
        if sha(item['path'])!=item['sha256']:raise ValueError('completed output pin mismatch')
    return receipt


def worker(config_path, scene_root, fingerprint):
    attempt=next_dir(scene_root,'attempt')
    started=time.monotonic()
    result=build(config_path,attempt/'build')
    outputs=[pin(path) for path in sorted((attempt/'build').glob('*')) if path.is_file()]
    receipt=dict(fingerprint=fingerprint,build=str(attempt/'build'),outputs=outputs,
                 elapsed_seconds=time.monotonic()-started,rows=result['candidates'])
    dump(Path(scene_root)/'COMPLETE.json',receipt)
    return receipt


def partition(args, scenes, config, run):
    marker=Path(args.output)/'PARTITION_DONE.json'
    if marker.is_file():
        part=read(marker)
        if part['fingerprint']!=run['fingerprint']:raise ValueError('partition pin mismatch')
        for item in part['outputs']:
            if sha(item['path'])!=item['sha256']:raise ValueError('partition output pin mismatch')
        return part
    directory=next_dir(args.output,'inputs')
    grouped=defaultdict(list);dispositions=Counter();seen=set();direct={}
    if args.direct_joins:
        with open(args.direct_joins) as f:
            for line in f:
                row=json.loads(line)
                if row['qid'] in direct:raise ValueError('duplicate direct join')
                direct[row['qid']]=row
    T=reference(args.rkit_root)[0].T
    with (directory/'normalization_refusals.jsonl').open('x') as refused:
        for path in args.input:
            with open(path) as source:
                for line in source:
                    row=json.loads(line)
                    qid=row['qid']
                    if qid in seen:raise ValueError('duplicate input qid')
                    seen.add(qid)
                    try:
                        if args.prepared_items:
                            item=row
                            if item['type'] not in TYPES:raise RowRefusal('direct_type')
                        else:item=normalize(row,scenes,T,direct.get(qid))
                    except RowRefusal as exc:
                        dispositions[str(exc)]+=1;refused.write(json.dumps(dict(qid=qid,reason=str(exc)))+'\n');continue
                    if item['scene'] not in scenes:raise ValueError('source scene missing from manifest')
                    grouped[item['scene']].append(item)
    normalized_rows=[r for items in grouped.values() for r in items]
    question_counts_before=set_report(normalized_rows)
    unique, duplicates = deduplicate(normalized_rows)
    grouped=defaultdict(list)
    for item in unique:grouped[item['scene']].append(item)
    selected=sorted(grouped)
    if args.max_scenes is not None:selected=selected[:args.max_scenes]
    configs={}
    for scene in selected:
        key=hashlib.sha256(scene.encode()).hexdigest()[:24]
        dest=directory/key;dest.mkdir()
        items=grouped[scene]
        if args.max_rows_per_scene is not None:items=items[:args.max_rows_per_scene]
        with (dest/'items.jsonl').open('x') as f:
            for row in items:f.write(json.dumps(row,allow_nan=False)+'\n')
        dump(dest/'scenes.json',{scene:scenes[scene]})
        cfg=dict(config,items=pin(dest/'items.jsonl'),scenes=pin(dest/'scenes.json'))
        dump(dest/'CONFIG.json',cfg);configs[scene]=str(dest/'CONFIG.json')
    outputs=[pin(path) for path in sorted(directory.glob('*/*')) if path.is_file()]
    outputs.append(pin(directory/'normalization_refusals.jsonl'))
    receipt=dict(fingerprint=run['fingerprint'],configs=configs,normalization_dispositions=dict(dispositions),
                 question_counts_before=question_counts_before,
                 duplicates_removed=duplicates, unique_questions_by_type=dict(Counter(r['type'] for r in unique)),
                 source_rows=len(seen),selected_scenes=len(configs),outputs=outputs)
    dump(marker,receipt)
    return receipt


def aggregate(args, scenes, fingerprints, run, partition_receipt):
    rows=[];counts=defaultdict(Counter);natural=Counter();receipts=[];all_candidates=0
    rules=defaultdict(Counter);miss_refusals=defaultdict(Counter);miss_rendered=0
    for scene in sorted(scenes):
        key=hashlib.sha256(scene.encode()).hexdigest()[:24]
        receipt=completed(Path(args.output)/'scenes'/key,fingerprints[scene])
        if receipt is None:raise ValueError('cannot aggregate incomplete scenes')
        receipts.append(receipt);root=Path(receipt['build']);r=read(root/'RECEIPT.json')
        all_candidates+=r['candidates']
        miss_rendered+=r['simulated_misses_rendered']
        for typ,values in r.get('operand_rule_refusals',{}).items():rules[typ].update(values)
        for typ,values in r.get('miss_candidate_refusals',{}).items():miss_refusals[typ].update(values)
        for typ,values in r['agreement'].items():
            counts[typ].update({k:v for k,v in values.items() if type(v) is int})
        natural.update(r['distance_bin_natural_gt_counts'])
        with (root/'gt_accepted.jsonl').open() as f:rows.extend(json.loads(line) for line in f)
    distribution=read(args.benchmark)
    edges=[0,.25,.5,1,2,4,8,16,None]
    bins=[dict(key=f'[{a},{b})',lo=a,hi=b) for a,b in zip(edges[:-1],edges[1:])]
    distribution['object_abs_distance']=dict(bins=bins,content={k:v for k,v in natural.items() if v},
        source='natural independent admitted-scene GT; ORCH 0533Z',cap_per_bin=args.distance_bin_cap)
    selected,balance=select_balanced(rows,distribution,args.per_type)
    selected_ids = {r['candidate_id'] for r in selected}
    for row in rows:
        row['balanced'] = row['candidate_id'] in selected_ids
    target=next_dir(args.output,'summary')
    for name,values in [('gt_accepted',rows),('balanced',selected)]:
        with (target/(name+'_training_rows.jsonl')).open('x') as f:
            for row in values:f.write(json.dumps(training_row(row),allow_nan=False)+'\n')
    result=dict(status='REVIEW-ONLY',fingerprint=run['fingerprint'],scenes=len(scenes),
                candidates=all_candidates,accepted=len(rows),balanced=len(selected),
                agreement=dict(counts),histogram_before=histogram(rows),histogram_after=histogram(selected),
                balance=balance,natural_gt_bin_counts=dict(natural),
                set_before=set_report(rows),set_after=set_report(selected),
                question_counts_before=partition_receipt.get('question_counts_before',{}),
                duplicates_removed=partition_receipt.get('duplicates_removed',{}),
                unique_questions_by_type=partition_receipt.get('unique_questions_by_type',{}),
                operand_rule_refusals={t:dict(c) for t,c in rules.items()},
                miss_candidate_refusals={t:dict(c) for t,c in miss_refusals.items()},
                canonical_wording_refusals={t:miss_refusals[t]['canonical_wording_contradiction'] for t in TYPES},
                realized_miss_rate=miss_rendered/max(1,all_candidates),
                realized_balanced_miss_rate=sum(bool(r['simulated_misses']) for r in selected)/max(1,len(selected)),
                simulated_miss_by_type={t:dict(selected=counts[t]['miss_selected'],rendered=sum(r['type']==t and bool(r['simulated_misses']) for r in rows),dropped_no_canonical=counts[t]['miss_dropped_no_canonical']) for t in TYPES},
                miss_rate_requested=args.miss_rate,simulated_misses=sum(bool(r['simulated_misses']) for r in rows),
                max_suffix_tokens=max((r['suffix_tokens'] for r in rows),default=0),
                admission='GT/replay/cap checks only; production membership, RGB joins, canonical-source admission and consumer form/total-token checks remain required',
                normalization=partition_receipt['normalization_dispositions'],
                scene_receipts=receipts,outputs=[pin(p) for p in sorted(target.glob('*.jsonl'))])
    dump(target/'RECEIPT.json',result);dump(Path(args.output)/'LATEST.json',dict(summary=str(target),receipt=pin(target/'RECEIPT.json')))
    return result


def main():
    p=argparse.ArgumentParser(__doc__)
    for name in ['manifest','gt-root','output','backend','spec','tokenizer','benchmark','rkit-root']:
        p.add_argument('--'+name,required=True)
    p.add_argument('--manifest-sha256',required=True)
    p.add_argument('--input',action='append',required=True)
    p.add_argument('--direct-joins')
    p.add_argument('--workers',type=int,default=7)
    p.add_argument('--per-type',type=int,default=10000)
    p.add_argument('--distance-bin-cap',type=int,default=1000)
    p.add_argument('--miss-rate',type=float,default=.10)
    p.add_argument('--miss-seed',type=int,default=0)
    p.add_argument('--set-policy',choices=['v2'],default='v2',help='deduplicate, shuffle and balance within option counts')
    p.add_argument('--backend-sha256',required=True,help='explicit reviewed lifting module pin')
    p.add_argument('--resume',action='store_true')
    p.add_argument('--resume-reason',choices=['user-stop','approved-rerun'])
    p.add_argument('--prepared-items',action='store_true',help='fixture/normalized input; raw CP2 rows are the default')
    p.add_argument('--max-scenes',type=int)
    p.add_argument('--max-rows-per-scene',type=int)
    p.add_argument('--stop-after-scenes',type=int,help='bounded stop/resume canary')
    args=p.parse_args()
    if not 1<=args.workers<=7:raise ValueError('use 1..7 workers, reserving one CPU for the coordinator')
    for key in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','RAYON_NUM_THREADS']:
        if os.environ.get(key)!='1':raise ValueError('set '+key+'=1 before launch')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise ValueError('hide GPUs')
    if args.resume and not args.resume_reason:raise ValueError('resume requires an explicit approved reason; never relaunch a cluster-killed run automatically')
    if sha(args.backend)!=args.backend_sha256:raise ValueError('backend pin mismatch')
    if sha(args.manifest)!=args.manifest_sha256:raise ValueError('manifest pin mismatch')
    scenes=read(args.manifest);gt_root=Path(args.gt_root).resolve()
    for entry in scenes.values():
        gt=Path(entry['gt']['path']).resolve()
        if not gt.is_relative_to(gt_root):raise ValueError('GT path escapes --gt-root')
        if not gt.is_file():raise FileNotFoundError(gt)
        if sha(gt)!=entry['gt']['sha256']:raise ValueError('GT input pin mismatch: '+str(gt))
    root=Path(args.output)
    if root.exists() and not args.resume:raise ValueError('output exists; resume explicitly or choose a new directory')
    root.mkdir(parents=True,exist_ok=True)
    P,_,_=reference(args.rkit_root)
    code=[pin(path) for path in sorted(Path(__file__).parent.glob('ground_v312*.py'))]
    code.extend(pin(Path(__file__).with_name(n+'.py')) for n in ['calculator','paraphrase','trace'])
    refs=[pin(path) for path in [P.__file__,P._reference.__file__,P.T.__file__,
           Path(args.rkit_root)/'rk/ground.py',Path(args.rkit_root)/'rk/scheme.py']]
    config=dict(backend=pin(args.backend),spec=pin(args.spec),tokenizer=pin(args.tokenizer),
                benchmark_distribution=pin(args.benchmark),rkit_root=args.rkit_root,reference_pins=refs,
                diagnostic_only=True,per_type=args.per_type,miss_rate=args.miss_rate,miss_seed=args.miss_seed,
                distance_bin_edges_m=[0,.25,.5,1,2,4,8,16,None],distance_bin_cap=args.distance_bin_cap)
    identity=dict(set_policy=args.set_policy,config=config,code=code,manifest=pin(args.manifest),sources=[pin(path) for path in args.input],
                  direct=pin(args.direct_joins) if args.direct_joins else None,prepared=args.prepared_items,
                  max_scenes=args.max_scenes,max_rows_per_scene=args.max_rows_per_scene)
    fingerprint=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
    run=dict(fingerprint=fingerprint,identity=identity)
    if (root/'RUN.json').exists() and read(root/'RUN.json')!=run:raise ValueError('resume input/code pins differ')
    dump(root/'RUN.json',run)
    part=partition(args,scenes,config,run)
    fingerprints={s:hashlib.sha256((fingerprint+sha(path)).encode()).hexdigest() for s,path in part['configs'].items()}
    pending=[];done=0
    for scene,path in part['configs'].items():
        dest=root/'scenes'/hashlib.sha256(scene.encode()).hexdigest()[:24]
        if completed(dest,fingerprints[scene]) is None:pending.append((scene,path,dest))
        else:done+=1
    stopping=[False]
    def stop(signum,frame):stopping[0]=True
    signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
    launched=0
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        active={}
        while pending or active:
            while pending and len(active)<args.workers and not stopping[0]:
                if args.stop_after_scenes is not None and launched>=args.stop_after_scenes:
                    stopping[0]=True;break
                scene,path,dest=pending.pop(0);future=pool.submit(worker,path,str(dest),fingerprints[scene]);active[future]=scene;launched+=1
            if not active:break
            ready,_=wait(active,return_when=FIRST_COMPLETED)
            for future in ready:
                scene=active.pop(future)
                try:receipt=future.result()
                except BaseException as exc:
                    dump(root/'FAILED.json',dict(scene=scene,error=repr(exc)));raise
                done+=1;print(json.dumps(dict(scene=scene,completed=done,rows=receipt['rows'])),flush=True)
    if pending:
        dump(root/'STOPPED.json',dict(completed=done,pending=len(pending),fingerprint=fingerprint))
        print(json.dumps(dict(status='STOPPED',completed=done,pending=len(pending))))
        return
    result=aggregate(args,part['configs'],fingerprints,run,part)
    print(json.dumps({k:result[k] for k in ['status','scenes','candidates','accepted','balanced']}))


if __name__=='__main__':main()
