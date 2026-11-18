"""Draft job B review.json and staging.json for OUT (build_b.py fix output). Usage: make_records_b.py OUT ORCHARD_CHECK.json UTC
ORCHARD_CHECK.json: {"rows": {"path", "sha256", "utc"}, "receipt": {"path", "sha256", "utc"}} from a read-only sha256 run on
the Orchard login. The review text takes effect only after the reviewer confirms these exact bytes."""
import json, sys, hashlib
from pathlib import Path
OUT, CHK, UTC = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text()), sys.argv[3]
ids = json.loads((OUT / 'ids.json').read_text()); rep = json.loads(Path('/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/REPACK_170050.json').read_text())
SRC = 'sha256:b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99'
assert CHK['rows']['sha256'] == ids['rows'] and CHK['receipt']['sha256'] == ids['receipt']
att = ('Independent review of source seal ' + SRC + ' and configuration identity ' + ids['identity'] + ', including the '
       'pinned-template-and-native-data-derivation admission contract with digest ' + ids['contract'] + ', verdict PASS. Basis: independently '
       'recomputed both digests using the derived kit\'s own gate code; verified the permitted configuration changes (streams.vqa, '
       'init_artifact.artifact, s1_routing.selection and catalog, output, preparation_output), unchanged gate code and sealed trainer archive, '
       'the receipt binding to rows ' + ids['rows'] + ' and the sealed division, the selection binding, and all nine export-member pins against '
       'the repack receipt. This review extends the supplied sealed-source review; it does not claim a fresh audit of the entire trainer. '
       'Remote payload bytes and upload capabilities were not independently checked. The native real-data derivation, parent-grounding checks, '
       'all-rank GPU first-step admission, resume and export remain mandatory and are not claimed to have passed. This attestation does not grant '
       'submission authorization.')
review = dict(admission_contract_sha256=ids['contract'], admission_scope='pinned-template-and-native-data-derivation', attestation=att,
              config_sha256=ids['identity'], note='independent review rounds 9 and 10 of the derived configuration; round 9 report sha256 '
              '39038d982a2f4de9e189174cc848535033ce7ea51c8d28257386a50b28d16250', reviewed_utc=UTC, reviewer='r10', source_revision=SRC, verdict='PASS')
staging = dict(status='PASS', source_revision=SRC, config_sha256=ids['identity'], missing=[], project_community_write_bytes=0,
    evidence=dict(scope='read-only verification of the inputs this configuration adds or changes; zero project writes by the verification itself',
        unchanged_inputs='staged and hash-checked by job 170050 (kit x_3b862883, same sealed k/0.json entries), o/170050.steps',
        m544=dict(path='/project/community/jjyeung/okh7/i_bb09a77d/m.tar', sha256=rep['tar']['sha256'], members=len(rep['members']),
                  check='repack receipt o/170050.REPACK.json and vt.py PASS in job 170050 (o/170050.vt.json)'),
        rows=CHK['rows'], receipt=CHK['receipt']))
for n, v in (('review.json', review), ('staging.json', staging)):
    (OUT / n).write_text(json.dumps(v, sort_keys=True, separators=(',', ':')) + '\n')
    print(n, hashlib.sha256((OUT / n).read_bytes()).hexdigest())
