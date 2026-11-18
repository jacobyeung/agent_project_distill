"""Run the pinned stages once; preserve failures and step logs."""
import argparse
import contextlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE.parent/'cohort'))
import official_adapter as A
from common import dump,sha


class HexLog:
    def __init__(self,stream):self.stream=stream
    def write(self,text):
        self.stream.write(text.encode().hex()+'\n');return len(text)
    def flush(self):self.stream.flush()


def utility(spec,script,args,python=None):
    runner=os.environ['A_TRACE_RUNNER']
    command=[python or spec['interpreters']['p1cpu'],'-s','-B',runner,
             '--root',os.environ['A_JOB_ROOT'],'--config',os.environ['A_JOB_CONFIG'],
             '--script',str(script),*map(str,args)]
    subprocess.run(command,check=True)


def run(config):
    spec=config['spec'];root=Path(spec['run']);root.mkdir(parents=True,exist_ok=True)
    proof=config.get('mode')=='proof'
    fixture=bool(config.get('proof_only'))
    mode='proof' if proof else 'production'
    (root/'logs').mkdir(exist_ok=True);(root/'metadata').mkdir(exist_ok=True)
    dump(root/'SPEC.json',spec)
    dump(root/'CODE_PINS.json',A.code_pins())
    dump(root/'START.json',dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),mode=mode,
                              synthetic=fixture,generation_synthetic=proof or fixture))
    dump(root/'RELEASE.json',config['release'])
    (root/'metadata/P1.json').write_bytes((Path(spec['package'])/'cohort/MEDIA_MANIFEST.json').read_bytes())
    (root/'metadata/T0.json').write_bytes((Path(spec['package'])/'TRANSPORT.json').read_bytes())
    def step(name,fn):
        started=time.time()
        with (root/'STEPS.jsonl').open('a') as f:f.write(json.dumps(dict(step=name,event='start',time=started))+'\n')
        try:
            with (root/'logs'/(name+'.log')).open('x') as log,contextlib.redirect_stdout(HexLog(log)),contextlib.redirect_stderr(HexLog(log)):
                result=fn()
        except BaseException as error:
            with (root/'STEPS.jsonl').open('a') as f:f.write(json.dumps(dict(step=name,event='failed',error=str(error),seconds=time.time()-started))+'\n')
            raise
        with (root/'STEPS.jsonl').open('a') as f:f.write(json.dumps(dict(step=name,event='complete',seconds=time.time()-started))+'\n')
        return result
    dest=root/'a0'
    try:
        plan=root/'FRAME_PLAN.json'
        step('p0',lambda:utility(spec,HERE.parent/'proof/runtime_checks.py',
            ['plan','--input',HERE.parent/'cohort/MEDIA_MANIFEST.json','--directory',spec['inputs']['video_root'],'--output',plan]))
        import frame_plan
        observed=json.loads(plan.read_text())
        supplied=Path(spec['inputs']['frame_plan'])
        if supplied.exists() and json.loads(supplied.read_text())!=observed:
            raise ValueError('Decoded plan differs from the supplied plan')
        if proof:
            # A separate interpreter prevents unchanged dev modules from shadowing
            # the package's official loader in this chain process.
            parity_dir=root/'p0'
            step('p1',lambda:utility(spec,HERE.parent/'parity/prove_prompts.py',
                ['--output',parity_dir,'--processor-dir',spec['models']['base']['path'],
                 '--reader-root',HERE,
                 '--kit-root',HERE],
                python=spec['interpreters']['vllm']))
            (root/'PARITY.json').write_bytes((parity_dir/'PARITY.json').read_bytes())
            parity=json.loads((root/'PARITY.json').read_text())
            if not fixture and not (parity.get('processor_checked') and parity.get('all_prompt_bytes_equal') and parity.get('prompt_pins_equal')):
                raise ValueError('Real processor parity is incomplete')
        cfg=step('a0',lambda:A.bind(dest,spec['models'],spec['inputs']['rows'],spec['inputs']['video_root'],mode=mode,step=spec['step']))
        ts=A.tasks(cfg);count=len(ts)
        dump(root/'PLAN.json',dict(plan_sha256=config['plan_sha256'],mode=mode,decision_arm='B2048',items=count))
        dump(root/'AUTHORIZATION.json',dict(schema='operator-package-v1',scope='direct',step=spec['step'],mode=mode,items=count,submission_performed_by_builder=False))
        step('a1',lambda:utility(spec,HERE.parent/'proof/runtime_checks.py',
            ['frames','--input',dest/'request.json','--output',dest/'frames']))
        index_sha=sha(dest/'frames/0.json')
        check=step('a2',lambda:frame_plan.check(ts,dest/'frames',plan,index_sha))
        dump(dest/'BIND_STATUS.json',dict(ready=True,frames_sha256=index_sha,frame_plan=check,frame_plan_sha256=sha(plan)))
        step('a3',lambda:A.launch(dest))
        import official_score
        cohort=HERE.parent/'cohort/c5.jsonl'
        if proof:
            selected={t['example_id'] for t in ts}
            cohort=root/'metadata/Q0.jsonl'
            cohort.write_text(''.join(json.dumps(r)+'\n' for r in A.load_rows(HERE.parent/'cohort/c5.jsonl') if str(r['id']) in selected))
        step('a4',lambda:official_score.score_run(dest,cohort,root/'report',allow_partial=proof or fixture,parent_answers=config.get("parent_answers")))
        if proof:
            from selection import verify_results
            step('a5',lambda:dump(root/'metadata/CHECKS.json',verify_results(root/'report',[t['example_id'] for t in ts])))
        if proof and config.get('phase_b'):
            step('b0',lambda:utility(spec,HERE.parent/'proof/phase_b.py',
                ['--config',os.environ['A_JOB_CONFIG']],python=spec['interpreters']['vllm']))
        dump(root/'COMPLETE.json',dict(plan_sha256=config['plan_sha256'],mode=mode,synthetic=fixture,
            generation_synthetic=proof or fixture,decision_arm='B2048',items=count))
        return root
    except BaseException as exc:
        dump(root/'FAILED.json',dict(error=str(exc),type=type(exc).__name__,mode=mode))
        raise


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);a=p.parse_args();run(json.loads(Path(a.config).read_text()))
if __name__=='__main__':main()
