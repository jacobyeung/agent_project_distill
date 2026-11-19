"""Entry point for an explicitly enabled preempt array; never submits jobs."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import time


def main():
    p=argparse.ArgumentParser();p.add_argument('config');p.add_argument('--enable-array',action='store_true')
    a=p.parse_args()
    if not a.enable_array:p.error('Array execution is OFF; pass --enable-array explicitly')
    cfg=json.loads(Path(a.config).read_text())
    count=cfg['shards'];index=int(os.environ['SLURM_ARRAY_TASK_ID'])
    if type(count) is not int or not 1<=count<=16 or not 0<=index<count:
        raise ValueError('Array index differs from the fixed shard plan')
    if 'SLURM_ARRAY_TASK_COUNT' in os.environ and int(os.environ['SLURM_ARRAY_TASK_COUNT'])!=count:
        raise ValueError('Scheduler array count differs from the fixed shard plan')
    if not os.environ.get('CUDA_VISIBLE_DEVICES'):
        raise ValueError('Array reads require an assigned GPU')
    duration=cfg['attempt_seconds']
    if type(duration) is not int or not 1800<=duration<=172800:
        raise ValueError('attempt_seconds must fit the declared two-day partition limit')
    root=Path(cfg['journal_root']);root.mkdir(parents=True,exist_ok=True)
    from . import launch
    from h1eval.items import load_manifest
    from orchard_h10.common import ORDER
    types=cfg['types']
    if not types or len(set(types))!=len(types) or any(t not in ORDER for t in types):
        raise ValueError('Invalid type list')
    now=time.time()
    args=['--items',cfg['items'],'--export',cfg['export'],'--export-pin',cfg['export_pin'],
          '--artifact-manifest',cfg['artifact_manifest'],'--reader-root',cfg['reader_root'],
          '--settings',cfg['settings'],'--out',str(root),'--shard',f'{index}/{count}',
          '--device','cuda:0','--arms','tower','--modes','none','--types',','.join(types),
          '--type-journals','--atomic-journal','--scene-shards',
          '--stop-at',str(now+duration-900),'--finish-by',str(now+duration-300)]
    with (root/f'array-{index}.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        rc=launch.main(args)
        if rc:return rc
        # A normal exit with an unfinished set must not masquerade as success.
        manifest=load_manifest(cfg['items'])
        chosen=launch.selected(manifest['items'],f'{index}/{count}',True)
        from .atomic_journal import AtomicJournal
        for kind in types:
            expected={r['id'] for r in chosen if r['question_type']==kind}
            folder=root/str(ORDER.index(kind))/str(index)
            if not folder.exists():
                if expected:return 75
                continue
            journal=object.__new__(AtomicJournal);journal.root=folder;journal.directory=folder/'committed'
            rows=journal.read()
            if {r['id'] for r in rows}!=expected:return 75
    return 0


if __name__=='__main__':raise SystemExit(main())
