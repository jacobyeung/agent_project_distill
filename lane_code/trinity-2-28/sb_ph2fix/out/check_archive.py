"""Check that the archive includes every staged file at its declared size and pinned controls."""
import hashlib
import json
from pathlib import Path
import tarfile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    manifest=OUT/'STAGING_PART2.json'
    stage=json.loads(manifest.read_text())
    archive=OUT/'sb_ph2fix.tar'
    checksum=OUT/'sb_ph2fix.tar.sha256'
    errors=[]
    with tarfile.open(archive,'r:') as tar:
        members={m.name:m for m in tar.getmembers()}
        for row in stage['inventory']:
            member=members.get(row['staged_path'])
            if not member or not member.isfile() or member.size!=row['bytes']:
                errors.append(row['staged_path']);continue
            if 'control' in row['roles']:
                with tar.extractfile(member) as f:
                    if hashlib.sha256(f.read()).hexdigest()!=row['sha256']: errors.append(row['staged_path'])
    record=dict(status='PASS' if not errors else 'FAIL',staged_files=len(stage['inventory']),archive_bytes=archive.stat().st_size,
                missing_or_changed=errors,command='env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 python -B out/check_archive.py',
                input_sha256={str(manifest):sha(manifest),str(archive):checksum.read_text().split()[0],str(checksum):sha(checksum),str(Path(__file__)):sha(Path(__file__))})
    (OUT/'ARCHIVE_VALIDATION.json').write_text(json.dumps(record,indent=1)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k!='input_sha256'},indent=1))
    if errors: raise SystemExit(1)

if __name__=='__main__':main()
