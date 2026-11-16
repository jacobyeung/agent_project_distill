raise RuntimeError('UNVERIFIED_MODULE_EXECUTED')
"""Parameter binding for the official read kit (brief 07): benchmark x export x reader.

The binding is a pure function of files the operator names; it refuses rather than guesses.
It writes BINDING.json, whose sha256 the job and every report carry.

Export:
  step544                -> artifact sha256 1d6eeb28... (LEG-S1 step 544)
  done:<path>            -> a D0 `.done` record, plain text `<object> <bytes> <sha256>`;
                            requires --init-selection naming the same sha256 and passes the
                            one-export ledger (no milestone other than the selected one is read on
                            official items).
Reader:
  direct                 -> the accepted direct kits (VSI f42aa1a4, ReVSI ea1a1b2d) re-bound to the
                            export; reads the direct groups only (six VSI tasks, five ReVSI categories).
  harness:<sha256>       -> the registered harness backend named by the P8 freeze file
                            official_reads/ROUTED_PATH_FROZEN_<date>.md, whose sha256 must equal the
                            parameter. Refused while no such file exists. A ReVSI read additionally
                            requires the freeze file to bind the K1-refit selector (B6 answer 2).
  e2e:<sha256>           -> the end-to-end reader of brief 04, named by the sha256 of its export
                            manifest; requires the EAT-1 report of that manifest. Without a PASS the
                            binding is refused for production and allowed for fixture mode only.
"""
import hashlib
import json
import re
from pathlib import Path

from . import frames as F
from . import spec as S

STEP544_SHA = '1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef'
DIRECT_KITS = {
    'vsibench5130': dict(kit='f42aa1a4', job=170008, accepted_return_sha256='4609adde0bb8a9ee734abacd29ac4df03766d4c48bf0bf0fa90552627500065f'),
    'revsi999t32': dict(kit='ea1a1b2d5b965017f7cacce9c02c13cbbe5522d87be8cc55ab755176ecd55d3b', job=170037,
                        accepted_return_sha256='785a097ff750fc3d82a5ffd18cb299527fbe1e207d5166c86326edddd21c2036'),
}
FREEZE_NAME = re.compile(r'^ROUTED_PATH_FROZEN_(\d{8})\.md$')
SHA = re.compile(r'^[0-9a-f]{64}$')
# NEXT_LEG_INIT_RULE_20261116.md: sha256 of the registered text (every byte before `## Registration`).
INIT_RULE_SHA = 'd53f9c1ac74c4c9e7a3d3bbdbcf74a0853ca529d62bb1d3afe1c03f121e260ba'
INIT_CANDIDATE_STEPS = (200, 400, 600, 800, 1000)  # init rule item 1: m1, m50, m100 and stop exports are not candidates
D0_OBJECT = re.compile(r'^q8/8865619b/359fcc3c_m(\d+)\.tar$')
D0_ENDED = ('completed_step_1000', 'stopped_under_rule', 'no_further_allocation')  # init rule item 8


class BindError(ValueError):
    pass


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def parse_done(text):
    parts = text.split()
    if len(parts) != 3:
        raise BindError('.done record must be `<object> <bytes> <sha256>`')
    obj, size, sha = parts
    if not size.isdigit() or int(size) <= 0:
        raise BindError('.done record bytes field is not a positive integer')
    if not SHA.match(sha):
        raise BindError('.done record sha256 field is malformed')
    if obj.startswith('gs://') or obj.startswith('/'):
        raise BindError('.done record object must be given without bucket or root')
    return dict(object=obj, bytes=int(size), sha256=sha)


def bind_export(spec_text, *, init_selection=None, ledger=None, benchmark=None):
    if spec_text == 'step544':
        return dict(kind='step544', sha256=STEP544_SHA, label='LEG-S1 step 544 (artifact 1d6eeb28)')
    if not spec_text.startswith('done:'):
        raise BindError('export must be `step544` or `done:<path to .done record>`')
    path = Path(spec_text[5:])
    rec = parse_done(path.read_text())
    if init_selection is None:
        raise BindError('a D0 export needs --init-selection: only the export the init rule selects is read on official items')
    sel = json.loads(Path(init_selection).read_text())
    check_init_selection(sel, rec)
    out = dict(kind='done', sha256=rec['sha256'], object=rec['object'], bytes=rec['bytes'],
               done_record=str(path), done_record_sha256=sha256_file(path),
               init_selection=str(init_selection), init_selection_sha256=sha256_file(init_selection),
               label=sel.get('label', 'D0 export selected by the init rule'))
    if ledger is not None:
        check_ledger(ledger, out, benchmark)
    return out


def check_init_selection(sel, rec):
    """The init-selection record must cite the registered rule, a candidate step and the end of D0."""
    if sel.get('selected_sha256') != rec['sha256']:
        raise BindError('the .done record names an export the init selection did not select')
    if sel.get('init_rule_sha256') != INIT_RULE_SHA:
        raise BindError('init selection does not cite the registered init rule (registered-text sha256 d53f9c1a...)')
    m = D0_OBJECT.match(rec['object'])
    if not m:
        raise BindError('the .done record names an object outside the D0 lineage 359fcc3c')
    step = int(m.group(1))
    if step not in INIT_CANDIDATE_STEPS or sel.get('selected_step') != step:
        raise BindError('init selection step must be a rule candidate (m200..m1000) and equal the .done object step')
    ended = sel.get('d0_ended') or {}
    if ended.get('reason') not in D0_ENDED or not ended.get('event'):
        raise BindError('init selection must name why and where D0 ended (init rule item 8)')
    return step


def check_ledger(ledger, export, benchmark):
    """At most one D0 export is ever read on official items, and each benchmark once per reader kind."""
    path = Path(ledger)
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()] if path.exists() else []
    d0 = {r['export_sha256'] for r in rows if r.get('export_kind') == 'done'}
    if export['kind'] == 'done' and d0 and d0 != {export['sha256']}:
        raise BindError('ledger already holds another D0 export on official items: ' + ','.join(sorted(d0)))
    return rows


def ledger_append(ledger, binding):
    path = Path(ledger)
    row = dict(export_kind=binding['export']['kind'], export_sha256=binding['export']['sha256'],
               benchmark=binding['benchmark'], reader=binding['reader']['kind'], reader_id=binding['reader']['id'],
               binding_sha256=binding['binding_sha256'], mode=binding['mode'])
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()] if path.exists() else []
    for r in rows:
        same = all(r.get(k) == row[k] for k in ('export_sha256', 'benchmark', 'reader', 'mode'))
        if same and row['mode'] == 'production':
            raise BindError('this export, benchmark and reader already have a production read in the ledger')
    with path.open('a') as f:
        f.write(json.dumps(row, sort_keys=True) + '\n')


def _freeze_values(text):
    """The P8 file's machine block: a fenced ```json block whose object has key "freeze_values"."""
    for block in re.findall(r'```json\s*\n(.*?)\n```', text, flags=re.S):
        try:
            obj = json.loads(block)
        except ValueError:
            continue
        if isinstance(obj, dict) and 'freeze_values' in obj:
            return obj['freeze_values']
    return None


def bind_reader(spec_text, benchmark, *, freeze_file=None, e2e_manifest=None, eat1_report=None, mode='production'):
    if spec_text == 'direct':
        kit = DIRECT_KITS[benchmark]
        return dict(kind='direct', id='direct kit ' + kit['kit'][:8], direct_kit=kit,
                    eat1=dict(passed=None, note='direct reader: no call is served; EAT-1 concerns served calls'))
    kind, _, sha = spec_text.partition(':')
    if kind not in ('harness', 'e2e') or not SHA.match(sha):
        raise BindError('reader must be `direct`, `harness:<sha256 of the P8 freeze file>` or `e2e:<sha256 of the brief-04 export manifest>`')
    if kind == 'harness':
        if freeze_file is None:
            raise BindError('harness reader needs --freeze-file (P8 file official_reads/ROUTED_PATH_FROZEN_<date>.md)')
        p = Path(freeze_file)
        if not p.exists():
            raise BindError('P8 freeze file does not exist; no official routed read runs before P8')
        if not FREEZE_NAME.match(p.name):
            raise BindError('freeze file name must be ROUTED_PATH_FROZEN_<YYYYMMDD>.md')
        got = sha256_file(p)
        if got != sha:
            raise BindError(f'freeze file sha256 {got} differs from the reader parameter {sha}')
        values = _freeze_values(p.read_text())
        if values is None:
            raise BindError('freeze file carries no ```json {"freeze_values": ...}``` block; the kit cannot bind backend values')
        sel = values.get('selector') or {}
        if benchmark == 'revsi999t32' and not (sel.get('source') == 'K1_refit' and sel.get('kill_rules_passed') is True):
            raise BindError('ReVSI mask read needs the K1-refit selector that passed its kill rules (B6 answer 2)')
        return dict(kind='harness', id='P8 ' + p.name + ' ' + sha[:12], freeze_file=str(p), freeze_sha256=sha,
                    freeze_values=values,
                    eat1=dict(passed=False, note='harness backend: fails EAT-1 by construction (A1, A3, A4, A5); numbers are harness-served'))
    # e2e
    if e2e_manifest is None:
        raise BindError('e2e reader needs --e2e-manifest (brief 04 export manifest)')
    got = sha256_file(e2e_manifest)
    if got != sha:
        raise BindError(f'e2e manifest sha256 {got} differs from the reader parameter {sha}')
    eat = dict(passed=None, note='no EAT-1 report given')
    if eat1_report is not None:
        rep = json.loads(Path(eat1_report).read_text())
        if rep.get('manifest_sha256') != sha:
            raise BindError('EAT-1 report concerns another manifest')
        clauses = rep.get('clauses') or {}
        passed = bool(clauses) and all(c.get('status') == 'PASS' for c in clauses.values()) and rep.get('verdict') == 'PASS'
        eat = dict(passed=passed, report=str(eat1_report), report_sha256=sha256_file(eat1_report),
                   failing=[k for k, c in clauses.items() if c.get('status') != 'PASS'])
    if mode == 'production' and eat['passed'] is not True:
        raise BindError('e2e reader without an EAT-1 PASS is allowed in fixture mode only')
    return dict(kind='e2e', id='e2e manifest ' + sha[:12], manifest=str(e2e_manifest), manifest_sha256=sha, eat1=eat)


def bind(benchmark, export, reader, *, mode='production', init_selection=None, ledger=None, freeze_file=None,
         e2e_manifest=None, eat1_report=None, frames=(32, 'duplicate'), frames_override_reason=None):
    if benchmark not in S.BENCHMARKS:
        raise BindError('benchmark must be one of ' + ', '.join(S.BENCHMARKS))
    if mode not in ('production', 'proof', 'fixture'):
        raise BindError('mode must be production, proof or fixture')
    if mode == 'production' and ledger is None:
        raise BindError('a production binding needs --ledger (one-D0-export rule)')
    ex = bind_export(export, init_selection=init_selection, ledger=ledger, benchmark=benchmark)
    rd = bind_reader(reader, benchmark, freeze_file=freeze_file, e2e_manifest=e2e_manifest, eat1_report=eat1_report, mode=mode)
    try:
        fr = F.bind_frames(frames[0], frames[1], export=ex['kind'], override_reason=frames_override_reason)
    except F.FrameError as e:
        raise BindError(str(e))
    sp = S.BENCHMARKS[benchmark]
    groups = S.direct_groups(sp) if rd['kind'] == 'direct' else tuple(sp['groups'])
    items = sp['direct_items'] if rd['kind'] == 'direct' else sp['items']
    # Harness: pre-registration fallback section (secondary = reader-side fallback to the direct-reader
    # answer) and amendment 3 item 6 (room served primary; unserved room secondary). The e2e reader has
    # no outside fallback (EAT-1 A4), so it reads one arm.
    arms = ['primary', 'secondary_fallback', 'secondary_room_unserved'] if rd['kind'] == 'harness' else ['primary']
    body = dict(schema='offkit-binding-v1', benchmark=benchmark, benchmark_label=sp['label'], mode=mode,
                export=ex, reader=rd, groups=list(groups), items=items, arms=arms,
                frames=fr,
                frame_path='PyAV rgb24, %d floor-uniform anchors %s, layout %s' % (fr['count'], fr['anchor_rule'], fr['layout']),
                budget='B2048 primary; native reads 2,048 + 64 tokens (pre-registration, fixed without re-selection)')
    body['binding_sha256'] = binding_sha256(body)
    return body


def binding_sha256(binding):
    body = {k: v for k, v in binding.items() if k != 'binding_sha256'}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def verify_binding(binding):
    if not isinstance(binding, dict) or binding.get('schema') != 'offkit-binding-v1':
        raise BindError('not an offkit binding')
    if binding.get('binding_sha256') != binding_sha256(binding):
        raise BindError('binding_sha256 does not match the binding body')
    return binding
