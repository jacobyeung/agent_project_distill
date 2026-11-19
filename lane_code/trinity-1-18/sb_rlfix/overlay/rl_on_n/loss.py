"""Exact-token sequence GRPO; injected responses and forced tokens have no loss."""
import torch
from .grpo_math import group_advantages, policy_logprobs, token_terms, settings

def attach(prompt_batch, record, reserved):
    ids=prompt_batch['input_ids']; gen=ids.new_tensor([record['tokens']])
    out={k:v for k,v in prompt_batch.items() if k not in ('labels','input_ids','attention_mask','mm_token_type_ids')}
    out['input_ids']=torch.cat((ids,gen),1)
    out['attention_mask']=torch.cat((prompt_batch['attention_mask'],torch.ones_like(gen)),1)
    if 'mm_token_type_ids' in prompt_batch:
        out['mm_token_type_ids']=torch.cat((prompt_batch['mm_token_type_ids'],torch.zeros_like(gen)),1)
    out['pg_mask']=torch.cat((torch.zeros_like(ids,dtype=torch.bool),
                                torch.tensor([[k=='s' for k in record['kinds']]],device=ids.device)),1)
    out['old_logp']=torch.tensor([v for v,k in zip(record['logp_tempered'],record['kinds']) if k=='s'],device=ids.device)
    out['reserved']=list(reserved)
    return out

def logprobs(model,batch,temperature=0.7):
    hidden=model.hidden(batch)
    mask=batch['pg_mask'][:,1:]
    logits=model.lm_head(hidden[:,:-1][mask])
    labels=batch['input_ids'][:,1:][mask]
    return policy_logprobs(logits,labels,torch.tensor(batch['reserved'],device=labels.device),temperature)

class Objective(torch.nn.Module):
    def __init__(self,model,grpo=None):
        super().__init__(); self.policy=model; self.settings=settings({'grpo':grpo or {}})
    def forward(self,batch,advantage,reference):
        lp=logprobs(self.policy,batch,self.settings['temperature'])
        terms,ratio,kl=token_terms(lp,batch['old_logp'].detach(),reference.detach(),advantage,self.settings)
        if not lp.numel():
            raise ValueError('No sampled tokens in rollout')
        return terms.mean(),dict(ratio=float(ratio.detach().mean()),kl=float(kl.detach().mean()),tokens=lp.numel())
