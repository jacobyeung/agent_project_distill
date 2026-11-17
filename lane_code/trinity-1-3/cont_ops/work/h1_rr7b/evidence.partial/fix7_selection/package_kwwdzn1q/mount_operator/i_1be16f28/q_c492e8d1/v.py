
import errno,hashlib,json,os,sys
from pathlib import Path
work=Path(__file__).parent
for prefix in ('/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung',
               '/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung'):
 p=Path(prefix)/'ap/8865619b/u/eb3429c5/a.jsonl.gz'
 assert p.read_bytes()==b'fixture gzip bytes'
 assert os.statvfs(p).f_flag & os.ST_RDONLY
 try:
  with p.open('ab') as f:f.write(b'bad')
 except OSError as exc:assert exc.errno in (errno.EROFS,errno.EACCES)
 else:raise AssertionError('Logical mount is writable')
p=work/'p/u/eb3429c5/a.jsonl.gz'
assert os.statvfs(p).f_flag & os.ST_RDONLY
try:
 with p.open('ab') as f:f.write(b'bad')
except OSError as exc:assert exc.errno in (errno.EROFS,errno.EACCES)
else:raise AssertionError('Staging alias is writable')
output=work/'o';output.mkdir();data=b'TEST_ONLY mount probe\n'
(output/'r.json').write_bytes(data)
(output/'q.json').write_text(json.dumps(dict(status='EQUAL',regenerated=True,
 selection_sha256=hashlib.sha256(data).hexdigest(),TEST_ONLY='mount probe, no selection')))
