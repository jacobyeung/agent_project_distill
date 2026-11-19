from pathlib import Path
import hashlib
import tarfile
import time

out=Path('/scratch/jjyeung/orch_n30/so_syncfix/out')
excluded={'SHA256SUMS','so_syncfix_bundle.tar.gz','so_syncfix_bundle.tar.gz.sha256'}
paths=sorted(p for p in out.rglob('*') if p.is_file() and str(p.relative_to(out)) not in excluded)
(out/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(out))+'\n' for p in paths))
archive=out/'so_syncfix_bundle.tar.gz'
with tarfile.open(str(archive),'w:gz') as stream:
    directory=tarfile.TarInfo('so_syncfix')
    directory.type=tarfile.DIRTYPE
    directory.mode=0o755
    directory.mtime=int(time.time())
    stream.addfile(directory)
    for p in paths+[out/'SHA256SUMS']:
        stream.add(str(p),arcname='so_syncfix/'+str(p.relative_to(out)),recursive=False)
digest=hashlib.sha256(archive.read_bytes()).hexdigest()
(out/'so_syncfix_bundle.tar.gz.sha256').write_text(digest+'  so_syncfix_bundle.tar.gz\n')
print('BUNDLE files=%d bytes=%d sha256=%s'%(len(paths),archive.stat().st_size,digest))
