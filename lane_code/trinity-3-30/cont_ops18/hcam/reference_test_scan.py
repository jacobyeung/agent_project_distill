"""Streaming fixture reused verbatim from E test_e.py."""
import io,json,tarfile,hashlib
sha=lambda b:hashlib.sha256(b).hexdigest()
from test_place_h import rejects
def test_scan(fill,w):
    data=b'weights';heads=b'heads';index=b'{}'
    artifact=dict(heads={'sha256':sha(heads)},full_weights={'sha256':''})
    full=dict(schema='full-ft-export-v1',dtype='bfloat16',files=[dict(name='weights',sha256=sha(data),bytes=len(data))],index=dict(name='index',sha256=sha(index)))
    fullraw=json.dumps(full).encode();artifact['full_weights']['sha256']=sha(fullraw)
    files={'m200/artifact.json':json.dumps(artifact).encode(),'m200/heads.pt':heads,'m200/full_weights/full_weights.json':fullraw,
           'm200/full_weights/weights':data,'m200/full_weights/index':index}
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w') as t:
        for n,d in sorted(files.items()):
            m=tarfile.TarInfo(n);m.size=len(d);t.addfile(m,io.BytesIO(d))
    raw=buf.getvalue();paths=[]
    for i in range(4):
        path=w/('part%d'%i);path.write_bytes(raw[i*len(raw)//4:(i+1)*len(raw)//4]);paths.append(path)
    done=w/'tiny.done';done.write_text('tiny %d %s\n'%(len(raw),sha(raw)))
    export,art,archive=fill.scan(paths,done,'tiny')
    assert archive['sha256']==sha(raw) and len(archive['parts'])==4
    assert [p['sha256'] for p in archive['parts']]==[sha(p.read_bytes()) for p in paths]
    done.write_text('tiny %d %s\n'%(len(raw),'0'*64));rejects(lambda:fill.scan(paths,done,'tiny'))
    return dict(parts=4,whole_hash_verified=True,bad_whole_hash_rejected=True,per_part_hashes_computed=True)

