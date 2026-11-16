"""One native vLLM engine per GPU; no model heads or routing hooks."""
import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import time
from data import tasks_for
from evalpath.items import digest
from media import load,kwargs
from parity import prompt,compare,probe_tasks
from scoring import score_item
from cells import frame_count,check_layout
from think_settings import sampling, select_tasks


def read_journal(path, binding, layout):
    from journal import records, retain
    rows={}
    for row,_ in records(path):
        if row.get('binding')!=binding:
            raise ValueError('Resume binding differs')
        check_layout(row,layout)
        if 'annotation_version' in row:
            raise ValueError('Historical annotated journals must never be resumed')
        retain(rows,row)
    return {k:r for k,r in rows.items() if r.get('status')=='complete'}


def append(path,row):
    path.parent.mkdir(parents=True,exist_ok=True)
    # A newline makes a partial final record ignorable without truncating the file.
    with path.open('a') as f:
        f.write('\n\n'+json.dumps(row,allow_nan=False)+'\n')
        f.flush()
        os.fsync(f.fileno())


def visual_report(processor,arrays):
    """Processed frame resolution and merged visual tokens per frame, recorded beside every video score."""
    from pointing_video import processed_hw
    v=getattr(processor,'video_processor',None)
    try:hw=processed_hw(processor,arrays.shape[1],arrays.shape[2],len(arrays)) if v is not None else None
    except ValueError:hw=None
    if hw is None:return dict(processed_height_width=None,visual_tokens_per_frame=None)
    unit=v.patch_size*v.merge_size
    return dict(processed_height_width=list(hw),visual_tokens_per_frame=(hw[0]//unit)*(hw[1]//unit)/v.temporal_patch_size)

async def run(a):
    # Bound PNG reads across workers while requests remain concurrent.
    asyncio.get_running_loop().set_default_executor(ThreadPoolExecutor(max_workers=2))
    from transformers import AutoProcessor
    from vllm import SamplingParams
    from vllm.engine.arg_utils import AsyncEngineArgs
    from vllm.sampling_params import RequestOutputKind
    from vllm.v1.engine.async_llm import AsyncLLM
    cfg=json.loads(Path(a.config).read_text())
    cell=cfg['cells'][a.cell]
    frames=frame_count(cell)
    tasks=[t for s in cfg['datasets'] if s['benchmark'] in cell['benchmarks'] for t in tasks_for(s,cfg['roots'])]
    tasks=sorted(select_tasks(tasks,cell),key=lambda t:(t['benchmark'],t['example_id']))
    if cfg.get('smoke_items'):
        # Retain >=16 tasks so the smoke can satisfy the full parity count.
        tasks=tasks[:cfg['smoke_items']]
    binding=digest({'request':cfg['binding'],'cell':a.cell})
    output=Path(cfg['output'])/str(a.cell)
    output.mkdir(parents=True,exist_ok=True)
    journal=output/('g'+str(a.rank)+'.jsonl')
    done={} if getattr(a, 'budget_only', False) else read_journal(journal,binding,cell['layout'])
    processor=AutoProcessor.from_pretrained(a.model,local_files_only=True)
    processor._student_pilot_student='qwen35'
    engine=AsyncLLM.from_engine_args(AsyncEngineArgs(model=a.model,dtype='bfloat16',
        max_model_len=cfg['max_model_len'],gpu_memory_utilization=0.90,max_num_seqs=cfg['max_seqs'],
        max_num_batched_tokens=8192,tensor_parallel_size=1,
        limit_mm_per_prompt={'video':1,'image':1 if 'pointing' in cell['benchmarks'] else 0},seed=17,enable_prefix_caching=False))
    params=sampling(cell,SamplingParams,RequestOutputKind.FINAL_ONLY)
    image_params=SamplingParams(temperature=0,max_tokens=48,output_kind=RequestOutputKind.FINAL_ONLY)
    point_video_params=SamplingParams(temperature=0,max_tokens=64,output_kind=RequestOutputKind.FINAL_ONLY)
    probe_params=SamplingParams(temperature=0,max_tokens=1,output_kind=RequestOutputKind.FINAL_ONLY)
    semaphore=asyncio.Semaphore(cfg['inflight'])
    checks=[]

    async def generate(task,probe=False,position=0):
        async with semaphore:
            key=task['benchmark']+':'+task['example_id']
            audit={}
            try:
                arrays,audit=await asyncio.to_thread(load,task,cell['layout'],a.cache,a.frames_sha256,
                                                     **({'frames':frames} if frames!=32 else {}),
                                                     **({'frame_set':cell['frame_set']} if 'frame_set' in cell else {}))
                is_image=task['benchmark']=='pointing'
                if is_image:
                    from PIL import Image
                    req=dict(prompt=prompt(processor,task,cell),multi_modal_data={'image':Image.fromarray(arrays[0])})
                else:
                    req=dict(prompt=prompt(processor,task,cell),multi_modal_data={'video':[(arrays,{**audit['metadata'],
                              'do_sample_frames':False})]},mm_processor_kwargs=kwargs(len(arrays)))
                final=None
                started=time.monotonic()
                chosen=point_video_params if task['benchmark']=='pointing_video' else (image_params if is_image else params)
                cap=64 if task['benchmark']=='pointing_video' else (48 if is_image else cell['max_tokens'])
                async for value in engine.generate(req,probe_params if probe else chosen,
                                                   request_id=('p' if probe else 'g')+key):
                    final=value
                if final is None:
                    raise RuntimeError('No terminal generation')
                if probe:
                    check=await asyncio.to_thread(compare,processor,engine,task,arrays,audit['metadata'],
                                                   final.prompt_token_ids,position<2,cell=cell)
                    checks.append(check)
                    return
                c=final.outputs[0]
                ids=list(c.token_ids)
                short=processor.tokenizer.decode(ids[:4096],skip_special_tokens=True)
                record={k:v for k,v in task.items() if k not in ('text','student_input')}
                record.update(key=key,binding=binding,status='complete',raw_generation=c.text,
                    thinking=cell['thinking'],model=cell['model'],decoding=cell['decoding'],
                    token_ids=ids,token_ids_sha256=digest(ids),
                    token_text=processor.tokenizer.decode(ids,skip_special_tokens=False),prompt_text=req['prompt'],
                    prompt_tokens=len(final.prompt_token_ids),finish_reason=c.finish_reason,
                    seconds=time.monotonic()-started,media=audit,frames=frames,layout=cell['layout'],anchor_indices=audit.get('anchor_indices'))
                record.update(score_item(record,c.text,len(ids),cap=cap,finish=c.finish_reason))
                record['at_4096']=dict(raw_generation=short,**score_item(record,short,min(len(ids),4096),
                                         cap=min(cap,4096),finish='length' if len(ids)>=4096 else c.finish_reason))
                if 'frame_set' in cell:
                    record.update(frame_set=cell['frame_set'],anchor_slots=audit.get('anchor_slots'))
                if not is_image:
                    record.update(visual_report(processor,arrays))
                append(journal,record)
            except Exception as exc:
                # Failures gate numbers but never prevent the remaining items from scoring.
                error=dict(thinking=cell['thinking'],model=cell['model'],decoding=cell['decoding'],layout=cell['layout'],key=key,binding=binding,status='error',benchmark=task['benchmark'],
                    example_id=task['example_id'],question_type=task['question_type'],error_type=type(exc).__name__,
                    error=str(exc)[:2000],frames=frames,anchor_indices=audit.get('anchor_indices'))
                if 'frame_set' in cell:
                    error.update(frame_set=cell['frame_set'],anchor_slots=audit.get('anchor_slots'))
                if task['benchmark']=='pointing_video':
                    error.update({k:task[k] for k in ('membership_id','variant','scene','obj','frame','source_index')})
                if probe:
                    checks.append(dict(example_id=task['example_id'],prompt_equal=False,error=error,pixels_required=position<2))
                else:
                    append(journal,error)

    async def run_on():
        # Distributed positions give exactly 16 ID checks and 2 pixel checks per layout.
        first=probe_tasks(cfg,tasks)
        await asyncio.gather(*(generate(t,True,i) for pos,(t,i) in enumerate(first) if pos%a.world==a.rank))
        parity=dict(rank=a.rank,world=a.world,layout=cell['layout'],expected_global=len(first),
                    pixel_expected_global=sum(i<2 for _,i in first),
                    checks=checks,attempt=a.attempt,vllm_version=__import__('vllm').__version__)
        (output/('p'+str(a.rank)+'_'+a.attempt+'.json')).write_text(json.dumps(parity,allow_nan=False)+'\n')
        await asyncio.gather(*(generate(t) for i,t in enumerate(tasks) if i%a.world==a.rank
                              and t['benchmark']+':'+t['example_id'] not in done))

    try:
        if not getattr(a, 'budget_only', False):
            await run_on()
        if cell['thinking']:
            from budget import derive, source_lines
            sources=source_lines(journal, strict=True)
            expected={t['benchmark']+':'+t['example_id'] for i,t in enumerate(tasks) if i%a.world==a.rank}
            if set(sources)!=expected:
                raise ValueError('Budget source shard is incomplete')
            async def request_for(source):
                arrays,audit=await asyncio.to_thread(load,source,cell['layout'],a.cache,a.frames_sha256)
                req=dict(prompt=prompt(processor,source,cell),
                    multi_modal_data={'video':[(arrays,{**audit['metadata'],'do_sample_frames':False})]},
                    mm_processor_kwargs=kwargs(len(arrays)))
                return req,audit
            await derive(sources=sources,cell=cell,source_binding=binding,request_binding=cfg['binding'],
                cell_index=a.cell,budgets=(2048,4096),tokenizer=processor.tokenizer,engine=engine,
                params=SamplingParams(temperature=0,max_tokens=64,output_kind=RequestOutputKind.FINAL_ONLY),
                request_for=request_for,path_for=lambda b:output/f'budget_{b}.g{a.rank}.jsonl',inflight=cfg['inflight'])
    finally:
        engine.shutdown()



if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('config','model','cache','attempt','frames-sha256'):p.add_argument('--'+k,required=True)
    for k in ('cell','rank','world'):p.add_argument('--'+k,required=True,type=int)
    p.add_argument('--budget-only',action='store_true')
    asyncio.run(run(p.parse_args()))
