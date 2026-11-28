# Orchard B0/B1: the first NaN is a forward loss; the producing operation is not recorded

**Ruling: keep kit `e6bccd3deea4d7ab` sealed.** The two failures do not both use checkpointing. They do share a sharper boundary: both first report NaN on the forward immediately after two ZeRO updates, starting at sampler index 128. The next batch and the updated weights change together. The saved traces cannot distinguish them; no kernel fix or 50-update pass is verified.

| Job | Actual settings on four H100s | Evidence |
|---|---|---|
| 176658 B1/m544 | GC on, LM train, microbatch 16/rank, DS accumulation 1 | `runs/B1_spd5_s0_s17_k1/config.yaml:8,32–33`; dump:184–186. Loss 0.74469, 0.81470, NaN. |
| 176670 B0/base | **GC off**, microbatch 8/rank, DS accumulation 2 | `runs/B0_spd5_s0_s17_k1/config.yaml:8,32–33`; `train_b0_gcs.sh:31–39`; dump:143–147. Microsteps 1–4 finite; microstep 5 NaN. Gate changes on 2 and 4, not 3 or 5. |
| 176668 B0/base | GC off, microbatch 16/rank | Confirmed CUDA OOM, **not** a NaN: rank 1, `QwenOFT.py:213` → head `F.linear`, 256 MiB requested, 98 MiB free (`runs/orchard_testl_v3/transcript.jsonl:161`, captured traceback). |

**What the measurement means.** `starVLA/model/framework/VLM4A/QwenOFT.py:195–226` takes the final VLM states at the 🔍 tokens, runs the regression head and computes masked L1. Lines 40–51 reject an empty mask. I read all 50 selected episode parquets: 0 nonfinites in raw action `[6281,7]` (including gripper) and state `[6281,8]`. That does not test the transformed batch, pixels, queries or predictions. `vl_train.py:137–142` fingerprints only language and actions, only rank 0 in the saved trace.

`train_starvla.py:420–440` computes loss **before** `accelerator.backward`; `accelerate/utils/deepspeed.py:264–275` calls `engine.backward` **and** `engine.step` there. `vl_train.py:171–179,207–218` checks the returned loss but logs the **post-step** norm/gate. B1’s NaN proprio weight on row 3 therefore does not establish that the head caused that forward. Its grad norm 1.4142135 is consistent with two invalid group norms: DS `stage_1_and_2.py:1723–1727,1796–1814` and `runtime/utils.py:826–831` replace NaN/Inf by −1 before combining norms. BF16 skips the FP16 overflow check (`stage_1_and_2.py:1843–1845`). This explains propagation, not origin. B0 row 5 reports row 4’s norm because it is between DS update boundaries.

**A separate, verified counting defect:** B0 `train.log:526–528` reports Accelerate accumulation **1**, total batch **32**; DS uses **2**. The scheduler and trainer counter advance per microbatch (`train_starvla.py:50–51,359–361,436–437`). B0 trace step 5 ≠ optimizer step 5. Do not change accumulation while localizing; count `engine.global_steps`. This mismatch cannot explain B1 (1/1).

**Dtypes:** B0’s 24 `A_log` and 24 `norm.weight` on disk are finite FP32 (ranges −4.71875…4.34375 and 0.0859375…1.3183594). `QWen3_5.py:68–74` requests BF16; DS `runtime/engine.py:1247–1254` casts the module to BF16. ZeRO-2 makes FP32 Adam master partitions (`stage_1_and_2.py:398–417`); Adam epsilon 1e−8 is not an FP16 zero here. B1’s storage dtype difference is not necessary for failure; no evidence prices a B1-only effect. Installed: torch 2.6.0+cu124, DS 0.16.9, Transformers 5.3.0, fla-core 0.3.2, Triton 3.2.0. HF `modeling_qwen3_5.py:587–601` forms FP32 log decay and calls the chunk rule with Q/K L2 normalization; no saved activation or gradient identifies it as the producer.

**Test L did not establish stability.** `slurm_{168293,168298,168348}.out` each lists **one** H100. Their three-step straight runs end at losses **12.36, 10.08, 12.24**, respectively. The BS16 GC probes in 168298/168348 run **one** step. `gpu_test.sh:13–20,34–41,84–90` describes CPU optimizer offload and the short probe. None is a matched four-GPU, 50-update success. The preserved kit manifest starts `af431489`; the deployed manifest starts `e6bccd3d`. Line references above use deployed source/config where they differ.

**Minimal decisive intervention:** replay the failing batch first, before any update (`SKIP=128`); match its rank-0 fingerprint to B0 `fca34329a83de4c9` or B1 `a5e147e573d86c84`. Compare with `SKIP=0`, same seed, shapes and warmup. A cold NaN implicates the input/forward path without requiring prior updates; a cold finite result directs the next comparison to the same batch before/after updates (including rank-local model state and kernel nondeterminism). Inspect the **first** bad boundary, not downstream hits. If the chunk is first bad with finite inputs, capture those operands and compare fused vs FP32 reference on them; if an Adam input is first bad, trace its incoming gradient before changing epsilon or clipping. Change only the demonstrated operation and repeat the same fingerprints. No `nan_to_num`, batch skipping, or blanket dtype change.

### Exact diagnostic and acceptance command (not run; no Slurm submission)
In a fresh, authorized Orchard four-H100 allocation, run this shell block **per arm** with `A=B0` or `A=B1`. `N=10 SKIP=0 PROBE=1` requests ten actual updates or the first failure; `SKIP=128` tests the cold batch. After a localized fix, set `PATCH_PY` to its job-local Python overlay if needed and use `N=60 SKIP=0 PROBE=0` for each arm. Ten updates alone cannot prove >50. Stage only with the required I/O approval.

```bash
set -euo pipefail
: "${SLURM_JOB_ID:?inside the allocation}" "${A:?set B0 or B1}"; [[ $A = B0 || $A = B1 ]]
export N=${N:-10} SKIP=${SKIP:-0} PROBE=${PROBE:-1}; export V=/project/community/jjyeung/45e92888780e
export K=$V/kit; source "$K/vl_env.sh"; [[ $(nvidia-smi --query-gpu=name --format=csv,noheader | grep -c H100) = 4 ]]
P=$(mktemp -d /tmp/nancheck.XXXXXXXX); export B=$P/stage TMPDIR_B1=$P XDG_CACHE_HOME=$P/xdg TRITON_CACHE_DIR=$P/triton
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True; mkdir -p "$XDG_CACHE_HOME"; test "$(cut -c1-16 "$K/KIT_SHA256")" = e6bccd3deea4d7ab
if [[ $A = B1 ]]; then KIT_TRAIN_ARM=$K/stage.sh bash "$V/bind/train_b1_544_gc.sh" B1; K=$P/b15_m544_$SLURM_JOB_ID/kit; bs=16; ga=1; gc=true
else bash "$K/stage.sh" B0; bs=8; ga=2; gc=false; fi
export K; train_env; export GA=$ga; R=$(mktemp -d "$V/out/nancheck_${SLURM_JOB_ID}_${A}.XXXXXXXX"); export R
python -IB - "$P" "$K" <<'PY'
import json,sys,pathlib,os
p,k=map(pathlib.Path,sys.argv[1:]); d=json.loads((k/'ds_z2.json').read_text()); d['gradient_accumulation_steps']=int(os.environ['GA'])
(p/'ds_z2.json').write_text(json.dumps(d)); (p/'acc.yaml').write_text((k/'acc_z2.yaml').read_text().replace('KITDIR',str(p)))
s=(k/'vl_train.py').read_text(); tag='if __name__ == "__main__":'; assert s.count(tag)==1
hook=r'''
N,SKIP,PROBE=(int(os.environ[k]) for k in ('N','SKIP','PROBE')); GA=int(os.environ['GA']); micro=0; seen=set()
si=StepIndexSampler.__init__
StepIndexSampler.__init__=lambda self,start,total:si(self,start+SKIP,total+SKIP)
def check(name, obj):
    from torch.utils._pytree import tree_leaves
    for i,x in enumerate(tree_leaves(obj)):
        if not isinstance(x,torch.Tensor) or not x.is_floating_point() or not x.numel(): continue
        key=(name,i)
        if key not in seen and not torch.isfinite(torch.stack(torch.aminmax(x.detach()))).all().item():
            seen.add(key); print('BAD',_rank(),micro,name,i,tuple(x.shape),x.dtype,flush=True)
build=T.build_framework
def instrument(cfg):
    m=build(cfg)
    for name,mod in m.named_modules():
        if type(mod).__name__ in ('Qwen3_5GatedDeltaNet','Qwen3_5Attention','FusedRMSNormGated','RegressionHead'):
            mod.register_forward_hook(lambda _,args,out,n=name:check(n+'.out',out))
        if hasattr(mod,'chunk_gated_delta_rule'):
            fn=mod.chunk_gated_delta_rule
            def tap(*a,_f=fn,_n=name,**kw):
                check(_n+'.chunk.in',(a,kw)); out=_f(*a,**kw); check(_n+'.chunk.out',out); return out
            mod.chunk_gated_delta_rule=tap
    for name,p in m.named_parameters():
        if p.requires_grad: p.register_hook(lambda g,n=name:check(n+'.grad',g))
    return m
if PROBE:
    T.build_framework=instrument
    adam=torch.optim.AdamW.step
    def audit_adam(opt,*a,**kw):
        def inspect(side):
            for j,group in enumerate(opt.param_groups):
                for k,p in enumerate(group['params']):
                    prefix=f'Adam.{side}.group{j}.partition{k}.'
                    for key,x in dict(weight=p,grad=p.grad,**opt.state.get(p,{})).items(): check(prefix+key,x)
        inspect('in'); out=adam(opt,*a,**kw); inspect('out'); return out
    torch.optim.AdamW.step=audit_adam
    oft=importlib.import_module('starVLA.model.framework.VLM4A.QwenOFT')
    lossfn=oft.masked_l1_loss
    def losscheck(pred,target,mask=None):
        check('L1.pred',pred); check('L1.target',target); return lossfn(pred,target,mask)
    oft.masked_l1_loss=losscheck
if os.getenv('PATCH_PY'): exec(compile(open(os.environ['PATCH_PY']).read(),os.environ['PATCH_PY'],'exec'),globals())
train=Trainer._train_step; losses=[]
def counted(self,batch,*a,**kw):
    global micro
    micro+=1
    if micro==1 or (micro-1)*len(batch)*_world()==128: print('BATCH',_rank(),micro,_fingerprint(batch),flush=True)
    result=train(self,batch,*a,**kw); losses.append(float(result['action_dit_loss']))
    n=int(self.model.global_steps)
    if n==N:
        assert not self.model.skipped_steps and len(losses)==N*GA and all(map(math.isfinite,losses))
        with open(os.path.join(os.environ['R'],f'rank{_rank()}.json'),'w') as f: json.dump(losses,f)
        dist.barrier(); raise SystemExit(0)
    return result
Trainer._train_step=counted
'''
(p/'probe.py').write_text(s.replace(tag,hook+'\n'+tag))
PY
(cd "$SV"; accelerate launch --config_file "$P/acc.yaml" --num_processes 4 --mixed_precision bf16 --main_process_port 29517 "$P/probe.py" --config_yaml "$K/arm_testL.yaml" --run_root_dir="$P" --run_id=probe --seed=17 --framework.qwenvl.base_vlm="$B/models/Qwen3.5-$A" --datasets.vla_data.data_root_dir="$B/data/lerobot" --datasets.vla_data.per_device_batch_size="$bs" --trainer.gradient_checkpointing="$gc" --trainer.gradient_accumulation_steps="$ga" --trainer.max_train_steps=1000 --trainer.num_warmup_steps=30) 2>&1 | tee "$R/train.log"
python -IB - "$R" "$N" "$GA" <<'PY'
import json,math,pathlib,statistics,sys
r=pathlib.Path(sys.argv[1]); n,g=map(int,sys.argv[2:]); a=[json.loads((r/f'rank{i}.json').read_text()) for i in range(4)]
assert all(len(v)==n*g and all(map(math.isfinite,v)) for v in a)
u=[statistics.mean(v[j] for v in a for j in range(i*g,(i+1)*g)) for i in range(n)]
x,y=statistics.median(u[:5]),statistics.median(u[-5:]); print(r,'actual updates',n,'first/last five median loss',x,y)
if n>=51: assert y<x, 'no measured downward trend'
PY
```
**Release criterion:** two fresh `SKIP=0` receipts, one per arm, each with 60 non-skipped optimizer updates, finite loss on all four ranks and lower last-five than first-five median update loss. Preserve the baseline reproducer and the single-change diff alongside those receipts. No such receipts exist in the inspected evidence.
