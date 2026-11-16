"""Venue-neutral command line for a bound read."""
import os
import sys
# Preserve the production numerical overlay before importing numerical packages.
if os.environ.get('READ_OVERLAY'):
    sys.path[:0]=os.environ['READ_OVERLAY'].split(':')
import argparse
from pathlib import Path
from adapter import *

def main(argv=None):
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('adapt')
    for k in ('items','media','frames','out'):q.add_argument('--'+k,required=True)
    q.add_argument('--sample',action='store_true');q.add_argument('--logical-root')
    for name in ('geometry','run','job'):
        q=sub.add_parser(name)
        for k in ('bound','spec','out'):q.add_argument('--'+k,required=True)
        q.add_argument('--fixture',action='store_true')
        if name in ('run','job'):
            q.add_argument('--geometry',required=name=='run');q.add_argument('--shard',default='0/1')
            q.add_argument('--deadline-utc');q.add_argument('--resume',nargs='*',default=[]);q.add_argument('--proof-result')
            q.add_argument('--canary-only',action='store_true');q.add_argument('--canary-receipt');q.add_argument('--limit',type=float,default=21600)
    q=sub.add_parser('merge');q.add_argument('--bound',required=True);q.add_argument('--out',required=True)
    q.add_argument('--partial',action='store_true');q.add_argument('shards',nargs='+')
    q=sub.add_parser('report');q.add_argument('--merged',required=True);q.add_argument('--out',required=True);q.add_argument('--comparators',nargs='*',default=[])
    q.add_argument('--proof');q.add_argument('--release-check')
    q=sub.add_parser('proof')
    for k in ('reference','request','spec','out'):q.add_argument('--'+k,required=True)
    q=sub.add_parser('score-check');q.add_argument('--comparators',nargs=2,required=True);q.add_argument('--out',required=True)
    a=p.parse_args(argv)
    if a.command=='adapt':
        value=prepare(a.items,a.media,a.frames,a.out,a.sample)
        return relocate_input(a.out,a.logical_root) if a.logical_root else value
    if a.command in ('geometry','run','job'):
        import engine
        import time,signal
        overall_started=time.monotonic()
        spec=load(a.spec);engine.initialize(spec);b=validate_bound(a.bound)
        if a.command in ('run','job'):
            def deadline(signum,frame):
                folder=Path(a.out)/'j' if a.command=='job' else Path(a.out)
                current=load(folder/'COMPLETE.json') if (folder/'COMPLETE.json').exists() else {}
                dump(Path(a.out)/'INTERRUPTED.json',dict(reason='sealed_time_limit',missing=current.get('missing',b['keys']),completed=current.get('keys',[])))
                raise TimeoutError('sealed read deadline reached')
            signal.signal(signal.SIGALRM,deadline);signal.setitimer(signal.ITIMER_REAL,a.limit)
        if a.fixture:
            from boundary import Boundary
            boundary=Boundary()
        else:boundary=engine.NativeBoundary(spec)
        if a.command=='job':
            import time
            started=overall_started;out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
            raw=engine.tower(b,spec,out/'g/raw',a.fixture)
            geometry=engine.prepare_geometry(b,spec,raw,out/'g/scaled',boundary)
            remaining=a.limit-(time.monotonic()-started)
            if remaining<=0:
                dump(out/'COMPLETE.json',dict(reason='time_limit_during_geometry',missing=b['keys'],synthetic=boundary.synthetic))
                return
            return engine.run(a.bound,spec,geometry,out/'j',a.shard,a.canary_only,a.canary_receipt,remaining,boundary,a.deadline_utc,a.resume,a.proof_result)
        if a.command=='geometry':
            out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
            raw=engine.tower(b,spec,out/'raw',a.fixture)
            return engine.prepare_geometry(b,spec,raw,out/'scaled',boundary)
        return engine.run(a.bound,spec,a.geometry,a.out,a.shard,a.canary_only,a.canary_receipt,a.limit,boundary,a.deadline_utc,a.resume,a.proof_result)
    if a.command=='merge':
        from engine import merge
        return merge(a.bound,a.shards,a.out,a.partial)
    if a.command=='report':
        from report import build
        return build(a.merged,a.out,a.comparators,a.proof,a.release_check)
    if a.command=='proof':
        from proof import run
        return run(a.reference,a.request,load(a.spec),a.out)
    if a.command=='score-check':
        from scorer import comparator_check
        return comparator_check(a.comparators,a.out)
if __name__=='__main__':main()
