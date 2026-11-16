"""Builds the D0 job B derive_kit overrides (v4 rows; TOKENS_B.json, ROWS_B.json, receipt_b.json in this folder). Inputs in this folder: TOKENS.json, receipt.json (job receipt), pool_selection_d0c.json,
E00_MEMBERS.json (Orchard listing of the sealed small tar), M544_SOURCE.json (member list of the GCS stop export) and
../base/runs/469ddece/m544/artifact.json. receipt.json = the row builder's Orchard receipt r.json (f1600070) with database.path moved to the job path.
Usage: make_over.py > over.json"""
import json, sys, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools')); import derive_kit as dk
H = Path(__file__).resolve().parent.parent / 'v1'; B = Path(__file__).resolve().parent; KIT = H.parent / 'kitfull'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
import os; tok = json.loads((B / os.environ.get('DK_TOKENS', 'TOKENS_B.json')).read_text()); ROWS = json.loads((B / 'ROWS_B.json').read_text()); cfg0 = json.loads((KIT / 'k/b02e4385.json').read_text())
cur0 = json.loads((KIT / 'k/0.json').read_text())
ROWS_PART = ROWS['rows_part']   # v4 store uploaded by rows_rebuild2
IN = '/project/community/jjyeung/okh7/i_' + tok['store'] + '/'           # this lane's uploads: job receipt, repacked m544
rec = json.loads((B / 'receipt_b.json').read_text()); assert rec['database']['sha256'] == ROWS['rows_sha256']; L = dk.AS + 'ap/' + tok['store'] + '/v/'
PSEL = 'pool_selection_' + tok['psel'] + '.json'   # rows builder's DEFERRED form, renamed to an opaque tag
psel = dict(path=dk.KIT_LOGICAL + PSEL, sha256=sha(H / PSEL))
extra = cur0['extra'] + [dict(dest=L + 'rows.sqlite', parts=[ROWS_PART], sha256=rec['database']['sha256']),
                         dict(dest=L + 'receipt.json', parts=[IN + 'vb.json'], sha256=sha(B / 'receipt_b.json'))]
art_path = H.parent / 'base/runs/469ddece/m544/artifact.json'; art = json.loads(art_path.read_text())
src = json.loads((H / 'M544_SOURCE.json').read_text()); assert sha(art_path) == src['artifact_sha256']
OLD, NEW = 'ap/8865619b/runs/469ddece/', 'ap/' + tok['art'] + '/m544/artifact.json'
members = [OLD + m['name'] for m in src['members'] if m['name'] != 'm544/artifact.json'] + [NEW]  # repack: m544/x -> OLD + m544/x; artifact only at NEW
fw_dir = art['full_weights']['path'].rsplit('/', 1)[0]
REP = json.loads((B / 'REPACK_170050.json').read_text())   # job A's repack receipt: every member's sha256 and the tar's
assert REP['artifact_logical'] == NEW and sorted(REP['members']) == sorted(members)
m544 = dict(parts=[IN + 'm.tar'], files={k: v['sha256'] for k, v in REP['members'].items()}, sha256=REP['tar']['sha256'])
a = dict(path=dk.AS + NEW, sha256=src['artifact_sha256'])
tars = [t for t in cur0['tars'] if not any(k.startswith('ap/f2ad01ad/runs/49becb79/m200/') for k in t['files'])] + [m544]
over = dict(run_key=tok['run'], kit_key=tok['kit'], persistent_run_root='/project/community/jjyeung/okh7/r/' + tok['root'],
            config=dict(streams=dict(vqa=dict(path=L + 'receipt.json', sha256=sha(B / 'receipt_b.json'))),
                        init_artifact=dict(artifact=a, lm='full', heads=['pose', 'depth']),
                        s1_routing=dict(selection=psel, catalog={**cfg0['s1_routing']['catalog'], psel['sha256']: psel['path']})),
            deployment=dict(extra=extra, init=dict(file=a['path'], sha256=a['sha256']), tars=tars),
            add_k={PSEL: dict(path=str(H / PSEL), sha256=psel['sha256'])},
            content={sha(B / 'receipt_b.json'): str(B / 'receipt_b.json'), src['artifact_sha256']: str(art_path), sha(B / 'full_weights.json'): str(B / 'full_weights.json')},
            sealed_docs=[str(H / 'sealed_vqa_receipt.json')],
            e00_listing=str(H / 'E00_MEMBERS.json'),
            tar_members={IN + 'm.tar': sorted(members)},
            accept_unstaged={rec['source']['sha256']: dict(field='source', reason='VQA receipt source: the row builder hash list S.sha256 '
                             '(Orchard project, outside the code-aws prefixes); provenance only: VQA rebuild and admission read the receipt database, not its source '
                             '(carrier_c1_data.py:543, s1_admission.py:189; reviewer r3 (b))')})
print(json.dumps(over, indent=1, sort_keys=True))
