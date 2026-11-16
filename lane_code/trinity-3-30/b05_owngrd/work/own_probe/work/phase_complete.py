"""Certify phase 1 from completed primary and control tasks before phase 2."""
import argparse,json
from pathlib import Path
from probe_common import RULES_PATH
from provenance import sha256,write_json

def certify(results,out):
    files={}
    for arm in ('A1','A7','A2'):
        for readout in ('four','final','unstandardized'):
            folder=Path(results)/arm
            if readout!='four':folder=folder/readout
            for task in ('T1','T4'):
                p=folder/(task+'.json');marker=folder/(task+'.done.json')
                value=json.loads(p.read_text());done=json.loads(marker.read_text())
                if value.get('status') not in ('complete','feature_complete_fusion_pending') or value.get('readout')!=readout or value.get('rules_sha256')!=sha256(RULES_PATH):raise ValueError('Phase 1 task is incomplete or stale')
                if done['outputs'].get(str(p))!=sha256(p):raise ValueError('Phase 1 task changed')
                files[str(p)]=sha256(p)
    write_json(out,dict(phase=1,status='complete',outputs=files,rules_sha256=sha256(RULES_PATH)))


def verify(path):
    certificate=json.loads(Path(path).read_text())
    if certificate.get('phase')!=1 or certificate.get('status')!='complete' or certificate.get('rules_sha256')!=sha256(RULES_PATH):raise ValueError('Stale phase-1 certificate')
    if len(certificate['outputs'])!=18:raise ValueError('Incomplete phase-1 certificate')
    for name,pin in certificate['outputs'].items():
        if sha256(name)!=pin:raise ValueError('Phase-1 result changed')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--results');p.add_argument('--out');p.add_argument('--verify')
    a=p.parse_args()
    if a.verify:verify(a.verify)
    elif a.results and a.out:certify(a.results,a.out)
    else:p.error('Supply --verify or both --results and --out')
