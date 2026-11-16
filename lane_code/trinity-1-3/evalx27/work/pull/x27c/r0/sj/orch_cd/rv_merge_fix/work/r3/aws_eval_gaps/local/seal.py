"""Seal the complete shipping stage and run the approved local anonymity gate."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import ROOT,archive,save,sha


def seal(artifact=None):
    artifact=Path(artifact).resolve() if artifact else ROOT
    if not (artifact.is_relative_to(ROOT.resolve()) or artifact.is_relative_to((ROOT.parent/'tmp').resolve())):raise ValueError('Artifact directory must stay in workspace')
    kit=artifact/'kit'
    files=sorted(p for d in ('b','k') for p in (kit/d).iterdir() if p.is_file())
    if not all((kit/p).is_file() for p in ('b/0.sh','b/1.py','k/0.tar','k/1.tar','k/2.json')):
        raise ValueError('Incomplete binding')
    sums=''.join(sha(p)+'  '+str(p.relative_to(kit))+'\n' for p in files)
    (kit/'SHA256SUMS.txt').write_text(sums)
    save(artifact/'anon/GATE_SPEC.json',{'local':[str(kit)]})
    (artifact/'checks').mkdir(parents=True,exist_ok=True)
    subprocess.run([sys.executable,'-I','-s','-B',str(ROOT/'anon/bin/anon_gate.py'),str(artifact/'anon/GATE_SPEC.json'),
                    '--no-remote','--report',str(artifact/'checks/ANON.json')],check=True)
    report=json.loads((artifact/'checks/ANON.json').read_text())
    if report['hits']:raise ValueError('Anonymity gate failed')
    # Runtime argv, paths and Slurm directives are strict-scanned as well.
    sys.path.insert(0,str(ROOT/'anon/bin'))
    import anonscan
    scanner=anonscan.Scanner(str(ROOT/'anon/bin/anon_words.json'))
    for line in (kit/'b/0.sh').read_text().splitlines():scanner.check('b/0.sh','runtime',line,code=True)
    for p in files:scanner.check('stage','name',str(p.relative_to(kit)))
    if scanner.hits:raise ValueError('Runtime anonymity scan failed')
    bundle=artifact/'transport'/(sha(kit/'SHA256SUMS.txt')[:24]+'.tar')
    archive(bundle,{str(p.relative_to(kit)):p.read_bytes() for p in files+[kit/'SHA256SUMS.txt']})
    save(artifact/'SEALED.json',dict(status='CLEAN',bundle=str(bundle.relative_to(artifact)),sha256=sha(bundle),
         manifest_sha256=sha(kit/'SHA256SUMS.txt'),gate_sha256=sha(artifact/'checks/ANON.json')))
    print('CLEAN '+str(bundle))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact-dir',type=Path)
    seal(p.parse_args().artifact_dir)
