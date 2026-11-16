"""Salt refute check on shipped tars (read-only). Reads the Trinity secret only to test its absence; prints only counts."""
import base64,gzip,hashlib,hmac,io,json,re,sys,tarfile
from pathlib import Path
B=Path('/scratch/jjyeung/orch_n30/b07_offread/builds')
SHIPS={'N':B/'N/out/code.tar','vsi':B/'R/out/package_vsi.tar','revsi':B/'R/out/package_revsi.tar'}
sec_hex=Path('/scratch/jjyeung/orch_n30/b07_offread/work/salt/SECRET').read_text().strip()
sec=bytes.fromhex(sec_hex)
needles=[sec,sec_hex.lower().encode(),sec_hex.upper().encode(),base64.b64encode(sec),base64.b64encode(sec).rstrip(b'='),
         base64.urlsafe_b64encode(sec).rstrip(b'='),hashlib.sha256(sec).hexdigest().encode()[:0] or b'\x00'*0]
needles=[n for n in needles if n]
src=(B/'R/kit/xnames.py').read_text().split('# Build processes share one pinned map')[0]
ns={};exec(compile(src,'xn','exec'),ns);WORDS=ns['WORDS']
names=set(WORDS)
for m in (B/'R/out/NAME_MAP.json',B/'N/out/NAME_MAP.json',B/'R/out/R2_NAME_MAP.json',B/'N/out/N4_CODE_NAME_MAP.json'):
    try:d=json.loads(m.read_text())
    except Exception:continue
    if isinstance(d,dict):
        for k in d:
            names.add(k);names.update(k.split('/'));names.add(k+'.py')
extra=['vsibench','vsi-bench','vsibench5130','revsi999t32','arkitscenes','scannet','scannetpp','matterport','qwen','qwen2.5','jyeung','jjyeung','av_dataengine_cot','distillation','split','reader','official_adapter']
names.update(extra);names.update(w.upper() for w in list(WORDS));names.update(w.capitalize() for w in list(WORDS))
unsalted={hashlib.sha256(n.encode()).hexdigest() for n in names}
tables=[];members=0;hits=[]
def walk(raw,label,depth=0):
    global members
    if raw[:2]==b'\x1f\x8b':
        try:raw=gzip.decompress(raw)
        except Exception:pass
    for n in needles:
        if n in raw:hits.append(label)
    if len(raw)>262 and raw[257:262]==b'ustar':
        with tarfile.open(fileobj=io.BytesIO(raw)) as tf:
            for m in tf:
                members+=1
                if not m.isfile():continue
                v=tf.extractfile(m).read()
                if m.name.endswith('x0.json') or m.name=='x0.json':tables.append((label+'!'+m.name,v))
                walk(v,label+'!'+m.name,depth+1)
    else:
        # hex-embedded bundles (batch scripts) and zlib bodies
        for mt in re.finditer(rb'[0-9a-f ]{2000,}',raw):
            try:inner=bytes.fromhex(mt[0].decode().replace(' ',''))
            except ValueError:continue
            walk(inner,label+'!hex',depth+1)
        if raw[:1]==b'\x78':
            import zlib
            try:walk(zlib.decompress(raw),label+'!zlib',depth+1)
            except Exception:pass
for k,p in SHIPS.items():walk(p.read_bytes(),k)
out={'members_scanned':members,'secret_hits':hits,'dictionary':len(names),'tables':[]}
salts=[]
for label,v in tables:
    t=json.loads(v);salt=t.get('salt');salts.append(salt)
    keys=set(t.get('tokens',{}))|set(t.get('aliases',{}))
    sb=bytes.fromhex(salt)
    salted={hashlib.sha256(sb+n.encode()).hexdigest() for n in names}
    out['tables'].append(dict(table=label,salt_ok=bool(re.fullmatch('[0-9a-f]{64}',salt or '')),keys=len(keys),
        unsalted_hits=len(keys&unsalted),salted_guess_hits=len(keys&salted),
        salt_not_trivial=salt not in {hashlib.sha256(b'').hexdigest(),hmac.new(bytes.fromhex('37'*32),b'',hashlib.sha256).hexdigest()}))
out['distinct_salts']=len(set(salts));out['n_tables']=len(salts)
print(json.dumps(out,indent=1))
