"""Reviewer's check of sb_rkfix2 configs/READER_RECEIPT.json: every input hash, every cited field, every frame list."""
import hashlib, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = Path('/scratch/jjyeung/orch_n30/sb_rkfix2')
ROOT = Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3')
J = ROOT / 'B5/ret/metadata/reads/0/metadata/journals/4/0'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


r = json.load(open(KIT / 'configs/READER_RECEIPT.json'))
out = dict(status=r['status'], missing=r['missing'])
out['inputs_ok'] = {p: Path(p).is_file() and sha(p) == h for p, h in r['input_sha256'].items()}
out['inputs_all_ok'] = all(out['inputs_ok'].values())
env = json.load(open(J / 'environment.json')); pin = json.load(open(ROOT / 'B5/ret/metadata/EXPORT_PIN.json'))
ident = json.load(open(ROOT / 'B5/ret/metadata/reads/0/metadata/READ_IDENTITY.json'))
items = json.load(open(ROOT / 'B/src/items/room134.json'))['items']; mapping = json.load(open(J / 'item_mapping.json'))['items']
journal = [json.loads(l) for l in (J / 'items.jsonl').read_text().splitlines()]
b = env['binding']
ev = r['field_evidence']
cite_ok = {k: (v if isinstance(v, list) else [v]) for k, v in ev.items()}
cite_ok = {k: all(Path(c['file']).is_file() and sha(c['file']) == c['sha256'] for c in v) for k, v in cite_ok.items()}
out['cited_file_hashes_ok'] = cite_ok
out['values'] = dict(
    checkpoint=r['checkpoint_sha256'] == b['export_sha256'] and env['binding']['fixture'] is False,
    step=r['step'] == b['step'] == pin['step'] == 200,
    read=r['read'] == ident['read'] == 0,
    journal=r['journal'] == '4/0' and ev['journal']['file'] == str(J / 'environment.json'),
    items=r['items_sha256'] == b['items_sha256'] == sha(ROOT / 'B/src/items/room134.json'),
    journal_sha=r['journal_sha256'] == sha(J / 'items.jsonl'),
    baseline=r['baseline_sha256'] == sha(KIT / 'evidence/direct_m200_room134.json'),
    archive=r['checkpoint_archive_sha256'] == pin['archive_sha256'])
man = json.load(open(KIT / 'configs/R0DEV_ROOM_MANIFEST.json'))['items']
ib = {i['id']: i for i in items}; mb = {m['id']: m for m in mapping}; jb = {j['id']: j for j in journal}
fr = r['frame_indices_by_item']
out['frames'] = dict(
    n=len(fr), ids_equal_manifest=set(fr) == {i['id'] for i in man},
    equal_manifest=sum(fr[i['id']] == i['frame_indices'] for i in man),
    equal_items=sum(fr[k] == ib[k]['frame_indices'] for k in fr),
    equal_mapping=sum(fr[k] == mb[k]['anchor_indices'] for k in fr),
    all_r0dev=all(ib[k]['r0_split'] == 'R0-dev' for k in fr),
    journal_complete=sum(jb[k]['complete'] is True for k in fr), len32=sum(len(v) == 32 for v in fr.values()))
direct = json.load(open(KIT / 'evidence/direct_m200_room134.json'))['rows']
rep = 0
for d in direct:
    m = re.search(r'</think>\s*(-?[0-9]+(?:\.[0-9]+)?)', jb[d['id']]['output']['text'])
    rep += bool(m) and float(m.group(1)) == d['direct'] and jb[d['id']]['output']['scores']['answer'] == d['direct_mra']
out['direct_rows_replayed'] = f'{rep}/{len(direct)}'
out['reader_host'] = env['host']
print(json.dumps({k: v for k, v in out.items() if k != 'inputs_ok'}, indent=1))
json.dump(out, open(HERE / 'out/RK_READER.json', 'w'), indent=1)
