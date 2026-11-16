"""Unrun CPU forward diagnostic using supplied local artifacts and native row loading.

This does not allocate optimizer state or update weights. The native full FT loader
uses FP32 masters and may exceed the mandatory 32 GiB address-space cap at 9B.
"""
import argparse
import copy
import json
import resource
from pathlib import Path
import torch
from student_pilot import carrier_c1_run as R, carrier_c1_routing as routing
from student_pilot.carrier_c1_data import mixed_indices
from student_pilot.carrier_c1_sweep import recipe_for
from student_pilot.p3_provenance import file_pin
p=argparse.ArgumentParser()
for key in ('config','manifest','receipt','artifact','output'):p.add_argument('--'+key,required=True)
p.add_argument('--world',type=int,choices=[4],default=4);a=p.parse_args()
K=Path(__file__).resolve().parents[1];out=Path(a.output).resolve()
if K not in out.parents:raise ValueError('output must be inside K')
# Reject nonlocal data before native loaders can follow pins; no network or NFS reads.
import sys,os

def local_reads(event,args):
    if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
        path=str(Path(os.fsdecode(args[0])).resolve())
        if path.startswith(('/home/','/data/','/data2/','/data3/','/lustre/')):
            raise PermissionError('CPU first batch requires node-local staged inputs: '+path)
    if event in ('socket.connect','subprocess.Popen','os.remove','os.rmdir'):
        raise PermissionError('CPU first batch forbids network, subprocesses and deletions')
sys.addaudithook(local_reads)
cfg=json.loads(Path(a.config).read_text());manifest=json.loads(Path(a.manifest).read_text());receipt=json.loads(Path(a.receipt).read_text())
recipe=recipe_for(cfg);receipt={**receipt,'recipe':recipe,'h1':cfg['h1']}
if not all(cfg['h1'].get(k) for k in ('faithful_own_camera_rows','routing_pose_targets')):raise ValueError('real diagnostic requires S1 and S2')
artifact=json.loads(Path(a.artifact).read_text())
if artifact.get('step')!=544:raise ValueError('expected the step-544 initialization export')
if file_pin(a.artifact)['sha256'] != cfg['init_artifact']['artifact']['sha256']:
    raise ValueError('step-544 artifact digest differs from the D0 initialization pin')
# Load in evaluation precision; head and language loss code still executes on CPU.
processor=R.processor_for_receipt(manifest,receipt)
loading={k:v for k,v in receipt.items() if k not in ('init_artifact','depth_init')}
model=R.load_model(manifest,loading,processor,evaluation=True)
R.load_artifact(model,file_pin(a.artifact));model.eval();model.recipe=recipe
rows=R.Rows(receipt,processor);counts={s:rows.count(s) for s in set(recipe['mix'])}
plan=next(mixed_indices(counts,1,seed=17,training_mode='final',mix=recipe['mix'],world=4))
gates=routing.Gates(recipe['scheduled_sampling'],getattr(model,'depth_stage1',False));factor=recipe.get('reference_world_size',4)//4
out.mkdir(parents=True,exist_ok=True)
with torch.no_grad(),(out/'first_batch.jsonl').open('w') as f:
    for rank in range(4):
        for micro,(stream,indices) in enumerate(plan):
            batch,targets,audit=rows.get(stream,indices[rank]);R.check_row(batch,targets,stream,model)
            if stream=='routing':batch,audit=R.own_values(model,rows,batch,audit,indices[rank],gates.decide(1,micro//factor),torch.device('cpu'))
            value=model(batch,targets,stream=stream)
            if not torch.isfinite(value['loss']):raise ValueError('nonfinite first-batch loss')
            record=dict(rank=rank,microstep=micro,stream=stream,audit=audit,loss=float(value['loss']),
                        components={k:float(v) for k,v in value['components'].items()},
                        trained_tokens=int((batch['labels']!=-100).sum()),peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            line=json.dumps(record);print(line,flush=True);f.write(line+'\n');f.flush()
rows.close()
