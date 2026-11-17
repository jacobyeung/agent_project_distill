"""Validate independent scan provenance and the narrow ORCH exemption."""
import copy
import hashlib
import json
import re

EXEMPTION_RECORD = 'events/r1_ops/20261117T1758Z_ORCH_ANSWER_anon_hits_exempt_submit_proof1.md'
EXEMPTION_SHA = '22a371b35e86ff8a48ed0b03c718d15fb656d1d342dd3c441d9986ac70ea0720'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def validate_certificate(cert, classified_raw, scan, exemption, pins, members):
    require(cert.get('status') == 'CLEAN' and type(cert.get('hits')) is int and cert['hits'] == 0 and cert.get('reviewer'), 'Independent CLEAN certificate required')
    require(cert.get('config_identity') == pins['identity'] and cert.get('operator_archive_sha256') == pins['outer'], 'Certificate packet identity differs')
    require(cert.get('exemption_record') == EXEMPTION_RECORD and sha(exemption) == EXEMPTION_SHA, 'Exemption authority differs')
    manifest = cert.get('manifest_sha256', '')
    require(re.fullmatch('[0-9a-f]{64}', manifest), 'Invalid manifest SHA')
    require(cert.get('scan_sha256') == sha(scan), 'Scan SHA differs')
    lines = scan.decode().splitlines()
    require(lines.count('PACKET '+pins['identity']+' ARCHIVE '+pins['outer']+' RUN '+pins['run']) == 1, 'Scan packet differs')
    require([line for line in lines if line.startswith('MANIFEST ')] == ['MANIFEST '+manifest], 'Scan manifest differs')
    classified = json.loads(classified_raw)
    require(classified.get('reviewer'), 'Independent classified reviewer required')
    require(classified.get('config_identity') == pins['identity'] or classified.get('operator_archive_sha256') == pins['outer'], 'Classified packet differs')
    for key, expected in [('config_identity', pins['identity']), ('operator_archive_sha256', pins['outer'])]:
        require(key not in classified or classified[key] == expected, 'Contradictory classified identity')
    inputs = classified.get('inputs', {})
    require(inputs.get('scan_sha256') == sha(scan) and inputs.get('manifest_sha256_in_scan') == manifest, 'Classified scan inputs differ')
    hits = classified.get('hits')
    require(isinstance(hits, list), 'Classified hits list required')
    private = cert.get('private_tree_contents_accepted', [])
    inherited = cert.get('inherited_token_accepted', [])
    require(isinstance(private, list) and isinstance(inherited, list), 'Exemption references must be lists')
    require(all(isinstance(x,str) for x in private+inherited), 'Invalid exemption ID')
    require(len(set(private+inherited)) == len(private+inherited), 'Duplicate exemption ID')
    remaining = set(private+inherited)
    visible_ids = set()
    for hit in hits:
        cls = hit.get('class')
        require(cls in ('inherited-accepted', 'exempt-content', 'new-visible'), 'Unclassified hit')
        if cls != 'new-visible':
            continue
        key = hit.get('id')
        require(isinstance(key,str) and key and key not in visible_ids, 'Unique visible hit ID required')
        visible_ids.add(key)
        surface = hit.get('surface', '')
        if key in private:
            require(re.fullmatch(r'log lines?: KH/o/<job>[.]proof[.]log', surface), 'Unsupported private content exemption')
        elif key in inherited:
            require(hit.get('inherited_token') is True and surface in ('/home/jjyeung', 'argv token: /home/jjyeung'), 'Unsupported inherited token exemption')
        else:
            raise ValueError('Unaccepted visible hit: '+key)
        remaining.discard(key)
    require(not remaining, 'Exemption references an unknown visible hit')
    expected = {pins['bundle']+'/'+name: sha(raw) for name,raw in members.items()}
    entries = cert.get('external', [])
    require(isinstance(entries,list) and len(entries) == len(expected), 'External inventory differs')
    actual = {entry['path']: entry['sha256'] for entry in entries}
    require(actual == expected, 'External member pins differ')
    result = copy.deepcopy(cert)
    result.update(scan_record_sha256=sha(classified_raw), exemption_sha256=sha(exemption), production_go_granted=False)
    return result
