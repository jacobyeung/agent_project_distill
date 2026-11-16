"""Run the production checkpoint entry with explicitly recorded CPU model boundaries."""
import argparse
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import sys
import time
B=Path(__file__).resolve().parents[2];W=B.parents[1]/'work';K=B/'out/guard_kit'
LOGICAL=Path('/scratch/jjyeung/orch_cd/evalx/work/milestone')
sys.path[:0]=[str(K),str(W/'from113/work/np226'),str(W/'from113/work/pyextra'),str(W/'from113/work/tree'),
             str(LOGICAL/'orchard_native'),str(LOGICAL/'native/out2'),str(LOGICAL)]
os.environ['G2_CORE']=str(LOGICAL)
from guard_core import read,write,sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--out',required=True);p.add_argument('--role',required=True);p.add_argument('--mismatch',action='store_true');a=p.parse_args()
    dest=Path(a.out);config=read(a.config)
    import torch
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    boundary=W/'from113/builds/02_c8r/out/rehearsal/cpu_boundary.py'
    spec=importlib.util.spec_from_file_location('cpu_boundary',boundary);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.B=W/'from113/builds/02_c8r';module.W=W/'from113/work'
    module.install(W/'from113/builds/01_c8/work/rehearsal_assets/d03de829ae52386f',dest/a.role)
    # Historical token generation is a fixture boundary; actual serving still replays calls.
    # The C8r default boundary deliberately injects failures and cannot match the reference.
    import perception as P
    import nomdg as N
    expected=read(config['reference']['path']);by={r['key']:r['decode'] for r in expected}
    original=P.generate
    if a.role=='proof':
        tasks,_=N.tasks_and_captures(config['baseline']['worker']['inputs'])
        def generate(model,processor,batch,geometry,**kwargs):
            if geometry is None:return original(model,processor,batch,geometry,**kwargs)
            prompt=processor.tokenizer.decode(batch['input_ids'][0].tolist(),skip_special_tokens=False)
            hits=[t for t in tasks if 'devrows:'+t['id'] in by and t['question'] in prompt]
            if len(hits)!=1:raise ValueError('Proof fixture prompt is ambiguous')
            return deepcopy(by['devrows:'+hits[0]['id']])
        P.generate=generate
    if a.mismatch:
        expected[0]['decode']['tokens'][0]+=1
        pin=dest/'altered_reference.json';write(pin,expected)
        config['reference']=dict(path=str(pin),sha256=sha(pin))
    from checkpoint import run
    def publish(path):
        write(dest/(path.stem+'.ready.json'),dict(path=str(path)))
        until=time.monotonic()+240;ack=dest/(path.stem+'.ack.json')
        while not ack.exists():
            if time.monotonic()>until:raise TimeoutError('Fixture publication acknowledgement absent')
            time.sleep(.5)
        if read(ack)!=dict(status='PASS',sha256=sha(path)):raise ValueError('Fixture acknowledgement differs')
    keys=[r['key'] for r in expected]
    # Candidate membership includes the sealed canary, then fills from the proof list.
    items=read(config['items']['path']);chosen=set(items['canary_keys'])
    for key in keys:
        if len(chosen)>=20:break
        chosen.add(key)
    keys=[key for key in items['keys'] if key in chosen]
    run(config,a.role,dest,publish,fixture=True,keys_override=keys if a.role=='candidate' else None)
    write(dest/(a.role+'_BOUNDARY.json'),dict(fixture=True,boundary_source_sha256=sha(boundary),
        override='Reference tokens for proof; C8r model/forward/prefill/generation boundaries for candidate',
        actual_model_weights_loaded=False,items=len(keys)))
if __name__=='__main__':main()
