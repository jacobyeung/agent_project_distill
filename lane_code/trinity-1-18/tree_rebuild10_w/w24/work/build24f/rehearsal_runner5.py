"""Run one bounded four-rank attempt against the selected immutable kit."""
from pathlib import Path
import argparse, json, os, signal, subprocess, sys, time
D=Path(__file__).resolve().parent; L=D.parents[1]; R=D/'rehearsal5'
sys.path.insert(0,str(D))
from rehearsal_copier5 import sha, put, read

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
        self.records=read(R/'STAGES.json');self.copier=None;self.started=time.monotonic()
        self.peak=0;self.last_disk=0;self.last_bytes=0
    def guard(self):
        if sha(self.kit/'SHA256SUMS.txt')!=self.seal: raise RuntimeError('Selected kit changed; stopped without retry')
        report_pin=sha(self.report) if self.report.exists() else None
        if report_pin!=self.report_pin: raise RuntimeError('BUILD24K_REPORT appeared or changed; stopped without retry')
        self.peak=max(self.peak,rss(os.getpid()))
        if self.peak>19_000_000_000: raise RuntimeError('Aggregate RSS exceeded 19 GB; stopped without retry')
        now=time.monotonic()
        if now-self.last_disk>5:
            self.last_bytes=0
            for path in R.rglob('*'):
                try:
                    if path.is_file() and not path.is_symlink(): self.last_bytes+=path.stat().st_size
                except FileNotFoundError: pass
            self.last_disk=now
        if self.last_bytes>900_000_000: raise RuntimeError('Disk guard reached 900 MB; stopped before 1 GB cap')
        if now-self.started>1800: raise RuntimeError('Rehearsal exceeded 30-minute run budget; stopped without retry')
        if self.copier is not None and self.copier.poll() is not None: raise RuntimeError('Copier exited unexpectedly; see copier.log')
    def run(self,stage,cmd,phase='fresh'):
        self.guard()
        env={**os.environ,'TK_REHEARSAL_PHASE':phase,'S1_CPU_REHEARSAL':'1','S1_REHEARSAL_ATTEMPT':'b24f_'+phase}
        env['TK_JOB_START']=str(int(time.time())-90000) if phase=='budget' else str(int(time.time())) if phase=='resume' else os.environ['TK_JOB_START']
        with (R/(stage+'.log')).open('w') as log:
            p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
            try:
                while p.poll() is None: self.guard();time.sleep(1)
            except BaseException: stop(p);raise
        self.records.append(dict(stage=stage,returncode=p.returncode,log=str(R/(stage+'.log')),
                                 peak_rss_bytes=self.peak,TK_JOB_START=env['TK_JOB_START']))
        put(R/'STAGES.json',self.records);print(stage,p.returncode,flush=True)
        if p.returncode: raise RuntimeError(stage+' refused; no automatic retry; inspect its log')
    def main(self):
        prepared=read(R/'PREPARED.json')
        assert prepared['kit']==self.seal and Path(prepared['kit_dir'])==self.kit
        if (R/'RUN_STARTED.json').exists(): raise ValueError('Rehearsal already attempted; preserve all evidence')
        put(R/'RUN_STARTED.json',dict(kit=str(self.kit),kit_seal=self.seal,build24k_report=self.report_pin))
        def interrupted(*_): raise RuntimeError('Rehearsal interrupted; no automatic retry')
        signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
        args=read(R/'VIEW.json');py=sys.executable;ns='/tmp/q_22c714e1'
        self.run('reproduction',[py,'-I','-s','-B',str(D/'rehearsal_repro5.py'),'--launch'])
        copier_log=(R/'copier.log').open('w')
        self.copier=subprocess.Popen([py,'-I','-s','-B',str(D/'rehearsal_copier5.py'),str(self.kit)],
                                     stdout=copier_log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            for phase in ('fresh','budget','resume'):
                if phase!='fresh': self.run('authorize_'+phase,args+[py,'-B',str(D/'rehearsal_authorize.py'),phase],phase)
                self.run('train_'+phase,args+[py,'-B',str(D/'rehearsal_boundary5.py'),str(self.kit/'b/t.py'),ns+'/p2',ns+'/v.json'],phase)
        finally:
            if self.copier.poll() is None:
                self.copier.send_signal(signal.SIGTERM)
                try: self.copier.wait(timeout=45)
                except subprocess.TimeoutExpired: stop(self.copier)
            copier_log.close()
        if self.copier.returncode: raise RuntimeError('Copier final pass failed; inspect copier.log')
        put(R/'RUN_FINISHED.json',dict(kit_seal=self.seal,peak_rss_bytes=self.peak))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kit',type=Path);a=p.parse_args()
    try: Runner(a.kit.resolve()).main()
    except Exception as error:
        put(R/'RUN_REFUSAL.json',dict(error=str(error),type=type(error).__name__))
        raise
