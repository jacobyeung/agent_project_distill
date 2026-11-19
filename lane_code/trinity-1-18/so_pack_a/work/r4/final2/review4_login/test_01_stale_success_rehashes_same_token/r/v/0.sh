#!/bin/bash
set -euo pipefail
umask 077
export PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung CUDA_VISIBLE_DEVICES=
trap 'rc=$?; if [ "$rc" != 0 ]; then printf "phase exit %s line %s\n" "$rc" "$LINENO" >&2; fi' EXIT
cd /scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review4_login/test_01_stale_success_rehashes_same_token/r
trap 'rc=$?; if [ "$rc" != 0 ]; then printf "%s\n" "$rc" >v/0.exit; fi' EXIT
/usr/bin/python3 -I -s -B - <<'PYCODE'
import hashlib,json,os,stat,tarfile
from pathlib import Path,PurePosixPath
def stamp(p):
 s=p.stat()
 if not stat.S_ISREG(s.st_mode):raise ValueError('Export part is not a regular file: '+str(p))
 return dict(bytes=s.st_size,mtime_ns=s.st_mtime_ns)
def snapshot(p):
 s=p.stat()
 return dict(stamp(p),ctime_ns=s.st_ctime_ns,device=s.st_dev,inode=s.st_ino)
def header(path,member):
 with Path(path).open('rb') as stream:raw=stream.read(512)
 entry=tarfile.TarInfo.frombuf(raw,'utf-8','strict')
 name=str(PurePosixPath(entry.name))
 if name!=member and not name.startswith(member+'/'):raise ValueError('Export tar member differs: '+name)
 if '..' in name.split('/') or entry.type not in (tarfile.REGTYPE,tarfile.AREGTYPE,tarfile.DIRTYPE):raise ValueError('Unsupported export tar header')
os.umask(0o077)
p=Path('/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review4_login/test_01_stale_success_rehashes_same_token/r')/'v';identity={'done': ['q8/abcdef01/abcdef01_m600.tar', '10240', '66c54757eeb20cff80e1f36aba368ed7844dd9e04555f999af157d886c8dfb92'], 'preparation': {'/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m10': '4ead362c4ff4cba3b997d37b18aa536b1d0835bab4d8c55a0b3f8ca2450c8228', '/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m11': 'e4be4c3ff8020a71bb95ccd86a4924f30ca14f875448c0b2fdc4f8f188ce4e68', '/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m12': 'd7b75752533f616d18404b5b55c2dd42a0ba31cc2e16906944d3d6030bbbc2fe'}, 'parts': [{'path': '/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review4_login/test_01_stale_success_rehashes_same_token/0', 'bytes': 2560, 'sha256': '15030f0511d81015f413be86a87491f73564be2ff08f79f752241d4f1e514dc0'}, {'path': '/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review4_login/test_01_stale_success_rehashes_same_token/1', 'bytes': 2560, 'sha256': '9f4c5aa51e0d3aa9569bc4d72256f5e5b020e97a7cbb92fee53ddc5c34acfbe2'}, {'path': '/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review4_login/test_01_stale_success_rehashes_same_token/2', 'bytes': 2560, 'sha256': '1d7dc022d0cf79c208941879d7c51c8cbc293d0e9552e364f53f6a422dfa3448'}, {'path': '/scratch/jjyeung/orch_n30/so_pack_a/work/r4/final2/review4_login/test_01_stale_success_rehashes_same_token/3', 'bytes': 2560, 'sha256': '8ce8ba8e726ee8925e6560d86ac35be1097691d1cfac888e6bd20e804ea9eb15'}], 'member_directory': 'm600'}
header(identity['parts'][0]['path'],identity['member_directory'])
rows=[]
for pin in identity['parts']:
 path=Path(pin['path']);before=snapshot(path)
 if before['bytes']!=pin['bytes']:raise ValueError('Export part size differs: '+str(path))
 h=hashlib.sha256()
 with path.open('rb') as stream:
  opened=os.fstat(stream.fileno())
  if (opened.st_dev,opened.st_ino)!=(before['device'],before['inode']):raise ValueError('Export part changed before hashing')
  for chunk in iter(lambda:stream.read(1024**2),b''):h.update(chunk)
 if snapshot(path)!=before:raise ValueError('Export part changed during hashing: '+str(path))
 if h.hexdigest()!=pin['sha256']:raise ValueError('Export part sha256 differs: '+str(path))
 rows.append(dict(before,path=pin['path'],sha256=h.hexdigest()))
for row in rows:
 if any(row[k]!=v for k,v in snapshot(Path(row['path'])).items()):raise ValueError('Export part changed after hashing')
receipt=dict(schema=1,parts=[{k:row[k] for k in ('path','bytes','mtime_ns','sha256')} for row in rows])
with (p/'0.json').open('x') as stream:
 json.dump(receipt,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())
with (p/'0.txt').open('x') as stream:stream.write('0\n')
print('verified')

PYCODE
