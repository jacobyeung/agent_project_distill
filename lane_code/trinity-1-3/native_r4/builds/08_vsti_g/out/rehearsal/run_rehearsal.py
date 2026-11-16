"""Run the real item pipeline with CPU model and tower boundaries."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
B=Path(__file__).resolve().parents[2];R=B.parents[1]
sys.path.append(str(B/'code'))
from adapter import *
sys.path.append(str(B/'work'))
from path_audit import build as audit_paths, assert_audit

def inner(dest,force_fixture=False):
    import coverage
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
    cov=coverage.Coverage(data_file=str(dest/'coverage'),source=[str(B/'code')]);cov.start()
    import engine,report,proof
    from boundary import Boundary
    spec=dict(tree=str(R/'from113/work/tree'),artifact=dict(path='fixture',sha256=digest('fixture')),
              config=dict(path='fixture',sha256=digest('fixture')),device='cpu',tower_device='cpu',
              weights=str(R/'dl/g3t_model.safetensors'),tower_config=str(R/'dl/g3t_config.json'))
    engine.initialize(spec)
    bound=prepare(R/'in/vsti/vstibench_repr_450_v3.json',R/'in/vsti/media.json',R/'in/vsti/frames_sample',dest/'i',True,selected_path=B/'work/absent_selection_fixture.json')
    complete_weights=not force_fixture and Path(spec['weights']+'.RECEIPT.json').is_file() and Path(spec['weights']).is_file() and Path(spec['weights']).stat().st_size==5627166200
    if complete_weights:
        # The real tower can be checked separately; synthetic scale/decode never claim a real read.
        real=engine.tower(bound,spec,dest/'real_raw',False)
    raw=engine.tower(bound,spec,dest/'raw',True);boundary=Boundary()
    geometry=engine.prepare_geometry(bound,spec,raw,dest/'g',boundary)
    completion=engine.run(dest/'i/BOUND.json',spec,geometry,dest/'j',boundary=boundary)
    engine.merge(dest/'i/BOUND.json',[dest/'j'],dest/'MERGED.json')
    report.build(dest/'MERGED.json',dest,[R/'in/comparators/f17.per_question_scores.jsonl',R/'in/comparators/p1m200.per_question_scores.jsonl'])
    reference=load(B/'work/proof_reference.json')
    proof.compare(reference,reference,reference,dest/'PROOF.json',True)
    cov.stop();cov.save();cov.json_report(outfile=str(dest/'coverage.json'))
    value=dict(passed=not completion['missing'],synthetic=True,items=len(completion['keys']),captures=len(load(dest/'i/FRAMES.json')['captures']),
               tower='real CPU tower also exercised' if complete_weights else 'pinned synthetic raw tower; real tower not exercised' if force_fixture else 'pinned synthetic raw tower; complete weight receipt absent',
               checkpoint_prefill='synthetic own depth and gravity; real scale conversion and gravity guard',
               decode='deterministic logits through the production Row loop and error injection',
               proof='comparison logic only; no historical GPU equality claim',
               completion=pin(dest/'j/COMPLETE.json'),report=pin(dest/'REPORT.json'),coverage=pin(dest/'coverage.json'))
    dump(dest/'RESULT.json',value);return value

def main():
    p=argparse.ArgumentParser();p.add_argument('--inner',action='store_true');p.add_argument('--dest');p.add_argument('--fixture-tower',action='store_true');a=p.parse_args()
    audit=audit_paths();assert_audit(audit)
    if not a.inner:dump(B/'out/PATH_AUDIT.json',audit)
    if a.inner:return inner(a.dest,a.fixture_tower)
    from venue import namespace
    root=B/'work'/('ns_'+uuid.uuid4().hex)
    bindings=[(str(R),str(R),False),(str(B),str(B),True)]
    args=namespace(root,bindings,cpu=True,host_bwrap=True)+['--setenv','PYTHONPATH',os.environ['PYTHONPATH'],
        sys.executable,'-s','-B',str(Path(__file__).resolve()),'--inner','--dest',str(root/'run')+'/job']
    if a.fixture_tower:args.append('--fixture-tower')
    result=subprocess.run(args,capture_output=True,text=True,timeout=55)
    dump(B/'out/rehearsal/NAMESPACE.json',dict(command=args,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr,
                                            host_shm_bound=False))
    if result.returncode==0:
        dest=root/'run/job';value=load(dest/'RESULT.json');value['namespace']='executed'
    else:
        # A denied nested namespace is a sandbox capability result, not a killed cluster job.
        dest=B/'work'/('rh_'+uuid.uuid4().hex);value=inner(dest,a.fixture_tower);value['namespace']='not available; see NAMESPACE.json'
    value['path_audit']=pin(B/'out/PATH_AUDIT.json');value['path_audit_passed']=True
    value['path']=str(dest);dump(B/'out/rehearsal/RESULT.json',value)
    for name in ('REPORT.json','REPORT.md'):(B/name).write_bytes((dest/name).read_bytes())
if __name__=='__main__':main()
