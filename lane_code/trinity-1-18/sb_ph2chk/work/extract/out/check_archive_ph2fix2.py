"""Stream-check every staged member in the final archive without extracting."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def main():
    manifest=OUT/'STAGING_PART2.json';stage=json.loads(manifest.read_text())
    archive=OUT/'sb_ph2fix2.tar';checksum=OUT/'sb_ph2fix2.tar.sha256'
    inventory={r['staged_path']:r for r in stage['inventory']};seen=set();errors=[]
    with tarfile.open(archive,'r|') as tar:
        for m in tar:
            if m.name not in inventory:continue
            r=inventory[m.name];seen.add(m.name)
            if not m.isfile() or m.size!=r['bytes']:
                errors.append(m.name);continue
            h=hashlib.sha256()
            with tar.extractfile(m) as f:
                for b in iter(lambda:f.read(8<<20),b''):h.update(b)
            if h.hexdigest()!=r['sha256']:errors.append(m.name)
    errors += sorted(inventory.keys()-seen)
    assert not errors,errors
    record=dict(status='PASS',verified_files=len(seen),staged_bytes=stage['bytes'],archive_bytes=archive.stat().st_size,
                command='env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 python -B out/check_archive_ph2fix2.py',
                reviewed_archive='PRESERVED: sha256sum -c out/sb_ph2fix.tar.sha256',
                input_sha256={str(manifest):sha(manifest),str(archive):checksum.read_text().split()[0],str(Path(__file__)):sha(Path(__file__)),str(OUT/'reviewed_archive_preserved.log'):sha(OUT/'reviewed_archive_preserved.log')})
    (OUT/'ARCHIVE_PH2FIX2.json').write_text(json.dumps(record,indent=1)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k!='input_sha256'},indent=1))
if __name__=='__main__':main()
