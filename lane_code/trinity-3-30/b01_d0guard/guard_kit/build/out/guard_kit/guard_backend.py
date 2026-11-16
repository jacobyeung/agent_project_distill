"""C8r preparation and one-arm serving in an already authenticated namespace.

Staging, allocation admission, and the runtime bootstrap must precede this module.
It cannot manufacture a preparation receipt for a new training run.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import gc
import sys
import time
from guard_core import check_pin, immutable, read, sha, write
from native_arm import compile_native

CORE = Path(__file__).resolve().parent/'sj/orch_cd/evalx/work/milestone'

def install_paths():
    sys.path[:0] = [str(CORE/'orchard_native'), str(CORE/'native/out2'), str(CORE)]

def authenticate_candidate(worker, baseline, step, output):
    install_paths()
    import read_runtime
    read_runtime.install_tree()
    from evalpath import runtime
    from student_pilot import carrier_c1_run as trainer
    checks = {}
    for field in ('inputs','expected_keys','pilot_selection','raw_tower','mask_cache',
                  'adapter_pins','kernel_source_pins','frames_root','geometry_captures'):
        checks[field] = immutable(worker[field], baseline[field])
    artifact = read(check_pin(worker['artifact']))
    cfg, receipt, model = read_runtime.prepared(worker['config'],worker['artifact'],worker['data_receipt'])
    init = runtime.check_init_spec(receipt,worker['artifact'])
    if artifact['step'] != step:
        raise ValueError('Candidate checkpoint step differs')
    baseline_cfg = read(check_pin(baseline['config']))
    # Training metadata can differ; inference architecture and route policy cannot.
    fields = ('base_identity','carrier_placement','training_mode','depth_enabled','depth_fov_source',
              'frame_layout','trace_program_version','tool_mode_flag','ground_target_filter','route_table')
    for field in fields:
        checks['inference.'+field] = immutable(cfg.get(field),baseline_cfg.get(field))
    values = dict(schema='g1-restoration-v1',status='PASS',independent=checks,
        baseline=dict(config=baseline['config'],data_receipt=baseline['data_receipt'],artifact=baseline['artifact'],
                      config_identity=trainer.identity(baseline_cfg)),
        candidate=dict(config=worker['config'],data_receipt=worker['data_receipt'],artifact=worker['artifact'],
                       config_identity=trainer.identity(cfg),preparation=cfg['preparation'],source_seal=artifact['source_seal'],
                       init_spec=init,model=receipt['model']))
    write(output,values)
    return values

class Session:
    def __init__(self, config, destination):
        install_paths()
        import native_worker as W
        import kernels as K
        import torch
        self.config, self.destination = config,Path(destination)
        self.W,self.K,self.torch = W,K,torch
        self.N,self.G = W.modules(config['worker'])
        W.cohort(self.N,config['worker'])
        self.context = None
        self.bound = None
        self.runner = None
        self.previous_prompt = None
        self.previous_generate = None
    def start(self):
        if self.context is not None:return
        N,G,W,K = self.N,self.G,self.W,self.K
        config,worker = self.config,self.config['worker']
        geom=self.destination/'geometry'
        geometry_seconds=W.prepare_full_geometry(config,N,G,geom)
        paired=self.destination/'paired'
        args=NS(arm='paired',scope='r1',parent_standin=False,step=config['step'],
            config=str(check_pin(worker['config'])),dest=str(paired),
            export=str(check_pin(worker['artifact'])),sha256=worker['artifact']['sha256'],dry=False,
            data_receipt=str(check_pin(worker['data_receipt'])),geometry=str(geom/'GEOMETRY_MANIFEST.json'),
            mask_cache=str(check_pin(worker['mask_cache'])),frames_root=worker['frames_root'],
            camera_cohort=str(check_pin(worker['inputs']['camera_cohort'])),device='cuda:0',first_minute=False)
        N.bind(args)
        bound=N.validate_request(N.load(paired/'request.json'),live=True)
        if bound['keys'] != worker['expected_keys']:raise ValueError('Bound cohort order differs')
        parts=K.load_parts(dict(nomdg=Path(N.__file__),geometry=Path(G.__file__)),worker['kernel_source_pins'])
        context=K.function(parts['restore'],vars(N))(args,bound)
        from evalpath import runtime
        self.previous_prompt=runtime.prompt_batch
        self.previous_generate=N.P.generate
        context.update(K.function(parts['parity'],{**vars(N),**context})(args,bound))
        context.update(g=N.load(check_pin(bound['grounding']['geometry_manifest'])),masks=N.P.Masks(bound['mask_cache']))
        self.context,self.bound,self.args=context,bound,args
        self.runner=compile_native(parts,{**vars(N),**context},K)
        write(self.destination/'PREPARATION.json',dict(geometry_seconds=geometry_seconds,
             geometry_manifest=bound['grounding']['geometry_manifest'],artifact=bound['artifact'],
             config=bound['config'],data_receipt=bound['data_receipt'],source_pins=worker['kernel_source_pins']))
    def __call__(self,keys):
        self.start()
        if len(set(keys)) != len(keys) or not set(keys) <= set(self.bound['keys']):
            raise ValueError('Requested subset differs')
        result=[]
        for key in keys:
            pair=self.runner(self.args,self.bound,key)
            if len(pair)!=1 or pair[0]['arm']!='unflagged':raise ValueError('Unexpected arm')
            result.extend(pair)
        return result
    def close(self):
        if self.previous_prompt is not None:
            from evalpath import runtime
            runtime.prompt_batch=self.previous_prompt
            self.N.P.generate=self.previous_generate
        self.runner=None;self.context=None
        gc.collect()
        self.torch.cuda.empty_cache()
