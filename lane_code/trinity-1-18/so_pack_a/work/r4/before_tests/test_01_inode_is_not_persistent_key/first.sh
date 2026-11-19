#!/bin/bash
set -euo pipefail
umask 077
export PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung CUDA_VISIBLE_DEVICES=
trap 'rc=$?; if [ "$rc" != 0 ]; then printf "phase exit %s line %s\n" "$rc" "$LINENO" >&2; fi' EXIT
/usr/bin/python3 -I -s -B - <<'PYCODE'
import os
from pathlib import Path
p=Path('/scratch/jjyeung/orch_n30/so_pack_a/work/r4/before_tests/test_01_inode_is_not_persistent_key/r')
p.mkdir(mode=0o700,exist_ok=True)
assert not p.is_symlink() and p.stat().st_uid==os.getuid() and not p.stat().st_mode & 0o077
assert {x.name for x in p.iterdir()}<={'v'}, 'Verify cannot run after placement'
v=p/'v'
try:v.mkdir(mode=0o700)
except FileExistsError:
 assert not v.is_symlink() and v.is_dir() and not v.stat().st_mode & 0o077
 failed=v/'0.exit'
 assert failed.is_file() and not failed.is_symlink() and failed.stat().st_size<16 and not (v/'0.txt').exists(), 'Verification active, successful or uncertain; do not relaunch'
 assert 0<int(failed.read_text())<256, 'Invalid verification failure receipt'
 archive=v/os.urandom(8).hex();archive.mkdir(mode=0o700)
 failed.rename(archive/'0.exit')
 for name in ('0.sh','0.log','0.json'):
  old=v/name
  if old.exists():
   assert not old.is_symlink() and old.is_file()
   old.rename(archive/name)
(v/'0.sh').write_text('#!/bin/bash\nset -euo pipefail\numask 077\nexport PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung CUDA_VISIBLE_DEVICES=\ntrap \'rc=$?; if [ "$rc" != 0 ]; then printf "phase exit %s line %s\\n" "$rc" "$LINENO" >&2; fi\' EXIT\ncd /scratch/jjyeung/orch_n30/so_pack_a/work/r4/before_tests/test_01_inode_is_not_persistent_key/r\ntrap \'rc=$?; if [ "$rc" != 0 ]; then printf "%s\\n" "$rc" >v/0.exit; fi\' EXIT\n/usr/bin/python3 -I -s -B - <<\'PYCODE\'\nimport hashlib,json,os,stat,tarfile\nfrom pathlib import Path\ndef stamp(p):\n s=p.stat()\n if not stat.S_ISREG(s.st_mode):raise ValueError(\'Export part is not a regular file: \'+str(p))\n return dict(bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,device=s.st_dev,inode=s.st_ino)\ndef header(path,member):\n with Path(path).open(\'rb\') as stream:raw=stream.read(512)\n entry=tarfile.TarInfo.frombuf(raw,\'utf-8\',\'strict\')\n name=entry.name.rstrip(\'/\')\n if name!=member and not name.startswith(member+\'/\'):raise ValueError(\'Export tar member differs: \'+name)\n if \'..\' in name.split(\'/\') or entry.type not in (tarfile.REGTYPE,tarfile.AREGTYPE,tarfile.DIRTYPE):raise ValueError(\'Unsupported export tar header\')\nos.umask(0o077)\np=Path(\'/scratch/jjyeung/orch_n30/so_pack_a/work/r4/before_tests/test_01_inode_is_not_persistent_key/r\')/\'v\';identity={\'done\': [\'q8/abcdef01/abcdef01_m600.tar\', \'10240\', \'66c54757eeb20cff80e1f36aba368ed7844dd9e04555f999af157d886c8dfb92\'], \'preparation\': {\'/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m10\': \'4ead362c4ff4cba3b997d37b18aa536b1d0835bab4d8c55a0b3f8ca2450c8228\', \'/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m11\': \'e4be4c3ff8020a71bb95ccd86a4924f30ca14f875448c0b2fdc4f8f188ce4e68\', \'/scratch/jjyeung/orch_n30/so_pack_a/work/r2/fixture/m12\': \'d7b75752533f616d18404b5b55c2dd42a0ba31cc2e16906944d3d6030bbbc2fe\'}, \'parts\': [{\'path\': \'/scratch/jjyeung/orch_n30/so_pack_a/work/r4/before_tests/test_01_inode_is_not_persistent_key/0\', \'bytes\': 2560, \'sha256\': \'15030f0511d81015f413be86a87491f73564be2ff08f79f752241d4f1e514dc0\'}, {\'path\': \'/scratch/jjyeung/orch_n30/so_pack_a/work/r4/before_tests/test_01_inode_is_not_persistent_key/1\', \'bytes\': 2560, \'sha256\': \'9f4c5aa51e0d3aa9569bc4d72256f5e5b020e97a7cbb92fee53ddc5c34acfbe2\'}, {\'path\': \'/scratch/jjyeung/orch_n30/so_pack_a/work/r4/before_tests/test_01_inode_is_not_persistent_key/2\', \'bytes\': 2560, \'sha256\': \'1d7dc022d0cf79c208941879d7c51c8cbc293d0e9552e364f53f6a422dfa3448\'}, {\'path\': \'/scratch/jjyeung/orch_n30/so_pack_a/work/r4/before_tests/test_01_inode_is_not_persistent_key/3\', \'bytes\': 2560, \'sha256\': \'8ce8ba8e726ee8925e6560d86ac35be1097691d1cfac888e6bd20e804ea9eb15\'}], \'member_directory\': \'m600\'}\nheader(identity[\'parts\'][0][\'path\'],identity[\'member_directory\'])\nrows=[]\nfor pin in identity[\'parts\']:\n path=Path(pin[\'path\']);before=stamp(path)\n if before[\'bytes\']!=pin[\'bytes\']:raise ValueError(\'Export part size differs: \'+str(path))\n h=hashlib.sha256()\n with path.open(\'rb\') as stream:\n  opened=os.fstat(stream.fileno())\n  if (opened.st_dev,opened.st_ino)!=(before[\'device\'],before[\'inode\']):raise ValueError(\'Export part changed before hashing\')\n  for chunk in iter(lambda:stream.read(1024**2),b\'\'):h.update(chunk)\n if stamp(path)!=before:raise ValueError(\'Export part changed during hashing: \'+str(path))\n if h.hexdigest()!=pin[\'sha256\']:raise ValueError(\'Export part sha256 differs: \'+str(path))\n rows.append(dict(before,path=str(path),sha256=h.hexdigest()))\nfor row in rows:\n if any(row[k]!=v for k,v in stamp(Path(row[\'path\'])).items()):raise ValueError(\'Export part changed after hashing\')\nreceipt=dict(schema=1,parts=rows)\nwith (p/\'0.json\').open(\'x\') as stream:\n json.dump(receipt,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())\nwith (p/\'0.txt\').open(\'x\') as stream:stream.write(\'0\\n\')\nprint(\'verified\')\n\nPYCODE\n')

PYCODE
cd /scratch/jjyeung/orch_n30/so_pack_a/work/r4/before_tests/test_01_inode_is_not_persistent_key/r
setsid nohup bash v/0.sh </dev/null >v/0.log 2>&1 &
