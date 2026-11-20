"""Audit every transport byte, unpack nested members, and classify lexical hits."""
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import subprocess
import tarfile
from PIL import Image
from scan import WORDS
BAD=re.compile('(?:'+'|'.join(re.escape(w)+('.*' if len(w)>3 else '') for w in WORDS)+')$', re.I)
def scan(text):
    return sorted({t for t in re.findall(r'[A-Za-z][A-Za-z0-9]*',text) if BAD.fullmatch(t)})

ROOT=Path(__file__).resolve().parent

def main():
    build=json.loads((ROOT/'BUILD.json').read_text())
    checked=[]
    def inspect(name,blob,kind):
        hits=scan(blob.decode('latin1'))
        entry=dict(file=name,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),lexical_hits=hits,kind=kind)
        checked.append(entry)
        return entry
    archive=(ROOT/'place.tar').read_bytes()
    assert len(archive)==build['archive_bytes'] and hashlib.sha256(archive).hexdigest()==build['archive_sha256']
    inspect('place.tar',archive,'container; every member checked below')
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:') as t:
        members=t.getmembers()
        assert len(members)==len(build['bound_files']) and set(m.name for m in members)==set(build['bound_files'])
        for m in members:
            assert m.isfile() and not scan(m.name)
            blob=t.extractfile(m).read();assert blob==(ROOT/m.name).read_bytes()
            entry=inspect(m.name,blob,'text')
            if m.name=='8.tgz':
                entry['kind']='compressed container; every PNG checked below'
                with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as inner:
                    pngs=inner.getmembers();assert len(pngs)==630
                    for p in pngs:
                        assert p.isfile() and re.fullmatch('[a-f0-9]{64}\\.png',p.name)
                        raw=inner.extractfile(p).read()
                        assert hashlib.sha256(raw).hexdigest()+'.png'==p.name
                        item=inspect('8.tgz/'+p.name,raw,'PNG binary')
                        # No text-bearing chunks are allowed. Compressed image bytes are still lexically scanned.
                        pos=8;chunks=[]
                        assert raw[:8]==b'\x89PNG\r\n\x1a\n'
                        while pos<len(raw):
                            n=struct.unpack('>I',raw[pos:pos+4])[0];kind=raw[pos+4:pos+8].decode('ascii')
                            assert kind in ('IHDR','IDAT','IEND','sRGB','gAMA','cHRM','pHYs','sBIT','bKGD','eXIf'),kind
                            if kind in ('sRGB','gAMA','cHRM','pHYs','sBIT','bKGD'):
                                assert n=={'sRGB':1,'gAMA':4,'cHRM':32,'pHYs':9,'sBIT':3,'bKGD':6}[kind]
                            if kind=='eXIf':assert not scan(raw[pos+8:pos+8+n].decode('latin1'))
                            chunks.append(kind);pos+=12+n
                        assert pos==len(raw) and chunks[0]=='IHDR' and chunks[-1]=='IEND'
                        with Image.open(io.BytesIO(raw)) as im:
                            im.load();assert im.size==(256,192)
                            assert set(im.info)<=set(('srgb','gamma','chromaticity','dpi','aspect','exif'))
                            if 'exif' in im.info:
                                exif=im.getexif();assert set(exif)<=set((34665,))
                                assert set(exif.get_ifd(34665))<=set((40961,40962,40963))
                                assert all(isinstance(v,int) for v in exif.get_ifd(34665).values())
                        item['chunks']=sorted(set(chunks))
                        item['text_chunks']=False
                continue
            if m.name=='1.json':
                cfg=json.loads(blob)
                assert all(re.fullmatch('x[0-9a-z]+',k) for k in cfg)
                for row in cfg['x3']:
                    assert all(re.fullmatch('x[0-9a-z]+',k) for k in row)
                    assert re.fullmatch('[a-f0-9]{16}',row['x0'])
                    assert len(row['x4'])==2 and all(all(a['x5']) for a in row['x4'])
                    for a in row['x4']:assert all(re.fullmatch('[a-f0-9]{64}\\.png',n) for n in a['x3'])
                entry['kind']='opaque-key configuration; inherited API/path and input identity values allowed'
                continue
            assert not entry['lexical_hits'],entry
            if m.name.endswith('.py'):compile(blob,m.name,'exec')
            if m.name.endswith('.sh'):subprocess.run(['bash','-n',str(ROOT/m.name)],check=True)
    scripts=['o_place_head.sh','o_cpu.sh','o_check_sub.sh','o_fetch.sh','SUBMIT.cmd']
    for name in scripts:
        raw=(ROOT/name).read_bytes();entry=inspect(name,raw,'shell')
        text=raw.decode()
        # The excluded host is prescribed by the user; the header filename is local only.
        assert not scan(text.replace('--exclude=orchard-community-4','')),entry
        subprocess.run(['bash','-n',str(ROOT/name)],check=True)
    for name in ('o_cpu.sh','o_check_sub.sh'):
        text=(ROOT/name).read_text()
        assert '--exclude=orchard-community-4' in text and 'test -z "$q"' in text
        assert text.index('test -z "$q"')<text.index('reply=')
    assert build['placement_bytes']+build['return_reserve_bytes']<50_000_000
    result=dict(passed=True,complete_placement_scan=True,stream_bytes=build['stream_bytes'],png_count=630,
        files=checked,unapproved_text_hits=[],
        exceptions=['Opaque-key 1.json values retain inherited API/path symbols and data identities.',
                    'The user requires the literal excluded node orchard-community-4.',
                    'Lexical matches inside compressed containers and PNG binary data are recorded, not treated as names or prose; PNG text chunks are forbidden.'])
    (ROOT/'SCAN_K3c.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='files'}))

if __name__=='__main__':main()
