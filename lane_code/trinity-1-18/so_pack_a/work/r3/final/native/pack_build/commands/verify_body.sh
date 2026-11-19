#!/bin/bash
set -euo pipefail
umask 077
export PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung CUDA_VISIBLE_DEVICES=
trap 'rc=$?; if [ "$rc" != 0 ]; then printf "phase exit %s line %s\n" "$rc" "$LINENO" >&2; fi' EXIT
cd /project/community/jjyeung/okh7/a15_cot_apb123456789abc
trap 'rc=$?; if [ "$rc" != 0 ]; then printf "%s\n" "$rc" >v/0.exit; fi' EXIT
/usr/bin/python3 -I -s -B - <<'PYCODE'
import hashlib,json,os,stat,tarfile
from pathlib import Path
def stamp(p):
 s=p.stat()
 if not stat.S_ISREG(s.st_mode):raise ValueError('Export part is not a regular file: '+str(p))
 return dict(bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,device=s.st_dev,inode=s.st_ino)
def header(path,member):
 with Path(path).open('rb') as stream:raw=stream.read(512)
 entry=tarfile.TarInfo.frombuf(raw,'utf-8','strict')
 name=entry.name.rstrip('/')
 if name!=member and not name.startswith(member+'/'):raise ValueError('Export tar member differs: '+name)
 if '..' in name.split('/') or entry.type not in (tarfile.REGTYPE,tarfile.AREGTYPE,tarfile.DIRTYPE):raise ValueError('Unsupported export tar header')
os.umask(0o077)
p=Path('/project/community/jjyeung/okh7/a15_cot_apb123456789abc')/'v';identity={'done': ['q8/8865619b/673bc60f_m200.tar', '21583032320', '795ef9ef7e59bf37443c14a4d3a7e734eabcb2fd5fcb289ad3d77ae7096e283b'], 'preparation': {'/project/community/jjyeung/okh7/eabcdef012345/10': '3b0051c4a9cc661d02019a645165fc3e23d658d2f24a6fd6fd86ec7877ba4fc1', '/project/community/jjyeung/okh7/eabcdef012345/11': '4c0dd9d6e4535a2945ed58754c1cdd5e9a316067be35f2e8440caa9a80e1c915', '/project/community/jjyeung/okh7/eabcdef012345/12': '7f654d2f0ae9f06083f2fc8fd793512c154b4d01ce8632fb733d4191205af770'}, 'parts': [{'path': '/project/community/jjyeung/okh7/eabcdef012345/5', 'bytes': 5395758080, 'sha256': '54c5c16ae8100ec501b2c6e650efa998a488db05afb7c9a4341defb9593730cf'}, {'path': '/project/community/jjyeung/okh7/eabcdef012345/6', 'bytes': 5395758080, 'sha256': '028aaee51b02d1265cc05d3ab2057625a14a4178429f1e2840301b1e77cc299a'}, {'path': '/project/community/jjyeung/okh7/eabcdef012345/7', 'bytes': 5395758080, 'sha256': '500f0643c46e7511e66e553766dcff4c6836ae02c997c6abbc51cc36cdffa9b2'}, {'path': '/project/community/jjyeung/okh7/eabcdef012345/8', 'bytes': 5395758080, 'sha256': '67988559d896dc33363066b6c89d3cb17479e6c8c93f11f978013f7d4a647dc8'}], 'member_directory': 'm200'}
header(identity['parts'][0]['path'],identity['member_directory'])
rows=[]
for pin in identity['parts']:
 path=Path(pin['path']);before=stamp(path)
 if before['bytes']!=pin['bytes']:raise ValueError('Export part size differs: '+str(path))
 h=hashlib.sha256()
 with path.open('rb') as stream:
  opened=os.fstat(stream.fileno())
  if (opened.st_dev,opened.st_ino)!=(before['device'],before['inode']):raise ValueError('Export part changed before hashing')
  for chunk in iter(lambda:stream.read(1024**2),b''):h.update(chunk)
 if stamp(path)!=before:raise ValueError('Export part changed during hashing: '+str(path))
 if h.hexdigest()!=pin['sha256']:raise ValueError('Export part sha256 differs: '+str(path))
 rows.append(dict(before,path=str(path),sha256=h.hexdigest()))
for row in rows:
 if any(row[k]!=v for k,v in stamp(Path(row['path'])).items()):raise ValueError('Export part changed after hashing')
receipt=dict(schema=1,parts=rows)
with (p/'0.json').open('x') as stream:
 json.dump(receipt,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())
with (p/'0.txt').open('x') as stream:stream.write('0\n')
print('verified')

PYCODE
