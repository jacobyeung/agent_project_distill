"""Ground-only read overlay. Live mode requires reviewed policy and reader pins."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
from capture import Capture, Writer
from parity import check

def hash_file(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


HERE=Path(__file__).resolve().parent


def arguments(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--step',type=int,choices=(544,400),default=544)
    p.add_argument('--frames',type=int,choices=(32,64,96),default=32)
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--package',type=Path)
    p.add_argument('--settings',type=Path)
    p.add_argument('--policy',type=Path,default=HERE/'policy.json')
    p.add_argument('--out',type=Path,required=True)
    return p.parse_args(argv)


def load_items(step):
    path=HERE/f'items{step}.json'
    pins=json.loads((HERE/'ITEM_PINS.json').read_text())
    if hash_file(path)!=pins[path.name]:raise ValueError('replay manifest checksum mismatch')
    data=json.loads(path.read_text())
    rows=data['items']
    if len(rows)!=150 or len({r['item_id'] for r in rows})!=150:
        raise ValueError('require all 150 distinct baseline items')
    if any(len(r['source_indices'])!=32 for r in rows):raise ValueError('anchor count')
    return rows


def policy_gate(policy, package):
    p=json.loads(policy.read_text())
    if p.get('status')!='APPROVED' or not p.get('source'):
        raise ValueError('BLOCKED: no record-backed numeric parity tolerance and reviewed reader pins')
    tol=p['gap_atol_m']
    if type(tol) not in (int,float) or not math.isfinite(tol) or tol<0 or p.get('frames_tolerance')!=0:
        raise ValueError('invalid parity policy')
    pins=p.get('reader_pins',{})
    for required in ('b/e2e_reader/stage1.py','b/e2e_reader/grounding.py','b/e2e_reader/parity.py',
                     'b/e2e_reader/real.py','b/e2e_reader/geometry.py'):
        if required not in pins:raise ValueError('missing reviewed source pin: '+required)
    for relative,digest in pins.items():
        path=(package/relative).resolve()
        if not path.is_relative_to(package.resolve()):raise ValueError('pin escapes package')
        if hash_file(path)!=digest:raise ValueError('reader pin mismatch: '+relative)
    return tol


def replay(gen, bound, reference):
    """One original prompt prefill, then recorded ground/gap calls, no decode loop."""
    import torch
    from student_pilot.carrier_c1_decode import _prepare_decode
    from student_pilot.ground_context import closed_adapters
    from e2e_reader.artifact import Audit
    from e2e_reader import stage1,grounding
    from h1eval.h10.parity_adapter import MaxCalls, PER_READ_CALL_CAP
    frames=bound['frames']
    if frames['anchor_indices']!=reference['source_indices'] or len(frames['native_frames'])!=reference['mapping']['dense_count']:
        raise ValueError('baseline frame binding mismatch')
    batch=gen.prompt_batch(gen.processor,bound['row'])
    batch={k:v.to(gen.device) if hasattr(v,'to') else v for k,v in batch.items()}
    memo=getattr(gen.perception,'memo',None)
    if memo is not None:
        memo.item_id=reference['item_id'];memo.begin_read()
    timings={};actual=[]
    with torch.no_grad(), Audit(gen.artifact) as audit, Capture(stage1.StageOne,grounding) as capture:
        state=closed_adapters(_prepare_decode)(gen.model,gen.processor,batch,max_new_tokens=16384)
        servers,built=gen.perception.lazy(frames,state,timings)
        gen.hook.begin(servers)
        gen.hook.max_calls=PER_READ_CALL_CAP['object_abs_distance']
        for c in reference['calls']:
            try:
                gen.hook.respond(c['call'])
            except MaxCalls:
                pass
            actual.append({k:gen.hook.records[-1].get(k) for k in ('call','response','served')})
        audit.entries=1
    return dict(schema='ground-capture-v1',item_id=reference['item_id'],capture=reference['capture'],
                source_indices=reference['source_indices'],dense_indices=frames['dense_indices'],
                geometry=capture.geometry,objects=capture.objects,calls=actual,
                timings=timings,audit=audit.report(),answer_pass=False)


def main(argv=None):
    a=arguments(argv);rows=load_items(a.step)
    if a.dry_run:
        from dry import dry_run
        report=dry_run(a.out,rows,a.frames,a.step)
        print(json.dumps(report,indent=2));return
    if a.frames!=32:
        raise ValueError('BLOCKED: 64/96 requires reviewed variable-frame adapter and bound extra frames')
    if a.package is None or a.settings is None:raise ValueError('package/settings required')
    tolerance=policy_gate(a.policy,a.package)
    if not os.environ.get('SLURM_JOB_ID'):raise ValueError('Orchard allocation required')
    if len(os.environ.get('CUDA_VISIBLE_DEVICES','').split(','))!=1 or not os.environ.get('CUDA_VISIBLE_DEVICES'):
        raise ValueError('exactly one assigned GPU required')
    sys.path[:0]=[str(a.package/'b'),str(a.package/'tree'),str(a.package)]
    from h1eval.h10.parity_adapter import settings_for,artifact_spec,prepare_runtime
    settings=settings_for(a.settings,'devs1_routed');prepare_runtime(settings)
    if settings['stage1_select_rule']!='candidates_argmax':raise ValueError('selection rule differs')
    if settings['perception_memo_modules']!=['g3t']:raise ValueError('unexpected memo modules')
    from e2e_reader import parity
    from h1eval.items import digest
    from h1eval.h10.parity_adapter import make_capped_real
    captures=parity._captures(settings.get('frames_json',parity.FRAMES))
    dense=parity._captures(settings.get('dense_manifest',parity.DENSE))
    for ref in rows:
        task=ref['task']; native=task['native']
        if digest(task)!=ref['mapping']['task_sha256']:
            raise ValueError('stored task digest differs')
        if digest(dict(anchors=captures[native],dense=dense[native]))!=ref['mapping']['frame_binding_sha256']:
            raise ValueError('baseline RGB/frame binding digest differs')
    factory=make_capped_real(settings['export_dir'],artifact_spec(settings['artifact_manifest']),
                             [r['task'] for r in rows],settings=settings,device='cuda:0')
    step=factory.load_info['export'].get('step')
    if step!=a.step:raise ValueError('export step mismatch')
    a.out.mkdir(parents=True,exist_ok=False)
    path=a.out/'0.jsonl.gz';writer=Writer(path)
    t=time.monotonic()
    for ref in rows:
        if not ref['calls']:
            row=dict(schema='ground-capture-v1',item_id=ref['item_id'],capture=ref['capture'],
                     source_indices=ref['source_indices'],dense_indices=[],geometry=None,objects=[],calls=[],answer_pass=False)
        else:
            bound=parity.bind_item(ref['task'],settings)
            row=replay(factory.generator,bound,ref)
        check(ref['calls'],row['calls'],tolerance)
        writer.append(row)
    writer.close()
    report=dict(trusted=True,items=writer.items,bytes=writer.bytes,
                gap_atol_m=tolerance,frames_tolerance=0,seconds=time.monotonic()-t,
                capture_sha256=hash_file(path),
                policy_sha256=hashlib.sha256(a.policy.read_bytes()).hexdigest(),step=a.step)
    (a.out/'1.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
