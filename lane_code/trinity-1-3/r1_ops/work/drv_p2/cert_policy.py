"""Bind an independently classified scan to this packet and its explicit exemptions."""
import hashlib,json,re
from pathlib import Path

EXEMPTION_RECORD='events/r1_ops/20261117T1758Z_ORCH_ANSWER_anon_hits_exempt_submit_proof1.md'

def validate_certificate(cert, record, scan, exemption, pins, members):
    def require(ok,message):
        if not ok:raise ValueError(message)
    sha=lambda raw:hashlib.sha256(raw).hexdigest()
    require(cert.get('status')=='CLEAN' and cert.get('hits')==0 and cert.get('reviewer'), 'Independent CLEAN certificate required')
    require(cert.get('config_identity')==pins['identity'] and cert.get('operator_archive_sha256')==pins['outer'], 'Certificate is not for proof 2')
    require(re.fullmatch('[0-9a-f]{64}',cert.get('manifest_sha256','')), 'Missing final manifest pin')
    require(cert.get('scan_sha256')==sha(scan), 'Scan output differs')
    require(cert.get('scan_record') and cert.get('exemption_record')==EXEMPTION_RECORD, 'Classified scan and ORCH 1758Z record required')
    review=json.loads(record)
    require(review.get('reviewer'), 'Classified record has no independent reviewer')
    require(review.get('config_identity')==pins['identity'] or review.get('operator_archive_sha256')==pins['outer'], 'Classified record does not name this packet identity')
    inputs=review.get('inputs',{})
    require(inputs.get('scan_sha256')==sha(scan) and inputs.get('manifest_sha256_in_scan')==cert['manifest_sha256'], 'Classified scan/manifest pins differ')
    text=scan.decode()
    require('PACKET '+pins['identity']+' ARCHIVE '+pins['outer']+' RUN '+pins['run'] in text, 'Scan output does not name proof 2')
    require('MANIFEST '+cert['manifest_sha256'] in text, 'Scan output manifest differs')
    hits=review.get('hits');require(isinstance(hits,list), 'Every scan hit must be classified')
    private_ids=set(cert.get('private_tree_contents_accepted',[]))
    inherited_ids=set(cert.get('inherited_token_accepted',[]))
    visible_ids=set()
    for hit in hits:
        category=hit.get('class')
        require(category in ('inherited-accepted','exempt-content','new-visible'), 'Unclassified scan hit')
        if category!='new-visible':continue
        key=hit.get('id');require(key and key not in visible_ids, 'Visible hit IDs must be unique')
        visible_ids.add(key)
        if key in private_ids:
            # The reviewer must identify file contents in the private output tree,
            # not shared argv, names, or scheduler output.
            require(re.fullmatch(r'log lines?: KH/o/<job>[.]proof[.]log',hit.get('surface','')), 'Exemption is limited to private proof log contents')
        elif key in inherited_ids:
            require(hit.get('matches')==['/home/jjyeung'] and hit.get('inherited_token') is True, 'Exemption is limited to the inherited account home token')
        else:raise ValueError('Unaccepted visible hit: '+str(key))
    require(not private_ids & inherited_ids and visible_ids==private_ids|inherited_ids, 'Exemption IDs do not match the classified record')
    require(sha(exemption)=='22a371b35e86ff8a48ed0b03c718d15fb656d1d342dd3c441d9986ac70ea0720', 'ORCH exemption SHA differs')
    authority=exemption.decode()
    require('N1, N2, N3' in authority and 'N4' in authority and 'contents' in authority and 'inherited argv token' in authority, 'ORCH exemption record differs')
    external=cert.get('external');require(isinstance(external,list) and external, 'Missing external packet pins')
    expected={pins['bundle']+'/'+name:sha(raw) for name,raw in members.items()}
    actual={item['path']:item['sha256'] for item in external}
    require(len(actual)==len(external) and actual==expected, 'External inventory must match all 35 sealed bundle members')
    result=dict(cert,scan_record_sha256=sha(record),exemption_sha256=sha(exemption))
    return result
