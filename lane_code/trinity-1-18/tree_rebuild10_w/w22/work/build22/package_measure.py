from pathlib import Path
import gzip,hashlib,json,re,tarfile,zlib
L=Path(__file__).resolve().parents[2];D=L/'work/build22'
m=json.loads((D/'PACKAGE_MANIFEST.json').read_text())['files']
uploads={r['opaque_name']:Path(r['local_path']) for r in json.loads((D/'UPLOADS.json').read_text())['files']}
records=[];cache={};immutable={};savings=0
for name,v in m.items():
    if v['bytes']<1_000_000:continue
    h=v['sha256']
    if h not in cache:
        p=L/name
        if not p.is_file():p=uploads[name.removeprefix('work/build22/upload/')]
        c=zlib.compressobj(9,zlib.DEFLATED,31);n=0
        with p.open('rb') as f:
            for raw in iter(lambda:f.read(1<<20),b''):n+=len(c.compress(raw))
        n+=len(c.flush());cache[h]=n
    n=cache[h];records.append(dict(name=name,bytes=v['bytes'],compressed=n))
    if re.fullmatch(r'work/build(?:21|22)/upload/u/[a-f0-9]{64}',name):
        if h in immutable:savings+=n
        else:immutable[h]=name
r=dict(large_files=sum(x['compressed'] for x in records),small_input_bytes=sum(v['bytes'] for v in m.values() if v['bytes']<1_000_000),immutable_dedup_savings=savings,files=sorted(records,key=lambda x:x['compressed'],reverse=True))
(D/'PACKAGE_SIZE.json').write_text(json.dumps(r,indent=2)+'\n')
print({k:v for k,v in r.items() if k!='files'})
print(json.dumps(r['files'][:22],indent=2))
