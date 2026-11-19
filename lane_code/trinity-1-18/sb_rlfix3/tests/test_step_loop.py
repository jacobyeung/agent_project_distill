"""Execute train.run on CPU; emulate collective sums without opening sockets."""
from contextlib import ExitStack
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import torch
from rl_on_n import train, provenance as P
from rl_on_n.grpo_math import policy_logprobs
from test_kit import ROOT, Tokenizer

PROMPT_CONFIG={'fixture':'info config from the A4 loader'}


class Stub(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.model=torch.nn.Module();self.model.language_model=torch.nn.Module()
        self.model.language_model.mlp=torch.nn.Module()
        self.model.language_model.mlp.up_proj=torch.nn.Linear(4,4)
        self.embedding=torch.nn.Embedding(9,4);self.lm_head=torch.nn.Linear(4,9)
        self.carrier_id=8
    def hidden(self,b):return self.model.language_model.mlp.up_proj(self.embedding(b['input_ids']))


def fixture(root,**changes):
    root.mkdir(parents=True,exist_ok=True)
    source=root/'source.json';poolpath=root/'pool.json';restore=root/'export/RESTORE.json'
    restore.parent.mkdir(exist_ok=True)
    P.write(source,dict(route_table={'room_size_estimation':'direct'}))
    prompts=[dict(prompt_id=str(i),type='room_size_estimation',gt_answer='1',row=dict(index=i)) for i in range(4)]
    P.write(poolpath,dict(prompts=prompts));P.write(restore,dict(fixture='export restore'))
    cfg=dict(tree_root=str(ROOT),world_size=4,steps=1,scale_std=False,checkpoint_every=25,
             export_restore=P.pin(restore),export_config=P.pin(source),pool_config=P.pin(source),pool=P.pin(poolpath),
             grounding={},greedy_replay={},cpu_threads=8,seed=17,adapter_rank=2,adapter_alpha=4,
             grpo={'norm':'seq','temperature':.7},learning_rate=.01,weight_decay=0.,
             prompts_per_step=4,draws_per_prompt=2,reward={},clip_norm=1.)
    cfg.update(changes);return cfg


def prompt_inputs(processor,row,config,device):
    if config is not PROMPT_CONFIG:raise AssertionError('prompt built from a config other than the loader info')
    return dict(input_ids=torch.tensor([[1,2+row['index']]]),attention_mask=torch.ones(1,2,dtype=torch.long))


def sample(m,p,b,*,seed,**kwargs):
    # Rewards depend on the prompt and draw, so prompt order changes the update.
    token=3 if (int(b['input_ids'][0,1])+seed)%2 else 4
    with torch.no_grad():
        logits=m.lm_head(m.hidden(b)[:,-1])
        lp=float(policy_logprobs(logits,torch.tensor([token]),torch.tensor([6,7,8]),.7)[0])
    return dict(text='room</think>'+('1' if token==3 else '100'),tokens=[token],kinds=['s'],
                logp_tempered=[lp],logp_raw=[lp],calls=[],finish='eos')


def emulate(cfg,config,rank,reduce,*,inputs=prompt_inputs,resume=None,replay=True):
    """Run one emulated rank of train.run; returns the model, adapters before training and spies."""
    torch.manual_seed(13);model=Stub();before={};advantages=[];original_install=train.install
    original_advantages=train.group_advantages
    tok=Tokenizer();tok.convert_tokens_to_ids=lambda t:6 if t=='<tool_response>' else 7
    processor=SimpleNamespace(tokenizer=tok);real_device=torch.device
    def install(*args):
        names=original_install(*args)
        before.update({n:p.detach().clone() for n,p in model.named_parameters() if p.requires_grad})
        return names
    def spy(rewards,**kwargs):
        value=original_advantages(rewards,**kwargs);advantages.append((list(rewards),value.clone()));return value
    P.write(config,cfg)
    with ExitStack() as stack:
        enter=stack.enter_context
        world=str(cfg['world_size'])
        enter(patch.dict(os.environ,{'WORLD_SIZE':world,'RANK':str(rank),'LOCAL_RANK':str(rank)}))
        for name in ('is_available','set_device','synchronize','reset_peak_memory_stats','max_memory_allocated'):
            enter(patch('torch.cuda.'+name,return_value=True if name=='is_available' else 0))
        enter(patch('torch.cuda.is_current_stream_capturing',return_value=False))
        enter(patch('torch.device',side_effect=lambda *a,**kw:real_device('cpu')))
        for name in ('init_process_group','destroy_process_group'):enter(patch('torch.distributed.'+name))
        enter(patch('torch.distributed.all_reduce',side_effect=reduce))
        enter(patch('rl_on_n.serving.load_binding'))
        if replay:enter(patch('rl_on_n.serving.require_replay'))
        enter(patch('rl_on_n.serving.build_reader',return_value={}))
        enter(patch.object(train,'validate_pool',return_value=P.load(cfg['pool_config']['path'])))
        load=enter(patch.object(train,'load_export',return_value=(model,processor,dict(config=PROMPT_CONFIG))))
        enter(patch.object(train,'install',side_effect=install))
        enter(patch.object(train,'native_kwargs',return_value={}))
        enter(patch.object(train,'sample',side_effect=sample))
        enter(patch.object(train,'prompt_inputs',side_effect=inputs))
        enter(patch.object(train,'group_advantages',side_effect=spy))
        spies=SimpleNamespace(model=model,before=before,advantages=advantages,load=load)
        try:train.run(config,resume)
        except Exception as exc:
            exc.spies=spies;raise
    return spies


def adapter_delta(spies):
    return sum(float((p.detach()-spies.before[n]).abs().sum()) for n,p in spies.model.named_parameters() if n in spies.before)


class StepLoop(unittest.TestCase):
    def test_run_with_one_refusing_rank(self):
        root=Path('out/step_loop');cfg=fixture(root);peer_grads=[];summaries=[]
        for rank in range(4):
            reduced=[0]
            def inputs(processor,row,config,device):
                if rank==1:raise train.PromptRefusal('TowerError: fixture refusing rank')
                return prompt_inputs(processor,row,config,device)
            def reduce(value):
                if not value.is_floating_point():value.copy_(torch.tensor([6,2]));return
                i=reduced[0];reduced[0]+=1
                if rank==0:peer_grads.append(value.detach().clone())
                if rank==1:self.assertEqual(float(value.abs().sum()),0.)
                value.copy_(peer_grads[i]*3)
            cfg['output']=str(root/f'rank{rank}')
            spies=emulate(cfg,root/f'config{rank}.json',rank,reduce,inputs=inputs)
            progress=P.load(Path(cfg['output'])/f'PROGRESS_rank{rank}.json')['steps'][0]
            self.assertEqual(progress['refusal_count'],2 if rank==1 else 0)
            self.assertEqual(progress['backward_draws'],0 if rank==1 else 2)
            self.assertEqual((progress['step_refusals'],progress['step_draws']),(2,8))
            self.assertEqual(reduced[0],len(spies.before))
            # The loader's info['config'] reaches every prompt; load_export receives the pinned bindings.
            spies.load.assert_called_once_with(cfg['export_restore'],cfg['export_config'],torch.device('cpu'),{})
            self.assertEqual(len(spies.advantages),1)
            for rewards,value in spies.advantages:
                centred=torch.tensor(rewards,dtype=torch.float64)-sum(rewards)/len(rewards)
                self.assertTrue(torch.allclose(value.double(),centred))
                if rank!=1:self.assertGreater(float(value.abs().sum()),0)
            delta=adapter_delta(spies);self.assertGreater(delta,0)
            summaries.append(dict(rank=rank,refusals=progress['refusal_count'],backwards=progress['backward_draws'],update_l1=delta))
        checkpoint=torch.load(root/'rank0/checkpoint_000001.pt',weights_only=True)
        self.assertTrue(checkpoint['optimizer']['state'])
        self.assertEqual(set(checkpoint)-{'adapters','optimizer'},{'step','cursor','order','rng','config_identity'})
        P.write('out/STEP_LOOP.json',dict(status='PASS',ranks=summaries,steps=1,
                scope='CPU stub model; real train.run, loss, backward, optimizer and checkpoint; mocked CUDA and collectives',
                command='bash scripts/run_tests.sh'))

    def test_refusals_above_limit_stop_every_rank(self):
        root=Path('out/step_loop_limit');shutil.rmtree(root,ignore_errors=True);cfg=fixture(root)
        for rank in range(4):
            grads=[0]
            def reduce(value):
                if not value.is_floating_point():value.copy_(torch.tensor([5,3]));return
                grads[0]+=1
            cfg['output']=str(root/f'rank{rank}')
            with self.assertRaisesRegex(ValueError,r'Refusals 3/8 exceed 25% of step 1; every rank stops') as caught:
                emulate(cfg,root/f'config{rank}.json',rank,reduce)
            self.assertEqual(grads[0],0)
            self.assertEqual(adapter_delta(caught.exception.spies),0.)
            self.assertFalse(list(Path(cfg['output']).glob('checkpoint_*')))
            progress=P.load(Path(cfg['output'])/f'PROGRESS_rank{rank}.json')['steps']
            self.assertEqual((len(progress),progress[0]['stopped'],progress[0]['step_refusals']),(1,'refusal_limit',3))

    def test_unbound_replay_refuses_before_loading(self):
        root=Path('out/step_loop_replay');shutil.rmtree(root,ignore_errors=True)
        cfg=fixture(root,output=str(root/'rank0'),greedy_replay=None)
        with self.assertRaisesRegex(ValueError,'MISSING greedy_replay') as caught:
            emulate(cfg,root/'config.json',0,lambda value:None,replay=False)
        caught.exception.spies.load.assert_not_called()
        self.assertFalse(Path(cfg['output']).exists())

    def test_resume_equals_uninterrupted(self):
        root=Path('out/step_loop_resume');shutil.rmtree(root,ignore_errors=True)
        reduce=lambda value:value.mul_(4)
        straight=fixture(root/'straight',steps=2,output=str(root/'straight/out'))
        whole=emulate(straight,root/'straight.json',0,reduce)
        first=fixture(root/'resumed',steps=1,output=str(root/'resumed/out'))
        emulate(first,root/'first.json',0,reduce)
        second=dict(first,steps=2)
        checkpoint=Path(second['output'])/'checkpoint_000001.json'
        resumed=emulate(second,root/'second.json',0,reduce,resume=str(checkpoint))
        a=torch.load(root/'straight/out/checkpoint_000002.pt',weights_only=True)
        b=torch.load(root/'resumed/out/checkpoint_000002.pt',weights_only=True)
        for name in a['adapters']:self.assertTrue(torch.equal(a['adapters'][name],b['adapters'][name]),name)
        for key in ('step','cursor','order','rng'):self.assertEqual(a[key],b[key],key)
        for index,state in a['optimizer']['state'].items():
            for key,value in state.items():self.assertTrue(torch.equal(value,b['optimizer']['state'][index][key]),key)
        for name,p in whole.model.named_parameters():self.assertTrue(torch.equal(p,dict(resumed.model.named_parameters())[name]))
        logs=P.load(Path(second['output'])/'PROGRESS_rank0.json')['steps']
        straight_logs=P.load(Path(straight['output'])/'PROGRESS_rank0.json')['steps']
        self.assertEqual([s['step'] for s in logs],[1,2])
        for x,y in zip(logs,straight_logs):self.assertEqual(x['mean_reward'],y['mean_reward'])
        # The shuffle at step 2 used the restored generator; the order differs from the initial one.
        self.assertNotEqual(a['order'],torch.load(Path(first['output'])/'checkpoint_000001.pt',weights_only=True)['order'])
        foreign=dict(second,seed=18)
        with self.assertRaisesRegex(ValueError,'different training config'):
            emulate(foreign,root/'foreign.json',0,reduce,resume=str(checkpoint))
        done=Path(second['output'])/'checkpoint_000002.json'
        with self.assertRaisesRegex(ValueError,'already reached'):emulate(second,root/'second.json',0,reduce,resume=str(done))
        tampered=root/'tampered';shutil.copytree(second['output'],tampered)
        meta=P.load(tampered/'checkpoint_000001.json');meta['weights']['path']=str((tampered/'checkpoint_000001.pt').resolve())
        P.write(tampered/'checkpoint_000001.json',meta)
        data=bytearray((tampered/'checkpoint_000001.pt').read_bytes());data[-40]^=1
        (tampered/'checkpoint_000001.pt').write_bytes(bytes(data))
        with self.assertRaisesRegex(ValueError,'MISSING or changed pinned input'):
            emulate(dict(second,output=str(tampered)),root/'tampered.json',0,reduce,resume=str(tampered/'checkpoint_000001.json'))
        P.INPUTS.pop(str((tampered/'checkpoint_000001.pt').resolve()),None)
        legacy=dict(meta,schema='rl-on-n-checkpoint-v1');P.write(tampered/'legacy.json',legacy)
        with self.assertRaisesRegex(ValueError,'lacks resumable data state'):
            emulate(dict(second,output=str(tampered)),root/'tampered.json',0,reduce,resume=str(tampered/'legacy.json'))
