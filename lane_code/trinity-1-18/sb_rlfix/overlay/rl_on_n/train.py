"""Training-only DDP runner. This module has no scheduler, SSH, or launch command."""
import argparse
from contextlib import nullcontext
from pathlib import Path
import os
import random
import torch
from . import provenance as P
from .adapters import install,reference,state
from .loss import Objective,attach,logprobs,group_advantages
from .rollout import sample,native_kwargs,tower_batch
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


def run(config_path):
    cfg=P.load(config_path);P.tree(cfg['tree_root'])
    if not torch.cuda.is_available():raise ValueError('Production RL requires assigned CUDA devices; use cpu_proof for synthetic CPU proof')
    world=int(os.environ.get('WORLD_SIZE','1'));rank=int(os.environ.get('RANK','0'));local=int(os.environ.get('LOCAL_RANK','0'))
    if world!=cfg['world_size'] or world not in (4,8):raise ValueError('World size differs from the selected config')
    # Unbound templates fail before allocating a model or opening distributed sockets.
    required=('source_config','pool_config','artifact','pool')
    for key in required:
        if not cfg.get(key):raise ValueError('MISSING config binding: '+key)
        P.checked(cfg[key])
    tower_cfg=cfg.get('frozen_tower') or {}
    for key in ('weights','config'):
        if not tower_cfg.get(key):raise ValueError('MISSING frozen_tower.'+key)
        P.checked(tower_cfg[key])
    torch.set_num_threads(min(cfg['cpu_threads'],16));torch.cuda.set_device(local)
    device=torch.device('cuda',local);torch.manual_seed(cfg['seed'])
    pool=P.load(cfg['pool']['path']);pool_cfg=validate_pool(pool,cfg['pool_config']['path'])
    source=P.load(cfg['source_config']['path'])
    model,processor=load_export(source,cfg['artifact'],device,cfg['start_mode'])
    from student_pilot.tower_read import attach_tower,prepare_tower
    attach_tower(model,dict(weights_path=tower_cfg['weights']['path'],config_path=tower_cfg['config']['path'],
                           device=str(device),dense_frames=tower_cfg['dense_frames'],depth_chunk_size=8,dtype='bf16'))
    selected=install(model,cfg['adapter_rank'],cfg['adapter_alpha'])
    model.eval();objective=Objective(model,cfg['grpo'])
    torch.distributed.init_process_group('nccl')
    from torch.nn.parallel import DistributedDataParallel as DDP
    ddp=DDP(objective,device_ids=[local],broadcast_buffers=False)
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
    logs=[]
    for step in range(cfg['steps']):
        if cursor+cfg['prompts_per_step']>len(order):rng.shuffle(order);cursor=0
        selected_prompts=order[cursor:cursor+cfg['prompts_per_step']];cursor+=cfg['prompts_per_step']
        mine=selected_prompts[rank*per_rank:(rank+1)*per_rank]
        optimizer.zero_grad(set_to_none=True);micro=0;step_rewards=[]
        for index in mine:
            prompt=prompts[index]
            native_batch=prompt_batch(processor,prompt['row'],source,'routed')
            batch={k:v.to(device) if isinstance(v,torch.Tensor) else v for k,v in native_batch.items()}
            batch=tower_batch(prompt['row'],batch)
            tower=prepare_tower(model,batch)
            records=[];rewards=[]
            for draw in range(draws):
                audit=output/f'audit/r{rank}/s{step}/p{index}/d{draw}'
                kwargs=native_kwargs(model,prompt,batch,cfg['artifact'],audit,cfg['grounding'])
                kwargs.update(tower_state=tower,max_new_tokens=16384)
                record=sample(model,processor,batch,seed=cfg['seed']+step*cfg['prompts_per_step']*draws+index*draws+draw,
                              max_tokens=cfg['max_sampled_tokens'],temperature=cfg['grpo']['temperature'],decode=kwargs)
                if record.get('tower_error'):raise RuntimeError('Tower failed: '+record['tower_error'])
                records.append(record);rewards.append(score(prompt,record,processor.tokenizer,pool_cfg['route_table'],weights))
            advantages=group_advantages([r['total'] for r in rewards]).to(device,dtype=torch.float32)
            step_rewards.extend(r['total'] for r in rewards)
            for record,adv in zip(records,advantages):
                b=attach(batch,record,reserved)
                with reference(model): ref=logprobs(model,b,cfg['grpo']['temperature'])
                micro+=1
                with ddp.no_sync() if micro<total else nullcontext():
                    loss,metrics=ddp(b,adv,ref)
                    (loss/total).backward()
        norm=torch.nn.utils.clip_grad_norm_(trainable,cfg['clip_norm'])
        if not torch.isfinite(norm):raise ValueError('Nonfinite RL gradient')
        optimizer.step()
        logs.append(dict(step=step+1,mean_reward=sum(step_rewards)/len(step_rewards),grad_norm=float(norm),**metrics))
        if rank==0:P.write(output/'PROGRESS.json',dict(schema='rl-on-n-progress-v1',steps=logs))
    if rank==0:
        torch.save(dict(adapters=state(model),optimizer=optimizer.state_dict(),step=cfg['steps']),output/'rl_adapters.pt')
        P.write(output/'RL_EXPORT.json',dict(schema='rl-on-n-adapter-export-v1',base_export=cfg['artifact'],
            source_config=cfg['source_config'],start_mode=cfg['start_mode'],init_seed=cfg['seed'],pool=cfg['pool'],adapter_rank=cfg['adapter_rank'],adapter_alpha=cfg['adapter_alpha'],
            adapter_modules=selected,weights=P.pin(output/'rl_adapters.pt'),steps=cfg['steps'],
            format_note='Adapter continuation on an immutable C1 export; not a native N/P SFT export.'))
    torch.distributed.destroy_process_group()

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);run(ap.parse_args().config)
