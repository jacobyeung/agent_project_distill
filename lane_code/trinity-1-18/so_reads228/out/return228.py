"""Create the existing A4 return layout and authenticated local return envelope."""
from pathlib import Path
import secrets
import tarfile
from common228 import *

def package_return(out, cfg, summary, rc, *, failure=None):
    out=Path(out);ret=out/'ret';ret.mkdir(exist_ok=True)
    # The actual journal tree lives in ret; bulky runtime caches and telemetry stay outside it.
    complete=bool(summary and summary.get('complete') and rc==0 and not failure)
    if complete:
        write(ret/'COMPLETE.json',dict(items=summary['completed'],plan_sha256=cfg['plan_sha256'],synthetic=False))
    elif failure:
        write(ret/'FAILED.json',dict(error=failure,no_retry=True))
    if summary:write(ret/'SUMMARY.json',summary)
    identity=read(ret/'metadata/RETURN_ID.json')
    deliver=out/'return';deliver.mkdir(exist_ok=False)
    archive=deliver/'result.tar.gz';expanded=0
    with tarfile.open(archive,'w:gz') as t:
        for p in sorted(ret.rglob('*')):
            if p.is_symlink():raise Refusal('Return cannot contain symlinks')
            if p.is_file():
                expanded+=p.stat().st_size
                if expanded>512*1024**2:raise Refusal('Return expanded size exceeds unpack limit')
                t.add(p,arcname=str(p.relative_to(ret)),recursive=False)
    if archive.stat().st_size>=90_000_000:raise Refusal('Return archive exceeds A4 fetch limit')
    digest=sha(archive)
    receipt=dict(schema='a3',archive=dict(name='result.tar.gz',bytes=archive.stat().st_size,sha256=digest),
        archive_bytes=archive.stat().st_size,archive_sha256=digest,archive_complete=True,
        complete=complete,conflicting_terminal_markers=False,job=identity['job'],
        token=identity['token'],plan_sha256=cfg['plan_sha256'],returncode=rc,
        status='COMPLETE' if complete else 'FAILED',mode='production',synthetic=False,
        execution_backend='trinity-local',orchard_reference_job='172744')
    write(deliver/'EXIT.json',receipt)
    # This is a local receipt, not a claim that a file was uploaded to Orchard's return pool.
    write(deliver/'LOCAL_RETURN.json',dict(archive=str(archive),exit=str(deliver/'EXIT.json'),
        complete=complete,sha256=digest,backend='trinity-local',uploaded=False))
    return dict(archive=str(archive),exit=str(deliver/'EXIT.json'),complete=complete,
                completed=(summary or {}).get('completed',0),sha256=digest)

def new_return_identity(out, cfg):
    number=secrets.randbelow(2**32-1)+1
    identity=dict(token=cfg['token']+format(number,'08x'),job=str(number),
                  execution_backend='trinity-local',id_kind='random_local_run_id_not_scheduler_job')
    write(Path(out)/'ret/metadata/RETURN_ID.json',identity)
    return identity
