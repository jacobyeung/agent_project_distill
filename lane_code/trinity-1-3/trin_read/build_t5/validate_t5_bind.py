"""CPU fixture comparison to e193; accepted pixel digests are inputs, not remeasured."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import trinity_read as T
import paired_read as P
from fixture_need import bind_fixture

E193 = Path('/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193')


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def differences(a, b, prefix=''):
    if isinstance(a, dict) and isinstance(b, dict):
        result = []
        for key in sorted(set(a)|set(b)):
            path = prefix+'.'+key if prefix else key
            result += differences(a[key], b[key], path) if key in a and key in b else [path]
        return result
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [p for i, (x,y) in enumerate(zip(a,b)) for p in differences(x,y,prefix+'['+str(i)+']')]
    return [] if a == b else [prefix]


def validate(family, slot, work):
    ids = T.read_ids(T.BUILD/('KEYS636_'+family+'.ids'))
    direct, origin, data, media, dest, cfg, tasks, captures, report = bind_fixture(
        dict(family=family, model_slot=None if slot=='step544' else slot, work=str(work), ids=ids))
    refdir = E193/'direct'/family
    accepted = T.load(refdir/'request.json')
    reasons = {
        'binding':'Derived request digest changes with paths, dry state, and model identity.',
        'build_only':'CPU dry bind cannot launch.',
        'devs1.payload':'Read-only physical fixture payload path.',
        'devs1.frames_root':'Local destination for future frame pulls.',
        'datasets[0].rows.path':'Read-only physical fixture task path; its hash is unchanged.',
        'roots.video_root':'Local identity-only path; no video is read.',
        'output':'Local fixture result destination.',
        'legs1.export_bytes_verified':'No model weights were read during dry binding.',
        'legs1.export_verification':'Full export verification is deferred until authorized production.',
        'camera_leg.wrapper_sha256':'Reconstructed wrapper identity; original bytes are unavailable.',
        'trinity_binding':'Pins this wrapper and the e193 protocol contract.',
    }
    if slot != 'step544':
        for path in ('models.cp1m200.path','models.cp1m200.sha256','models.cp1m200.kind',
                     'legs1.artifact.path','legs1.artifact.sha256','legs1.step','legs1.name'):
            reasons[path] = 'Selected model identity; the CP1 protocol cell is unchanged.'
    changed = differences(cfg, accepted)
    assert set(changed) <= set(reasons), 'Unexpected request differences: '+str(set(changed)-set(reasons))
    assert cfg['build_only'] is True and cfg['legs1']['export_verification'] is None
    assert cfg['cells'] == accepted['cells']
    normalized = copy.deepcopy(cfg)
    # Normalize only the enumerated path/provenance/model differences.
    for key in ('binding','build_only','roots','output','models','legs1'):
        normalized[key] = copy.deepcopy(accepted[key])
    normalized['datasets'][0]['rows']['path'] = accepted['datasets'][0]['rows']['path']
    for key in ('payload','frames_root'):
        normalized['devs1'][key] = accepted['devs1'][key]
    if 'camera_leg' in normalized:
        normalized['camera_leg']['wrapper_sha256'] = accepted['camera_leg']['wrapper_sha256']
    normalized.pop('trinity_binding', None)
    assert encoded(normalized) == (refdir/'request.json').read_bytes()
    assert (dest/'PROMPT_PINS.json').read_bytes() == (refdir/'PROMPT_PINS.json').read_bytes()
    rows = {}
    with (refdir/'results/0/budget_2048.jsonl').open() as stream:
        for line in stream:
            row = json.loads(line)
            if row['example_id'] in set(ids): rows[row['example_id']] = row
    assert set(rows) == set(ids)
    accepted_index = T.load(refdir/'frames/0.json')
    index = dict(schema=1, binding=accepted['binding'], source_sha256=cfg['source_sha256'],
                 items={}, decodes=0, errors=0, workers=1, seconds=None)
    receipts = set()
    for task in tasks:
        original = rows[task['example_id']]
        normalized_task = dict(task, video_path=original['video_path'])
        rec = origin.receipt_template(normalized_task, cfg['cells'][0], captures[task['native']], media)
        audit = dict(original['media']); expected_receipt = audit.pop('frame_receipt')
        rec['audit']['pixel_sha256'] = audit['pixel_sha256']
        assert rec['audit'] == audit, task['example_id']
        name = 'receipts/'+origin.digest(rec['identity'])+'.json'
        pin = dict(path=name, sha256=hashlib.sha256(encoded(rec)).hexdigest())
        assert pin == expected_receipt, task['example_id']
        key = media.item_key(task, cfg['cells'][0]['layout'])
        assert pin == accepted_index['items'][key]
        index['items'][key] = pin
        receipts.add(name)
    index['decodes'] = len(receipts)
    expected = copy.deepcopy(accepted_index)
    expected['items'] = {k:v for k,v in expected['items'].items() if k in index['items']}
    expected['decodes'] = len({v['path'] for v in expected['items'].values()})
    assert encoded(index) == encoded(expected)
    if family == 'camera':
        assert encoded(index) == (refdir/'frames/0.json').read_bytes()
    # This is reconstructed evidence, deliberately outside the executable packet's frames/.
    T.dump(work/'comparison/frames/0.json', index)
    T.dump(work/'comparison/request.json', normalized)
    evidence = dict(family=family, slot=slot, items=len(tasks), request_normalized_byte_equal=True,
        request_differences={k:reasons[k] for k in changed}, prompts_byte_equal=True,
        prompt_scope='Entire family, as emitted by the unchanged binder',
        frames_normalized_byte_equal=True, frames_scope='Selected items; main decodes counts only selected captures',
        frames_sha256=hashlib.sha256(encoded(index)).hexdigest(),
        pixel_digest_source='Accepted e193 result rows; no Trinity PNG bytes read',
        actual_pixels_verified=False, namespace_executed=False, fixture=True,
        model=cfg['models']['cp1m200'], cell_used=cfg['cells'][0])
    T.dump(work/'BIND_PARITY.json', evidence)
    print(json.dumps(dict(family=family, slot=slot, items=len(tasks), passed=True)))
    return evidence


if __name__ == '__main__':
    validate(sys.argv[1], sys.argv[2], Path(sys.argv[3]))
