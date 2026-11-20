"""Run one bounded four-rank attempt against the selected immutable kit."""
from pathlib import Path
import argparse, json, os, signal, subprocess, sys, time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rehearsal_paths_k4 import L,D,R,NS,reseal
from rehearsal_copier_k4 import sha,put,read
from rehearsal_inputs_k4 import usage,DISK_LIMIT
import base64,hashlib

def rss(pid):
    try:
        status=Path(f'/proc/{pid}/status').read_text()
        own=int(next(line.split()[1] for line in status.splitlines() if line.startswith('VmRSS:')))*1024
        children=Path(f'/proc/{pid}/task/{pid}/children').read_text().split()
        return own+sum(rss(int(child)) for child in children)
    except (OSError,StopIteration): return 0

def stop(p):
    if p.poll() is not None: return
    os.killpg(p.pid,signal.SIGTERM)
    try: p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=10)

class Runner:
    def __init__(self,kit):
        self.kit=kit; self.seal=sha(kit/'SHA256SUMS.txt')
        self.report=L/'out/BUILD24K_REPORT.md'
        self.report_pin=sha(self.report) if self.report.exists() else None
        self.records=[];self.copier=None;self.started=time.monotonic()
        self.peak=0;self.last_disk=0;self.last_bytes=0
    def guard(self):
        if sha(self.kit/'SHA256SUMS.txt')!=self.seal: raise RuntimeError('Selected kit changed; stopped without retry')
        report_pin=sha(self.report) if self.report.exists() else None
        if report_pin!=self.report_pin: raise RuntimeError('BUILD24K_REPORT appeared or changed; stopped without retry')
        self.peak=max(self.peak,rss(os.getpid()))
        if self.peak>19_000_000_000: raise RuntimeError('Aggregate RSS exceeded 19 GB; stopped without retry')
        now=time.monotonic()
        if now-self.last_disk>5:
            measured=usage(R)
            self.last_bytes=max(measured['new_bytes'],measured['allocated_bytes'])
            self.last_disk=now
        if self.last_bytes>DISK_LIMIT: raise RuntimeError('Disk guard exceeded 2.85 GB; stopped; measure final bytes before any further work')
        if now-self.started>3900: raise RuntimeError('Rehearsal exceeded 65-minute run budget; stopped without retry')
        if self.copier is not None and self.copier.poll() is not None: raise RuntimeError('Copier exited unexpectedly; see copier.log')
    def run(self,stage,cmd,phase='fresh'):
        self.guard()
        env={**os.environ,'TK_REHEARSAL_PHASE':phase,'SLURM_JOB_ID':'91','S1_CPU_REHEARSAL':'1','S1_REHEARSAL_ATTEMPT':'b24k4_'+phase}
        env['TK_JOB_START']=str(int(time.time())-90000) if phase=='budget' else str(int(time.time())) if phase=='resume' else os.environ['TK_JOB_START']
        with (R/(stage+'.log')).open('w') as log:
            p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
            try:
                while p.poll() is None: self.guard();time.sleep(1)
            except BaseException as error:
                stop(p)
                self.records.append(dict(stage=stage,returncode=p.returncode,error=str(error),log=str(R/(stage+'.log'))))
                put(R/'STAGES.json',self.records)
                raise
        self.records.append(dict(stage=stage,returncode=p.returncode,log=str(R/(stage+'.log')),
                                 peak_rss_bytes=self.peak,TK_JOB_START=env['TK_JOB_START']))
        put(R/'STAGES.json',self.records);print(stage,p.returncode,flush=True)
        if p.returncode: raise RuntimeError(stage+' refused; no automatic retry; inspect its log')
    def main(self,probe=False):
        setup=read(R/'SETUP.json')
        assert setup['kit']==self.seal and Path(setup['kit_dir'])==self.kit
        if (R/'RUN_STARTED.json').exists(): raise ValueError('Rehearsal already attempted; preserve all evidence')
        put(R/'RUN_STARTED.json',dict(kit=str(self.kit),kit_seal=self.seal,probe=probe))
        def interrupted(*_): raise RuntimeError('Rehearsal interrupted; no automatic retry')
        signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
        args=['--ro-bind' if x=='--bind' else x for x in read(L/'work/build24d/GO_VIEW.json')]
        args+=['--bind',str(R),str(R),'--bind',str(R),NS,
               '--ro-bind',str(R/'source'),str(L/'work/tree_r1')]
        put(R/'VIEW.json',args)
        py=sys.executable;kit=R/'kit_n_go'
        boundary=[py,'-I','-s','-B',str(D/'rehearsal_boundary_k4a.py')]
        self.run('routing',args+boundary+[str(kit/'b/a.py'),'r',NS+'/p2',NS+'/r2.json'])
        selection=R/'p2/routing_selection.json';h=sha(selection)
        self.run('dbb2',[py,'-I','-s','-B',str(D/'rehearsal_dbb_k4.py')])
        (R/'target/u'/h).write_bytes(selection.read_bytes())
        (R/'p2').rename(R/'routing_retained')
        host=read(kit/'k/h.json');host['routing_selection']=dict(path='u/'+h,sha256=h)
        doc=json.loads((kit/'k/h.json').read_text());raw=(json.dumps(host,sort_keys=True,indent=2)+'\n').encode()
        doc.update(payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())
        (kit/'k/h.json').write_text(json.dumps(doc))
        request=read(R/'r2.json');request['_resolved']['kit_sha256']=reseal(kit);put(R/'r2.json',request)
        self.run('canary',args+boundary+[str(kit/'b/a.py'),'q',NS+'/p2',NS+'/r2.json'])
        result=read(R/'p2/q/RESULT.json')
        assert result['status']=='ADMIT' and result['host_receipt']['sha256']==sha(R/'p2/q/host.json')
        if probe: raise RuntimeError('Probe unexpectedly passed; expected unfixed handover refusal')
        self.run('rooms',args+[py,'-I','-s','-B',str(kit/'b/d.py'),NS+'/p2/s',NS+'/r.json',NS+'/n.json',NS+'/rooms.json'])
        self.run('v_config',args+[py,'-I','-s','-B',str(kit/'b/h.py'),NS+'/p2',NS+'/v.json'])
        self.run('review',args+[py,'-I','-s','-B',str(D/'rehearsal_review_k4.py')])
        self.run('authorize_fresh',args+[py,'-I','-s','-B',str(D/'rehearsal_authorize_k4.py'),'fresh'])
        put(R/'PREPARED.json',dict(kit=self.seal,kit_dir=str(self.kit),native_canary=True,fixture_kit=sha(kit/'SHA256SUMS.txt')))
        copier_log=(R/'copier.log').open('w')
        self.copier=subprocess.Popen([py,'-I','-s','-B',str(D/'rehearsal_copier_k4.py'),str(self.kit)],
                                     stdout=copier_log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            for phase in ('fresh','budget','resume'):
                if phase!='fresh': self.run('authorize_'+phase,args+[py,'-I','-s','-B',str(D/'rehearsal_authorize_k4.py'),phase],phase)
                self.run('train_'+phase,args+boundary+[str(kit/'b/t.py'),NS+'/p2',NS+'/v.json'],phase)
        finally:
            if self.copier.poll() is None:
                self.copier.send_signal(signal.SIGTERM)
                try: self.copier.wait(timeout=45)
                except subprocess.TimeoutExpired: stop(self.copier)
            copier_log.close()
        if self.copier.returncode: raise RuntimeError('Copier final pass failed; inspect copier.log')
        assert sha(self.kit/'SHA256SUMS.txt')==self.seal
        put(R/'RUN_FINISHED.json',dict(kit_seal=self.seal,peak_rss_bytes=self.peak))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kit',type=Path);p.add_argument('--probe',action='store_true');a=p.parse_args()
    try: Runner(a.kit.resolve()).main(a.probe)
    except Exception as error:
        put(R/'RUN_REFUSAL.json',dict(error=str(error),type=type(error).__name__))
        raise
