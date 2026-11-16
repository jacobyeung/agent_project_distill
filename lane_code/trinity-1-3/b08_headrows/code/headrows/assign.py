"""Per-item path assignment for the both-path mix (brief 08 part B).

Each training item gets exactly one decision from the deployed pipeline's response on that item:
  head      status 'ok', the answer is right (numeric within 15% of a positive GT; counts and option letters as exact
            strings), every operand's accepted instance ids equal its GT instance ids, and the Session record that
            ground_rows.pack consumes binds to that answer
  direct    the response is wrong, or its masks do not match GT, or GT instances are missing
  recovery  the status is the runtime's own '<name>: not seen' text and the record holds the call and that status
  drop      ineligible identity (dev-S1, benchmark, withheld, R0 reserve, unresolvable), type outside the mix or
            without ground grammar, operator fault, missing or unknown status, bad provenance, unusable record,
            non-positive numeric GT
Any decision other than head leaves the item on its current form. No head row copies a silently wrong response.

Input records (JSONL), one per item:
  item:     {qid, type, dataset, scene, answer, room?, canonical?, physical_group?, native?, options?, operands?,
             gt_instances?: {operand: [ids]}}
  response: {qid, status, pred, selected?: {operand: [ids]}, pipeline: str, pipeline_sha256: 64 hex,
             record: v3.12-3.14 Session record (qid, type, question, options, answer, gt_answer, candidate_id,
             spec_version, events [{call, response}], suffix)}
"""
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUTH = HERE.parent.parent / 'work' / 'auth'
TREE = Path('/scratch/jjyeung/orch_n30/rows_rebuild/work/tree/src')

NUMERIC = {'object_size_estimation', 'object_abs_distance'}
COUNT = {'object_counting'}
OPTION = {'object_rel_distance', 'object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard'}
MIX_TYPES = NUMERIC | COUNT | OPTION
MAJORITY = {t: 'direct' for t in MIX_TYPES} | {'object_abs_distance': 'head'}
# room size is a direct type (ORCH 2026-11-16T12:27Z); appearance order waits for brief 11
EXCLUDED_TYPES = {'room_size_estimation', 'obj_appearance_order'}
# the sealed ground grammar (trace_format/ground_v312.py, ground_v313.py) has no program for these two;
# under the ORCH both-path ruling they keep their current (direct) form
NO_GRAMMAR = {'object_size_estimation', 'object_rel_direction_easy'}
REL_TOL = Decimal('0.15')
MAX_CAP, MAX_PER_ROOM = 2000, 4
# the only failure status the deployed runtime prints for a failed ground call (trace ruling 2.1, 2.4 (b), (c))
REAL_FAILURE_LINE = re.compile(r'[^:\n<>]+: not seen')
# operator faults a correct deployment never prints (trace ruling 2.4 (d))
OPERATOR_FAULTS = ('Routed policy requires a fixed named candidate universe', 'form_requires_v3.13',
                   'frozen_fusion_requires_depth_cut_receipt', 'mask_source_unavailable_for_type')
SHA = re.compile(r'[0-9a-f]{64}')
RECORD_FIELDS = ('qid', 'type', 'question', 'options', 'answer', 'gt_answer', 'candidate_id', 'spec_version',
                 'events', 'suffix')
PINS = {'dev_scene_exclusions.json': 'a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5',
        'benchmark_scene_exclusions.json': '3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970',
        'WITHHELD_ROOMS_80.json': '634820b44927b1a50c18db9b90246b4b99f8954b0d7f5f2893e547f1c92879ed',
        'R0_ROOMS.txt': 'bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3',
        'R0_SCENES.json': 'f7c458176426e22a13e47908b03abd2c6f5939d3e48eb7c24e7eba45b75ad479',
        'alias_map.json': '488480ab4b7f352eba9c81e99313c8bfcc247e9cc463a11620be087a42f579cf'}
ALIAS = dict(scannet='d1', scannetpp='d2', scannetppv2='d2', arkitscenes='d3', d1='d1', d2='d2', d3='d3')
NATIVE = re.compile(r'(?P<ds>scannet|scannetpp|scannetppv2|arkitscenes)/(?P<id>[^/]+)')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def room_of(canonical):
    """Physical room of a canonical capture: ScanNet sceneNNNN (all rescans), ScanNet++ scene id, ARKitScenes video."""
    m = NATIVE.fullmatch(canonical)
    if m is None:
        return None
    ds, ident = m['ds'], m['id']
    if ds == 'scannet':
        r = re.fullmatch(r'(scene\d{4})(?:_\d{2})?', ident)
        return r and 'scannet/' + r[1]
    if ds in ('scannetpp', 'scannetppv2'):
        return 'scannetpp/' + ident
    return 'arkitscenes/' + ident


class Eligibility:
    """Refuses dev-S1, benchmark, withheld and R0 reserve rooms with the sealed Exclusions class and pinned lists.
    Every identifier the item carries is checked; an unresolvable or inconsistent identity is refused."""

    def __init__(self, auth=AUTH):
        for name, want in PINS.items():
            if sha256(Path(auth) / name) != want:
                raise ValueError('pin mismatch: ' + name)
        if str(TREE) not in sys.path:
            sys.path.insert(0, str(TREE))
        from student_pilot.s1_exclusions import Exclusions
        pin = lambda n: {'path': str(Path(auth) / n), 'sha256': PINS[n]}
        self.exclusions = Exclusions(pin('dev_scene_exclusions.json'), pin('benchmark_scene_exclusions.json'))
        withheld = json.loads((Path(auth) / 'WITHHELD_ROOMS_80.json').read_text())
        self.withheld = {a.casefold() for v in withheld['aliases'].values() for a in v} | {r.casefold() for r in withheld['rooms']}
        self.r0 = {l.strip() for l in (Path(auth) / 'R0_ROOMS.txt').read_text().splitlines() if l.strip()}
        self.r0 |= {v['room'] for v in json.loads((Path(auth) / 'R0_SCENES.json').read_text())['captures'].values()}
        self.alias = json.loads((Path(auth) / 'alias_map.json').read_text())

    def canonical(self, item):
        dataset, scene = item['dataset'], item['scene']
        if '/' in scene:
            prefix, bare = scene.split('/', 1)
            if ALIAS.get(prefix.casefold()) != ALIAS.get(dataset.casefold()):
                raise ValueError('dataset_scene_mismatch')
        else:
            bare = scene
        short = ALIAS.get(dataset.casefold())
        if short is None:
            raise ValueError('unknown_dataset')
        found = {c for c in (self.alias.get(f'{short}/{bare}'), self.alias.get(f'{short}/{scene}'), item.get('canonical')) if c}
        for ds in ('scannet', 'scannetppv2', 'arkitscenes'):
            if ALIAS[ds] == short and NATIVE.fullmatch(f'{ds}/{bare}') and room_of(f'{ds}/{bare}'):
                native = f'{ds}/{bare}'
                if ds != 'scannet' or re.fullmatch(r'scene\d{4}_\d{2}', bare):
                    found.add(native)
        if len(found) != 1:
            raise ValueError('canonical_unresolved' if not found else 'canonical_ambiguous')
        return found.pop()

    def reason(self, item):
        """Return a refusal reason, or None when eligible; sets item['room_key'] for the per-room cap."""
        e = self.exclusions
        try:
            canonical = self.canonical(item)
            room = room_of(canonical)
            if room is None:
                return 'room_unresolved'
            cds, cid = canonical.split('/', 1)
            rows = [dict(dataset=item['dataset'], scene=item['scene'].split('/', 1)[-1]), dict(dataset=cds, scene=cid)]
            hits = [e.matches(r) for r in rows]
            names = [n for n in (item.get(k) for k in ('room', 'physical_group', 'native', 'canonical')) if n]
            names += [canonical, room]
            keys = {e.key(n) for n in names if isinstance(n, str) and '/' in n and n.split('/', 1)[0].casefold() in ALIAS}
        except Exception as error:  # unknown prefix, malformed or unresolvable identity: refuse
            return 'eligibility_error:' + (str(error) if isinstance(error, ValueError) else type(error).__name__)
        if any(h['dev'] for h in hits) or keys & e.names['dev']:
            return 'dev_s1'
        if any(h['benchmark'] for h in hits) or keys & e.names['benchmark']:
            return 'benchmark'
        plain = {str(n).casefold() for n in names} | {(item['dataset'] + '/' + item['scene'].split('/', 1)[-1]).casefold()}
        if plain & self.withheld:
            return 'withheld'
        if room in self.r0 or {room_of(n) for n in names if isinstance(n, str) and NATIVE.fullmatch(n)} & self.r0:
            return 'r0_reserve'
        item['room_key'] = room if not room.startswith('arkitscenes/') else (item.get('room') or room)
        return None


def decimal(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        x = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    return x if x.is_finite() else None


def correct(qtype, pred, answer):
    """True / False, or None when the GT cannot carry a relative tolerance (non-positive)."""
    if qtype in NUMERIC:
        p, a = decimal(pred), decimal(answer)
        if a is None or a <= 0:
            return None
        return p is not None and abs(p - a) <= REL_TOL * a
    if qtype in COUNT:  # exact digit strings: the sealed validator compares str(answer) == str(gt_answer)
        p, a = str(pred).strip(), str(answer).strip()
        return bool(re.fullmatch(r'\d+', a)) and p == a
    p, a = str(pred).strip(), str(answer).strip()
    return bool(re.fullmatch(r'[A-Z]', a)) and p == a


def masks_match(item, response):
    gt, sel = item.get('gt_instances'), response.get('selected')
    operands = item.get('operands') or list(gt or ())
    if not gt or not operands or set(gt) != set(operands):
        return False, 'mask_unverified'
    if not isinstance(sel, dict) or set(sel) != set(gt):
        return False, 'mask_operands_differ'
    for operand in operands:
        ids, got = gt[operand], list(sel.get(operand) or ())
        if not ids:
            return False, 'mask_unverified'
        if 'unmatched' in got or len(got) != len(set(got)) or set(got) != set(ids):
            return False, 'mask_mismatch:' + operand
    return True, None


def status_kind(status):
    if not isinstance(status, str):
        return 'no_status'
    text = status.strip()
    if text == 'ok':
        return 'ok'
    if any(f in text for f in OPERATOR_FAULTS):
        return 'operator_fault'
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines and all(REAL_FAILURE_LINE.fullmatch(l) for l in lines):
        return 'real_failure'
    return 'unknown_status'


def record_problem(item, response, *, head):
    """The Session record that ground_rows.pack consumes must exist and bind to the judged answer."""
    rec = response.get('record')
    if not isinstance(rec, dict) or any(k not in rec for k in RECORD_FIELDS):
        return 'record_missing'
    if rec['qid'] != item['qid'] or rec['type'] != item['type']:
        return 'record_identity'
    events, suffix = rec['events'], rec['suffix']
    if not isinstance(events, list) or not events or not isinstance(suffix, str):
        return 'record_events'
    cursor = 0
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get('call'), str) or not isinstance(event.get('response'), str):
            return 'record_events'
        at = suffix.find(event['call'] + '\n' + event['response'], cursor)
        if at < 0:
            return 'record_events'
        cursor = at + len(event['call']) + 1 + len(event['response'])
    if head:
        if rec.get('not_seen') or str(rec['answer']) != str(response.get('pred')).strip():
            return 'record_answer'
        if str(rec['gt_answer']).strip() != str(item['answer']).strip():
            return 'record_gt'
        if not suffix.endswith('\n</think>\n<answer>' + str(rec['answer']) + '</answer>'):
            return 'record_suffix'
    elif response['status'].strip().splitlines()[0].strip() not in suffix:
        return 'record_status'
    return None


def decide(item, response, eligibility):
    """Return (decision, reason) for one item. Any decision other than head leaves the item on its current form."""
    qtype = item.get('type')
    if qtype in EXCLUDED_TYPES or qtype not in MIX_TYPES:
        return 'drop', 'type_outside_mix'
    if qtype in NO_GRAMMAR:
        return 'drop', 'no_head_grammar'
    if response is None or response.get('qid') != item.get('qid'):
        return 'drop', 'no_response'
    if not isinstance(response.get('pipeline'), str) or not response['pipeline'].strip() or \
            not isinstance(response.get('pipeline_sha256'), str) or not SHA.fullmatch(response['pipeline_sha256']):
        return 'drop', 'response_without_provenance'
    why = eligibility.reason(item)
    if why:
        return 'drop', why
    kind = status_kind(response.get('status'))
    if kind not in ('ok', 'real_failure'):
        return 'drop', kind
    if kind == 'real_failure':
        bad = record_problem(item, response, head=False)
        return ('drop', bad) if bad else ('recovery', 'real_failure')
    right = correct(qtype, response.get('pred'), item.get('answer'))
    if right is None:
        return 'drop', 'nonpositive_gt'
    if not right:
        return 'direct', 'response_wrong'
    ok, why = masks_match(item, response)
    if not ok:
        return 'direct', why
    bad = record_problem(item, response, head=True)
    return ('drop', bad) if bad else ('head', 'right_and_masks_match')


def order_key(seed, qid):
    return hashlib.sha256(f'{seed}:{qid}'.encode()).hexdigest()


def select(decisions, *, cap=MAX_CAP, per_room=MAX_PER_ROOM, recovery_cap=None, seed='b08-20261116'):
    """Choose the minority family per type: head rows on direct-majority types, direct rows on head-majority
    types, plus recovery rows. Deterministic order by sha256(seed:qid); at most per_room rows per (type, room, form)."""
    recovery_cap = cap if recovery_cap is None else recovery_cap
    if not (0 < cap <= MAX_CAP and 0 < recovery_cap <= MAX_CAP and 0 < per_room <= MAX_PER_ROOM):
        raise ValueError('caps exceed the brief: at most 2,000 per (type, form) and 4 per (type, room, form)')
    chosen, used, seen = [], Counter(), Counter()
    for d in sorted(decisions, key=lambda d: order_key(seed, d['qid'])):
        form = d['decision']
        if form == 'drop':
            continue
        minority = form == 'recovery' or form != MAJORITY[d['type']]
        if not minority:
            continue
        limit = recovery_cap if form == 'recovery' else cap
        room_key = (d['type'], d['room_key'], form)
        if used[(d['type'], form)] >= limit or seen[room_key] >= per_room:
            continue
        used[(d['type'], form)] += 1
        seen[room_key] += 1
        chosen.append(d)
    return chosen, used


def run(items_path, responses_path, out_dir, *, cap=2000, per_room=4, seed='b08-20261116', auth=AUTH):
    eligibility = Eligibility(auth)
    responses = {}
    with open(responses_path) as f:
        lines = f.readlines()
    for line in lines:
        r = json.loads(line)
        if r['qid'] in responses:
            raise ValueError('duplicate response qid ' + r['qid'])
        responses[r['qid']] = r
    decisions, tally, qids = [], defaultdict(Counter), set()
    with open(items_path) as f:
        item_lines = f.readlines()
    for line in item_lines:
        item = json.loads(line)
        if item['qid'] in qids:
            raise ValueError('duplicate item qid ' + item['qid'])
        qids.add(item['qid'])
        r = responses.get(item['qid'])
        decision, reason = decide(item, r, eligibility)
        tally[item.get('type')][decision + ':' + reason] += 1
        decisions.append(dict(qid=item['qid'], type=item.get('type'), room=item.get('room'), room_key=item.get('room_key'),
                              scene=item.get('scene'),
                              decision=decision, reason=reason,
                              pipeline=(r or {}).get('pipeline'), pipeline_sha256=(r or {}).get('pipeline_sha256')))
    chosen, used = select(decisions, cap=cap, per_room=per_room, seed=seed)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / 'DECISIONS.jsonl', 'w') as f:
        for d in decisions:
            f.write(json.dumps(d, sort_keys=True) + '\n')
    with open(out / 'SELECTED.jsonl', 'w') as f:
        for d in chosen:
            f.write(json.dumps(d, sort_keys=True) + '\n')
    summary = dict(items=str(items_path), items_sha256=sha256(items_path), responses=str(responses_path),
                   responses_sha256=sha256(responses_path), code_sha256=sha256(__file__), pins=PINS,
                   params=dict(cap=cap, per_room=per_room, seed=seed, rel_tol=str(REL_TOL)), majority=MAJORITY,
                   tally={k: dict(v) for k, v in tally.items()}, selected={f'{t}|{f}': n for (t, f), n in used.items()},
                   decisions_sha256=sha256(out / 'DECISIONS.jsonl'), selected_sha256=sha256(out / 'SELECTED.jsonl'))
    (out / 'ASSIGN_SUMMARY.json').write_text(json.dumps(summary, indent=1, sort_keys=True))
    return summary


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--items', required=True)
    p.add_argument('--responses', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--cap', type=int, default=2000)
    p.add_argument('--per-room', type=int, default=4)
    p.add_argument('--seed', default='b08-20261116')
    a = p.parse_args()
    s = run(a.items, a.responses, a.out, cap=a.cap, per_room=a.per_room, seed=a.seed)
    print(json.dumps(dict(selected=s['selected'], decisions_sha256=s['decisions_sha256']), indent=1))
