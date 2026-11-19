"""Training-only runner with explicit gradient collectives. This module has no scheduler, SSH, or launch command."""
import argparse
import hashlib
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

REFUSAL_LIMIT=.25


class PromptRefusal(ValueError):
    """The sealed prompt builder refused a row; the draw scores zero."""


def load_export(restore_pin,config_pin,device,grounding=None):
    """Load the policy with A4's deployed loader; the greedy replay certifies this function."""
    from .serving import load_binding,reader_runtime,PAYLOAD
    settings=load_binding(grounding)
    restore=P.checked(restore_pin);config=P.checked(config_pin)
    with reader_runtime():
        from e2e_reader.parity import load_native
        model,processor,info=load_native(str(restore.parent),device=str(device),
            settings=dict(settings,tree=str(PAYLOAD/'tree'),config=str(config),export_dir=str(restore.parent)))
    if info['config'].get('tool_mode_flag'):raise ValueError('Deployed prompts require the unflagged config')
    return model,processor,info


def prompt_inputs(processor,row,config,device):
    """The routed prompt A4's make_real builds: its prompt_batch under the sealed tree.

    A4's tree types only TowerError as a row refusal; its other ValueErrors raise.
    """
    from .serving import reader_runtime
    with reader_runtime():
        from evalpath.runtime import prompt_batch
        from student_pilot.tower_errors import TowerError
        try:batch=prompt_batch(processor,row,config,'routed')
        except TowerError as exc:raise PromptRefusal(type(exc).__name__+': '+str(exc)) from exc
    return {k:v.to(device) if isinstance(v,torch.Tensor) else v for k,v in batch.items()}


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


def config_identity(cfg):
    # A resumed run may extend steps or move its output; everything else must match.
    value={k:v for k,v in cfg.items() if k not in ('input_sha256','steps','output')}
    return hashlib.sha256(P.canonical(value).encode()).hexdigest()


def save_checkpoint(model,optimizer,output,step,data=None):
    data=dict(data or {})
    target=Path(output)/f'checkpoint_{step:06d}.pt'
    temporary=target.with_suffix('.pt.pending')
    torch.save(dict(adapters=state(model),optimizer=optimizer.state_dict(),step=step,**data),temporary)
    temporary.replace(target)
    P.write(target.with_suffix('.json'),dict(schema='rl-on-n-checkpoint-v2',step=step,weights=P.pin(target),
                                             config_identity=data.get('config_identity')))


def resume_state(path,model,optimizer,identity):
    meta=P.load(path)
    if meta.get('schema')!='rl-on-n-checkpoint-v2':raise ValueError('Checkpoint lacks resumable data state: '+str(path))
    if meta.get('config_identity')!=identity:raise ValueError('Checkpoint belongs to a different training config')
    saved=torch.load(P.checked(meta['weights']),map_location='cpu',weights_only=True)
    if saved['step']!=meta['step'] or saved.get('config_identity')!=identity:
        raise ValueError('Checkpoint contents differ from its JSON pin')
    live={n:p for n,p in model.named_parameters() if p.requires_grad}
    if set(live)!=set(saved['adapters']):raise ValueError('Adapter parameter set differs')
    with torch.no_grad():
        for name,p in live.items():
            if p.shape!=saved['adapters'][name].shape:raise ValueError('Adapter shape differs: '+name)
            p.copy_(saved['adapters'][name])
    optimizer.load_state_dict(saved['optimizer'])
    version,internal,gauss=saved['rng'];rng=random.Random();rng.setstate((version,tuple(internal),gauss))
    return saved['step'],saved['cursor'],list(saved['order']),rng


def run(config_path,resume=None):
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
    required=('export_restore','export_config','pool_config','pool')
    for key in required:
        if not cfg.get(key):raise ValueError('MISSING config binding: '+key)
        P.checked(cfg[key])
    export_dir=Path(cfg['export_restore']['path']).parent
    from .serving import load_binding,build_reader,require_replay
    load_binding(cfg.get('grounding'))
    require_replay(cfg.get('greedy_replay'),cfg['tree_root'],export_dir)
    torch.set_num_threads(min(cfg['cpu_threads'],8));torch.cuda.set_device(local)
    device=torch.device('cuda',local);torch.manual_seed(cfg['seed'])
    pool=P.load(cfg['pool']['path']);pool_cfg=validate_pool(pool,cfg['pool_config']['path'])
    model,processor,info=load_export(cfg['export_restore'],cfg['export_config'],device,cfg.get('grounding'))
    prompt_config=info['config']
    selected=install(model,cfg['adapter_rank'],cfg['adapter_alpha'])
    reader=build_reader(model,processor,cfg['grounding'],device)
    model.eval();objective=Objective(model,cfg['grpo'])
    if world>1:torch.distributed.init_process_group('nccl')
    trainable=[p for p in model.parameters() if p.requires_grad]
    optimizer=torch.optim.AdamW(trainable,lr=cfg['learning_rate'],weight_decay=cfg['weight_decay'])
    output=Path(cfg['output']);output.mkdir(parents=True,exist_ok=True)
    prompts=pool['prompts'];per_rank=cfg['prompts_per_step']//world;draws=cfg['draws_per_prompt']
    if not per_rank or cfg['prompts_per_step']%world or len(prompts)<cfg['prompts_per_step']:
        raise ValueError('Insufficient admitted prompts or unequal rank layout')
    reserved=[processor.tokenizer.convert_tokens_to_ids(x) for x in ('<tool_response>','</tool_response>')]+[model.carrier_id]
    order=list(range(len(prompts)));rng=random.Random(cfg['seed']);rng.shuffle(order);cursor=0
    weights=Weights(**cfg['reward']);total=per_rank*draws;step_draws=cfg['prompts_per_step']*draws
    identity=config_identity(cfg);start=0;logs=[]
    progress=output/f'PROGRESS_rank{rank}.json'
    if resume:
        start,cursor,order,rng=resume_state(resume,model,optimizer,identity)
        if start>=cfg['steps']:raise ValueError('Checkpoint already reached the configured steps')
        if progress.is_file():logs=[s for s in P.load(progress)['steps'] if s['step']<=start]
    from student_pilot.tower_errors import TowerError
    from student_pilot.carrier_c1_batch_decode import RowRefusal
    for step in range(start,cfg['steps']):
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
                batch=prompt_inputs(processor,prompt['row'],prompt_config,device)
            except PromptRefusal as exc:
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
        counts=torch.tensor([backwards,len(failures)],device=device)
        if world>1:torch.distributed.all_reduce(counts)
        refusals=int(counts[1])
        logs.append(dict(step=step+1,rank=rank,mean_reward=sum(step_rewards)/len(step_rewards),
            backward_draws=backwards,refusal_count=len(failures),refusals=failures,
            step_refusals=refusals,step_draws=step_draws,metrics=metrics))
        # Every rank sees the same reduced count, so all ranks stop together.
        if refusals>REFUSAL_LIMIT*step_draws:
            logs[-1].update(stopped='refusal_limit',seconds=time.monotonic()-started)
            P.write(progress,dict(schema='rl-on-n-progress-v3',steps=logs))
            raise ValueError(f'Refusals {refusals}/{step_draws} exceed {REFUSAL_LIMIT:.0%} of step {step+1}; every rank stops')
        average_gradients(trainable,world)
        norm=torch.nn.utils.clip_grad_norm_(trainable,cfg['clip_norm'])
        if not torch.isfinite(norm):raise ValueError('Nonfinite RL gradient')
        if counts[0].item():optimizer.step()
        torch.cuda.synchronize()
        logs[-1].update(grad_norm=float(norm),seconds=time.monotonic()-started,
                        peak_cuda_bytes=torch.cuda.max_memory_allocated())
        P.write(progress,dict(schema='rl-on-n-progress-v3',steps=logs))
        if rank==0 and checkpoint_due(step+1,cfg['steps']):
            save_checkpoint(model,optimizer,output,step+1,dict(cursor=cursor,order=order,rng=rng.getstate(),
                                                               config_identity=identity))
    if rank==0:
        P.write(output/'RL_EXPORT.json',dict(schema='rl-on-n-adapter-export-v2',export_restore=cfg['export_restore'],
            export_config=cfg['export_config'],grounding=cfg['grounding'],init_seed=cfg['seed'],pool=cfg['pool'],
            adapter_rank=cfg['adapter_rank'],adapter_alpha=cfg['adapter_alpha'],
            adapter_modules=selected,weights=P.pin(output/f'checkpoint_{cfg["steps"]:06d}.pt'),steps=cfg['steps'],
            format_note='Adapter continuation on an immutable export read by A4\'s loader; not a native N/P SFT export.'))
    if world>1:torch.distributed.destroy_process_group()

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True)
    ap.add_argument('--resume',help='checkpoint_NNNNNN.json written by a run of this config')
    a=ap.parse_args();run(a.config,a.resume)
