"""Stdlib process/thread line sets, keyed by source hash; no installed tracer."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import threading

_STATE=None


class Recorder:
    def __init__(self,root,config):
        self.root=Path(root)
        package=Path(config['spec']['package'])
        self.prefixes=[(str(self.root/'bootstrap')+'/', 'launcher/'),
            (str(package)+'/', ''),
            (str(self.root/'sj'/package.relative_to('/scratch/jjyeung'))+'/', ''),
            (str(self.root/'sj/orch_cd/legs1_reads')+'/', 'runtime_2/reader/'),
            ('/scratch/jjyeung/orch_cd/legs1_reads/', 'runtime_2/reader/'),
            ('/scratch/jjyeung/orch_cd/rv_merge_fix/', 'runtime_2/kit/'),
            (str(self.root/'sj/orch_cd/rv_merge_fix')+'/', 'runtime_2/kit/'),
            (str(Path(config['spec']['run']))+'/', 'bound/')]
        self.lines={};self.names={};self.cache={}
        self.directory=self.root/'t';self.directory.mkdir(exist_ok=True)

    def trace(self,frame,event,arg):
        name=frame.f_code.co_filename
        if name not in self.cache:
            self.cache[name]=next((label+name[len(prefix):] for prefix,label in self.prefixes
                                  if name.startswith(prefix) and name.endswith('.py')),None)
        mapped=self.cache[name]
        if mapped is None:return None
        if event=='line':
            self.lines.setdefault(name,set()).add(frame.f_lineno)
            self.names[name]=mapped
        return self.trace

    def save(self):
        records=[]
        for path,lines in list(self.lines.items()):
            try:digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
            except OSError:continue
            records.append(dict(file=self.names[path],sha256=digest,lines=sorted(lines)))
        raw=json.dumps(dict(schema=1,pid=os.getpid(),python=sys.executable,files=records),sort_keys=True).encode()
        (self.directory/(str(os.getpid())+'.json.gz')).write_bytes(gzip.compress(raw,mtime=0))


def snapshot():
    if _STATE is not None:_STATE.save()


def collect(root,destination):
    records={};processes=[]
    directory=Path(root)/'t'
    for path in sorted(directory.glob('*.json.gz')):
        value=json.loads(gzip.decompress(path.read_bytes()))
        processes.append(dict(pid=value['pid'],python=value['python']))
        for row in value['files']:
            key=(row['file'],row['sha256'])
            records.setdefault(key,set()).update(row['lines'])
    result=dict(schema=1,processes=processes,files=[dict(file=n,sha256=h,lines=sorted(v)) for (n,h),v in sorted(records.items())])
    raw=gzip.compress(json.dumps(result,sort_keys=True,separators=(',',':')).encode(),mtime=0)
    if len(raw)>=900000:raise ValueError('Trace exceeds proof sidecar allowance')
    Path(destination).write_bytes(raw)
    return result


def main():
    global _STATE
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--config',required=True)
    p.add_argument('--script',required=True);a,rest=p.parse_known_args()
    cfg=json.loads(Path(a.config).read_text());proof=cfg.get('mode')=='proof'
    if proof:
        _STATE=Recorder(a.root,cfg)
        sys.settrace(_STATE.trace);threading.settrace(_STATE.trace)
    os.environ['A_JOB_ROOT']=a.root;os.environ['A_JOB_CONFIG']=a.config
    os.environ['A_TRACE_RUNNER']=str(Path(__file__).resolve())
    # Job and chain receive their contract. Utility scripts use explicit arguments.
    if Path(a.script).name=='orchard_job.py':rest=['--root',a.root,'--config',a.config]+rest
    elif Path(a.script).name in ('chain.py','phase_b.py'):rest=['--config',a.config]+rest
    sys.argv=[a.script]+rest
    try:
        runpy.run_path(a.script,run_name='__main__')
    finally:
        snapshot()
        sys.settrace(None);threading.settrace(None)
        if proof and Path(a.script).name=='orchard_job.py':
            collect(a.root,Path(a.root)/'FINAL_TRACE.json.gz')
            if (Path(a.root)/'RETURN.json').is_file():
                import orchard_results
                try:orchard_results.final_trace(a.root,cfg)
                except Exception as error:
                    (Path(a.root)/'TRACE_RETURN_INCOMPLETE.json').write_text(json.dumps(dict(error=str(error)))+'\n')



if __name__=='__main__':
    sys.modules['trace_runtime']=sys.modules[__name__]
    main()
