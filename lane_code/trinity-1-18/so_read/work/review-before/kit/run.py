"""GPU parity kit. Deliberately inert unless --enable-gpu is supplied."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
TYPES=['object_abs_distance','camera_displacement','camera_rotation','camera_movement_direction','room_size_estimation']


def worker(cfg,mode,out,enabled,shard='0/1'):
    if not enabled:raise ValueError('GPU execution is OFF; pass --enable-gpu explicitly')
    if not os.environ.get('CUDA_VISIBLE_DEVICES'):raise ValueError('Assign one GPU on the intended GPU host first')
    source=Path(cfg['source_root']).resolve()
    sys.path[:0]=[str(source),str(source/'tree'),str(source/'b')]
    import numpy as np
    import torch
    import transformers
    torch.set_num_threads(8)
    if not torch.cuda.is_available():raise ValueError('CUDA is unavailable')
    random.seed(17);np.random.seed(17);torch.manual_seed(17)
    from h1eval.h10.parity_adapter import settings_for
    settings=settings_for(cfg['settings'],'devs1_routed')
    settings.pop('item_sets',None)
    active=set(cfg.get('enable_caches',['processor','vision','sam'])) if mode=='ON' else set()
    if active-{'processor','vision','sam'}:raise ValueError('Unknown cache switch')
    for name in ('processor','vision','sam'):settings['read_'+name+'_cache']='on' if name in active else 'off'
    settings['read_cache_bytes']=cfg.get('read_cache_bytes',4*1024**3)
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    settings_path=out/'settings.json';settings_path.write_text(json.dumps(settings,indent=2,sort_keys=True)+'\n')
    identity=json.loads((HERE/'SAMPLE_IDENTITY.json').read_text())
    sample=HERE/'sample50.json'
    if hashlib.sha256(sample.read_bytes()).hexdigest()!=identity['sample_sha256']:
        raise ValueError('Fixed sample has changed')
    before=time.perf_counter()
    from h1eval.h10 import launch
    from e2e_reader import parity
    kernel_info={}
    original_load=parity.load_native
    def observed_load(*args,**kwargs):
        result=original_load(*args,**kwargs);model=result[0]
        kernel_info['attention_implementation']=getattr(model.config.text_config,'_attn_implementation',None)
        implementations=set()
        for module in model.modules():
            if hasattr(module,'chunk_gated_delta_rule') and hasattr(module,'recurrent_gated_delta_rule'):
                for name in ('chunk_gated_delta_rule','recurrent_gated_delta_rule'):
                    fn=getattr(module,name)
                    implementations.add((name,getattr(fn,'__module__','unknown'),getattr(fn,'__name__',type(fn).__name__)))
        kernel_info['linear_attention_implementations']=sorted(implementations)
        return result
    parity.load_native=observed_load
    args=['--items',str(sample),'--export',cfg['export'],'--export-pin',cfg['export_pin'],
          '--artifact-manifest',cfg['artifact_manifest'],'--reader-root',str(source/'b'),
          '--settings',str(settings_path),'--out',str(out/'journals'),
          '--types',','.join(TYPES),'--type-journals','--arms','tower','--modes','none',
          '--shard',shard,'--scene-shards','--device','cuda:0','--atomic-journal']
    torch.cuda.synchronize()
    rc=launch.main(args)
    torch.cuda.synchronize()
    elapsed=time.perf_counter()-before
    record=dict(mode=mode,returncode=rc,worker_wall_seconds=elapsed,torch=torch.__version__,
                transformers=transformers.__version__,cuda=torch.version.cuda,
                device=torch.cuda.get_device_name(0),sample_sha256=identity['sample_sha256'],
                deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
                cudnn_deterministic=torch.backends.cudnn.deterministic,
                cudnn_benchmark=torch.backends.cudnn.benchmark,
                matmul_allow_tf32=torch.backends.cuda.matmul.allow_tf32,
                cudnn_allow_tf32=torch.backends.cudnn.allow_tf32,
                max_cuda_memory_bytes=torch.cuda.max_memory_allocated(),
                max_host_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                kernels=kernel_info,
                env={k:os.environ.get(k) for k in ('CUBLAS_WORKSPACE_CONFIG','CUDA_VISIBLE_DEVICES','OMP_NUM_THREADS')})
    (out/'RUN.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    return rc


def main():
    p=argparse.ArgumentParser();p.add_argument('config');p.add_argument('--out',required=True)
    p.add_argument('--enable-gpu',action='store_true');p.add_argument('--repeat-baseline',action='store_true')
    p.add_argument('--shards',type=int,default=0,help='Also validate N whole-scene shards sequentially on the same GPU')
    p.add_argument('--shard',default='0/1')
    p.add_argument('--worker',choices=['OFF','OFF_REPEAT','ON']);a=p.parse_args()
    cfg=json.loads(Path(a.config).read_text())
    if not a.enable_gpu:p.error('This kit was not run here. GPU execution requires --enable-gpu.')
    if not 0<=a.shards<=16:p.error('--shards must be in [0,16]')
    if a.worker:return worker(cfg,a.worker,a.out,a.enable_gpu,a.shard)
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',
             OPENBLAS_NUM_THREADS='8',TOKENIZERS_PARALLELISM='false',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    for mode in (['OFF','OFF_REPEAT','ON'] if a.repeat_baseline else ['OFF','ON']):
        command=[sys.executable,'-I','-s','-B',str(Path(__file__).resolve()),a.config,
                 '--out',str(out/mode),'--worker',mode,'--enable-gpu']
        with (out/(mode+'.log')).open('xb') as log:
            result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:raise SystemExit(result.returncode)
    if a.shards:
        (out/'SHARDED').mkdir()
        for index in range(a.shards):
            command=[sys.executable,'-I','-s','-B',str(Path(__file__).resolve()),a.config,
                     '--out',str(out/'SHARDED'/f'shard-{index}'),'--worker','ON','--enable-gpu',
                     '--shard',f'{index}/{a.shards}']
            with (out/f'SHARD-{index}.log').open('xb') as log:
                result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
            if result.returncode:raise SystemExit(result.returncode)
    spec=__import__('importlib.util',fromlist=['util'])
    module_spec=spec.spec_from_file_location('parity50_compare',HERE/'compare.py')
    checker=spec.module_from_spec(module_spec);module_spec.loader.exec_module(checker)
    sample=json.loads((HERE/'sample50.json').read_text())
    pairs=[('OFF','ON')]+([('OFF','OFF_REPEAT')] if a.repeat_baseline else [])
    if a.shards:pairs.append(('ON','SHARDED'))
    passed=True
    for left,right in pairs:
        result=checker.compare(out/left,out/right,sample);passed &= result['passed']
        (out/(left+'_vs_'+right+'.json')).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps(dict(comparison=f'{left}/{right}',passed=result['passed'],
                              differences=len(result['differences']))))
    if a.shards:
        source=Path(cfg['source_root']).resolve()
        sys.path[:0]=[str(source),str(source/'tree'),str(source/'b')]
        from h1eval.h10.merge_read import merge
        one=merge(sample,sorted((out/'ON/journals').glob('*/*')),out/'MERGED_SINGLE')
        many=merge(sample,sorted((out/'SHARDED').glob('shard-*/journals/*/*')),out/'MERGED_SHARDS')
        same=(out/'MERGED_SINGLE/answer_trace_return.tgz').read_bytes()==(out/'MERGED_SHARDS/answer_trace_return.tgz').read_bytes()
        passed &= same
        (out/'MERGE_PARITY.json').write_text(json.dumps(dict(passed=same,single=one,sharded=many),indent=2)+'\n')
    return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
