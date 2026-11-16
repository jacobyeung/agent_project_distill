"""Per-item path assignment for the both-path mix (brief 08 part B).

Each training item gets exactly one decision from the deployed pipeline's response on that item:
  head      status 'ok', the answer is right (numeric within 15% of a non-negative plain-decimal GT in exact arithmetic;
            counts and option letters as exact strings, as ground_rows.validate compares them), every operand's
            accepted instance ids equal its non-empty GT ids (no 'unmatched', no extra operands, and no duplicate id:
            two accepted candidates on one GT instance are a grounding error even when the set is equal), and the
            Session record packs with the sealed ground_rows.pack and binds to that answer and to the item's GT
Every head or recovery record must carry record['replay'], the receipt of replay_receipt(): the sealed derivgen
replay of its exact events through a fresh Session of the producing pipeline (pipeline_sha256). Runtime semantics
(call validity per spec version, the status a call can print) are established there; assign.py checks offline that
calls parse as sealed forms with valid names, that no response holds an operator fault, and that head responses hold
no failure text.
  direct    the response is wrong, or its masks do not match GT, or GT instances are missing
  recovery  the status is the runtime's own '<name>: not seen | unresolved | box unavailable' text, the record's
            last call grounded <name> and printed exactly that status, and it packs with the sealed code; the recovery renderer replaces the final answer with the GT
            answer (trace ruling 2.4 recovery family), so the record's own final answer is never copied
  drop      ineligible or inconsistent identity (dev-S1, benchmark, withheld, R0 reserve, unresolvable, conflicting
            identifiers), type outside the mix or without ground grammar, operator fault, missing or unknown status,
            bad provenance, unusable record, malformed or negative GT
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
from decimal import Decimal, InvalidOperation, localcontext
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
# failure statuses the sealed runtime prints for a failed ground call (box_v313 replay_audit; trace ruling 2.4 (b))
REAL_FAILURE_LINE = re.compile(r'(?P<name>[^\n<>]+): (?P<state>not seen|unresolved|box unavailable)')
# any runtime failure text a head record may not contain (ground_v312, ground_v313, box_v313 response bodies)
HEAD_FAILURE_LINE = re.compile(r'(?:[^\n<>]+: (?:not seen|unresolved|box unavailable|0 found)|not seen|unresolved|'
                               r'unavailable|[^\n<>]* unavailable)')
REPLAY_FUNCTION = 'generator.derivgen_v7.derivgen.ground_v312.replay'
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
ALIAS = {'scannet': 'd1', 'scannetpp': 'd2', 'scannetppv2': 'd2', 'scannet++': 'd2', 'arkitscenes': 'd3',
         'd1': 'd1', 'd2': 'd2', 'd3': 'd3'}
NATIVE_NAME = {'d1': 'scannet', 'd2': 'scannetppv2', 'd3': 'arkitscenes'}
NATIVE_ID = {'d1': re.compile(r'scene\d{4}_\d{2}'), 'd2': re.compile(r'[0-9a-f]{10}'), 'd3': re.compile(r'\d{8}')}
ROOM_ID = {'d1': re.compile(r'scene\d{4}'), 'd2': NATIVE_ID['d2'], 'd3': NATIVE_ID['d3']}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def room_of(short, ident):
    """Physical room: ScanNet sceneNNNN (all rescans), ScanNet++ scene id, ARKitScenes capture id."""
    if short == 'd1':
        return 'scannet/' + ident[:9]
    return ('scannetpp/' if short == 'd2' else 'arkitscenes/') + ident


class Eligibility:
    """Refuses dev-S1, benchmark, withheld and R0 reserve rooms with the sealed Exclusions class and pinned lists.
    Every identifier the item carries must resolve to the same physical room; otherwise the item is refused."""

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
        self.withheld_names = {a for v in withheld['aliases'].values() for a in v} | set(withheld['rooms'])
        self.r0 = {l.strip() for l in (Path(auth) / 'R0_ROOMS.txt').read_text().splitlines() if l.strip()}
        self.r0 |= {v['room'] for v in json.loads((Path(auth) / 'R0_SCENES.json').read_text())['captures'].values()}
        self.alias = json.loads((Path(auth) / 'alias_map.json').read_text())
        self.withheld_rooms = set()
        for name in self.withheld_names:
            try:
                self.withheld_rooms.add(self.resolve(name)[1])
            except ValueError:
                pass

    def resolve(self, name):
        """'<dataset>/<id>' (capture, alias token or room) -> (canonical capture or None, physical room)."""
        if not isinstance(name, str) or name.count('/') < 1:
            raise ValueError('identifier_not_qualified')
        prefix, ident = name.split('/', 1)
        short = ALIAS.get(prefix.casefold())
        if short is None:
            raise ValueError('unknown_dataset')
        if '/' in ident:  # alias-map keys carry the native prefix, e.g. d1/scannet/scene0000_00
            inner, ident = ident.split('/', 1)
            if ALIAS.get(inner.casefold()) != short:
                raise ValueError('dataset_scene_mismatch')
        mapped = self.alias.get(f'{short}/{ident}') or self.alias.get(f'{short}/{NATIVE_NAME[short]}/{ident}')
        if mapped:
            mprefix, mident = mapped.split('/', 1)
            if ALIAS.get(mprefix) != short or not NATIVE_ID[short].fullmatch(mident):
                raise ValueError('alias_map_entry_malformed')
            return f'{NATIVE_NAME[short]}/{mident}', room_of(short, mident)
        if NATIVE_ID[short].fullmatch(ident):
            return f'{NATIVE_NAME[short]}/{ident}', room_of(short, ident)
        if ROOM_ID[short].fullmatch(ident):
            return None, room_of(short, ident)
        raise ValueError('identifier_unresolved')

    def reason(self, item):
        """Return a refusal reason, or None when eligible; sets item['room_key'] for the per-room cap."""
        e = self.exclusions
        try:
            scene = item['scene']
            primary = scene if '/' in scene else item['dataset'] + '/' + scene
            if '/' in scene and ALIAS.get(scene.split('/', 1)[0].casefold()) != ALIAS.get(str(item['dataset']).casefold()):
                raise ValueError('dataset_scene_mismatch')
            canonical, room = self.resolve(primary)
            if canonical is None:
                raise ValueError('scene_is_not_a_capture')
            names = [primary, canonical, room]
            for key in ('room', 'physical_group', 'native', 'canonical'):
                value = item.get(key)
                if value is None:
                    continue
                if self.resolve(value)[1] != room:
                    raise ValueError('identity_conflict:' + key)
                names.append(value)
            keys = set()
            for n in names:
                keys |= e.identifiers({'scene': n.replace('scannet++/', 'scannetpp/', 1) if n.startswith('scannet++/') else n})
            hit = e.matched(keys)
        except Exception as error:  # unknown prefix, malformed, unresolvable or conflicting identity: refuse
            return 'eligibility_error:' + (str(error) if isinstance(error, ValueError) else type(error).__name__)
        if hit['dev']:
            return 'dev_s1'
        if hit['benchmark']:
            return 'benchmark'
        if room in self.withheld_rooms or set(names) & self.withheld_names:
            return 'withheld'
        if room in self.r0:
            return 'r0_reserve'
        item['room_key'] = room
        return None


PLAIN_NUMBER = re.compile(r'-?\d{1,15}(?:\.\d{1,15})?')


def decimal(value):
    """Plain decimal strings only (no exponent, no whitespace, at most 15 + 15 digits), so arithmetic is exact."""
    if not isinstance(value, str) or not PLAIN_NUMBER.fullmatch(value):
        return None
    return Decimal(value)


def gt_problem(qtype, answer, options=()):
    """The item's GT must be a valid label for its type (an option letter must name one of the item's options);
    negative numeric GT has no relative tolerance."""
    if qtype in NUMERIC:
        a = decimal(answer)
        return 'gt_malformed' if a is None else 'negative_gt' if a < 0 else None
    if qtype in COUNT:
        return None if isinstance(answer, str) and re.fullmatch(r'\d+', answer) else 'gt_malformed'
    if not (isinstance(answer, str) and re.fullmatch(r'[A-Z]', answer)):
        return 'gt_malformed'
    if str(TREE) not in sys.path:
        sys.path.insert(0, str(TREE))
    from trace_format.ground_v312 import option_map
    try:
        return None if answer in option_map(options or []) else 'gt_not_an_option'
    except ValueError:
        return 'options_malformed'


def correct(qtype, pred, answer):
    """Exact comparison of byte strings for counts and options; numeric within 15% in exact arithmetic.
    Call only after gt_problem(qtype, answer) is None."""
    if qtype in NUMERIC:
        p, a = decimal(pred), decimal(answer)
        if p is None:
            return False
        with localcontext() as ctx:
            ctx.prec = 64  # exact for at most 15 + 15 digits
            return abs(p - a) <= REL_TOL * a
    return isinstance(pred, str) and pred == answer


def masks_match(item, response):
    gt, sel = item.get('gt_instances'), response.get('selected')
    operands = item.get('operands') or list(gt or ())
    if not gt or not operands or set(gt) != set(operands):
        return False, 'mask_unverified'
    if not isinstance(sel, dict) or set(sel) != set(gt):
        return False, 'mask_operands_differ'
    for operand in operands:
        ids, got = gt[operand], sel.get(operand)
        if not isinstance(ids, list):
            return False, 'mask_unverified'
        if not isinstance(got, list):
            return False, 'mask_mismatch:' + operand
        if not ids or not all(isinstance(i, str) and i and i != 'unmatched' for i in ids):
            return False, 'mask_unverified'
        if not all(isinstance(i, str) and i for i in got) or 'unmatched' in got or len(got) != len(set(got)) or set(got) != set(ids):
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


def call_patterns():
    """The call forms the sealed Session and calculator execute (ground_v312, ground_v313, box_v313, calculator)."""
    if str(TREE) not in sys.path:
        sys.path.insert(0, str(TREE))
    from trace_format import box_v313, calculator, ground_v312, ground_v313
    return (ground_v312.GROUND, ground_v312.GAP, ground_v313.INSTANCE, ground_v313.SURFACE, ground_v313.EXTENT,
            box_v313.GROUND, box_v313.GAP, box_v313.CAMGAP, *(re.compile(f) for _, f in calculator._FORMS))


def call_ok(call, patterns):
    """A call parses as a sealed form and every object name passes the sealed valid_name."""
    from trace_format.ground_v312 import RowRefusal, valid_name
    if not any(p.fullmatch(call) for p in patterns):
        return False
    try:
        for name in re.findall(r'(?:obj|a|b)="([^"]*)"', call):
            valid_name(name)
    except RowRefusal:
        return False
    return True


def events_sha256(events):
    return hashlib.sha256(json.dumps(events, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def replay_receipt(record, session, pipeline_sha256):
    """For the cache lane: replay the record's exact events through a fresh Session of the producing pipeline with
    the sealed derivgen replay (re-executes every call and compares response text) and return the receipt
    assign.py requires as record['replay']."""
    if str(TREE) not in sys.path:
        sys.path.insert(0, str(TREE))
    from generator.derivgen_v7.derivgen.ground_v312 import replay
    replay(record, session)
    return dict(function=REPLAY_FUNCTION, ok=True, session_sha256=pipeline_sha256, events_sha256=events_sha256(record['events']))


def response_body(event):
    return [l.strip() for l in event['response'].replace('<tool_response>', '').replace('</tool_response>', '').splitlines()
            if l.strip()]


def sealed_pack(item, record, *, head=True):
    """Pack the record with the sealed ground_rows.pack (validate_evidence + render_ground) after setting the
    builder's membership flags; refuse head records whose own flags contradict them (a failure record may carry
    not_seen, which the runtime sets on failures)."""
    if (head and record.get('not_seen')) or record.get('gt_agrees') is False or record.get('training_admitted') is True:
        raise ValueError('record_flags')
    if str(TREE) not in sys.path:
        sys.path.insert(0, str(TREE))
    from student_pilot import ground_rows
    if record.get('spec_version') not in ground_rows.FORMS:
        raise ValueError('record_spec_version')
    row = dict(record, gt_agrees=True, training_admitted=False, not_seen=False)
    packed = ground_rows.pack(row, {})
    target, spans, _ = ground_rows.render_ground(packed['events'], packed['answer'])
    if target != row['suffix'] or not spans:
        raise ValueError('record_render')
    if head and item['type'] not in NUMERIC:
        # counts and options: the sealed validate must accept the packed row as it stands; its absolute-distance
        # rule (GT to 2 dp within 5%) fits GT-geometry rows only and waits for the amended validate (spec item 7)
        ground_rows.validate(packed)
    return packed


def record_problem(item, response, *, head):
    """The Session record ground_rows.pack consumes must exist, pack with the sealed code and bind to the judgement."""
    rec = response.get('record')
    if not isinstance(rec, dict) or any(k not in rec for k in RECORD_FIELDS):
        return 'record_missing'
    if rec['qid'] != item['qid'] or rec['type'] != item['type']:
        return 'record_identity'
    events = rec['events']
    if not isinstance(events, list) or not events or not all(
            isinstance(ev, dict) and isinstance(ev.get('call'), str) and isinstance(ev.get('response'), str) for ev in events):
        return 'record_events'
    patterns = call_patterns()
    if not all(call_ok(ev['call'], patterns) for ev in events):
        return 'record_call_grammar'
    receipt = rec.get('replay')
    if not (isinstance(receipt, dict) and receipt.get('function') == REPLAY_FUNCTION and receipt.get('ok') is True
            and receipt.get('session_sha256') == response['pipeline_sha256']
            and receipt.get('events_sha256') == events_sha256(events)):
        return 'record_replay_missing'
    if any(f in ev['response'] for ev in events for f in OPERATOR_FAULTS):
        return 'record_operator_fault'
    prose = rec['suffix']
    for ev in events:
        prose = prose.replace(ev['call'] + '\n' + ev['response'], '', 1)
    if '<' in re.sub(r'</?(?:think|answer)>', '', prose):
        return 'record_unrecorded_tag'
    if rec['gt_answer'] != item['answer'] or not isinstance(rec['answer'], str):
        return 'record_gt'
    if rec['options'] != (item.get('options') or []) or ('question' in item and rec['question'] != item['question']):
        return 'record_question'
    if item['type'] in OPTION and (not rec['options'] or rec.get('answer_content') is None):
        return 'record_options'
    try:
        sealed_pack(item, rec, head=head)
    except Exception as error:
        return 'sealed_pack_refused:' + (str(error) or type(error).__name__)[:80]
    if head:
        if any(HEAD_FAILURE_LINE.fullmatch(l) for ev in events for l in response_body(ev)):
            return 'record_failure_in_head'
        if rec['answer'] != response.get('pred'):
            return 'record_answer'
        if item['type'] in OPTION:
            from trace_format.ground_v312 import option_map
            try:
                content = option_map(item['options']).get(rec['answer'])
            except ValueError:
                return 'record_options'
            if content is None or content != rec['answer_content']:
                return 'record_answer_content'
        return None
    # recovery: some response must be the failure status itself, and nothing after it may be a successful call
    status = [l.strip() for l in response['status'].strip().splitlines()]
    failed = [i for i, ev in enumerate(events) if response_body(ev) == status]
    if not failed:
        return 'record_status'
    if failed[-1] != len(events) - 1:
        return 'record_call_after_failure'
    called = re.match(r'<ground obj="([^"<>]+)"', events[failed[-1]]['call'])
    names = [REAL_FAILURE_LINE.fullmatch(l)['name'] for l in status]
    if called is None or names != [called[1]]:
        return 'record_status_operand'
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
    bad = gt_problem(qtype, item.get('answer'), item.get('options'))
    if bad:
        return 'drop', bad
    kind = status_kind(response.get('status'))
    if kind not in ('ok', 'real_failure'):
        return 'drop', kind
    if kind == 'real_failure':
        bad = record_problem(item, response, head=False)
        return ('drop', bad) if bad else ('recovery', 'real_failure')
    if not correct(qtype, response.get('pred'), item['answer']):
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
