"""Random-init, real-width Qwen3.5 CPU integration; no export or dataset claim."""
import argparse
import copy
import resource
import time
from types import SimpleNamespace
from pathlib import Path
import torch
from . import provenance as P

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--tree',default='/scratch/jjyeung/orch_n30/sb_f64/pkg/work/tree_r1')
    ap.add_argument('--meta',default='/scratch/jjyeung/orch_n30/sb_f64/in/qwen35_9b_meta')
    ap.add_argument('--out',default='out/CPU_PROOF.json');a=ap.parse_args()
    start=time.monotonic();torch.set_num_threads(8);torch.set_num_interop_threads(1);torch.manual_seed(17)
    P.tree(a.tree)
    P.sha(Path(a.tree).parents[2]/'in/tree_rebuild_b18_60e6ea72.tar')
    from transformers import Qwen3_5Config,Qwen3_5ForConditionalGeneration,AutoTokenizer
    from student_pilot.carrier_c1 import CarrierC1
    from student_pilot.camera_config import DEFAULTS,CARRIER_TOKEN
    from student_pilot.point_depth_head import POINT_DEPTH_DEFAULTS
    from student_pilot.carrier_c1_data import insert_frame_carriers,C1_A
    from student_pilot.carrier_c1_routing import add_routing_tokens
    from student_pilot.tower_read import TowerState
    from .adapters import install,reference
    from .rollout import sample
    from .reward import score
    from .loss import attach,logprobs,Objective,group_advantages
    import numpy as np
    raw=P.load(Path(a.meta)/'config.json');reduced=copy.deepcopy(raw)
    reduced['text_config']['num_hidden_layers']=4
    reduced['text_config']['layer_types']=raw['text_config']['layer_types'][:4]
    reduced['vision_config']['depth']=3
    cfg=Qwen3_5Config(**reduced)
    for c in (cfg,cfg.text_config,cfg.vision_config): c._attn_implementation='sdpa'
    for name in ('tokenizer.json','tokenizer_config.json'): P.sha(Path(a.meta)/name)
    tok=AutoTokenizer.from_pretrained(a.meta,local_files_only=True)
    tok.add_special_tokens({'additional_special_tokens':['<tool_response>','</tool_response>']})
    processor=SimpleNamespace(tokenizer=tok)
    add_routing_tokens(processor)
    assert len(tok)<=cfg.text_config.vocab_size, 'Proof must preserve the full native vocabulary dimension'
    print('Constructing real-width 4-text-layer, 3-vision-layer Qwen3.5 random model',flush=True)
    old=torch.get_default_dtype();torch.set_default_dtype(torch.bfloat16)
    try: base=Qwen3_5ForConditionalGeneration(cfg)
    finally: torch.set_default_dtype(old)
    # All native head dimensions remain default. Private depth taps the three retained vision layers.
    sidecar=Path(a.out).with_name('CPU_SYNTHETIC_SIDECAR.json')
    P.write(sidecar,dict(schema='rl-cpu-synthetic-sidecar-v1',scope='constructor-only synthetic test; no dataset rows'))
    camera=dict(DEFAULTS);camera['supervision']=P.pin(sidecar)
    depth={**POINT_DEPTH_DEFAULTS,'vit_layers':[1,2,3]}
    model=CarrierC1(base,camera,depth,tok.convert_tokens_to_ids(CARRIER_TOKEN),C1_A,'final',True,
                    frame_layout='duplicate',depth_fov_source='pose_head')
    # Native full_ft prepares FP32 masters. RL freezes these and stores the immutable LM in BF16.
    model.model.to(torch.bfloat16);model.lm_head.to(torch.bfloat16)
    selected=install(model,rank=16,alpha=32);model.eval()
    # Native 32-frame duplicate layout, one merged visual token per frame; synthetic RGB patches.
    prefix=tok.encode('Camera motion?\n<think>\n',add_special_tokens=False)
    ids=torch.tensor([[cfg.vision_start_token_id,cfg.video_token_id,cfg.vision_end_token_id]*32+prefix])
    width=3*cfg.vision_config.temporal_patch_size*cfg.vision_config.patch_size**2
    batch=dict(input_ids=ids,attention_mask=torch.ones_like(ids),mm_token_type_ids=torch.where(ids==cfg.video_token_id,2,0),
               video_grid_thw=torch.tensor([[32,2,2]]),pixel_values_videos=torch.randn(128,width,dtype=torch.bfloat16),
               frame_indices=list(range(32)),tower_frame_indices=list(range(32)),tower_anchor_slots=list(range(32)))
    batch=insert_frame_carriers(batch,tok,carrier_placement=C1_A,frame_layout='duplicate')
    # The sole substituted tower is frozen G3T: finite synthetic poses/depth grids enter its native TowerState.
    pose=np.tile([0.,0.,0.,0.,0.,0.,1.,1.,1.],(32,1));pose[:,0]=np.arange(32)*.1
    tower=TowerState(pose,np.ones((32,51,51)),np.tile(np.linspace(.1,1.,51*51).reshape(1,51,51),(32,1,1)),np.arange(32),np.arange(32))
    prompt=dict(type='camera_displacement',gt_answer='0.1',options=[])
    cfg_pin=Path(a.tree).parents[1]/'work/build18/inputs/config.json'
    routes=P.load(cfg_pin)['route_table']
    reserved=[tok.convert_tokens_to_ids(t) for t in ('<tool_response>','</tool_response>',CARRIER_TOKEN)]
    records=[];scores=[];batches=[]
    # Forced test prefixes exercise both sides of the routing reward; free suffix tokens come from the model.
    # No answer is forced, and forced-prefix tokens never enter the policy gradient.
    for i,prefix in enumerate(('Call: <move from=1 to=2>\n','Locate: camera in frame 1.\n')):
        print('Rollout',i,flush=True)
        record=sample(model,processor,batch,seed=17+i,max_tokens=2,prefix=prefix,
                      decode=dict(pose_source='tower',tower_state=tower,max_calls=4))
        records.append(record);scores.append(score(prompt,record,tok,routes))
        batches.append(attach(batch,record,reserved))
    assert records[0]['calls'] and not records[1]['calls'], records
    assert records[0]['errors']==0, records[0]
    advantages=group_advantages([s['total'] for s in scores]).float()
    assert advantages.abs().sum()>0, scores
    objective=Objective(model);losses=[];metrics=[];ref_lp=[]
    with reference(model):
        for b in batches: ref_lp.append(logprobs(model,b).detach())
    optimizer=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=1e-5)
    print('Recompute policy and backward',flush=True)
    for b,adv,ref in zip(batches,advantages,ref_lp):
        loss,metric=objective(b,adv,ref);(loss/len(batches)).backward()
        losses.append(float(loss.detach()));metrics.append(metric)
    grads=[p.grad for p in model.parameters() if p.requires_grad and p.grad is not None]
    grad_l1=sum(float(g.abs().sum()) for g in grads)
    assert grad_l1>0 and all(torch.isfinite(g).all() for g in grads)
    ratio_error=max(abs(m['ratio']-1.) for m in metrics)
    assert ratio_error<.1, ('decoder/loss mismatch',metrics)
    changed=next(p for p in model.parameters() if p.requires_grad and p.grad is not None and p.grad.abs().sum()>0)
    before=changed.detach().clone();optimizer.step();update=float((changed.detach()-before).abs().sum())
    assert update>0
    print('Writing proof',flush=True)
    P.write(a.out,dict(schema='rl-on-n-cpu-proof-v1',status='PASS',scope='synthetic integration, not admitted training',
        torch_version=torch.__version__,transformers_version=__import__('transformers').__version__,
        text_layers=4,vision_layers=3,original_text_layers=raw['text_config']['num_hidden_layers'],
        hidden_size=cfg.text_config.hidden_size,vocab_size=cfg.text_config.vocab_size,
        layer_types=cfg.text_config.layer_types,parameters=sum(p.numel() for p in model.parameters()),
        trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad),adapter_modules=selected,
        dtype='bfloat16 LM and vision; float32 native heads and adapters',threads=8,
        substitutions=['Frozen G3T tower output replaced by synthetic native TowerState'],
        unexercised=['SAM3/MDG grounding and object-distance path','production export reload','production prompt pool'],
        synthetic_inputs='32 frame duplicate layout; 2x2 patch grid per frame; random RGB patches; two forced test prefixes',
        scores=scores,advantages=advantages.tolist(),losses=losses,metrics=metrics,gradient_l1=grad_l1,adapter_update_l1=update,
        ratio_error=ratio_error,seconds=time.monotonic()-start,peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**2,
        records=[dict(tokens=r['tokens'],kinds=r['kinds'],text=r['text'],calls=r['calls'],finish=r['finish'],
                      sampled_tokens=r['kinds'].count('s'),response_tokens=r['kinds'].count('r')) for r in records]))
if __name__=='__main__':main()
