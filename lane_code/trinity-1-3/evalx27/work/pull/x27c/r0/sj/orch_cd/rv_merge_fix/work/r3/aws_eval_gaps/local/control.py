"""Parent-only network controls, one reused SSH control connection per action."""
import argparse
import datetime as dt
import fcntl
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time
from common import ROOT,LEDGER,save,sha
from remote import DEPLOY,SUBMIT


def context(artifact=None):
    artifact=Path(artifact).resolve() if artifact else ROOT
    if not artifact.is_relative_to(ROOT.resolve()):raise ValueError('Artifact directory must stay in workspace')
    seal=json.loads((artifact/'SEALED.json').read_text())
    bundle=artifact/seal['bundle']
    if seal['status']!='CLEAN' or sha(bundle)!=seal['sha256'] or sha(artifact/'kit/SHA256SUMS.txt')!=seal['manifest_sha256']:
        raise ValueError('Stage differs from seal')
    for line in (artifact/'kit/SHA256SUMS.txt').read_text().splitlines():
        expected,name=line.split('  ',1)
        p=artifact/'kit'/name
        if not p.resolve().is_relative_to((artifact/'kit').resolve()) or sha(p)!=expected:raise ValueError('Stage changed')
    return seal,bundle,json.loads((artifact/'DESTINATIONS.json').read_text())['root']


def ssh_args():
    return ['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20','-o','ControlMaster=auto','-o','ControlPersist=30m','code-aws']


def remote(payload,args):
    result=subprocess.run(ssh_args()+['python3 -I -B - '+' '.join(shlex.quote(str(x)) for x in args)],
                           input=payload,text=True,capture_output=True,timeout=120)
    save(ROOT/'retained'/('r'+str(time.time_ns())+'.json'),dict(rc=result.returncode,stdout=result.stdout,stderr=result.stderr))
    if result.returncode:raise RuntimeError('Control request failed; inspect retained receipt; never retry automatically')
    return json.loads(result.stdout)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['push','deploy','submit'])
    p.add_argument('--parent-authorized',action='store_true',required=True)
    p.add_argument('--artifact-dir',type=Path)
    a=p.parse_args()
    seal,bundle,root=context(a.artifact_dir)
    incoming=str(Path(root).parent/('.'+Path(root).name+'.tar'))
    with (ROOT/'retained/control.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        # Establish/reuse one master; subsequent rsync/SSH requests reuse it.
        subprocess.run(ssh_args()+['true'],check=True,timeout=30)
        if a.action=='push':
            subprocess.run(['rsync','--bwlimit=8000','--partial','-e',shlex.join(ssh_args()[:-1]),
                            str(bundle),'code-aws:'+incoming],check=True,timeout=300)
            print(json.dumps({'pushed':True,'bytes':bundle.stat().st_size}))
        elif a.action=='deploy':
            print(json.dumps(remote(DEPLOY,[root,incoming,seal['sha256']])))
        else:
            value=remote(SUBMIT,[root,seal['manifest_sha256']])
            row=dict(value,ts=dt.datetime.now(dt.timezone.utc).isoformat(),lane='evalx',cluster='code-aws',
                event='submitted',nodes=1,partition='batch',qos='normal',workdir=root,
                manifest_sha256=seal['manifest_sha256'])
            # Append only; do not read or scan the shared ledger.
            with Path(LEDGER).open('a') as f:
                fcntl.flock(f,fcntl.LOCK_EX);f.write(json.dumps(row,sort_keys=True)+'\n');f.flush()
            save(ROOT/'retained'/('s'+str(value['job_id'])+'.json'),row)
            print(json.dumps(row,sort_keys=True))


if __name__=='__main__':main()
