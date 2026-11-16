"""Adapt the reviewed stager's checker subprocess to the C8r namespace."""
from pathlib import Path
import argparse
import subprocess
import sys
sys.path[:0]=[str(Path(__file__).resolve().parent/'reviewed'),str(Path(__file__).resolve().parent)]
import export_stage as reviewed
from guard_core import read,write,sha
from guard_export import stage

def run(root,archive,done,step,expected,checker):
    def check(root,artifact,digest,step,full,receipt_dir,bwrap):
        if not full:raise ValueError('Full checker required')
        for name,pin in reviewed.CHECKER_PINS.items():
            if sha(Path(__file__).parent/'reviewed/checker'/name)!=pin:raise ValueError('Reviewed checker source differs')
        output=receipt_dir/'CHECK.json'
        command=checker['prefix']+[str(Path(__file__).parent/'reviewed/checker/export_check.py'),
            '--export',artifact,'--sha256',digest,'--base',checker['base'],'--step',str(step),'--output',str(output)]
        write(receipt_dir/'COMMAND.json',dict(argv=command,full=True,pins=reviewed.CHECKER_PINS))
        result=subprocess.run(command,env=checker['environment'],capture_output=True)
        (receipt_dir/'check.hex').write_text(result.stdout.hex()+'\n'+result.stderr.hex()+'\n')
        if result.returncode:raise RuntimeError('Full export check failed')
        value=read(output)
        if value.get('status')!='VERIFIED' or value.get('step')!=step:raise ValueError('Checker receipt differs')
        return value
    reviewed.run_export_checker=check
    return stage(root,archive,done,step,expected,reviewed)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--request',required=True);a=p.parse_args();q=read(a.request)
    result=run(q['root'],q['archive'],q['done'],q['step'],q['expected'],q['checker'])
    write(Path(q['root'])/'CANDIDATE_STAGE.json',result)
