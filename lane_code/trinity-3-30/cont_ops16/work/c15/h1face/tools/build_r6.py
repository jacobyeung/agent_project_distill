"""Build one opaque question asset, reusing the registered frame archive."""
from collections import Counter
import hashlib
import hmac
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/scratch/jjyeung/orch_n30/rows_r1/out/vsti_rel_dev_r0')
PINS = {
    'items.jsonl': 'b5853845aaf815c85e48e32f913efd14e8e7938c00723ff8c4a378375c4bfea3',
    'R0DEV_VSTI_QUESTIONS.jsonl': '08551bb2b9bd6ce47623c5efd9cba4f15872c0229bf8191235af5d63d957797d',
    'capture.py': 'bbc735c3daf0fe8a7126883cb955097a1e52a2dcc738a19b902cb8e8c120c87b',
}
TYPES = ('camera_obj_rel_dist_v1', 'camera_obj_rel_dist_v2', 'camera_obj_rel_dist_v3',
         'obj_obj_relative_pos_lr', 'obj_obj_relative_pos_nf', 'obj_obj_relative_pos_ud')
ITEM_NAME = 'b62c14e9.jsonl'


def dump(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')


def build():
    source = {}
    for name, expected in PINS.items():
        raw = (SOURCE/name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('Source pin differs: '+name)
        source[name] = raw
    items = [json.loads(line) for line in source['items.jsonl'].splitlines()]
    reader = [json.loads(line) for line in source['R0DEV_VSTI_QUESTIONS.jsonl'].splitlines()]
    assert len(items) == len(reader) == 900
    assert Counter(r['question_type'] for r in items) == {t:150 for t in TYPES}
    assert len({r['scene'] for r in items}) == 68
    extra = json.loads((ROOT/'kit/launcher/EXTRA.json').read_text())
    oldmap = json.loads((ROOT/'evidence/ID_MAP.json').read_text())
    oldrows = [json.loads(line) for line in (ROOT/'assets/e52a690b.jsonl').read_text().splitlines()]
    frames = {}; rooms = {}; metadata = {}
    for row in oldrows:
        source_row = oldmap[row['id']]
        key = (source_row['dataset'], source_row['scene'])
        rooms[key] = row['room']
        metadata[key] = (row['fps'], row['total_num_frames'], row['source_frame_indices'])
        for index, ref in zip(row['source_frame_indices'], row['frame_refs']):
            k = (*key, index)
            if k in frames and frames[k] != ref:
                raise ValueError('Ambiguous frame mapping')
            frames[k] = ref
    key = bytes.fromhex(json.loads((ROOT/'evidence/ID_KEY.json').read_text())['key_hex'])
    rewritten = []; mapping = {}; used = set()
    for line, (row, layout) in enumerate(zip(items, reader), 1):
        assert all(layout[k] == v for k,v in row.items())
        roomkey = (row['dataset'], row['scene'])
        assert metadata[roomkey] == (row['fps'], row['total_num_frames'], row['frame_indices'])
        assert len(row['frames']) == len(row['frame_indices']) == 32
        refs = []
        for index, frame in zip(row['frame_indices'], row['frames']):
            assert frame['tar_member'] == f'frames/{roomkey[0]}/{roomkey[1]}/{index:06d}.png'
            ref = frames[(*roomkey, index)]
            assert extra['frames'][ref]['sha256'] == frame['sha256']
            refs.append(ref); used.add(ref)
        ident = hmac.new(key, ('r6-item\0'+row['qid']).encode(), hashlib.sha256).hexdigest()[:24]
        assert ident not in mapping and ident not in oldmap
        mapping[ident] = dict(id=row['qid'], source_qid=row['qid'], source_line=line,
                             room=row.get('room', '/'.join(roomkey)), scene=row['scene'])
        rewritten.append(dict(id=ident, example_id=ident, room=rooms[roomkey], scene=rooms[roomkey],
            benchmark='devrows', question_type=row['question_type'], question=row['question'],
            options=row['options'], ground_truth=row['answer'], answer=row['answer'],
            unit=layout['unit'], answer_type='multiple_choice', source_frame_indices=row['frame_indices'],
            frame_refs=refs, fps=row['fps'], total_num_frames=row['total_num_frames'],
            subtype=layout['subtype'], thinking=True))
    path = ROOT/'assets'/ITEM_NAME
    raw = ''.join(json.dumps(row, sort_keys=True)+'\n' for row in rewritten).encode()
    path.write_bytes(raw); path.chmod(0o600)
    item_pin = dict(path='/project/community/jjyeung/okh7/af83c921/'+ITEM_NAME,
                    bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    registration = dict(items=900, type_counts={t:150 for t in TYPES}, rooms_with_items=68,
        registered_rooms=68, deferred_rooms=0, deferred_room_ids=[],
        item_name=ITEM_NAME, files={ITEM_NAME:item_pin, 'd81f4a26.tar':extra['files']['d81f4a26.tar']},
        frames=extra['frames'], used_frames=sorted(used), layout='duplicate',
        anchors_per_item=32, frames_per_item=64, capture_sha256=PINS['capture.py'])
    dump(ROOT/'kit/launcher/R6.json', registration)
    dump(ROOT/'evidence/R6_ID_MAP.json', mapping)
    (ROOT/'kit/reader/c6.py').write_bytes(source['capture.py'])
    audit = dict(source=str(SOURCE), source_sha256=PINS, items=900, type_counts=registration['type_counts'],
        rooms=68, frame_references=900*32, reused_frames=len(used),
        reused_frame_bytes=sum(extra['frames'][ref]['bytes'] for ref in used),
        missing_frames=[], new_frame_bytes=0, files=registration['files'], capture_module='kit/reader/c6.py')
    dump(ROOT/'evidence/FIXV1_ASSETS.json', audit)
    print(json.dumps(audit, sort_keys=True))


if __name__ == '__main__':
    build()
