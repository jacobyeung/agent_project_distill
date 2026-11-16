"""Independent stdlib recomputation from real NPY rotations; not wrapper execution."""
import ast, hashlib, json, math, statistics, struct, zipfile
from pathlib import Path
B=Path(__file__).resolve().parents[1]
W=B.parents[1]/'work'
manifest=json.loads((W/'p9/native/geometry/GEOMETRY_MANIFEST.json').read_text())

def array(path,member):
    with zipfile.ZipFile(str(path)) as archive:data=archive.read(member+'.npy')
    assert data[:6]==b'\x93NUMPY'
    major=data[6]
    n=struct.unpack('<H' if major==1 else '<I',data[8:10] if major==1 else data[8:12])[0]
    offset=10 if major==1 else 12
    h=ast.literal_eval(data[offset:offset+n].decode('latin1').strip())
    assert not h['fortran_order'] and h['descr'] in ('<f8','<f4')
    body=data[offset+n:]
    values=struct.unpack('<'+('d' if h['descr']=='<f8' else 'f')*(len(body)//(8 if h['descr']=='<f8' else 4)),body)
    return h['shape'],values

records=[]
for record in manifest['records']:
    p=W/'p9/native/geometry'/(record['clip']+'.npz')
    data=p.read_bytes()
    assert hashlib.sha256(data).hexdigest()==record['output']['sha256']
    shape,flat=array(p,'camera_to_world')
    assert shape==(32,4,4)
    plane=[math.hypot(flat[i*16+8],flat[i*16+9]) for i in range(32)]
    margin=[-flat[i*16+9] for i in range(32)]
    usable=[margin[i]/plane[i] for i in range(32) if plane[i]>=.3]
    reviewed=margin[0]<=0 if plane[0]>=.3 else bool(usable) and statistics.median(usable)<=0
    sealed=margin[0]<=0
    assert sealed==(record['status']=='REFUSED')
    records.append(dict(native=record['native'],source=str(p),sha256=hashlib.sha256(data).hexdigest(),
                        sealed_refused=sealed,reviewed_refused=reviewed,
                        reference_plane=plane[0],reference_margin=margin[0],
                        usable_frames=len(usable),median_usable=statistics.median(usable) if usable else None))
value=dict(evidence='Independent stdlib arithmetic on real camera_to_world arrays; production guard not executed',
    captures=len(records),sealed_refused=[r['native'] for r in records if r['sealed_refused']],
    reviewed_refused=[r['native'] for r in records if r['reviewed_refused']],records=records)
(B/'out/GUARD_CENSUS.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({k:v for k,v in value.items() if k!='records'}))
