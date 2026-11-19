"""Execute train.run on CPU; emulate collective sums without opening sockets."""
from contextlib import ExitStack
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import torch
from rl_on_n import train, provenance as P
from rl_on_n.grpo_math import policy_logprobs
from test_kit import ROOT, Tokenizer

class Stub(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.model=torch.nn.Module();self.model.language_model=torch.nn.Module()
        self.model.language_model.mlp=torch.nn.Module()
        self.model.language_model.mlp.up_proj=torch.nn.Linear(4,4)
        self.embedding=torch.nn.Embedding(9,4);self.lm_head=torch.nn.Linear(4,9)
        self.carrier_id=8
    def hidden(self,b):return self.model.language_model.mlp.up_proj(self.embedding(b['input_ids']))

class StepLoop(unittest.TestCase):
    def test_run_with_one_refusing_rank(self):
        from student_pilot.carrier_c1_batch_decode import RowRefusal
        root=Path('out/step_loop');root.mkdir(parents=True,exist_ok=True)
        source=root/'source.json';poolpath=root/'pool.json'
        P.write(source,dict(route_table={'room_size_estimation':'direct'}))
        prompts=[dict(prompt_id=str(i),type='room_size_estimation',gt_answer='1',row={}) for i in range(4)]
        P.write(poolpath,dict(prompts=prompts))
        tok=Tokenizer();tok.convert_tokens_to_ids=lambda t:6 if t=='<tool_response>' else 7
        processor=SimpleNamespace(tokenizer=tok)
        cfg=dict(tree_root=str(ROOT),world_size=4,steps=1,scale_std=False,checkpoint_every=25,
                 source_config=P.pin(source),pool_config=P.pin(source),artifact=P.pin(source),pool=P.pin(poolpath),
                 grounding={},greedy_replay={},cpu_threads=8,seed=17,start_mode='n_export',adapter_rank=2,adapter_alpha=4,
                 grpo={'norm':'seq','temperature':.7},learning_rate=.01,weight_decay=0.,
                 prompts_per_step=4,draws_per_prompt=2,reward={},clip_norm=1.)
        real_device=torch.device;peer_grads=[];summaries=[];original_install=train.install
        for rank in range(4):
            torch.manual_seed(13);model=Stub();draw=[0];reduced=[0];before={}
            def install(*args):
                names=original_install(*args)
                before.update({n:p.detach().clone() for n,p in model.named_parameters() if p.requires_grad})
                return names
            def prompt_batch(*args):
                if rank==1:raise RowRefusal('fixture refusing rank')
                return dict(input_ids=torch.tensor([[1,2]]),attention_mask=torch.ones(1,2,dtype=torch.long))
            def sample(m,p,b,**kwargs):
                token=3+draw[0];draw[0]+=1
                with torch.no_grad():
                    logits=m.lm_head(m.hidden(b)[:,-1])
                    lp=float(policy_logprobs(logits,torch.tensor([token]),torch.tensor([6,7,8]),.7)[0])
                return dict(text='room</think>'+('1' if token==3 else '100'),tokens=[token],kinds=['s'],
                            logp_tempered=[lp],logp_raw=[lp],calls=[],finish='eos')
            def reduce(value):
                if value.ndim==0:value.fill_(6);return
                i=reduced[0];reduced[0]+=1
                if rank==0:peer_grads.append(value.detach().clone())
                if rank==1:self.assertEqual(float(value.abs().sum()),0.)
                value.copy_(peer_grads[i]*3)
            cfg['output']=str(root/f'rank{rank}');config=root/f'config{rank}.json';P.write(config,cfg)
            with ExitStack() as stack:
                stack.enter_context(patch.dict(os.environ,{'WORLD_SIZE':'4','RANK':str(rank),'LOCAL_RANK':str(rank)}))
                for name in ('is_available','set_device','synchronize','reset_peak_memory_stats','max_memory_allocated'):
                    stack.enter_context(patch('torch.cuda.'+name,return_value=True if name=='is_available' else 0))
                stack.enter_context(patch('torch.cuda.is_current_stream_capturing',return_value=False))
                stack.enter_context(patch('torch.device',side_effect=lambda *a,**kw:real_device('cpu')))
                for name in ('init_process_group','destroy_process_group'):stack.enter_context(patch('torch.distributed.'+name))
                stack.enter_context(patch('torch.distributed.all_reduce',side_effect=reduce))
                stack.enter_context(patch('rl_on_n.serving.load_binding'))
                stack.enter_context(patch('rl_on_n.serving.require_replay'))
                stack.enter_context(patch('rl_on_n.serving.build_reader',return_value={}))
                stack.enter_context(patch.object(train,'validate_pool',return_value=P.load(source)))
                stack.enter_context(patch.object(train,'load_export',return_value=(model,processor)))
                stack.enter_context(patch.object(train,'install',side_effect=install))
                stack.enter_context(patch.object(train,'native_kwargs',return_value={}))
                stack.enter_context(patch.object(train,'sample',side_effect=sample))
                stack.enter_context(patch('evalpath.runtime.prompt_batch',side_effect=prompt_batch))
                train.run(config)
            progress=P.load(Path(cfg['output'])/f'PROGRESS_rank{rank}.json')['steps'][0]
            self.assertEqual(progress['refusal_count'],2 if rank==1 else 0)
            self.assertEqual(progress['backward_draws'],0 if rank==1 else 2)
            self.assertEqual(reduced[0],len(before))
            delta=sum(float((p.detach()-before[n]).abs().sum()) for n,p in model.named_parameters() if n in before)
            self.assertGreater(delta,0)
            summaries.append(dict(rank=rank,refusals=progress['refusal_count'],backwards=progress['backward_draws'],update_l1=delta))
        checkpoint=torch.load(root/'rank0/checkpoint_000001.pt',weights_only=True)
        self.assertTrue(checkpoint['optimizer']['state'])
        P.write('out/STEP_LOOP.json',dict(status='PASS',ranks=summaries,steps=1,
                scope='CPU stub model; real train.run, loss, backward, optimizer and checkpoint; mocked CUDA and collectives',
                command='bash scripts/run_tests.sh'))
