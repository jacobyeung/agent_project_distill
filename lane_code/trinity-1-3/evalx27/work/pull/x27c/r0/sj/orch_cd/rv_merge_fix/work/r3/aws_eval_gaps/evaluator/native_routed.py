"""Official CP1 worker: one pinned policy, native own-head calls, standard 32 anchors."""
import argparse,fcntl,json,os,subprocess,sys,time
from collections import Counter
from pathlib import Path
from data import tasks_for
from evalpath.items import digest,pinned,sha256,assert_prompt_equal
from media import load
from routing import validate_table,action,record,CP1_SHA,PROTOCOL,route_report,reuse_direct,deadline_reached
from scoring import benchmark_summary,score_item
from worker import append,read_journal

def selected_tasks(cfg,cell):
    return sorted([t for s in cfg['datasets'] if s['benchmark'] in cell['benchmarks'] for t in tasks_for(s,cfg['roots'])],key=lambda t:(t['benchmark'],t['example_id']))

def row_from_cache(task,cache,cache_sha):
    arrays,audit=load(task,'duplicate',cache,cache_sha)
    receipt=json.loads(pinned(dict(path=str(Path(cache)/audit['frame_receipt']['path']),sha256=audit['frame_receipt']['sha256'])).read_text())
    meta=audit['metadata']
    frames=[dict(path=str(Path(cache)/p['path']),sha256=p['sha256']) for p in receipt['frames'][::2]]
    row=dict(qid=task['example_id'],dataset=task['dataset'],scene=task['scene_name'],student_input=dict(
        frames=frames,frame_indices=meta['frames_indices'][::2],timestamps=[x/meta['fps'] for x in meta['frames_indices'][::2]],
        fps=meta['fps'],total_num_frames=meta['total_num_frames'],question=task['question'],options=task['options']))
    if len(frames)!=32:raise ValueError('Native routed read requires exactly 32 decoded frames')
    return row,audit

def validate_record(r,t,binding,table_sha,selected):
    if (r.get('binding')!=binding or r.get('route_table_sha256')!=table_sha or r.get('route_action')!=selected
        or r.get('checkpoint_sha256')!=CP1_SHA or r.get('protocol')!=PROTOCOL or r.get('frames')!=32 or r.get('layout')!='duplicate'):
        raise ValueError('Routed journal binding/policy/model differs')
    for key in ('benchmark','example_id','question_type','ground_truth','options','question','scene_name','revsi_tier','video_sha256','source_frame_indices'):
        if r.get(key)!=t.get(key):raise ValueError('Routed journal task/tier differs')
    if r.get('status')=='complete':
        expected=record(t,r['decode'],selected,table_sha)
        if (r['raw_generation'],r['response_text'],r['score'])!=(expected['raw_generation'],expected['response_text'],expected['score']):
            raise ValueError('Routed journal score differs')

def worker(config,work,index,rank,cache_sha,attempt):
    import torch
    from evalpath.runtime import load_model,prompt_batch,generate
    from evalpath.routed_parity import run_suite
    from native_direct import native_generate
    from student_pilot.carrier_c1_run import move
    cfg=json.loads(Path(config).read_text());cell=cfg['cells'][index];routing=cfg['routing']
    table=validate_table(json.loads(pinned(routing['table']).read_text()), dev=cell['benchmarks']==['devrows']);table_sha=routing['table']['sha256']
    if cell.get('layout')!='duplicate':raise ValueError('Native layout must be duplicate')
    tasks=selected_tasks(cfg,cell);assigned=tasks[rank::cfg['gpus']]
    reusable={}
    for benchmark,pin in routing.get('direct_answers',{}).items():
        reusable.update(reuse_direct([t for t in tasks if t['benchmark']==benchmark],pin,table,cfg['routing'].get('direct_requests',{}).get(benchmark)))
    generation_tasks=[t for t in tasks if t['benchmark']+':'+t['example_id'] not in reusable]
    out=Path(cfg['output'])/str(index);out.mkdir(parents=True,exist_ok=True)
    binding=digest(dict(request=cfg['binding'],cell=index));mode=cell.get('route_mode','policy')
    choose=lambda t:action(table,t) if mode=='policy' else mode
    journal=out/f'g{rank}.jsonl'
    with (out/f'g{rank}.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        done=read_journal(journal,binding,cell['layout']);bykey={t['benchmark']+':'+t['example_id']:t for t in assigned}
        for key,r in done.items():
            if key not in bykey:raise ValueError('Resume shard differs')
            validate_record(r,bykey[key],binding,table_sha,choose(bykey[key]))
        for t in assigned:
            key=t['benchmark']+':'+t['example_id']
            if key in reusable and key not in done:
                if deadline_reached(cfg):break
                r=dict(reusable[key],binding=binding,route_table_sha256=table_sha,seconds=0)
                append(journal,r);done[key]=r
        if not generation_tasks:
            (out/f'p{rank}_{attempt}.json').write_text(json.dumps(dict(**{'pass':True},binding=binding,route_table_sha256=table_sha,reuse_only=True))+'\n')
            return
        if deadline_reached(cfg):return
        def progress(e):append(out/f'startup{rank}_{attempt}.jsonl',e)
        model,p,info=load_model('routed',routing['cfg'],artifact_pin=cfg['models']['cp1m200'],
            snapshot=cfg['models']['base']['path'],device='cuda:0',selected_trainer=routing['trainer'],on_stage=progress)
        # Parity uses production prompts and independent trainer re-encoding.
        probes=[row_from_cache(t,Path(work)/'f',cache_sha)[0] for t in generation_tasks[:5]]
        parity=run_suite(model,p,routing['cfg'],'routed',probes,max_new_tokens=16384)
        parity.update(binding=binding,route_table_sha256=table_sha,model=info)
        (out/f'p{rank}_{attempt}.json').write_text(json.dumps(parity)+'\n')
        if not parity['pass']:raise ValueError('Native P1/P2/P3 parity failed; no official generations admitted')
        generated_count=0;rate_start=time.monotonic()
        for task in assigned:
            key=task['benchmark']+':'+task['example_id']
            if key in done:continue
            if deadline_reached(cfg):
                print('Deadline reached before item '+key,flush=True);break
            started=time.monotonic();selected=choose(task)
            r=dict(task,key=key,binding=binding,status='error',route_action=selected,
                   route_table_sha256=table_sha,checkpoint_sha256=CP1_SHA,protocol=PROTOCOL,layout='duplicate',frames=32)
            try:
                row,audit=row_from_cache(task,Path(work)/'f',cache_sha);assert_prompt_equal(p,row)
                batch=move(prompt_batch(p,row,routing['cfg'],'routed'),'cuda:0')
                decoded=(generate(model,p,batch,'routed',16384) if selected=='routed' else native_generate(model,p,batch))
                r.update(record(task,decoded,selected,table_sha,audit))
                r['input_tokens']=int(batch['input_ids'].shape[1])
                grid=batch['video_grid_thw'][0].tolist()
                r['processed_height_width']=[grid[1]*16,grid[2]*16]
                r['visual_tokens_per_frame']=grid[0]*grid[1]*grid[2]/4/32
            except Exception as exc:r['error']=f'{type(exc).__name__}: {exc}'
            r['seconds']=time.monotonic()-started;append(journal,r)
            generated_count+=1
            print(json.dumps(dict(rank=rank,generated=generated_count,items_per_hour=3600*generated_count/max(time.monotonic()-rate_start,1e-9))),flush=True)

def merge_native(cfg,index,attempt):
    cell=cfg['cells'][index];tasks=selected_tasks(cfg,cell);out=Path(cfg['output'])/str(index)
    table=validate_table(json.loads(pinned(cfg['routing']['table']).read_text()), dev=all(c['benchmarks']==['devrows'] for c in cfg['cells']));table_sha=cfg['routing']['table']['sha256']
    binding=digest(dict(request=cfg['binding'],cell=index));records={};parity=True
    mode=cell.get('route_mode','policy')
    if cell.get('layout')!='duplicate':raise ValueError('Native merge layout differs')
    reusable={}
    for benchmark,pin in cfg['routing'].get('direct_answers',{}).items():
        reusable.update(reuse_direct([t for t in tasks if t['benchmark']==benchmark],pin,table,cfg['routing'].get('direct_requests',{}).get(benchmark)))
    for rank in range(cfg['gpus']):
        wanted={t['benchmark']+':'+t['example_id']:t for t in tasks[rank::cfg['gpus']]}
        path=out/f'g{rank}.jsonl'
        if path.exists():
            for line in path.read_text().splitlines():
                if not line.strip():continue
                try:r=json.loads(line)
                except json.JSONDecodeError:continue
                key=r['key']
                if key not in wanted:raise ValueError('Routed journal membership/shard differs')
                t=wanted[key];validate_record(r,t,binding,table_sha,action(table,t) if mode=='policy' else mode)
                if key in reusable:
                    expected=reusable[key]
                    if any(r.get(f)!=expected.get(f) for f in ('raw_generation','score','direct_source_pin','direct_source_request_pin','reused_direct')):
                        raise ValueError('Reused answer differs from pinned direct journal')
                elif r.get('reused_direct'):
                    raise ValueError('Unpinned reused answer')
                if key in records and records[key]['status']=='complete':raise ValueError('Duplicate completed routed generation')
                records[key]=r
        pp=out/f'p{rank}_{attempt}.json'
        p=json.loads(pp.read_text()) if pp.exists() else {}
        parity &= bool(p.get('pass')) and p.get('binding')==binding and p.get('route_table_sha256')==table_sha
    summary=dict(binding=binding,route_table_sha256=table_sha,protocol=PROTOCOL,layout=cell['layout'],benchmarks={},**route_report(table,tasks,mode))
    for benchmark in cell['benchmarks']:
        ts=[t for t in tasks if t['benchmark']==benchmark];rs=[r for r in records.values() if r['benchmark']==benchmark]
        summary['benchmarks'][benchmark]=benchmark_summary(rs,ts,parity)
        done=[r for r in rs if r['status']=='complete']
        summary['benchmarks'][benchmark].update(layout=cell['layout'],route_actions=summary['route_actions'][benchmark],absent_types=summary['absent_types'][benchmark],reused_direct=sum(r.get('reused_direct',False) for r in done),frames=32,temporal_input_frames=64,
            processed_height_width=dict(Counter('x'.join(map(str,r['processed_height_width'])) for r in done if r.get('processed_height_width'))),
            visual_tokens_per_frame=dict(Counter(str(r['visual_tokens_per_frame']) for r in done)))
    (out/f'summary_{attempt}.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/f'items_{attempt}.jsonl').write_text(''.join(json.dumps(r)+'\n' for _,r in sorted(records.items())))
    return summary

def launch(config,work):
    from frame_env import prepare_frames
    cfg=json.loads(Path(config).read_text());validate_table(json.loads(pinned(cfg['routing']['table']).read_text()), dev=all(c['benchmarks']==['devrows'] for c in cfg['cells']))
    cache_sha=prepare_frames(config,work);devices=os.environ['CUDA_VISIBLE_DEVICES'].split(',')
    if len(devices)!=cfg['gpus']:raise ValueError('GPU allocation differs')
    attempt=os.environ['SLURM_JOB_ID'];python=os.environ.get('EVALX_FRAME_PY',sys.executable)
    for index in range(len(cfg['cells'])):
        children=[]
        for rank,gpu in enumerate(devices):
            env=dict(os.environ,CUDA_VISIBLE_DEVICES=gpu,OMP_NUM_THREADS='1',PYTHONPATH=str(Path(__file__).parent))
            with (Path(work)/f'native{index}_{rank}.log').open('ab') as log:
                children.append(subprocess.Popen([python,'-B',__file__,config,str(work),str(index),str(rank),cache_sha,attempt],env=env,stdout=log,stderr=log))
        statuses=[p.wait() for p in children];merge_native(cfg,index,attempt)
        if any(statuses):raise RuntimeError('Native routed worker failed')

if __name__=='__main__':worker(sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),sys.argv[5],sys.argv[6])
