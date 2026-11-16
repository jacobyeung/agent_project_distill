"""Prepare a sealed candidate plan; block launch while release checks are unresolved."""
import argparse
from copy import deepcopy
from pathlib import Path
import re
import secrets
import sys
import tarfile
sys.path.insert(0, str(Path(__file__).resolve().parent))
from guard_core import STEPS, check_pin, digest, parse_done, read, sha, write
from names import scan_json

REQUIRED_METADATA = {'config','data_receipt','preparation','source_seal','inventory'}

def safe_tar(path):
    with tarfile.open(path,'r:*') as stream:
        seen=set()
        for member in stream:
            name=Path(member.name)
            if (name.is_absolute() or '..' in name.parts or member.name in seen
                    or not (member.isfile() or member.isdir())):
                raise ValueError('Input archive must have unique safe regular members and no links')
            seen.add(member.name)
    return True

def submit_argv(config, batch):
    if not re.fullmatch('[a-f0-9]{16}',config['token']):raise ValueError('Token must be fresh hexadecimal')
    return ['sbatch','--partition=general','--gres=gpu:1','--ntasks=1','--nodes=1',
            '--cpus-per-task=16','--mem=200G','--time='+config['time_limit'],
            '--job-name=a15_cot_ap'+config['token'],str(batch)]

def prepare(family_path,done_path,step,metadata_path,destination,token=None):
    family=read(family_path)
    if step not in STEPS:raise ValueError('Candidate step is not admitted')
    done=parse_done(Path(done_path).read_bytes(),'359fcc3c',step)
    token=token or secrets.token_hex(8)
    if not re.fullmatch('[a-f0-9]{16}',token):raise ValueError('Invalid token')
    meta=read(metadata_path)
    if set(meta)!=REQUIRED_METADATA:raise ValueError('Candidate training closure is incomplete')
    for name in REQUIRED_METADATA:check_pin(meta[name])
    cfg=read(meta['config']['path']);data=read(meta['data_receipt']['path'])
    if '/runs/359fcc3c/' not in meta['config']['path'] or '/runs/359fcc3c/' not in meta['data_receipt']['path']:
        raise ValueError('Candidate configuration and data receipt must belong to the candidate run')
    if cfg.get('preparation')!=meta['preparation'] or cfg.get('code')!=meta['source_seal']:
        raise ValueError('Candidate preparation/source seal does not bind its configuration')
    if data.get('config')!=meta['config'] or data.get('preparation')!=meta['preparation']:
        raise ValueError('Candidate data receipt does not bind the preparation')
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    config=dict(schema='g1-plan-v1',token=token,step=step,run='359fcc3c',gpus=1,partition='general',
        family=dict(path=str(Path(family_path).resolve()),sha256=sha(family_path)),
        done=done,done_sha256=sha(done_path),candidate_metadata=meta,
        proof_transport=family['proof_transport'],independent=family['independent'],
        distance_list=family['distance_list'],reference=family['reference'],
        time_limit=family['time_limit'],release_ready=False)
    config['plan_sha256']=digest(config)
    write(destination/'CONFIG.json',config)
    write(destination/'PREPARED.json',dict(status='PREPARED_NOT_AUTHORIZED',config_sha256=sha(destination/'CONFIG.json')))
    return config

def packet(config_path,review_path,order_path,destination):
    config=read(config_path);family=read(check_pin(config['family']))
    if config['plan_sha256']!=digest({k:v for k,v in config.items() if k!='plan_sha256'}):
        raise ValueError('Plan seal differs')
    if family.get('release_ready') is not True or family.get('blockers'):
        raise ValueError('Release is blocked: '+'; '.join(family.get('blockers', ['unvalidated release'])))
    review=read(review_path)
    if (review.get('verdict')!='ACCEPT' or review.get('family_sha256')!=config['family']['sha256']):
        raise ValueError('Review does not authorize this family')
    line='LAUNCH G1 '+str(config['step'])+' '+config['token']+' '+config['plan_sha256']
    if Path(order_path).read_text().splitlines().count(line)!=1:raise ValueError('Exact launch order is absent')
    if scan_json(config) or scan_json(family):raise ValueError('Job-visible naming scan failed')
    # A release cannot be enabled by changing a JSON boolean alone.
    raise ValueError('Production batch integration is incomplete; no executable packet is emitted')

def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True)
    a=s.add_parser('prepare')
    for name in ('family','done','metadata','out'):a.add_argument('--'+name,required=True)
    a.add_argument('--step',type=int,required=True);a.add_argument('--token')
    a=s.add_parser('packet')
    for name in ('config','review','order','out'):a.add_argument('--'+name,required=True)
    a=p.parse_args()
    if a.cmd=='prepare':prepare(a.family,a.done,a.step,a.metadata,a.out,a.token)
    else:packet(a.config,a.review,a.order,a.out)
if __name__=='__main__':main()
