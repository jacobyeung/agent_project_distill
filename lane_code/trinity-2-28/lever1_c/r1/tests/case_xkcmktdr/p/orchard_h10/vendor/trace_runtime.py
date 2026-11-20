
exec(bytes.fromhex('2222224f7061717565204a534f4e207472616e73706f72743b2063616e6f6e6963616c206861736865732072657461696e207468656972206c6f676963616c20726570726573656e746174696f6e2e2222220a696d706f7274206a736f6e0a0a6966206e6f742068617361747472286a736f6e2c20275f61305f6c6f61647327293a0a202020206a736f6e2e5f61305f6c6f616473203d206a736f6e2e6c6f6164730a202020206a736f6e2e5f61305f64756d7073203d206a736f6e2e64756d70730a0a776972655f6c6f616473203d206a736f6e2e5f61305f6c6f6164730a776972655f64756d7073203d206a736f6e2e5f61305f64756d70730a544147203d20276130270a0a0a646566207261772864617461293a0a2020202076616c7565203d20776972655f6c6f6164732864617461290a202020206966206973696e7374616e63652876616c75652c20646963742920616e64207365742876616c756529203d3d207b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c20737472293a0a202020202020202072657475726e2062797465732e66726f6d6865782876616c75655b5441475d290a2020202072657475726e20646174612e656e636f64652829206966206973696e7374616e636528646174612c207374722920656c736520646174610a0a0a646566207061636b2864617461293a0a202020206966206973696e7374616e636528646174612c20737472293a646174613d646174612e656e636f646528290a2020202072657475726e2028776972655f64756d7073287b5441473a646174612e68657828297d2c736570617261746f72733d28272c272c20273a2729292b275c6e27292e656e636f646528290a0a0a646566206c6f61647328646174612c202a617267732c202a2a6b7761726773293a0a2020202076616c75653d776972655f6c6f61647328646174612c2a617267732c2a2a6b7761726773290a202020206966206973696e7374616e63652876616c75652c646963742920616e64207365742876616c7565293d3d7b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c737472293a0a202020202020202072657475726e20776972655f6c6f6164732862797465732e66726f6d6865782876616c75655b5441475d292c2a617267732c2a2a6b7761726773290a2020202072657475726e2076616c75650a0a0a646566206c6f61642873747265616d2c202a617267732c202a2a6b7761726773293a72657475726e206c6f6164732873747265616d2e7265616428292c202a617267732c202a2a6b7761726773290a0a0a6465662064756d70732876616c75652c202a617267732c202a2a6b7761726773293a0a2020202064617461203d20776972655f64756d70732876616c75652c202a617267732c202a2a6b7761726773290a2020202072657475726e207061636b2864617461292e6465636f646528292e72737472697028275c6e2729206966206b77617267732e6765742827696e64656e742729206973206e6f74204e6f6e6520656c736520646174610a0a0a6465662064756d702876616c75652c2073747265616d2c202a617267732c202a2a6b7761726773293a0a2020202073747265616d2e7772697465287061636b28776972655f64756d70732876616c75652c202a617267732c202a2a6b776172677329292e6465636f64652829290a0a0a64656620696e7374616c6c28293a0a202020206a736f6e2e6c6f6164733d6c6f6164733b6a736f6e2e6c6f61643d6c6f61643b6a736f6e2e64756d70733d64756d70733b6a736f6e2e64756d703d64756d700a').decode(),_a0:={});_a0['install']()
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
