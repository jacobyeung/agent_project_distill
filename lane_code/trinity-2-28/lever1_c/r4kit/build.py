"""Deterministic local builder. Never places, submits, or opens a network connection."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parent
import importlib.util
_spec=importlib.util.spec_from_file_location('a_storage',ROOT/'src/storage.py')
storage=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(storage)
BASE = ROOT/'in/D400'
SRC = BASE/'src'
DENY = 'split vsi revsi scannet arkit sam g3t depth distill qwen ground dev bench mask tower reader student teacher k1 t1 word template'.split()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def jd(obj):
    return (json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def pin(raw):
    return dict(bytes=len(raw), sha256=digest(raw))


def archive(files):
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode='wb', mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode='w', format=tarfile.USTAR_FORMAT) as t:
            for name, raw in sorted(files.items()):
                m = tarfile.TarInfo(name); m.size=len(raw); m.mode=0o600; m.mtime=0
                t.addfile(m, io.BytesIO(raw))
    return out.getvalue()


def wrap(raw):
    return ('exec(compile(bytes.fromhex('+repr(raw.hex())+'),__file__,"exec"))\n').encode()


def inputs():
    manifest = json.loads((SRC/'items/dist580.json').read_text())
    captures = json.loads((SRC/'inputs/room_captures.json').read_text())['captures']
    ids = set(manifest['sets']['R0-dev-twin'])
    selected = sorted((r for r in manifest['items'] if r['id'] in ids),key=lambda r:r['id'])
    assert len(selected)==290
    rooms = sorted({r['room_key'] for r in selected})
    rmap = {r:digest(r.encode())[:24] for r in rooms}
    assert len(set(rmap.values()))==98
    rows=[]; cs={}; mapping=[]
    for r in selected:
        i=digest(r['id'].encode())[:24]; room=rmap[r['room_key']]
        q=r['question']; assert q.count('the distance between')==1 and r['unit']=='m'
        assert q.startswith('Measuring from the closest point of each object, what is the distance between the ')
        assert q.endswith(' (in meters)?')
        c=captures[r['native']]
        assert r['frame_paths']==[f['path'] for f in c['frames']]
        cs[room]={k:c[k] for k in ('anchor_indices','anchor_slots','fps','frames','timestamps','total_num_frames')}
        for arm in (0,1):
            rows.append(dict(i=i,r=room,a=arm,q=q if arm==0 else q.replace('the distance between','the direct distance between')))
        mapping.append(dict(i=i,r=room,source_id=r['id'],source_room=r['room_key']))
    return dict(rows=rows,captures=cs),mapping


def build():
    frozen=(ROOT/'FROZEN.json').read_bytes(); f=json.loads(frozen)
    assert digest(frozen)==(ROOT/'FROZEN.sha256').read_text().split()[0]
    for name,h in f['sources'].items():
        assert digest((ROOT/name).read_bytes())==h
    data,mapping=inputs()
    token='d93a17be024f5'
    package='/project/community/jjyeung/okh7/a15_cot_ap'+token
    base_inputs=json.loads((BASE/'package/a/1.json').read_text())
    # Geometry's dedicated archive is not needed. The shared environment archive
    # stays pinned; neither external component is instantiated or served.
    ins={k:base_inputs[k] for k in ('archives','env_roots','python','frames_root')}
    ins['archives']=[a for i,a in enumerate(ins['archives']) if i!=1]
    ins['files']={k:base_inputs['files'][k] for k in ('artifact','heads','full_weights','base_config','original_model')}
    assets=json.loads((SRC/'orchard_h10/vendor/ORCHARD_ASSETS.json').read_text())
    assets={k:assets[k] for k in ('groups','bwrap_pin')}
    cfg=dict(token=token,package=package,frozen=digest(frozen),logical='/scratch/jjyeung/b01ec87a6f29b',
             inputs=ins,assets=assets,export=json.loads((BASE/'package/a/export.json').read_text()))
    # Only source code travels. No task files, fixture rows, result journals,
    # source item manifests, preparation receipts or answer banks are bundled.
    sources={}
    for p in sorted((SRC/'tree').rglob('*.py')):
        rel=p.relative_to(SRC)
        if set(rel.parts)&{'tests','tools','verifykit'}:
            continue
        sources['c/'+str(rel)]=p.read_text()
    for p in sorted((SRC/'b').rglob('*.py')):
        if 'tests' not in p.parts:
            sources['c/'+str(p.relative_to(SRC))]=p.read_text()
    p=SRC/'tree/trace_format/vsi_scannet_vocab.json'
    sources['c/'+str(p.relative_to(SRC))]=p.read_text()
    for p in sorted((SRC/'orchard_h10/vendor').glob('*.py')):
        sources['v/'+p.name]=p.read_text()
    # Authenticate full archives, but materialize only admitted inputs. Native
    # third-party runtime/model assets retain their required wire representation.
    n='v/orchard_stage.py'
    text=sources[n].replace('strip=0, overlay=False):', 'strip=0, overlay=False, retain_roots=None):')
    text=text.replace('            target = destination/str(path)',
        "            if retain_roots is not None and path.parts[0] not in retain_roots:\n                continue\n            target = destination/str(path)")
    text=text.replace("with archive.extractfile(item) as source, target.open('wb' if overlay else 'xb') as output:",
        "with archive.extractfile(item) as source, _output(target, 'wb' if overlay else 'xb', retain_roots is not None and path.parts[0] in ('p0','m400') and target.suffix=='.json' and 'full_weights' not in path.parts) as output:")
    text += "\n@contextmanager\ndef _output(path, mode, encode):\n    if not encode:\n        with path.open(mode) as f: yield f\n    else:\n        import io\n        with io.BytesIO() as f:\n            yield f\n            path.write_text(json.dumps({'a0':f.getvalue().hex()})+'\\n')\n"
    sources[n]=text
    source_blob=storage.pack(jd(sources))
    payload={'1.json':storage.pack(jd(data)),'2.json':storage.pack(jd(cfg)),'6.json':b'{}\n',
             '9.py':wrap((ROOT/'src/storage.py').read_bytes()),
             '10.py':wrap((ROOT/'src/batch.py').read_bytes()),
             '5.py':wrap((ROOT/'src/runtime.py').read_bytes()),
             '7.py':wrap((ROOT/'src/probe.py').read_bytes()),'8.bin':source_blob}
    files=dict(payload)
    files['0.tgz']=archive(payload)
    files['3.py']=wrap((ROOT/'src/control.py').read_bytes())
    files['4.sh']=('#!/bin/bash\nset -eu\nexec /usr/bin/python3 -I -s -B '+package+'/3.py work\n').encode()
    files['0.json']=jd(dict(files={n:pin(raw) for n,raw in sorted(files.items())},frozen=digest(frozen)))
    for name,raw in files.items():
        assert not any(x in name.lower() for x in DENY),name
        if name.endswith(('.py','.sh')):
            assert not any(x in raw.decode().lower() for x in DENY),name
    delivery=archive(files)
    out=ROOT/'out';out.mkdir(exist_ok=True)
    (out/'delivery.tgz').write_bytes(delivery)
    (ROOT/'PAIR_MAP.json').write_bytes(jd(mapping))
    (ROOT/'BUILD.json').write_bytes(jd(dict(package=package,token=token,delivery=pin(delivery),
        payload=pin(files['0.tgz']),expanded_delivery_bytes=sum(map(len,files.values())),
        expanded_payload_bytes=sum(map(len,payload.values())),private_source_bytes=sum(len(v.encode()) for v in sources.values()),
        frozen=digest(frozen),data=pin(payload['1.json']),source_blob=pin(source_blob),
        sources={n:digest(v.encode()) for n,v in sources.items()},
        implementation={str(p.relative_to(ROOT)):pin(p.read_bytes()) for p in sorted((ROOT/'src').glob('*.py'))})))
    print(json.dumps(dict(delivery=pin(delivery),package=package),sort_keys=True))


if __name__=='__main__':
    build()
