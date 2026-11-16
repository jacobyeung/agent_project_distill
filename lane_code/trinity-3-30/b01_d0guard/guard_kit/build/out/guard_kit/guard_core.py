"""Strict inputs and sequencing for the internal guard instrument."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re

STEPS = (200, 400, 600, 800, 1000)
RUN = '359fcc3c'
ARM = 'unflagged'

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.pending')
    with temporary.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        import os
        os.fsync(stream.fileno())
    temporary.replace(path)

def read(path):
    return json.loads(Path(path).read_text())

def check_pin(pin):
    path = Path(pin['path'])
    if not path.is_absolute() or '..' in path.parts or path.is_symlink() or not path.is_file():
        raise ValueError('Noncanonical pinned file')
    if sha(path) != pin['sha256']:
        raise ValueError('Pinned file digest differs')
    return path

def parse_done(raw, run, step):
    if run != RUN or type(step) is not int or step not in STEPS:
        raise ValueError('Export is outside the candidate milestones')
    obj = 'q8/8865619b/'+run+'_m'+str(step)+'.tar'
    match = re.fullmatch(re.escape(obj).encode()+rb' ([1-9][0-9]*) ([0-9a-f]{64})\n?', raw)
    if match is None:
        raise ValueError('Completion record identity or format differs')
    return dict(object=obj, bytes=int(match[1]), sha256=match[2].decode())

def verify_archive(path, done):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size != done['bytes']:
        raise ValueError('Whole archive bytes differ')
    if sha(path) != done['sha256']:
        raise ValueError('Whole archive digest differs')
    return done

def immutable(actual, expected):
    if actual != expected:
        raise ValueError('Export-independent contract differs')
    return dict(status='PASS', actual_sha256=digest(actual), expected_sha256=digest(expected))

def rows_in_order(rows, keys):
    if [r.get('key') for r in rows] != keys or len(set(keys)) != len(keys):
        raise ValueError('Ordered item membership differs')
    if any(r.get('arm') != ARM for r in rows):
        raise ValueError('Only the native arm is admitted')
    return rows

def identity_record(row):
    decoded = row.get('decode')
    if not isinstance(decoded, dict) or not isinstance(decoded.get('tokens'), list):
        raise ValueError('Identity proof requires actual decoded tokens')
    if any(type(token) is not int for token in decoded['tokens']):
        raise ValueError('Identity proof token type differs')
    calls = decoded.get('calls')
    if not isinstance(calls, list):
        raise ValueError('Identity proof requires calls')
    fields = ('call', 'kind', 'response', 'at_token', 'forced_tokens', 'spec_version', 'spec_revision')
    for call in calls:
        if not all(k in call for k in ('call', 'kind', 'response')):
            raise ValueError('Identity proof call is incomplete')
    if not isinstance(decoded.get('text'), str):
        raise ValueError('Identity proof requires the complete answer text')
    return dict(key=row['key'], tokens=decoded['tokens'],
                calls=[{k:c[k] for k in fields if k in c} for c in calls],
                answer=decoded['text'], no_answer=row['no_answer'], scores=row['scores'],
                finish=decoded.get('finish'))

def proof(reference, reread, destination, publish=lambda p: None, *, fixture=False):
    receipt = dict(schema='g1-proof-v1', status='FAIL', candidate_started=False,
                   reference_sha256=digest(reference), compared=[], error=None,
                   fixture=fixture, backend_identity_proven=False)
    try:
        keys = [r['key'] for r in reference]
        if len(keys) != 20:
            raise ValueError('Identity proof requires the sealed twenty items')
        actual = rows_in_order(reread(keys), keys)
        for expected, observed in zip(reference, actual):
            left, right = identity_record(expected), identity_record(observed)
            receipt['compared'].append(dict(key=expected['key'], expected=digest(left), actual=digest(right)))
            if left != right:
                raise ValueError('Backend identity mismatch at '+expected['key'])
        receipt['status'] = 'PASS'
        receipt['backend_identity_proven'] = not fixture
    except Exception as error:
        receipt['error'] = str(error)
    finally:
        write(destination, receipt)
        publish(Path(destination))
    if receipt['status'] != 'PASS':
        raise ValueError(receipt['error'])
    return receipt

def zero_nonanswers(rows):
    result = deepcopy(rows)
    for row in result:
        decoded = row.get('decode') or {}
        refused = (row.get('geometry_refusal') or row.get('refusal') or row.get('no_answer')
                   or row.get('parse_failed') or row.get('strict_no_answer')
                   or decoded.get('strict_no_answer') or decoded.get('parse_failed')
                   or decoded.get('finish') in ('program_refusal', 'call_limit', 'error')
                   or 'text' in decoded and re.search(r'</think\s*>', decoded['text'] or '', re.I) is None)
        if refused:
            row['scores'] = {key: None if value is None else 0.0 for key, value in row['scores'].items()}
    return result

def pipeline(reference, proof_reader, candidate_reader, keys, canary_keys, destination, publish=lambda p: None, *, fixture=False):
    destination = Path(destination)
    proof(reference, proof_reader, destination/'PROOF.json', publish, fixture=fixture)
    if len(canary_keys) != 10 or len(set(canary_keys)) != 10 or not set(canary_keys) <= set(keys):
        raise ValueError('Canary membership differs')
    receipt = dict(schema='g1-canary-v1', status='FAIL', keys=canary_keys, full_started=False, fixture=fixture)
    try:
        canary = rows_in_order(candidate_reader(canary_keys), canary_keys)
        receipt.update(status='PASS', rows_sha256=digest(canary), items=len(canary),
                       called=sum(bool(r.get('called')) for r in canary),
                       no_answer=sum(bool(r.get('no_answer')) for r in canary))
    except Exception as error:
        receipt['error'] = str(error)
        raise
    finally:
        write(destination/'CANARY.json', receipt)
        publish(destination/'CANARY.json')
    remaining = [key for key in keys if key not in set(canary_keys)]
    tail = rows_in_order(candidate_reader(remaining), remaining) if remaining else []
    indexed = {r['key']:r for r in canary+tail}
    all_rows = zero_nonanswers(rows_in_order([indexed[k] for k in keys], keys))
    result = dict(schema='legs1-r1-nomdg-v1', synthetic=fixture, arms={ARM:all_rows}, expected_keys=keys,
                  training_decision_allowed=False, report_scope='Internal instrument; never a claimed result')
    write(destination/'R1.json', result)
    return result
