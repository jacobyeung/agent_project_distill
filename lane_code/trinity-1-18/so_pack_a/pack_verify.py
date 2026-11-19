"""Generated Python 3.6 verification; receipts never authorize changed inputs."""
COMMON = '''import hashlib,json,os,stat,tarfile
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
'''

def verify_code(root, identity):
    return COMMON+'''os.umask(0o077)
p=Path(%r)/'v';identity=%r
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
with (p/'0.txt').open('x') as stream:stream.write('0\\n')
print('verified')
''' % (root, identity)

def preflight_code(root, identity):
    # Keep a standalone snippet so no pack module is needed on Orchard.
    return COMMON+'''p=Path(%r)/'v';identity=%r
if not (p/'0.txt').is_file() or not (p/'0.json').is_file():raise ValueError('Export verification receipt missing; run verify before place')
if (p/'0.txt').read_text()!='0\\n':raise ValueError('Export verification incomplete')
if (p/'0.json').stat().st_size>16384:raise ValueError('Export verification receipt too large')
receipt=json.loads((p/'0.json').read_text())
if receipt.get('schema')!=1 or len(receipt.get('parts',[]))!=4:raise ValueError('Export verification receipt invalid')
for row,pin in zip(receipt['parts'],identity['parts']):
 if any(row.get(k)!=pin[k] for k in ('path','bytes','sha256')):raise ValueError('Export verification receipt differs from binding')
 if any(row.get(k)!=v for k,v in stamp(Path(pin['path'])).items()):raise ValueError('Export verification receipt is stale: '+pin['path'])
header(identity['parts'][0]['path'],identity['member_directory'])
''' % (root, identity)
