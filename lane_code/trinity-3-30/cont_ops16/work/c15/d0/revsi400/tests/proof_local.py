"""Guarded in-process binding and synthetic proof using the kit's real worker and scorers."""
import offline_guard
import asyncio
from contextlib import ExitStack
import json
from pathlib import Path
import sys
from unittest.mock import patch
import uuid
ROOT=Path(__file__).resolve().parents[1]
K=ROOT/'kit'
for path in ('launcher','reader','reader/evaluator','cohort','proof'):
    sys.path.insert(0,str(K/path))
import fixtures as F
import official_adapter as A
import official_score as O
import frame_plan
import frame_stage
import data
import fakes


class PipeLoop(asyncio.SelectorEventLoop):
    """Use an anonymous pipe for asyncio wakeups; the audit guard forbids socketpair."""
    def _make_self_pipe(self):
        import os
        self._read_fd,self._write_fd=os.pipe2(os.O_NONBLOCK|os.O_CLOEXEC)
        self._internal_fds+=1
        self._add_reader(self._read_fd,self._read_from_self)
    def _read_from_self(self):
        import os
        try:os.read(self._read_fd,4096)
        except BlockingIOError:pass
    def _write_to_self(self):
        import os
        try:os.write(self._write_fd,b'0')
        except BlockingIOError:pass
    def _close_self_pipe(self):
        import os
        self._remove_reader(self._read_fd)
        os.close(self._read_fd);os.close(self._write_fd);self._internal_fds-=1


def run(work):
    work=Path(work);work.mkdir(parents=True)
    fixture=work/'fixture';fixture.mkdir()
    base,bm,export,artifact=F.models(fixture,fixture/'e/artifact.json')
    models=dict(base=dict(kind='snapshot',path=str(base),manifest=dict(path=str(bm),sha256=F.sha(bm))),
                cp1m200=dict(kind='c1_export',path=str(artifact),sha256=F.sha(artifact)))
    reference=(ROOT/'evidence/reference544/a0/PROMPT_PINS.json').read_bytes()
    binds=[]
    with patch.object(A,'BASE_SHA',F.sha(bm)):
        for step in (200,400,600,800,1000):
            value=json.loads(artifact.read_text());value['step']=step;F.js(artifact,value)
            models['cp1m200']['sha256']=F.sha(artifact)
            dest=work/('bind'+str(step))
            cfg=A.bind(dest,models,K/'inputs/i1.json',work/'v',step=step)
            assert (dest/'PROMPT_PINS.json').read_bytes()==reference
            assert cfg['max_seqs']==32 and cfg['inflight']==16 and len(A.tasks(cfg))==679
            binds.append(dict(step=step,items=679,prompt_bytes_equal=True,checker=cfg['reader']['export_verification']['status']))
        value=json.loads(artifact.read_text());value['step']=400;F.js(artifact,value)
        models['cp1m200']['sha256']=F.sha(artifact)
        selected=F.select(O.read_rows(K/'cohort/c5.jsonl'))
        video_info=json.loads((K/'inputs/i3.json').read_text());manifest=[]
        for i,scene in enumerate(sorted({r['scene'] for r in selected})):
            file=F.video(work/'v'/(scene+'.mp4'),i)
            video_info['files'][scene].update(sha256=F.sha(file),bytes=file.stat().st_size)
            manifest.append(dict(relative_path=file.name,sha256=F.sha(file)))
        videos=F.js(work/'v.json',video_info);manifest_path=F.js(work/'manifest.json',manifest)
        original_dataset=A.dataset
        def dataset(rows):
            spec=original_dataset(rows);spec['videos']=dict(path=str(videos),sha256=F.sha(videos));return spec
        with patch.object(A,'dataset',dataset),patch.object(data,'REVSI999_VIDEOS',{32:F.sha(videos)}):
            dest=work/'proof';cfg=A.bind(dest,models,K/'inputs/i1.json',work/'v',mode='proof',step=400)
            tasks=A.tasks(cfg)
            plan=F.js(work/'plan.json',frame_plan.compute(work/'v',manifest_path,workers=2))
            result=frame_stage.stage(dest/'request.json',dest/'frames',2)
            assert result['errors']==0
            index_sha=F.sha(dest/'frames/0.json')
            check=frame_plan.check(tasks,dest/'frames',plan,index_sha)
            F.js(dest/'BIND_STATUS.json',dict(ready=True,frames_sha256=index_sha,frame_plan=check))
            processor,engine=fakes.install()
            import scoring
            scoring._METRIC_CLASS=None
            def runner(coro):
                with asyncio.Runner(loop_factory=PipeLoop) as runner:return runner.run(coro)
            with patch.object(fakes,'install_engine',lambda ids:setattr(engine,'selected',ids)),patch.object(A.asyncio,'run',runner):
                merged=A.launch(dest)
            assert merged['parity_pass']
            cohort=work/'selected.jsonl';cohort.write_text(''.join(json.dumps(r)+'\n' for r in selected))
            O.score_run(dest,cohort,work/'report',allow_partial=True)
            from selection import verify_results
            checked=verify_results(work/'report',[t['example_id'] for t in tasks])
    report=dict(passed=True,synthetic=True,real_processor=False,real_export=False,binds=binds,
                frame_plan=check,checks=checked,boundaries=['miniature weights','synthetic tier-32 clips','fake processor and engine','pipe-based asyncio wakeup'])
    F.js(work/'RESULT.json',report)
    return report


if __name__=='__main__':
    print(json.dumps(run(ROOT/'evidence'/('local_proof_'+uuid.uuid4().hex)),indent=2))
