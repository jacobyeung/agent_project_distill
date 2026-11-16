"""Fixed hash selection and exact decode equality before official decoding."""
import hashlib
from .io import rows
CAMERA = {'camera_displacement','camera_movement_direction','camera_rotation'}

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

def compare(reference, actual, kind):
    expected = {r['key']:r for r in reference}
    observed = {r['key']:r for r in actual}
    if len(observed) != len(actual) or set(expected) != set(observed):
        raise ValueError('proof membership differs')
    checks = []
    for key, ref in expected.items():
        required = kind == 'harness' or ref['question_type'] in CAMERA
        equal = signature(ref['decode']) == signature(observed[key]['decode'])
        checks.append(dict(key=key, equal=equal, required=required, question_type=ref['question_type']))
    return dict(passed=all(c['equal'] for c in checks if c['required']), checks=checks)


def query_signature(decoded):
    """Use C8r's canonical query digest, not a replay of recorded responses."""
    from .c8 import install
    install()
    import reader_policy
    value=reader_policy.journal_decode(decoded,False)
    return value.get('heads',{}).get('ground_queries_digest')


def verify_served(reference, actual):
    expected=reference['decode'];got=actual['decode']
    response_equal=[c.get('response','').encode() for c in expected['calls']]==[c.get('response','').encode() for c in got['calls']]
    want=query_signature(expected)
    have=query_signature(got)
    return {'response_equal':response_equal,'query_digest_equal':want==have,
            'expected_query_digest':want,'actual_query_digest':have,
            'passed':response_equal and want==have}


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
    # This factory loads the original checkpoint and the bound reader, not forced logits.
    reader, frames_for, by_key = reader_factory(assets,kind)
    actual=[]
    for ref in reference:
        item=by_key[ref['key']]
        first=reader.generate(frames_for(item),item)
        repeat=reader.generate(frames_for(item),item)
        if signature(first)!=signature(repeat):raise ValueError('identity proof repeat differs: '+ref['key'])
        value=dict(key=ref['key'],question_type=ref['question_type'],decode=first)
        independent=verify_served(ref,value)
        value['serving_proof']=independent
        required=kind=='harness' or ref['question_type'] in CAMERA
        if required and not reader.replay(first):raise ValueError('independent response replay failed: '+ref['key'])
        if kind=='harness' and not independent['passed']:
            raise ValueError('served query/response digest differs: '+ref['key'])
        actual.append(value)
    return reference,actual
