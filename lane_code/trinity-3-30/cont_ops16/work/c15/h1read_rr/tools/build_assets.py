"""Build a deterministic local asset; no transfer or extraction of the reserve tree."""
import hashlib
import json
from pathlib import Path
import struct
import tarfile
import io

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/scratch/jjyeung/n30_mirror/b10_reserve/R0_RESERVE_20261116.tar')
TARGET = '/project/community/jjyeung/okh7/af83c921'

def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def opaque(value):
    return hashlib.sha256(value.encode()).hexdigest()[:24]

def dump(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')

def build():
    q = ROOT/'in/out/qsets/R0_QUESTIONS_dev_f32.jsonl'
    manifest = ROOT/'in/out/FRAMES_MANIFEST.json'
    assert sha(q).startswith('b4e278f2') and sha(manifest).startswith('450e4125')
    source_sha = sha(SOURCE)
    if source_sha != '2bbae12a984fde1228bdb571f5aee390c1e6a82dc554310aa04c6fd0fe80a116':
        raise ValueError('Reserve archive digest differs')
    rows = [json.loads(l) for l in q.read_text().splitlines()]
    assert len(rows) == 2169 and len({(r['dataset'],r['scene']) for r in rows}) == 98
    wants = {}
    rewritten = []
    mapping = {}
    for source_line, r in enumerate(rows, 1):
        indices = r['frame_indices']
        if len(indices)!=32 or len(set(indices))!=32 or indices!=sorted(indices):
            raise ValueError('Invalid f32 indices')
        key = r['dataset']+'/'+r['scene']
        room = opaque(key)
        refs = []
        for i in indices:
            name = f'frames/{key}/{i:06d}.png'
            dest = room+'/'+opaque(str(i))+'.png'
            wants[name] = dest
            refs.append(dest)
        ident = opaque(str(source_line)+'|'+r['qid'])
        mapping[ident] = dict(qid=r['qid'],source_line=source_line,dataset=r['dataset'],scene=r['scene'],room=key)
        rewritten.append(dict(id=ident,example_id=ident,scene=room,room=room,
            benchmark='devrows',question_type=r['question_type'],question=r['question'],
            options=r['options'],ground_truth=r['answer'],answer=r['answer'],unit=r['unit'],
            answer_type='multiple_choice' if r['options'] else 'numerical',
            source_frame_indices=indices,frame_refs=refs,fps=r['fps'],
            total_num_frames=r['total_num_frames'],subtype=r['subtype'],thinking=True))
    out = ROOT/'assets'; out.mkdir(exist_ok=True)
    archive_path=out/'d81f4a26.tar'
    inventory={}
    with tarfile.open(SOURCE,'r:') as source:
        found={}
        for member in source:
            name=member.name.removeprefix('./')
            if name in wants:
                if not member.isfile() or name in found:
                    raise ValueError('Invalid requested source member')
                found[name]=member
        if set(found)!=set(wants):raise ValueError('Missing requested frames')
        with tarfile.open(archive_path,'x',format=tarfile.USTAR_FORMAT) as target:
            for name in sorted(wants,key=wants.get):
                data=source.extractfile(found[name]).read()
                if data[:8]!=b'\x89PNG\r\n\x1a\n' or struct.unpack('>II',data[16:24])!=(640,480):
                    raise ValueError('Unexpected PNG dimensions')
                dest=wants[name]; item=tarfile.TarInfo(dest)
                item.size=len(data);item.mode=0o644;item.uid=item.gid=item.mtime=0
                item.uname=item.gname=''
                target.addfile(item,io.BytesIO(data))
                inventory[dest]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    item_path=out/'e52a690b.jsonl'
    item_path.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rewritten))
    files={p.name:dict(path=TARGET+'/'+p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in (archive_path,item_path)}
    registration=dict(items=2169,rooms_with_items=98,registered_rooms=100,deferred_rooms=2,
        deferred_room_ids=sorted(opaque(k) for k,v in json.loads((ROOT/'in/out/DEFERRED.json').read_text())['deferred'].items() if v['r0_split']=='R0-dev'),
        files=files,frames=inventory,layout='spread',frames_per_item=32)
    dump(ROOT/'kit/launcher/EXTRA.json',registration)
    dump(ROOT/'evidence/ID_MAP.json',mapping)
    dump(ROOT/'evidence/ASSET_BUILD.json',dict(source=str(SOURCE),source_bytes=SOURCE.stat().st_size,
        source_sha256=source_sha,provided_digest_prefix='2bbae12a984fde12',
        full_expected_digest_supplied=False,questions_sha256=sha(q),manifest_sha256=sha(manifest),
        selected_frames=len(inventory),expanded_bytes=sum(v['bytes'] for v in inventory.values()),files=files))
    print(json.dumps(dict(source_sha256=source_sha,selected_frames=len(inventory),files=files)))

if __name__=='__main__':build()
