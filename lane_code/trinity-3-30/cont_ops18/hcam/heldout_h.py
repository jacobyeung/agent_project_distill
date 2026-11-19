"""Frozen H manifest, native-task and frame admission checks (Python 3.6)."""
import hashlib
import json
import re
from collections import Counter

TYPES = ['camera_displacement','camera_rotation','camera_movement_direction']
ITEM_NAMES = ['HELDOUT_CAMERA_ITEMS.json','HELDOUT_CAMERA_TWINS.json','HELDOUT_NATIVE_TASKS.jsonl']
PINS = dict(zip(ITEM_NAMES, [
    '2b90676111c229965d91132ad65b0f019703556c5934123fa0734bc6bffb3bdf',
    '5ec7e2a62e54f56a3bdc8f1de51f0a96d98dd14da8dd5326bc92618654f7b104',
    '92a441ce08376e33ce1b66875d62fbd84315fc72d3c39c377aa045608a71cf8d']))
SCORER_OLD = '2736e479888481cda4c1682f2db3d8b54f0b6d5957d8a4603d86469dc2b493fd'
SCORER_NEW = 'd032f96986ad7ee6fa8ba3de6ec00beb98f4c18336a0648771c487451c283302'
sha = lambda b: hashlib.sha256(b).hexdigest()
def digest(v):return sha(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())

def question_pair(item):
    q=item['question'].lower()
    # Singular endpoints, plural endpoints and ranges; repeated reference frames are allowed.
    matches=list(re.finditer(r'\bframes?\s+(\d+)(?:\s*(?:and|[–-])\s*(\d+))?',q))
    numbers=[]
    for m in matches:
        for n in m.groups():
            if n is not None and int(n) not in numbers:numbers.append(int(n))
    if numbers != item['display_frame_pair']:
        raise ValueError('Question/display frame disagreement: '+item['id'])
    return numbers

def validate_payload(m):
    assert m['name']=='heldout_camera_wording' and m['count']==900
    assert m['development_only'] is True and digest(m['items'])==m['item_set_sha256']
    assert Counter(i['question_type'] for i in m['items'])==dict.fromkeys(TYPES,300)
    assert len({i['id'] for i in m['items']})==900
    assert m['r0_check']==dict(checked=900,found=0,pin=dict(path='auth/R0_ROOMS.txt',sha256='bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3'))
    for i in m['items']:
        assert all(type(x) is int for x in i['display_frame_pair'])
        assert 1<=i['display_frame_pair'][0]<i['display_frame_pair'][1]<=32
        question_pair(i)

def validate(pf):
    for n,h in PINS.items():assert sha(pf['items/'+n])==h,n
    m=json.loads(pf['items/'+ITEM_NAMES[0]]);validate_payload(m)
    twins=json.loads(pf['items/'+ITEM_NAMES[1]])['twins']
    tasks=[json.loads(x) for x in pf['items/'+ITEM_NAMES[2]].splitlines()]
    by={i['id']:i for i in m['items']};native={i['id']:i for i in tasks}
    old={i['id']:i for i in json.loads(pf['items/devs1_routed.json'])['items']}
    assert len(tasks)==len(native)==900 and set(native)==set(by)
    assert len(twins)==450 and len({t['original_id'] for t in twins})==450
    assert {t[k] for t in twins for k in ('original_id','reworded_id')}==set(by)
    frames=json.loads(pf['b/work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json'])['captures']
    dense=json.loads(pf['b/work/meta/x/sj/orch_cd/evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json'])['captures']
    # Both source frame inventories are immutable A4 payload members.
    if isinstance(frames,list):frames={c['native']:c for c in frames}
    if isinstance(dense,list):dense={c['native']:c for c in dense}
    for t in twins:
        o,r=by[t['original_id']],by[t['reworded_id']]
        assert o==old[o['id']]
        assert digest(o)==t['original_item_sha256'] and digest(r)==t['reworded_item_sha256']
        assert o['question_type']==r['question_type']==t['type']
        for key in o:
            if key not in ('id','question'):assert o[key]==r[key],(key,o['id'])
        for i in (o,r):
            assert {k:v for k,v in i.items() if k!='room_key'}==native[i['id']]
            assert i['native'] in frames and i['native'] in dense, 'Frames absent from A4: '+i['id']
    return dict(items=900,twins=450,captures=len({i['native'] for i in by.values()}),question_frame_agreements=900,
                originals_byte_equivalent=True,frame_fields_equal=True,native_tasks_unique=900)
