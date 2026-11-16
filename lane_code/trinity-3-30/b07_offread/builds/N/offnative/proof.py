"""Fixed hash selection and exact decode equality before official decoding."""
import hashlib
from .io import rows
CAMERA = {'camera_displacement','camera_movement_direction','camera_rotation'}
LOSS_RECORD_SHA256 = 'f1ba60b7d987d57420ddd457428adbcb8069e508fd1bc00ac9c5498add1a5362'
REDUCED_LIMIT = ('Distance items are reported only: token, call and answer equality are recorded '
                 'where decoding reaches them. Lost masks are never loaded or served. '
                 'Distance response equality, query digests, independent replay and model-logit '
                 'identity are not required or established. Camera equality remains required.')

def loss_record(pin, reference=None, *, journal=None, keys=None):
    """Admit only the owner's pinned declaration for the five lost job-170056 masks."""
    from .io import load, sha
    if not isinstance(pin, dict) or pin.get('sha256') != LOSS_RECORD_SHA256:
        raise ValueError('reduced proof requires the pinned lost-mask declaration')
    if sha(pin['path']) != LOSS_RECORD_SHA256:
        raise ValueError('lost-mask declaration content differs')
    record = load(pin['path'])
    masks = record.get('masks', [])
    if (record.get('schema') != 'native-proof-mask-loss-v1' or record.get('job') != 170056
            or record.get('status') != 'lost' or len(masks) != 5
            or any(m.get('status') != 'lost' for m in masks)):
        raise ValueError('mask pins are not declared lost')
    if reference is not None:
        distance = {r['key'] for r in reference if r['question_type'] == 'object_abs_distance'}
        if distance != {m['key'] for m in masks}:
            raise ValueError('lost masks do not cover the selected distance items')
    if journal is not None and sha(journal) != record['journal_sha256']:
        raise ValueError('lost-mask declaration names another journal')
    if keys is not None and sha(keys) != record['proof_keys_sha256']:
        raise ValueError('lost-mask declaration names another key selection')
    return record

def select(path):
    selected = []
    for family in (CAMERA, {'object_abs_distance'}):
        candidates = []
        for r in rows(path):
            if r['arm'] == 'unflagged' and r['question_type'] in family:
                candidates.append(r)
        chosen = sorted(candidates, key=lambda r:hashlib.sha256(r['key'].encode()).hexdigest())[:5]
        selected.extend({k:r[k] for k in ('key','question_type','decode','perception')} for r in chosen)
    if len(selected) != 10 or len({r['key'] for r in selected}) != 10:
        raise ValueError('proof requires five camera and five distance keys')
    return selected

def signature(decoded):
    return dict(tokens=decoded['tokens'], text_utf8=decoded['text'].encode().hex(),
                calls=[c['call'] for c in decoded['calls']],
                responses=[c.get('response', '').encode().hex() for c in decoded['calls']])

def compare(reference, actual, kind, *, mode='full', loss_pin=None):
    if mode not in ('full', 'reduced'):
        raise ValueError('unknown identity proof mode')
    if mode == 'reduced':
        loss_record(loss_pin, reference)
    expected = {r['key']:r for r in reference}
    observed = {r['key']:r for r in actual}
    if len(observed) != len(actual) or set(expected) != set(observed):
        raise ValueError('proof membership differs')
    checks = []
    for key, ref in expected.items():
        required = ref['question_type'] in CAMERA or (kind == 'harness' and mode == 'full')
        equal = signature(ref['decode']) == signature(observed[key]['decode'])
        check = dict(key=key, equal=equal, required=required, question_type=ref['question_type'])
        if mode == 'reduced':
            independent = observed[key].get('independent_responses') is True
            if ref['question_type'] in CAMERA:
                check['independent_responses'] = independent
                check['equal'] = equal and independent
            else:
                want,got=signature(ref['decode']),signature(observed[key]['decode'])
                checks_equal={n:want[n]==got[n] for n in ('tokens','calls','text_utf8')}
                check.update(comparisons=checks_equal,independent_responses=False,
                             status='reported',equal=all(checks_equal.values()),served_response_required=False)
        checks.append(check)
    return dict(passed=all(c['equal'] for c in checks if c['required']), checks=checks,
                mode=mode, loss_record_sha256=LOSS_RECORD_SHA256 if mode == 'reduced' else None,
                limitation=REDUCED_LIMIT if mode == 'reduced' else None)


def query_signature(decoded):
    """Use C8r's canonical query digest, not a replay of recorded responses."""
    from .c8 import install
    install()
    import reader_policy
    value=reader_policy.journal_decode(decoded,False)
    return value.get('heads',{}).get('ground_queries_digest')


def verify_served(reference, actual, *, require_digest=False):
    expected=reference['decode'];got=actual['decode']
    response_equal=[c.get('response','').encode() for c in expected['calls']]==[c.get('response','').encode() for c in got['calls']]
    want=query_signature(expected)
    have=query_signature(got)
    from .io import digest
    want_response = digest([c.get('response','').encode().hex() for c in expected['calls']])
    have_response = digest([c.get('response','').encode().hex() for c in got['calls']])
    valid = not require_digest or (isinstance(want, dict) and isinstance(want.get('sha256'), str)
                                  and len(want['sha256']) == 64 and want.get('query_count', 0) > 0)
    return {'response_equal':response_equal,'query_digest_equal':want==have,
            'expected_query_digest':want,'actual_query_digest':have,
            'expected_response_digest':want_response,'actual_response_digest':have_response,
            'response_digest_equal':want_response==have_response,
            'passed':valid and response_equal and want==have and want_response==have_response}


def in_job(reader_factory, assets, keys, *, kind):
    """Restore the original export before decoding the fixed historical questions."""
    from .io import load, sha
    from offkit.bind import STEP544_SHA
    for name in ('journal','request','artifact','tasks','frames'):
        p=assets[name]
        if sha(p['path'])!=p['sha256']:raise ValueError('proof input differs: '+name)
    if assets['artifact']['sha256']!=STEP544_SHA:
        raise ValueError('identity proof must use the original step-544 export')
    reference=select(assets['journal']['path'])
    if [r['key'] for r in reference]!=[r['key'] for r in keys['keys']]:
        raise ValueError('identity proof differs from PROOF_KEYS.json')
    mode = assets.get('proof_mode', 'full')
    if mode not in ('full', 'reduced'):
        raise ValueError('unknown identity proof mode')
    if mode == 'reduced':
        loss_record(assets.get('lost_masks'), reference, journal=assets['journal']['path'])
    # This factory loads the original checkpoint and the bound reader, not forced logits.
    reader, frames_for, by_key = reader_factory(assets,kind)
    actual=[]
    for ref in reference:
        item=by_key[ref['key']]
        first=reader.generate(frames_for(item),item)
        repeat=reader.generate(frames_for(item),item)
        if signature(first)!=signature(repeat):raise ValueError('identity proof repeat differs: '+ref['key'])
        value=dict(key=ref['key'],question_type=ref['question_type'],decode=first)
        independent=verify_served(ref,value, require_digest=mode=='reduced' and ref['question_type'] not in CAMERA)
        value['serving_proof']=independent
        required=ref['question_type'] in CAMERA or (kind=='harness' and mode=='full')
        replay_required = required and (mode != 'reduced' or ref['question_type'] in CAMERA)
        if replay_required and not reader.replay(first):raise ValueError('independent response replay failed: '+ref['key'])
        value['independent_responses'] = replay_required
        if required and not independent['passed']:
            raise ValueError('served query/response digest differs: '+ref['key'])
        actual.append(value)
    return reference,actual
