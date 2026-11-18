"""Rebuild salted assets from the authenticated, retained local frame asset."""
import hashlib
import hmac
import io
import json
from pathlib import Path
import secrets
import shutil
import struct
import tarfile
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'evidence/FIX1_ASSET_SOURCE'
TARGET = '/project/community/jjyeung/okh7/af83c921'
KEY_PATH = ROOT/'evidence/ID_KEY.json'


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')


def opaque(key, domain, value):
    return hmac.new(key, (domain+'\0'+value).encode(), hashlib.sha256).hexdigest()[:24]


def build():
    if shutil.disk_usage(ROOT).free < 200*1024**3+900*1024**2:
        raise ValueError('Asset rebuild would breach the local free-space floor')
    q = ROOT/'in/out/qsets/R0_QUESTIONS_dev_f32.jsonl'
    manifest = ROOT/'in/out/FRAMES_MANIFEST.json'
    if sha(q)!='b4e278f242e143d8ee66fa527449c7e02fad753bbbb528bd0c31fb9e47aea181' or not sha(manifest).startswith('450e4125'):
        raise ValueError('Source registration differs')
    # Retain the complete input before replacing outputs. Subsequent builds reuse it.
    if not SOURCE.exists():
        SOURCE.mkdir(mode=0o700)
        for src,dst in [('kit/launcher/EXTRA.json','EXTRA.json'),('evidence/ID_MAP.json','ID_MAP.json'),
                        ('assets/e52a690b.jsonl','items.jsonl'),('evidence/ASSET_BUILD.json','BUILD.json'),
                        ('evidence/FINAL_PINS.json','FINAL_PINS.json')]:
            (SOURCE/dst).write_bytes((ROOT/src).read_bytes())
        (ROOT/'assets/d81f4a26.tar').rename(SOURCE/'d81f4a26.tar')
    original=json.loads((SOURCE/'EXTRA.json').read_text())
    source=SOURCE/'d81f4a26.tar'
    source_sha=sha(source)
    original_pins=json.loads((SOURCE/'FINAL_PINS.json').read_text())
    if sha(SOURCE/'ID_MAP.json')!=original_pins['evidence/ID_MAP.json']:
        raise ValueError('Local identifier map digest differs')
    if source_sha!=original_pins['assets/d81f4a26.tar']:
        raise ValueError('Local frame asset differs from original final pins')
    if source_sha!=original['files'][source.name]['sha256']:
        raise ValueError('Local frame asset digest differs')
    if sha(SOURCE/'items.jsonl')!=original['files']['e52a690b.jsonl']['sha256']:
        raise ValueError('Local item asset digest differs')
    if not KEY_PATH.exists() and 'key_sha256' in json.loads((ROOT/'evidence/ASSET_BUILD.json').read_text()):
        raise ValueError('Identifier key is missing; refusing to rotate IDs')
    if not KEY_PATH.exists():
        with KEY_PATH.open('x') as stream:
            KEY_PATH.chmod(0o600)
            stream.write(json.dumps(dict(schema=1,key_hex=secrets.token_hex(32)))+'\n')
    key=bytes.fromhex(json.loads(KEY_PATH.read_text())['key_hex'])
    if len(key)!=32:raise ValueError('Invalid local identifier key')
    old_map=json.loads((SOURCE/'ID_MAP.json').read_text())
    old_rows={old_map[r['id']]['source_line']:r for r in map(json.loads,(SOURCE/'items.jsonl').read_text().splitlines())}
    rows=list(map(json.loads,q.read_text().splitlines()))
    assert len(rows)==2169 and len({(r['dataset'],r['scene']) for r in rows})==98
    wants={};rewritten=[];mapping={};occurrences=Counter()
    for source_line,r in enumerate(rows,1):
        indices=r['frame_indices'];old=old_rows[source_line]
        if len(indices)!=32 or indices!=sorted(set(indices)) or indices!=old['source_frame_indices']:
            raise ValueError('Invalid anchor indices')
        room_key=r['dataset']+'/'+r['scene'];room=opaque(key,'room',room_key)
        refs=[]
        for i,previous in zip(indices,old['frame_refs']):
            dest=room+'/'+opaque(key,'frame',room_key+'/'+str(i))+'.png'
            if previous in wants and wants[previous]!=dest:raise ValueError('Conflicting frame identity')
            wants[previous]=dest;refs.append(dest)
        occurrences[r['qid']]+=1
        logical_id=r['qid'] if occurrences[r['qid']]==1 else r['qid']+'#2'
        if occurrences[r['qid']]>2 or (occurrences[r['qid']]==2 and r['qid'] not in
                ('r0_5f3b5ae38f23ff697994','r0_c07cd9b246d953847b90')):
            raise ValueError('Unexpected duplicate source qid')
        ident=opaque(key,'item',logical_id)
        if ident in mapping:raise ValueError('Duplicate opaque item identity')
        mapping[ident]=dict(id=logical_id,source_qid=r['qid'],source_line=source_line,
                            dataset=r['dataset'],scene=r['scene'],room=room_key)
        rewritten.append(dict(id=ident,example_id=ident,scene=room,room=room,
            benchmark='devrows',question_type=r['question_type'],question=r['question'],options=r['options'],
            ground_truth=r['answer'],answer=r['answer'],unit=r['unit'],
            answer_type='multiple_choice' if r['options'] else 'numerical',source_frame_indices=indices,
            frame_refs=refs,fps=r['fps'],total_num_frames=r['total_num_frames'],subtype=r['subtype'],thinking=True))
    out=ROOT/'assets';out.mkdir(exist_ok=True);out.chmod(0o700)
    archive_path=out/'d81f4a26.tar';inventory={}
    with tarfile.open(source,'r:') as archive:
        found={}
        for member in archive:
            if not member.isfile() or member.name in found or member.name not in wants:
                raise ValueError('Unexpected local frame member')
            found[member.name]=member
        if set(found)!=set(wants):raise ValueError('Missing requested frames')
        def write_frames(target):
            for name in sorted(wants,key=wants.get):
                data=archive.extractfile(found[name]).read();pin=original['frames'][name]
                if len(data)!=pin['bytes'] or hashlib.sha256(data).hexdigest()!=pin['sha256']:
                    raise ValueError('Frame digest differs')
                if data[:8]!=b'\x89PNG\r\n\x1a\n' or struct.unpack('>II',data[16:24])!=(640,480):
                    raise ValueError('Unexpected PNG dimensions')
                dest=wants[name];item=tarfile.TarInfo(dest)
                item.size=len(data);item.mode=0o644;item.uid=item.gid=item.mtime=0;item.uname=item.gname=''
                target.addfile(item,io.BytesIO(data));inventory[dest]=pin
        class DigestSink:
            def __init__(self):self.digest=hashlib.sha256()
            def write(self,data):self.digest.update(data);return len(data)
        sink=DigestSink()
        with tarfile.open(fileobj=sink,mode='w|',format=tarfile.USTAR_FORMAT) as target:
            write_frames(target)
        if not archive_path.exists() or sha(archive_path)!=sink.digest.hexdigest():
            with tarfile.open(archive_path,'w',format=tarfile.USTAR_FORMAT) as target:
                write_frames(target)
    item_path=out/'e52a690b.jsonl'
    item_path.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rewritten))
    for path in (archive_path,item_path):path.chmod(0o600)
    files={p.name:dict(path=TARGET+'/'+p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in (archive_path,item_path)}
    registration=dict(items=2169,rooms_with_items=98,registered_rooms=100,deferred_rooms=2,
        deferred_room_ids=sorted(opaque(key,'room',k) for k,v in json.loads((ROOT/'in/out/DEFERRED.json').read_text())['deferred'].items() if v['r0_split']=='R0-dev'),
        files=files,frames=inventory,layout='duplicate',anchors_per_item=32,frames_per_item=64)
    dump(ROOT/'kit/launcher/EXTRA.json',registration)
    dump(ROOT/'evidence/ID_MAP.json',mapping)
    provenance=json.loads((SOURCE/'BUILD.json').read_text())
    provenance.update(files=files,selected_frames=len(inventory),expanded_bytes=sum(v['bytes'] for v in inventory.values()),
        rebuild_source=str(source.relative_to(ROOT)),rebuild_source_sha256=source_sha,
        id_rule='HMAC-SHA256 with a fixed local random 256-bit key and room/frame/item domains; first 24 hex characters',
        logical_id_rule='Source qid; only the second occurrence of either registered duplicate qid gets #2',
        logical_id_ruling='20261116T2218Z_ORCH_RULING_r0dev_dup_qids.md',
        key_sha256=sha(KEY_PATH),layout='duplicate',anchors_per_item=32,frames_per_item=64)
    dump(ROOT/'evidence/ASSET_BUILD.json',provenance)
    lines=['# Operator upload plan','',
        'The operator uploads only the two files below through the IO governor. No transfer was performed.',
        'Set `/project/community/jjyeung/okh7/af83c921/` to mode **0700** and both files to **0600**. The job refuses other modes, symlinks or nonregular files before hashing or extraction.','',
        '| Local file | Exact Orchard target | Bytes | SHA256 |','|---|---|---:|---|']
    lines += [f"| `assets/{name}` | `{v['path']}` | {v['bytes']} | `{v['sha256']}` |" for name,v in files.items()]
    lines += ['',f"Total upload: **{sum(v['bytes'] for v in files.values()):,} bytes**. Extracted PNGs: **{provenance['expanded_bytes']:,} bytes**, {len(inventory):,} files.",'',
        'After upload, the operator sets and checks permissions and verifies the full digests:', '', '```bash',
        'chmod 0700 '+TARGET,'chmod 0600 '+' '.join(v['path'] for v in files.values()),
        "stat -c '%a %n' "+TARGET+' '+' '.join(v['path'] for v in files.values())]
    lines += ["printf '%s  %s\\n' '"+v['sha256']+"' '"+v['path']+"' | sha256sum -c -" for v in files.values()]
    lines += ['```','',
        '`kit/reader/x7.py:stage_assets` checks modes, file sizes and complete SHA256, exact item/type/room membership, frame-reference closure, safe tar members and every PNG digest. Loading checks RGB, dimensions and pixel digests. The trained cell supplies 32 anchors twice (64 input frames).','',
        'Keep `evidence/ID_KEY.json`, `evidence/ID_MAP.json`, `evidence/FAMILY_ALIASES.json`, source snapshots, reports and tests on Trinity. None enters the batch, configuration or returns. The key is generated once and reused for deterministic rebuilds.', '',
        'The retained local frame asset supplies all frame bytes; its full digest is checked before every rebuild. `evidence/ASSET_BUILD.json` preserves the original reserve provenance. Tests reconstruct the deterministic sorted USTAR stream and compare its full digest.']
    (ROOT/'UPLOAD_PLAN.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(selected_frames=len(inventory),files=files)))

if __name__=='__main__':build()
