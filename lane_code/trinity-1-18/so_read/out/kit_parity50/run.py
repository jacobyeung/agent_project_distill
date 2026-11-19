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
CACHE_NAMES=('processor','vision','sam')
DIRS={'ORIGINAL':'u0','OFF':'u1','OFF_REPEAT':'u2','ON':'u3','ON_JOURNAL':'u4','SHARDED':'u5'}
SAMPLE=HERE/'u0.json' if (HERE/'u0.json').is_file() else HERE/'sample50.json'
IDENTITY=HERE/'u1.json' if (HERE/'u1.json').is_file() else HERE/'SAMPLE_IDENTITY.json'
COMPARE=HERE/'u1.py' if (HERE/'u1.py').is_file() else HERE/'compare.py'
TYPES=['object_abs_distance','camera_displacement','camera_rotation','camera_movement_direction','room_size_estimation']


def launch_args(cfg,source,settings_path,out,sample,mode,shard,durable_scene):
    args=['--items',str(sample),'--export',cfg['export'],'--export-pin',cfg['export_pin'],
          '--artifact-manifest',cfg['artifact_manifest'],'--reader-root',str(source/'b'),
          '--settings',str(settings_path),'--out',str(out/'journals'),
          '--types',','.join(TYPES),'--type-journals','--arms','tower','--modes','none',
          '--shard',shard,'--device','cuda:0']
    if durable_scene:
        if mode!='ON':raise ValueError('Original/OFF must use original journal and shard defaults')
        args+=['--scene-shards','--atomic-journal']
    return args


def validate_roots(cfg):
    original=Path(cfg['original_source_root']).resolve()
    source=Path(cfg['source_root']).resolve()
    if original==source:raise ValueError('Original and patched source roots must differ')
    pin_path=HERE/'u3.json' if (HERE/'u3.json').is_file() else HERE/'EXTENSION_PINS.json'
    from a9 import read_wire
    pins=read_wire(json.loads(pin_path.read_bytes()))
    if not pins:raise ValueError('Extension inventory is empty')
    actual={str(p.relative_to(source)):p for p in (source/'u0').rglob('*') if p.is_file()}
    if set(actual)!=set(pins):raise ValueError('Extension inventory differs from MANIFEST')
    if any(p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=pins[n] for n,p in actual.items()):
        raise ValueError('Extension hash differs from MANIFEST')
    if (original/'u0').exists():raise ValueError('Original source contains extensions')
    base_path=HERE/'u4.json' if (HERE/'u4.json').is_file() else HERE/'BASE_PIN.json'
    base=read_wire(json.loads(base_path.read_bytes()))
    expected=base['inventory']
    pin=hashlib.sha256(json.dumps(sorted(expected.items()),sort_keys=True,
                      separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    if not expected or base['files']!=len(expected) or pin!=base['sha256']:
        raise ValueError('Invalid base pin')
    for root in (original,source):
        paths=[p for p in root.rglob('*') if p.relative_to(root).parts[0]!='u0'
               and '__pycache__' not in p.parts and p.suffix!='.pyc']
        if any(p.is_symlink() for p in paths):raise ValueError('Base contains symlinks')
        actual={str(p.relative_to(root)):p for p in paths if p.is_file()}
        if set(actual)!=set(expected):raise ValueError('Base inventory differs from MANIFEST')
        if any(hashlib.sha256(p.read_bytes()).hexdigest()!=expected[n] for n,p in actual.items()):
            raise ValueError('Base hash differs from MANIFEST')



def worker(cfg,mode,out,enabled,shard='0/1',durable_scene=False):
    if not enabled:raise ValueError('GPU execution is OFF; pass --enable-gpu explicitly')
    if not os.environ.get('CUDA_VISIBLE_DEVICES'):raise ValueError('Assign one GPU on the intended GPU host first')
    source=Path(cfg['original_source_root'] if mode=='ORIGINAL' else cfg['source_root']).resolve()
    sys.path[:0]=[str(source),str(source/'tree'),str(source/'b')]
    sys.argv.extend(['--settings',cfg['settings']])
    if mode=='ON':
        sys.path.insert(0,str(source/'u0'))
        from a8 import activate
        activate(enabled=True)
    else:
        # Bind the staged reader before h1eval adds its legacy fallback path.
        from e2e_reader import parity
    import numpy as np
    import torch
    import transformers
    torch.set_num_threads(8)
    if not torch.cuda.is_available():raise ValueError('CUDA is unavailable')
    random.seed(17);np.random.seed(17);torch.manual_seed(17)
    from h1eval.h10.parity_adapter import settings_for
    settings=settings_for(cfg['settings'],'devs1_routed')
    settings.pop('item_sets',None)
    active={CACHE_NAMES[i] for i in cfg.get('enable_caches',[0,1,2])} if mode=='ON' else set()
    if active-{'processor','vision','sam'}:raise ValueError('Unknown cache switch')
    if mode=='ON':
        for name in ('processor','vision','sam'):settings['read_'+name+'_cache']='on' if name in active else 'off'
        settings['read_cache_bytes']=cfg.get('read_cache_bytes',12*1024**3 if 'sam' in active else 4*1024**3)
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    from a9 import seal_settings,Codec,PublicJSON
    settings_path=out/'settings.json';seal_settings(settings,settings_path)
    identity=json.loads(IDENTITY.read_text())
    sample=SAMPLE
    sample_value=json.loads(sample.read_text())
    wire=PublicJSON(Codec(sample_value,cfg,settings))
    if hashlib.sha256(sample.read_bytes()).hexdigest()!=identity['sample_sha256']:
        raise ValueError('Fixed sample has changed')
    before=time.perf_counter()
    from h1eval.h10 import launch
    launch.json=wire
    if mode=='ON':
        from h1eval.h10 import atomic_journal
        atomic_journal.json=wire
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
    args=launch_args(cfg,source,settings_path,out,sample,mode,shard,durable_scene)
    torch.cuda.synchronize()
    rc=launch.main(args)
    if mode!='ON' and ('e2e_reader.read_cache' in sys.modules or 'a8' in sys.modules):
        raise AssertionError('OFF imported new extension code')
    torch.cuda.synchronize()
    elapsed=time.perf_counter()-before
    record=dict(mode=mode,returncode=rc,worker_wall_seconds=elapsed,torch=torch.__version__,
                transformers=transformers.__version__,cuda=torch.version.cuda,
                device=torch.cuda.get_device_name(0),sample_sha256=identity['sample_sha256'],
                kit_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                transport_sha256=hashlib.sha256((HERE/'a9.py').read_bytes()).hexdigest(),
                deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
                cudnn_deterministic=torch.backends.cudnn.deterministic,
                cudnn_benchmark=torch.backends.cudnn.benchmark,
                matmul_allow_tf32=torch.backends.cuda.matmul.allow_tf32,
                cudnn_allow_tf32=torch.backends.cudnn.allow_tf32,
                max_cuda_memory_bytes=torch.cuda.max_memory_allocated(),
                max_host_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                kernels=kernel_info,
                env={k:os.environ.get(k) for k in ('CUBLAS_WORKSPACE_CONFIG','CUDA_VISIBLE_DEVICES','OMP_NUM_THREADS')})
    (out/'RUN.json').write_text(wire.dumps(record,indent=2,sort_keys=True)+'\n')
    return rc


def main():
    p=argparse.ArgumentParser();p.add_argument('config');p.add_argument('--out',required=True)
    p.add_argument('--enable-gpu',action='store_true');p.add_argument('--public',action='store_true');p.add_argument('--repeat-baseline',action='store_true')
    p.add_argument('--shards',type=int,default=0,help='Also validate N whole-scene shards sequentially on the same GPU')
    p.add_argument('--shard',default='0/1')
    p.add_argument('--durable-scene',action='store_true')
    p.add_argument('--worker',choices=['ORIGINAL','OFF','OFF_REPEAT','ON']);a=p.parse_args()
    if not a.enable_gpu:p.error('This kit was not run here. GPU execution requires --enable-gpu.')
    if not a.public:p.error('GPU execution requires --public and a token-only staged kit')
    sys.path.insert(0,str(HERE))
    from a9 import install_wire_decoder,install_log_boundary,Codec,PublicJSON,RAW_LOADS,OPAQUE_PATH
    if not OPAQUE_PATH.fullmatch(str(Path(a.out))):p.error('Use an opaque output path')
    for path in (Path(a.config),SAMPLE,IDENTITY):
        raw=RAW_LOADS(path.read_bytes())
        if not isinstance(raw,dict) or set(raw)!={'u0'}:p.error('Stage token-only configuration and manifests first')
    install_wire_decoder();install_log_boundary()
    cfg=json.loads(Path(a.config).read_text())
    from a9 import validate_paths
    validate_paths(cfg);validate_paths(json.loads(Path(cfg['settings']).read_bytes()))
    if any(type(i) is not int or not 0<=i<3 for i in cfg.get('enable_caches',[0,1,2])):
        raise ValueError('Cache selectors must be numeric slots 0..2')
    wire=PublicJSON(Codec(json.loads(SAMPLE.read_text()),cfg))
    if not 0<=a.shards<=16:p.error('--shards must be in [0,16]')
    validate_roots(cfg)
    if a.worker:return worker(cfg,a.worker,a.out,a.enable_gpu,a.shard,a.durable_scene)
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',
             OPENBLAS_NUM_THREADS='8',TOKENIZERS_PARALLELISM='false',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    for mode in ['ORIGINAL','OFF','OFF_REPEAT','ON']:
        command=[sys.executable,'-I','-s','-B',str(Path(__file__).resolve()),a.config,
                 '--out',str(out/DIRS[mode]),'--worker',mode,'--enable-gpu','--public']
        with (out/(DIRS[mode]+'.log')).open('xb') as log:
            result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:raise SystemExit(result.returncode)
    if a.shards:
        command=[sys.executable,'-I','-s','-B',str(Path(__file__).resolve()),a.config,
                 '--out',str(out/DIRS['ON_JOURNAL']),'--worker','ON','--enable-gpu','--public','--durable-scene']
        with (out/'u4.log').open('xb') as log:
            result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:raise SystemExit(result.returncode)
        (out/DIRS['SHARDED']).mkdir()
        for index in range(a.shards):
            command=[sys.executable,'-I','-s','-B',str(Path(__file__).resolve()),a.config,
                     '--out',str(out/DIRS['SHARDED']/f'u{index:x}'),'--worker','ON','--enable-gpu','--public',
                     '--shard',f'{index}/{a.shards}','--durable-scene']
            with (out/f'u6{index:x}.log').open('xb') as log:
                result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
            if result.returncode:raise SystemExit(result.returncode)
    spec=__import__('importlib.util',fromlist=['util'])
    module_spec=spec.spec_from_file_location('parity50_compare',COMPARE)
    checker=spec.module_from_spec(module_spec);module_spec.loader.exec_module(checker)
    sample=json.loads(SAMPLE.read_text())
    pairs=[('ORIGINAL','OFF'),('OFF','OFF_REPEAT'),('OFF','ON')]
    if a.shards:pairs.extend([('ON','ON_JOURNAL'),('ON_JOURNAL','SHARDED')])
    passed=True
    for pair_index,(left,right) in enumerate(pairs):
        enabled=[CACHE_NAMES[i] for i in cfg.get('enable_caches',[0,1,2])] if right in ('ON','ON_JOURNAL','SHARDED') else []
        if right=='ON' and not enabled:raise ValueError('At least one cache must be enabled')
        result=checker.compare(out/DIRS[left],out/DIRS[right],sample,enabled_caches=enabled,
                               cache_sides=('left','right') if left.startswith('ON') else ('right',),codec=wire.codec)
        if (left,right)==('ORIGINAL','OFF'):
            result['source_hash_parity']=checker.compare_source_hashes(out/DIRS[left],out/DIRS[right],codec=wire.codec)
            result['passed'] &= result['source_hash_parity']['passed']
        passed &= result['passed']
        (out/f'u{6+pair_index:x}.json').write_text(wire.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps(dict(comparison=f'{left}/{right}',passed=result['passed'],
                              differences=len(result['differences']))))
    if a.shards:
        source=Path(cfg['source_root']).resolve()
        sys.path[:0]=[str(source),str(source/'tree'),str(source/'b')]
        sys.path.insert(0,str(source/'u0'))
        from a8 import activate
        activate(enabled=True)
        from h1eval.h10.merge_read import merge
        one=merge(sample,sorted((out/DIRS['ON_JOURNAL']/'journals').glob('*/*')),out/'uc',public_codec=wire.codec)
        many=merge(sample,sorted((out/DIRS['SHARDED']).glob('u*/journals/*/*')),out/'ud',public_codec=wire.codec)
        same=(out/'uc/answer_trace_return.tgz').read_bytes()==(out/'ud/answer_trace_return.tgz').read_bytes()
        passed &= same
        (out/'ub.json').write_text(wire.dumps(dict(passed=same,single=one,sharded=many),indent=2)+'\n')
    return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
