exec /usr/bin/python3 -I -s -B -c 'import hashlib,io,json,os,sys,tarfile
from pathlib import Path
os.umask(0o077)
p=Path('"'"'/project/community/jjyeung/ac794e028b16f'"'"')
b=sys.stdin.buffer.read(44687361)
if len(b)!=44687360 or hashlib.sha256(b).hexdigest()!='"'"'68ad7e8f901e0409ca52a92421b5598dd81fdcd753e1ad6c4443a6834e115855'"'"':raise ValueError('"'"'E40'"'"')
with tarfile.open(fileobj=io.BytesIO(b),mode='"'"'r:'"'"') as t:
    members=t.getmembers()
    if len(members)!=6 or set(m.name for m in members)!={'"'"'3.json'"'"', '"'"'1.json'"'"', '"'"'BATCH.sh'"'"', '"'"'2.py'"'"', '"'"'8.tgz'"'"', '"'"'0.py'"'"'} or any(not m.isfile() for m in members):raise ValueError('"'"'E41'"'"')
    data={m.name:t.extractfile(m).read() for m in members}
if sum(map(len,data.values()))>=45500000:raise ValueError('"'"'E42'"'"')
for n,h in json.loads(data['"'"'3.json'"'"']).items():
    if hashlib.sha256(data[n]).hexdigest()!=h:raise ValueError('"'"'E43'"'"')
p.mkdir(mode=0o700)
for n,b in data.items():
    with (p/n).open('"'"'xb'"'"') as f:f.write(b)
print(sum(map(len,data.values())))
'
