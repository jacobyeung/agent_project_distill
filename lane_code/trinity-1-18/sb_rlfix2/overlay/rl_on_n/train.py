"""Training-only runner with explicit gradient collectives. This module has no scheduler, SSH, or launch command."""
import argparse
from pathlib import Path
import os
import random
import time
import torch
from . import provenance as P
from .adapters import install,reference,state
from .loss import Objective,attach,logprobs,group_advantages
from .rollout import sample,native_kwargs,refused
from .reward import score,Weights


def load_export(source_cfg,artifact_pin,device,mode="n_export"):
    from student_pilot import carrier_c1_run as native
    from student_pilot.r1_training import training_components
    from student_pilot.source_seal import check_export
    from student_pilot.trace_version import resolve
    from evalpath.runtime import check_init_spec
    # This is a training entrypoint: do not call N's refused legacy benchmark loader.
    training_components(source_cfg['r1_training']['registry'],source_cfg)
    receipt,manifest=native.prepared(source_cfg,admission=True)
    artifact=P.load(P.checked(artifact_pin))
    processor=native.processor_for_receipt(manifest,receipt)
    if mode=='n_export':
        check_export(receipt,artifact);resolve(artifact,receipt)
        check_init_spec(receipt,artifact_pin)
        if artifact['base_identity']!=source_cfg['base_identity'] or artifact['config_sha256']!=native.identity(source_cfg):
            raise ValueError('Starting export must match its own authenticated donor configuration')
        loading={k:v for k,v in receipt.items() if k!='init_artifact'}
        model=native.load_model(manifest,loading,processor,evaluation=True)
        model.readout_evaluation_config=source_cfg
        native.load_artifact(model,artifact_pin,evaluation_config=source_cfg)
    elif mode=='p_handover':
        # Use N's complete P continuation contract, never silently reinterpret a P export.
        if source_cfg.get('init_artifact',{}).get('artifact')!=artifact_pin:
            raise ValueError('P export differs from the admitted N continuation binding')
        from student_pilot.r1_handover import donor
        donor(source_cfg,artifact)
        model=native.load_model(manifest,receipt,processor,evaluation=False)
        if not getattr(model,'init_report',None):raise ValueError('Native P initialization did not produce a receipt')
    else:raise ValueError('Unknown start_mode')
    model.model.to(dtype=torch.bfloat16);model.lm_head.to(dtype=torch.bfloat16)
    return model.to(device).eval(),processor


def validate_pool(pool,pool_cfg):
    if pool.get('schema')!='rl-on-n-pool-v1' or pool.get('status')!='ADMITTED':
        raise ValueError('MISSING admitted RL prompt pool')
    if not pool.get('input_sha256'):raise ValueError('Pool lacks input hashes')
    # Verify the actual source configuration and all recorded dependencies, not a caller label.
    for path,sha in pool['input_sha256'].items(): P.checked(dict(path=path,sha256=sha))
    if pool['source_config']['sha256']!=P.sha(pool_cfg):raise ValueError('Pool config differs')
    cfg=P.load(pool_cfg)
    from .pool import from_prepared
    rebuilt=from_prepared(cfg,seed=pool['seed'])
    # A limit can only select a deterministic prefix of this admitted population.
    if rebuilt[:len(pool['prompts'])]!=pool['prompts']:raise ValueError('Pool rows differ from native admitted population')
    return cfg


def zero_gradients(parameters):
    # Every rank participates even when every local draw was refused.
    for p in parameters:p.grad=torch.zeros_like(p)


def average_gradients(parameters,world):
    if world>1:
        for p in parameters:
            if p.grad is None:p.grad=torch.zeros_like(p)
            torch.distributed.all_reduce(p.grad)
            p.grad.div_(world)


def backward_draw(model,objective,batch,record,adv,reserved,temperature,total):
    if record.get('refusal') or record.get('tower_error') or 's' not in record.get('kinds',[]):
        return None
    b=attach(batch,record,reserved)
    with reference(model):ref=logprobs(model,b,temperature)
    loss,metrics=objective(b,adv,ref)
    (loss/total).backward()
    return metrics


def checkpoint_due(step,final):
    return step%25==0 or step==final


def save_checkpoint(model,optimizer,output,step):
    target=Path(output)/f'checkpoint_{step:06d}.pt'
    temporary=target.with_suffix('.pt.pending')
    torch.save(dict(adapters=state(model),optimizer=optimizer.state_dict(),step=step),temporary)
    temporary.replace(target)
    P.write(target.with_suffix('.json'),dict(schema='rl-on-n-checkpoint-v1',step=step,weights=P.pin(target)))


def run(config_path):
    cfg=P.load(config_path);P.tree(cfg['tree_root'])
    if not torch.cuda.is_available():raise ValueError('Production RL requires assigned CUDA devices; use cpu_proof for synthetic CPU proof')
    world=int(os.environ.get('WORLD_SIZE','1'));rank=int(os.environ.get('RANK','0'));local=int(os.environ.get('LOCAL_RANK','0'))
    if world!=cfg['world_size'] or world not in (1,4,8):raise ValueError('World size differs from the selected config')
    if world==1 and (not cfg.get('dry_run') or cfg['steps']!=2):
        raise ValueError('One GPU is reserved for the timed two-step dry run')
    if cfg.get('scale_std',False) is not False:
        raise ValueError('Training requires unscaled centered advantages')
    if cfg.get('checkpoint_every',25)!=25:
        raise ValueError('Checkpoint interval must be 25 steps')
    # Unbound templates fail before allocating a model or opening distributed sockets.
    required=('source_config','pool_config','artifact','pool')
    for key in required:
        if not cfg.get(key):raise ValueError('MISSING config binding: '+key)
        P.checked(cfg[key])
    from .serving import load_binding,build_reader,require_replay
    load_binding(cfg.get('grounding'))
    require_replay(cfg.get('greedy_replay'),cfg['tree_root'])
    torch.set_num_threads(min(cfg['cpu_threads'],8));torch.cuda.set_device(local)
    device=torch.device('cuda',local);torch.manual_seed(cfg['seed'])
    pool=P.load(cfg['pool']['path']);pool_cfg=validate_pool(pool,cfg['pool_config']['path'])
    source=P.load(cfg['source_config']['path'])
    model,processor=load_export(source,cfg['artifact'],device,cfg['start_mode'])
    selected=install(model,cfg['adapter_rank'],cfg['adapter_alpha'])
    reader=build_reader(model,processor,cfg['grounding'],device)
    model.eval();objective=Objective(model,cfg['grpo'])
    if world>1:torch.distributed.init_process_group('nccl')
    trainable=[p for p in model.parameters() if p.requires_grad]
    optimizer=torch.optim.AdamW(trainable,lr=cfg['learning_rate'],weight_decay=cfg['weight_decay'])
    output=Path(cfg['output']);output.mkdir(parents=True,exist_ok=True)
    from evalpath.runtime import prompt_batch
    prompts=pool['prompts'];per_rank=cfg['prompts_per_step']//world;draws=cfg['draws_per_prompt']
    if not per_rank or cfg['prompts_per_step']%world or len(prompts)<cfg['prompts_per_step']:
        raise ValueError('Insufficient admitted prompts or unequal rank layout')
    reserved=[processor.tokenizer.convert_tokens_to_ids(x) for x in ('<tool_response>','</tool_response>')]+[model.carrier_id]
    order=list(range(len(prompts)));rng=random.Random(cfg['seed']);rng.shuffle(order);cursor=0
    weights=Weights(**cfg['reward']);total=per_rank*draws
    from student_pilot.tower_errors import TowerError
    from student_pilot.carrier_c1_batch_decode import RowRefusal
    logs=[]
    for step in range(cfg['steps']):
        torch.cuda.synchronize();started=time.monotonic()
        torch.cuda.reset_peak_memory_stats()
        if cursor+cfg['prompts_per_step']>len(order):rng.shuffle(order);cursor=0
        selected_prompts=order[cursor:cursor+cfg['prompts_per_step']];cursor+=cfg['prompts_per_step']
        mine=selected_prompts[rank*per_rank:(rank+1)*per_rank]
        zero_gradients(trainable);step_rewards=[];failures=[];metrics=[];backwards=0
        for index in mine:
            prompt=prompts[index]
            prep_error=None
            try:
                native_batch=prompt_batch(processor,prompt['row'],source,'routed')
                batch={k:v.to(device) if isinstance(v,torch.Tensor) else v for k,v in native_batch.items()}
            except (RowRefusal,TowerError) as exc:
                prep_error=exc
            records=[];rewards=[]
            for draw in range(draws):
                if prep_error is not None:
                    record=refused(prep_error)
                else:
                    try:
                        kwargs=native_kwargs(processor,prompt,batch,reader)
                        record=sample(model,processor,batch,seed=cfg['seed']+step*cfg['prompts_per_step']*draws+index*draws+draw,
                                      temperature=cfg['grpo']['temperature'],decode=kwargs)
                    except (RowRefusal,TowerError) as exc:
                        record=refused(exc)
                if record.get('refusal') or record.get('tower_error'):
                    failures.append(dict(prompt_id=prompt['prompt_id'],draw=draw,
                                         reason=record.get('refusal') or record['tower_error']))
                records.append(record);rewards.append(score(prompt,record,processor.tokenizer,pool_cfg['route_table'],weights))
            advantages=group_advantages([r['total'] for r in rewards],scale_std=False).to(device,dtype=torch.float32)
            step_rewards.extend(r['total'] for r in rewards)
            for record,adv in zip(records,advantages):
                metric=backward_draw(model,objective,batch if prep_error is None else None,
                                     record,adv,reserved,cfg['grpo']['temperature'],total)
                if metric is not None:metrics.append(metric);backwards+=1
        average_gradients(trainable,world)
        count=torch.tensor(backwards,device=device)
        if world>1:torch.distributed.all_reduce(count)
        norm=torch.nn.utils.clip_grad_norm_(trainable,cfg['clip_norm'])
        if not torch.isfinite(norm):raise ValueError('Nonfinite RL gradient')
        if count.item():optimizer.step()
        torch.cuda.synchronize()
        logs.append(dict(step=step+1,rank=rank,mean_reward=sum(step_rewards)/len(step_rewards),
            grad_norm=float(norm),backward_draws=backwards,refusal_count=len(failures),refusals=failures,
            seconds=time.monotonic()-started,peak_cuda_bytes=torch.cuda.max_memory_allocated(),
            metrics=metrics))
        P.write(output/f'PROGRESS_rank{rank}.json',dict(schema='rl-on-n-progress-v2',steps=logs))
        if rank==0 and checkpoint_due(step+1,cfg['steps']):
            save_checkpoint(model,optimizer,output,step+1)
    if rank==0:
        P.write(output/'RL_EXPORT.json',dict(schema='rl-on-n-adapter-export-v1',base_export=cfg['artifact'],
            source_config=cfg['source_config'],start_mode=cfg['start_mode'],init_seed=cfg['seed'],pool=cfg['pool'],adapter_rank=cfg['adapter_rank'],adapter_alpha=cfg['adapter_alpha'],
            adapter_modules=selected,weights=P.pin(output/f'checkpoint_{cfg["steps"]:06d}.pt'),steps=cfg['steps'],
            format_note='Adapter continuation on an immutable C1 export; not a native N/P SFT export.'))
    if world>1:torch.distributed.destroy_process_group()

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);run(ap.parse_args().config)
