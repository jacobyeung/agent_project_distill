"""Run sequential model/layout cells with independent one-GPU workers."""
import json
import os
from pathlib import Path
import subprocess
import sys
from merge import merge
from stage import prepare
from frame_env import prepare_frames


def main(config,work):
    cfg=json.loads(Path(config).read_text())
    root=Path(__file__).parent
    work=Path(work)
    attempt=os.environ['SLURM_JOB_ID']
    if cfg.get('build_only') or cfg.get('unbound'):raise ValueError('Unbound review request')
    if cfg.get('engine') == 'native_routed':
        from native_routed import launch
        return launch(config, work)
    if __import__('vllm').__version__!='0.32.0':raise ValueError('Require pinned vLLM version')
    frames_sha256=prepare_frames(config,work)
    base=prepare(cfg['models']['base'],None,work/'m'/'0')
    model_paths={'base':base}
    devices=os.environ.get('CUDA_VISIBLE_DEVICES','').split(',')
    if len(devices)!=cfg['gpus'] or not all(devices):raise ValueError('GPU allocation differs')
    failures=[]
    for index,cell in enumerate(cfg['cells']):
        name=cell['model']
        if name not in model_paths:
            model_paths[name]=prepare(cfg['models'][name],base,work/'m'/str(len(model_paths)))
        children=[]
        for rank in range(cfg['gpus']):
            env=dict(os.environ,CUDA_VISIBLE_DEVICES=devices[rank],OMP_NUM_THREADS='4',
                VLLM_CACHE_ROOT=str(work/'cache'/str(rank)),TRITON_CACHE_DIR=str(work/'triton'/str(rank)),
                TORCHINDUCTOR_CACHE_DIR=str(work/'inductor'/str(rank)))
            log=work/(str(index)+'_'+str(rank)+'.log')
            with log.open('ab') as f:
                p=subprocess.Popen([sys.executable,'-B',str(root/'worker.py'),'--config',config,
                    '--model',str(model_paths[name]),'--cell',str(index),'--cache',str(work/'f'),
                    '--frames-sha256',frames_sha256,
                    '--rank',str(rank),'--world',str(cfg['gpus']),'--attempt',attempt],env=env,stdout=f,stderr=f)
            children.append(p)
        statuses=[p.wait() for p in children]
        # Even a worker failure must produce a gated summary from retained journals.
        merge(cfg,index,attempt)
        if any(statuses):failures.append(index)
    if failures:raise RuntimeError('Worker failure')


if __name__=='__main__':main(*sys.argv[1:])
