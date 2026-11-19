"""Execute the original A10b dispatch with explicit memory observation and optional so_read overlays."""
import argparse
import os
from pathlib import Path
import resource
import runpy
import sys
import time
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common228 import *
from observe228 import install,is_oom

def main():
    ap=argparse.ArgumentParser();ap.add_argument('config');ap.add_argument('--observe',action='store_true')
    args=ap.parse_args()
    if not args.observe:raise Refusal('Worker observation/launch requires explicit --observe')
    target_host()
    cfg=read(args.config);out=Path(cfg['adapter']['out']);worker=cfg['worker'];source=Path(worker['package'])
    install_imports(source)
    # Orchard imports h1eval with only the entry and dispatch argv. Preserve that branch.
    sys.argv=[str(source/'orchard_h10/entry.py'),str(args.config)]
    if cfg['adapter']['on']:
        extension=Path(cfg['adapter']['extensions'])
        sys.path.insert(0,str(extension/'u0'))
        from a8 import activate
        activate(enabled=True)
    from e2e_reader import parity
    from h1eval.h10 import launch
    import torch,transformers
    if not torch.cuda.is_available() or torch.cuda.device_count()!=1:raise Refusal('Worker requires exactly one visible CUDA device')
    prop=torch.cuda.get_device_properties(0)
    if 'RTX 6000 Ada' not in prop.name:raise Refusal('Worker GPU differs from occupancy evidence')
    state=install(parity,launch,torch,out,Path(worker['config']['stop_file']),cfg['adapter']['items'],enabled=True)
    record=dict(utc=utc(),mode='ON' if cfg['adapter']['on'] else 'OFF',torch=torch.__version__,
        transformers=transformers.__version__,cuda=torch.version.cuda,device=prop.name,total_memory=prop.total_memory,
        capability=[prop.major,prop.minor],visible=os.environ['CUDA_VISIBLE_DEVICES'],
        deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
        cudnn_deterministic=torch.backends.cudnn.deterministic,cudnn_benchmark=torch.backends.cudnn.benchmark,
        matmul_allow_tf32=torch.backends.cuda.matmul.allow_tf32,cudnn_allow_tf32=torch.backends.cudnn.allow_tf32,
        num_threads=torch.get_num_threads(),seed_action='none; preserve sealed A10b behavior')
    old_load=parity.load_native
    def observed_load(*a,**kw):
        result=old_load(*a,**kw);model=result[0]
        record['attention_implementation']=getattr(getattr(model.config,'text_config',model.config),'_attn_implementation',None)
        kernels=set()
        for module in model.modules():
            for name in ('chunk_gated_delta_rule','recurrent_gated_delta_rule'):
                if hasattr(module,name):
                    fn=getattr(module,name);kernels.add((name,getattr(fn,'__module__','unknown'),getattr(fn,'__name__',type(fn).__name__)))
        record['linear_attention_implementations']=sorted(kernels)
        write(out/'telemetry/FRAMEWORK.json',record)
        return result
    parity.load_native=observed_load
    write(out/'telemetry/FRAMEWORK.json',record)
    dispatch=out/'metadata/worker_dispatch.json';write(dispatch,worker)
    rc=0;begin=time.monotonic()
    try:
        # Exact sealed orchard_h10.entry action 2 -> worker_args -> h1eval.h10.launch.main.
        sys.argv=[str(source/'orchard_h10/entry.py'),str(dispatch)]
        runpy.run_path(str(source/'orchard_h10/entry.py'),run_name='__main__')
    except SystemExit as error:rc=int(error.code or 0)
    except BaseException as error:
        rc=42 if is_oom(error,torch) else 1
        failure=dict(phase=state['active']['phase'],item=state['active']['item'],
                     error=str(error),exception=type(error).__name__,no_retry=True)
        if rc==42:
            failure.update(state['peaks']());write(out/'telemetry/OOM.json',failure)
        write(out/'telemetry/WORKER_FAILURE.json',failure)
        Path(worker['config']['stop_file']).write_text('Worker failure: no retry\n')
        traceback.print_exc()
    finally:
        if not cfg['adapter']['on'] and ('a8' in sys.modules or 'e2e_reader.read_cache' in sys.modules):
            rc=1;record['off_violation']='Extension module imported'
        record.update(returncode=rc,worker_seconds=time.monotonic()-begin,
            committed_items=len(state['committed']),max_host_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        write(out/'telemetry/FRAMEWORK.json',record)
        state['restore']();parity.load_native=old_load
    return rc

if __name__=='__main__':
    try:raise SystemExit(main())
    except (Refusal,OSError,ValueError) as e:print('REFUSED: '+str(e),file=sys.stderr);raise SystemExit(2)
