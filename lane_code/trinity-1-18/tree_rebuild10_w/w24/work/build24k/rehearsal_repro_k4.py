"""One ownership ablation using the trainer's native FULL_SHARD wrapper."""
from pathlib import Path
import argparse, json, os, sys, subprocess, time, signal

sys.path.insert(0,str(Path(__file__).resolve().parent))
from rehearsal_paths_k4 import L,D,R
sys.path[:0]=[str(D),str(R/'source')]

def write(name, value):
    (R/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')

def rss(pid):
    try:
        status=Path(f'/proc/{pid}/status').read_text()
        own=int(next(s.split()[1] for s in status.splitlines() if s.startswith('VmRSS:')))*1024
        children=Path(f'/proc/{pid}/task/{pid}/children').read_text().split()
        return own+sum(rss(int(p)) for p in children)
    except (OSError,StopIteration):return 0

def launch():
    # Separate worker groups avoid reusing FSDP state after the expected error.
    for mode in ('tied','untied'):
        if (R/f'repro_{mode}.json').exists():
            raise RuntimeError('Reproduction evidence exists; do not overwrite a completed attempt')
        cmd=[sys.executable,'-I','-s','-B','-m','torch.distributed.run','--standalone','--nnodes=1',
             '--nproc_per_node=4',str(Path(__file__).resolve()),'--mode',mode]
        peak=0
        with (R/f'repro_{mode}.log').open('w') as log:
            p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            while p.poll() is None:
                peak=max(peak,rss(os.getpid()))
                if peak>19_000_000_000:
                    os.killpg(p.pid,signal.SIGTERM)
                    p.wait(timeout=30)
                    raise RuntimeError('Reproduction exceeded aggregate 19 GB RAM; stopped, no retry')
                time.sleep(1)
        assert p.returncode==0,f'{mode} reproduction failed: see repro_{mode}.log'
        print(f'FSDP reproduction {mode}: PASS; aggregate peak RSS {peak}',flush=True)

def check(single, mode):
    import torch
    import torch.distributed as dist
    from transformers import Qwen3_5ForConditionalGeneration, Qwen3_5Config
    from student_pilot import carrier_c1_run as C, full_ft
    from rehearsal_model import untie
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    base=Qwen3_5ForConditionalGeneration.from_pretrained(
        L/'work/build24/proofs/capacity/model',local_files_only=True,
        dtype=torch.float32,attn_implementation='sdpa')
    assert base.lm_head.weight is base.get_input_embeddings().weight
    _,report=full_ft.prepare_model(base,full_ft.normalize({'train':{'llm':True,'vision_blocks':False,'merger':False}}))
    class Probe(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.model,self.lm_head,self.config=base.model,base.lm_head,base.config
            self.auxiliary_heads=torch.nn.Module();self.full_ft_report=report
            self.head_shapes=[]
            self.lm_head.register_forward_pre_hook(lambda m,a:self.head_shapes.append(list(m.weight.shape)))
        def get_input_embeddings(self):return self.model.get_input_embeddings()
        def get_output_embeddings(self):return self.lm_head
        def forward(self, ids):
            hidden=self.get_input_embeddings()(ids)
            # The same later head access used by carrier_c1.py's pose touch.
            return self.lm_head(hidden[:, :1]).sum()*0.+hidden.square().sum()
    model=Probe()
    if single:
        expected=model(torch.tensor([[2]])).detach()
        untie(model)
        observed=model(torch.tensor([[2]])).detach()
        prod=Qwen3_5Config.from_pretrained('/scratch/jjyeung/devs1c_models/cp1/base',local_files_only=True)
        assert not prod.tie_word_embeddings and not prod.text_config.tie_word_embeddings
        # Instantiate only metadata for the exact pinned 9B architecture.
        # Meta tensors allocate no weight storage and touch no GPU.
        with torch.device('meta'):
            production=Qwen3_5ForConditionalGeneration(prod)
        assert production.lm_head.weight is not production.get_input_embeddings().weight
        assert torch.equal(expected,observed)
        assert model.lm_head.weight is not model.get_input_embeddings().weight
        model(torch.tensor([[2]])).backward()
        assert torch.isfinite(model.lm_head.weight.grad).all()
        result=dict(status='PASS',tied_alias=True,untied_alias=False,exact_forward_equal=True,
                    production_top_tie=False,production_text_tie=False,
                    production_meta_alias=False,production_meta_head_shape=list(production.lm_head.weight.shape),
                    parameters_before=report['base_parameters'],parameters_after=model.full_ft_report['base_parameters'],
                    backward_finite=True,distributed_run=False)
        write('SINGLE_PROCESS.json',result);print(json.dumps(result));return
    from datetime import timedelta
    dist.init_process_group('gloo',timeout=timedelta(seconds=90))
    assert dist.get_world_size() in (2,3,4)
    if mode=='untied':untie(model)
    wrapped=C.wrap_model(model,torch.device('cpu'),mixed_precision=False)
    result=dict(rank=dist.get_rank(),mode=mode,world_size=dist.get_world_size(),
                torch_version=torch.__version__,wrapping='carrier_c1_run.wrap_model/full_ft.wrap_full_model',
                backend=dist.get_backend(),use_orig_params=True,sharding='FULL_SHARD')
    try:
        loss=wrapped(torch.tensor([[2]]));loss.backward()
        gradients_finite=all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in wrapped.parameters())
        result.update(error=None,finite=bool(torch.isfinite(loss)),backward_finite=gradients_finite,head_shapes=model.head_shapes)
    except RuntimeError as exc:
        result.update(error=str(exc),finite=False,head_shapes=model.head_shapes)
    gathered=[None]*dist.get_world_size()
    dist.all_gather_object(gathered,result)
    if dist.get_rank()==0:write(f'repro_{mode}.json',gathered)
    if mode=='tied':
        assert all(x['error'] and ('size mismatch' in x['error'] or 'mat2 must be a matrix' in x['error'])
                   and any(len(shape)==1 for shape in x['head_shapes']) for x in gathered),gathered
    else:
        assert all(x['error'] is None and x['finite'] and x['backward_finite'] and [248064,4] in x['head_shapes'] for x in gathered),gathered
    print(json.dumps(result),flush=True)
    dist.destroy_process_group()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--launch',action='store_true')
    parser.add_argument('--single',action='store_true');parser.add_argument('--mode',choices=['tied','untied'])
    args=parser.parse_args()
    if args.launch:launch()
    elif args.single or args.mode:check(args.single,args.mode)
    else:parser.error('Choose --single, --launch, or --mode')
