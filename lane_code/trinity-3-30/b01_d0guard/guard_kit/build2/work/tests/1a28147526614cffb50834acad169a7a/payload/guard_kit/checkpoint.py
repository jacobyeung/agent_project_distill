"""One checkpoint per process; the parent owns staging and publication transport."""
import argparse
from copy import deepcopy
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from guard_core import read,write,proof,rows_in_order,digest,check_pin
from guard_backend import Session,authenticate_candidate,install_paths

def run(config,role,dest,publish,fixture=False,keys_override=None):
    install_paths()
    if role not in ('proof','candidate'):raise ValueError('Unknown checkpoint role')
    worker=deepcopy(config['baseline'])
    selected=config['candidate'] if role=='candidate' else None
    if selected:
        worker['step']=config['step'];worker['worker'].update({k:selected[k] for k in ('artifact','config','data_receipt')})
        from closure import authenticate,members,unpack
        from student_pilot import carrier_c1_run as trainer
        files={name:(Path(config['closure_root'])/name).read_bytes() for name in config['closure_names']}
        anchor=config.get('baseline_anchor',config['baseline']['worker']['artifact'])
        receipt=authenticate(files,config['step'],trainer,check_pin(anchor),selected['artifact']['path'])
        write(Path(dest)/'CLOSURE_ADMISSION.json',receipt)
        authenticate_candidate(worker['worker'],config['baseline']['worker'],config['step'],Path(dest)/'RESTORATION.json')
    session=None
    try:
        if role=='proof':
            reference=read(check_pin(config['reference']))
            def reader(keys):
                nonlocal session
                session=Session(worker,Path(dest)/role)
                return session(keys)
            proof(reference,reader,Path(dest)/'PROOF.json',publish,fixture=fixture)
        else:
            items=read(check_pin(config['items']));keys=keys_override or items['keys']
            canary=items['canary_keys'] if keys_override is None else keys[:10]
            receipt=dict(schema='g2-canary-v1',status='FAIL',keys=canary,full_started=False,fixture=fixture)
            try:
                session=Session(worker,Path(dest)/role)
                head=rows_in_order(session(canary),canary)
                receipt.update(status='PASS',items=len(head),rows_sha256=digest(head),
                    called=sum(bool(r['called']) for r in head),no_answer=sum(bool(r['no_answer']) for r in head))
            except Exception as error:
                receipt['error']=str(error);raise
            finally:
                write(Path(dest)/'CANARY.json',receipt);publish(Path(dest)/'CANARY.json')
            tailkeys=[k for k in keys if k not in set(canary)]
            tail=rows_in_order(session(tailkeys),tailkeys) if tailkeys else []
            indexed={r['key']:r for r in head+tail}
            from admission import merge
            merge(session,[indexed[k] for k in keys],keys,dest,fixture)
    finally:
        if session is not None:session.close()

def main():
    p=argparse.ArgumentParser()
    for name in ('config','role','out'):p.add_argument('--'+name,required=True)
    a=p.parse_args();config=read(a.config)
    # The parent acknowledges a receipt only after durable, verified publication.
    def publish(path):
        write(Path(a.out)/(path.stem+'.ready.json'),dict(path=str(path)))
        import time
        ack=Path(a.out)/(path.stem+'.ack.json');deadline=time.monotonic()+240
        while not ack.exists():
            if time.monotonic()>deadline:raise TimeoutError('Receipt publication acknowledgement absent')
            time.sleep(.5)
        if read(ack)!=dict(status='PASS',sha256=__import__('guard_core').sha(path)):
            raise ValueError('Receipt publication acknowledgement differs')
    run(config,a.role,a.out,publish)
if __name__=='__main__':main()
