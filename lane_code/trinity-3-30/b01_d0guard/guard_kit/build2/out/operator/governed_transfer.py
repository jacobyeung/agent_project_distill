"""Operator-only serial governor pipeline. No network or governor action on import."""
import argparse
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import time

HELPERS=Path('/scratch/jjyeung/io_governor')
STATE=Path('/data3/jjyeung/orch_n13_20261026/io_governor/STATE.md')
PYTHON='/usr/bin/python3'

def running(text,lane):
    for line in text.splitlines():
        cells=[cell.strip().strip('`') for cell in line.split('|')]
        if lane in cells and any(re.fullmatch(r'running(?:\s.*)?',cell) for cell in cells):return True
    return False

def wait_running(lane,state=STATE):
    while True:
        if time.time()-state.stat().st_mtime>120:raise RuntimeError('Governor STATE.md is stale; inspect, do not retry')
        content=state.read_text()
        if running(content,lane):return
        time.sleep(20)

def gated_source(job):
    # Registration binds this Python PID, cwd, comm and command line. Never exec.
    os.kill(os.getpid(),signal.SIGSTOP)
    wait_running(job['lane'])
    producer=subprocess.Popen(job['producer'],stdout=subprocess.PIPE)
    with producer.stdout as source:
        while chunk:=source.read(65536):
            sys.stdout.buffer.write(chunk);sys.stdout.buffer.flush()
    code=producer.wait()
    if code:raise RuntimeError('Producer failed; no automatic restart: '+str(code))

def gated_sink(job):
    wait_running(job['lane'])
    return subprocess.run(job['consumer'],stdin=sys.stdin.buffer).returncode

def registration(lane,root,limiter,expected_bytes,writes_nfs=False):
    command=[PYTHON,'-s',str(HELPERS/'register.py'),'--lane',lane,'--pid',str(root),
        '--member-pid',str(limiter),'--rl-pid',str(limiter),'--expected-bytes',str(expected_bytes),
        '--tier','3','--kind','copy','--nominal-mbps','8','--io-weight','1','--allow-resume']
    if writes_nfs:command.append('--writes-nfs')
    return command

def launch(job,path):
    if not socket.gethostname().split('.')[0].startswith('trinity-'):raise ValueError('Compute host required')
    if not str(Path.cwd()).startswith('/scratch/'):raise ValueError('Working directory must be on scratch')
    if not re.fullmatch('[A-Za-z0-9_.-]+',job['lane']):raise ValueError('Invalid lane')
    if type(job['expected_bytes']) is not int or job['expected_bytes']<=0:raise ValueError('Positive byte bound required')
    if bool(job.get('output'))==bool(job.get('consumer')):raise ValueError('Choose one output or consumer')
    if job.get('writes_nfs') and job.get('consumer'):raise ValueError('NFS writes need an explicit output path')
    sys.path.insert(0,str(HELPERS))
    from ioconfig import CFG
    record=Path(CFG['streams_dir'])/(job['lane']+'.json')
    if record.exists():raise ValueError('Stream record exists; inspect it, do not replace or retry')
    sink=None;target=None
    command=[sys.executable,'-I','-s','-B',str(Path(__file__).resolve()),'--job',str(path)]
    if job.get('output'):
        output=Path(job['output']).resolve()
        writes_nfs=str(output).startswith(('/home/','/data'))
        if writes_nfs!=bool(job.get('writes_nfs')):raise ValueError('NFS write declaration differs from destination')
        if not writes_nfs and not str(output).startswith('/scratch/'):raise ValueError('Output must be on scratch or declared NFS')
        target=output.open('xb')
    source=subprocess.Popen(command+['--role','source'],stdout=subprocess.PIPE)
    limiter=subprocess.Popen([PYTHON,'-s',str(HELPERS/'ratelimit.py'),'-q','-L','1000','-B','65536'],
                             stdin=source.stdout,stdout=target if target else subprocess.PIPE)
    source.stdout.close()
    if target:target.close()
    if job.get('consumer'):
        sink=subprocess.Popen(command+['--role','sink'],stdin=limiter.stdout)
        limiter.stdout.close()
    # These local startup checks move no payload and create no login.
    deadline=time.monotonic()+10
    while True:
        stopped=Path('/proc')/str(source.pid)/'stat'
        comm=Path('/proc')/str(limiter.pid)/'comm'
        if stopped.read_text().rsplit(')',1)[1].split()[0]=='T' and comm.read_text().strip()=='ratelimit':break
        if time.monotonic()>deadline:raise RuntimeError('Pipeline did not reach its gate; inspect, do not retry')
        time.sleep(.02)
    subprocess.run(registration(job['lane'],source.pid,limiter.pid,job['expected_bytes'],bool(job.get('writes_nfs'))),check=True)
    print('Registered '+job['lane']+'; waiting for running in '+str(STATE),flush=True)
    # Only the governor resumes the root. The root and sink also await STATE.md.
    codes=[source.wait(),limiter.wait()]
    if sink:codes.append(sink.wait())
    record.rename(record.with_name(job['lane']+'.done.'+str(int(time.time()))))
    if any(codes):raise RuntimeError('Transfer failed; record closed, no retry: '+repr(codes))
    return 0

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job',required=True);parser.add_argument('--role',choices=('source','sink'))
    args=parser.parse_args();path=Path(args.job).resolve();job=json.loads(path.read_text())
    if args.role=='source':gated_source(job);return 0
    if args.role=='sink':return gated_sink(job)
    return launch(job,path)

if __name__=='__main__':sys.exit(main())
