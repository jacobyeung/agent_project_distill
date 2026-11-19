"""Apply the delivered patches and verify the tested byte set; no Git or SSH."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import pack as P

INPUT=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30')


def sources():
    result={name:HERE/name for name in
            ('pack.py','pack_probes.py','test_pack.py','test_delivery.py','test_builder_tokens.py')}
    for rel,local in (
        ('cont_ops17/work/so_pack_builders/build_r10.py','routed/build_r10.py'),
        ('cont_ops18/dbuild/so_pack_builders/build_d.py','d/build_d.py'),
        ('cont_ops18/dbuild/so_pack_builders/build_support.py','d/build_support.py'),
        ('cont_ops18/dbuild/so_pack_builders/make_items_d.py','d/make_items_d.py')):
        result[rel]=HERE/rel if (HERE/rel).exists() else HERE/'work/builders'/local
    return result


def main():
    a=argparse.ArgumentParser();a.add_argument('--work',required=True)
    a.add_argument('--artifacts',default=str(HERE/'out'));a=a.parse_args()
    P.limit_resources();os.umask(0o077)
    root=Path(a.work).resolve()
    P.require(P.inside(root,'/scratch/jjyeung/orch_n30/so_pack'),'Test writes must stay under so_pack')
    root.mkdir(parents=True,exist_ok=False)
    artifacts=Path(a.artifacts).resolve()
    # Only the small native checker inputs are copied, never a repository tree.
    native=['build_d.py','build_support.py','make_items_d.py','check_release_d.py',
            'place_fill_d.py','dryres_d.py','score_d.py','o_build_D.sh','bind_D200.json',
            'bind_D544.json','TIMING_D.json','evidence/items/dist580.json']
    unchanged={}
    for rel in ['cont_ops17/work/build_r10.py','cont_ops17/work/gen400b.py']+[
            'cont_ops18/dbuild/'+n for n in native]:
        p=root/rel;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes((INPUT/rel).read_bytes());unchanged[rel]=P.file_sha(p)
    for name in ('01_pack_gate.diff','02_explicit_builder_tokens.diff'):
        with (artifacts/'patches'/name).open('rb') as source:
            r=subprocess.run(['nice','-n','10','patch','-p1','--batch','--forward',
                '--reject-file='+str(root/(name+'.rej'))],cwd=str(root),stdin=source,
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
        (root/(name+'.log')).write_bytes(r.stdout)
        P.require(r.returncode==0,'Patch failed: '+name)
    expected=sources()
    delivered={n:P.file_sha(root/n) for n in expected}
    P.require(delivered=={n:P.file_sha(p) for n,p in expected.items()},
              'F04 applied patch bytes differ from authoritative source')
    P.require(unchanged=={n:P.file_sha(root/n) for n in unchanged},
              'F07 patch modified native sources or embedded assets')
    P.require(delivered==P.read(artifacts/'TOOL_SHA256.json'),
              'F04 TOOL_SHA256 does not describe the delivered tree')
    for name in ('REPORT.md','NOTE_FOR_CONT_OPS.md','ORCHARD_ONLY_CHECKS.md'):
        text=(artifacts/name).read_text()
        P.require('Review round 1: finding -> fix -> test' in text,'F15 missing review mapping: '+name)
    orchard=(artifacts/'ORCHARD_ONLY_CHECKS.md').read_text()
    for phrase in ('sacct','60 seconds','300 seconds','USR1@1800','Trinity ledger',
                   '3.6.8','before any transport'):
        P.require(phrase in orchard,'F15 missing operational contract: '+phrase)
    P.write(root/'PATCH_VERIFIED.json',dict(passed=True,utc=P.utc(),files=delivered,
        native_sources_unchanged=unchanged,patches={n:P.file_sha(artifacts/'patches'/n)
        for n in ('01_pack_gate.diff','02_explicit_builder_tokens.diff')}))
    print('F04_PATCH_EQUALS_TESTED_SOURCE_PASS files='+str(len(delivered)))
    print('F07_NATIVE_BUILDER_AND_EMBEDDED_ASSETS_UNCHANGED_PASS files='+str(len(unchanged)))
    print('F15_DOCUMENTED_REMOTE_CONTRACT_PASS')


if __name__=='__main__':main()
