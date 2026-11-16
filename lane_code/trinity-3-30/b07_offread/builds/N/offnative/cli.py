"""Operator binding, opaque naming, governed fetch, and local report entry points."""
import argparse
import fcntl
from pathlib import Path
import re
import secrets
from .paths import ROOT, r_launcher
from .io import dump, load, sha, digest, journal, owned, extract
from .cohort import cohort, media_manifest, name_inventory, canary
from .reporting import report
from offkit.bind import bind, check_ledger, ledger_append
from offkit.frames import bind_frames
from offkit.report import ReadMode
POOL = '/project/community/jjyeung/okh7/4f6a2c8d19e073b5'
GCS = 'gs://cmu-gpucloud-jjyeung/q8/4f6a2c8d19e073b5'


def binding(args):
    if args.reader == 'direct':
        raise ValueError('Direct mode is owned by build R; use builds/R/kit/rebind.py')
    b = bind(args.benchmark,args.export,args.reader,mode=args.mode,freeze_file=args.freeze_file,
             e2e_manifest=args.e2e_manifest,eat1_report=args.eat1_report,
             init_selection=args.init_selection,ledger=args.ledger,
             frames=(args.frames,args.frame_layout),frames_override_reason=args.override_reason)
    frames = b['frames']
    from .source import bind_source
    g3t = bind_source(getattr(args,'g3t_source','original'), freeze=b['reader'].get('freeze_values'),
                      mapping=getattr(args,'original_mapping',None), production=args.mode!='fixture',
                      reader=b['reader']['kind'], benchmark=args.benchmark)
    b['read_config'] = dict(frames=frames, g3t=g3t)
    b['frame_path'] = frames['anchor_rule']+'; layout '+frames['layout']
    b['binding_sha256'] = digest({k:v for k,v in b.items() if k!='binding_sha256'})
    return b

def prepare(args):
    b = binding(args)
    items = cohort(args.benchmark)
    dest = owned(args.destination)
    if dest.exists(): raise ValueError('destination exists; preparation never overwrites it')
    dest.mkdir(parents=True)
    token = args.token or ('a'+secrets.token_hex(12)[1:])
    if not re.fullmatch('[a-f][0-9a-f]{23}',token): raise ValueError('token must be 24 hex characters')
    if b['benchmark']=='vsibench5130' and b['reader']['kind']=='harness' and not getattr(args,'_shard',None):
        from .shards import plan
        from copy import copy
        partition=plan(items)
        dump(dest/'BINDING.json',b);dump(dest/'COHORT.json',items)
        results=[]
        for shard in partition['shards']:
            child=copy(args);child._shard=shard;child.destination=dest/('%02d'%shard['index'])
            child.token=None
            results.append(prepare(child))
        dump(dest/'SHARDS.json',dict(partition,prepared=results))
        return dict(destination=str(dest),shards=results,count=partition['count'])
    job = 'a15_cot_ap'+secrets.token_hex(8)
    dump(dest/'BINDING.json',b)
    dump(dest/'COHORT.json',items)
    dump(dest/'MEDIA_MANIFEST.json',media_manifest(args.benchmark,items))
    dump(dest/'NAMES.json',name_inventory(items))
    dump(dest/'CANARY.json',canary(items,ReadMode(args.benchmark,b['reader']['kind'])))
    # Only opaque identities and numeric parameters belong in an Orchard-facing config.
    config = dict(schema='orchkit-config-v1',x0=b['binding_sha256'],x1=b['export']['sha256'],
                  token=token,job_name=job,pool=POOL,gcs=GCS+'/'+token+'/',
                  job=dict(gpus=1,cpus=16,mem_gb=200,time_limit_s=21600),
                  spec=dict(frames=b['read_config']['frames']),ready=False)
    if getattr(args,'_shard',None):config['shard']=args._shard
    dump(dest/'CONFIG.json',config)
    from .admission import check
    inputs=load(args.inputs) if getattr(args,'inputs',None) else None
    reasons=check(b,inputs)
    if inputs is not None:dump(dest/'INPUTS.json',inputs)
    from .portable import build
    packet=build(dest,config,b,items,inputs)
    verdict='BLOCKED' if reasons else 'INPUTS_BOUND'
    dump(dest/'ADMISSION.json',dict(verdict=verdict,reasons=reasons,
         packet_sha256=packet['sha256'],config_sha256=sha(dest/'CONFIG.json'),
         binding_sha256=b['binding_sha256']))
    journal(ROOT/'work/ORCHARD_LEDGER.jsonl',dict(schema='orchkit-ledger-v1',event='minted',token=token,
        job_name=job,meaning=dict(benchmark=args.benchmark,export=b['export'],reader=b['reader']),
        binding_sha256=b['binding_sha256'],pool=POOL,gcs=config['gcs']))
    return dict(destination=str(dest),verdict=verdict,reasons=reasons,packet_sha256=packet['sha256'])

def checked(dest):
    d = Path(dest)
    b,c,a = (load(d/n) for n in ('BINDING.json','CONFIG.json','ADMISSION.json'))
    if digest({k:v for k,v in b.items() if k!='binding_sha256'}) != b['binding_sha256']:
        raise ValueError('binding changed')
    if c['x0'] != b['binding_sha256'] or a['config_sha256'] != sha(d/'CONFIG.json'):
        raise ValueError('config or binding identity changed')
    return d,b,c,a

def submission(args):
    d,b,c,a = checked(args.destination)
    if a['reasons']:raise ValueError('Production admission: '+ '; '.join(a['reasons']))
    from .admission import check
    reasons=check(b,load(d/'INPUTS.json'))
    if reasons:raise ValueError('Production admission: '+ '; '.join(reasons))
    if sha(d/'packet.tar')!=a['packet_sha256']:raise ValueError('packet changed')
    evidence=d/'REHEARSAL.json'
    if not evidence.is_file():raise ValueError('missing evidence: production-CONFIG transport-only rehearsal')
    rehearsal=load(evidence)
    if (rehearsal.get('verdict')!='PASS' or rehearsal.get('config_sha256')!=sha(d/'CONFIG.json') or
            rehearsal.get('packet_sha256')!=sha(d/'packet.tar') or
            rehearsal.get('only_transport_changed') is not True):
        raise ValueError('production-CONFIG rehearsal identity differs')
    from .transport import submission_argv
    if getattr(args,'command','submit-command')=='submit-command':
        return {'argv':submission_argv(c,c['pool']+'/'+c['token']+'/1.sh',packet_sha256=sha(d/'packet.tar')),
            'packet':str(d/'packet.tar'),'executed':False}
    answer=(d/'SUBMIT.out').read_text().strip()
    if not re.fullmatch(r'[0-9]+(?:;[A-Za-z0-9_-]+)?',answer):
        raise ValueError('uncertain submission; reconcile before continuing')
    lock=owned(args.ledger).with_suffix('.lock');lock.parent.mkdir(parents=True,exist_ok=True)
    with lock.open('a') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX)
        previous=check_ledger(args.ledger,b['export'],b['benchmark'])
        already=any(r.get('benchmark')==b['benchmark'] and r.get('reader')==b['reader']['kind'] and
               r.get('mode')=='production' for r in previous)
        group=d.parent/'GROUP.json'
        if already:
            if not c.get('shard') or not group.exists() or load(group).get('binding_sha256')!=b['binding_sha256']:
                raise ValueError('production read already recorded')
            if load(group).get('cohort_sha256')!=c['shard']['cohort_sha256']:
                raise ValueError('shard belongs to another read')
        result={'status':'SUBMITTED','job':int(answer.split(';')[0]),'token':c['token'],
                'config_sha256':sha(d/'CONFIG.json'),'packet_sha256':sha(d/'packet.tar')}
        with (d/'SUBMISSION.json').open('x') as out:__import__('json').dump(result,out)
        if not already:
            ledger_append(args.ledger,b)
            if c.get('shard'):dump(group,dict(binding_sha256=b['binding_sha256'],cohort_sha256=c['shard']['cohort_sha256']))
    return result


def fetch(args):
    d,b,c,a = checked(args.destination)
    from .transport import authenticate,fetch_remote
    if not args.return_archive:
        return fetch_remote(d,channel=getattr(args,'channel','pool'))
    if not getattr(args,'return_receipt',None):
        raise ValueError('missing input: authenticated return receipt (--return-receipt)')
    p=Path(args.return_archive)
    if args.return_sha256 and sha(p)!=args.return_sha256:raise ValueError('return SHA256 differs')
    authenticate(d,load(args.return_receipt),p)
    extract(p,d/'fetched')
    return {'fetched':str(d/'fetched')}


def governed_transfer(argv, output, errors, size, token):
    """Reuse build R's stopped-source, rate-limiter and governor registration protocol."""
    return r_launcher().governed_transfer(argv,output,errors,size,token)

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='command',required=True)
    q = sub.add_parser('prepare')
    q.add_argument('--benchmark',choices=['revsi999t32','vsibench5130'],required=True)
    q.add_argument('--export',required=True)
    q.add_argument('--reader',required=True)
    q.add_argument('--mode',choices=['proof','production','fixture'],default='production')
    for name in ('freeze-file','e2e-manifest','eat1-report','init-selection','override-reason','token'):
        q.add_argument('--'+name)
    q.add_argument('--g3t-source',choices=['clip32','original'],default='original')
    q.add_argument('--original-mapping',default=str(ROOT/'out/REVSI_DENSE_MAPPING.json'))
    q.add_argument('--inputs')
    q.add_argument('--frames',type=int,choices=[32,64],default=32)
    q.add_argument('--frame-layout',choices=['duplicate','spread'],default='duplicate')
    for name in ('submit-command','record-submission','fetch','report','merge-shards'):
        sub.add_parser(name)
    for q in sub.choices.values():
        q.add_argument('--destination',required=True)
        q.add_argument('--ledger',default=str(ROOT/'work/OFFICIAL_READ_LEDGER.jsonl'))
    sub.choices['merge-shards'].add_argument('--returns',nargs='+',required=True)
    sub.choices['fetch'].add_argument('--return-archive')
    sub.choices['fetch'].add_argument('--return-sha256')
    sub.choices['fetch'].add_argument('--return-receipt')
    sub.choices['fetch'].add_argument('--channel',choices=['pool','gcs'],default='pool')
    args = p.parse_args()
    if args.command=='prepare': value=prepare(args)
    elif args.command in ('submit-command','record-submission'): value=submission(args)
    elif args.command=='fetch': value=fetch(args)
    elif args.command=='merge-shards':
        from .shards import merge_returns
        value=merge_returns(Path(args.destination),[Path(p) for p in args.returns])
    else:
        d,b,c,a = checked(args.destination)
        value=report(b,load(d/'COHORT.json'),d/'fetched',owned(d/'reports'))
    print(__import__('json').dumps(value,sort_keys=True))
