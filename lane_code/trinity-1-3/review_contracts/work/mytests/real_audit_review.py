"""Reviewer's rerun of the real-row audit with an independent operand source (generator roles)."""
import collections, copy, gzip, json, sys
TREE = sys.argv[1]
sys.path.insert(0, TREE)
from trace_format.contracts import contract_epoch
from student_pilot.training_contract import audit_training_contract, call_responses
from student_pilot.phrases import candidate_phrases, normalize_phrase
X = '/scratch/jjyeung/orch_n30/contracts_rebuild/work/real/x/'
m = json.load(open(X + '66caacf5c9191457.json'))
out = dict(verdicts=collections.Counter(), roles=collections.Counter(), examples=collections.defaultdict(list), corrupt={})
sample = []
with contract_epoch(True):
    for d in m['sets']:
        for role, pin in d['files'].items():
            with gzip.open(X + pin['sha256'][:16] + '.jsonl.gz', 'rt') as f:
                for line in f:
                    r = json.loads(line)
                    typ = r.get('question_type', r.get('type'))
                    if typ not in ('object_abs_distance', 'room_size_estimation'):
                        continue
                    try:
                        v = audit_training_contract([r])[0]
                    except Exception as e:
                        v = 'RAISED ' + type(e).__name__ + ': ' + str(e)[:80]
                    out['verdicts'][f'{role}:{typ}:{v}'] += 1
                    if typ == 'object_abs_distance' and role == 'packed' and len(sample) < 300 and any(e.get('kind') == 'ground_call' for e in r.get('events', [])):
                        sample.append(r)
                    if typ == 'object_abs_distance' and role == 'admitted' and 'roles' in r:
                        a, b = r['roles'].get('a'), r['roles'].get('b')
                        try:
                            u = set(candidate_phrases(r['question'], r.get('options', []), None))
                            ra, rb = normalize_phrase(a), normalize_phrase(b)
                            key = ('both_in' if {ra, rb} <= u else 'missing') + ('|exact' if u == {ra, rb} else '|extra')
                        except Exception as e:
                            key = 'RAISED ' + type(e).__name__
                            u = set()
                        out['roles'][key] += 1
                        if not key.startswith('both_in|exact') and len(out['examples'][key]) < 5:
                            out['examples'][key].append(dict(qid=r['qid'], q=r['question'], roles=r['roles'], parser=sorted(u)))
                        # operands actually called vs roles
                        called = [c.split('"')[1] for c, _ in call_responses(r) if isinstance(c, str) and c.startswith('<ground obj="')]
                        k2 = 'calls==roles' if [normalize_phrase(x) for x in called] == [normalize_phrase(a), normalize_phrase(b)] else 'calls!=roles'
                        out['roles'][k2] += 1
    # corruption: per-row deferral, never abort
    def w(t): return t
    cases = {}
    def mutate(r, how):
        r = copy.deepcopy(r); ev = r['events']
        resp = [e for e in ev if e.get('kind', '').endswith('_response') or 'response' in e]
        if how == 'drop_last_response':
            ev.remove(resp[-1])
        elif how == 'operator_fault':
            resp[0]['text'] = 'error: Routed policy requires a fixed named candidate universe; answer directly from the video'
            resp[0].pop('response', None)
        elif how == 'not_seen_then_gap':
            name = [e for e in ev if e.get('kind') == 'ground_call'][0]['token'].split('"')[1]
            resp[0]['text'] = name + ': not seen'
        elif how == 'heading_unavailable_then_gap':
            name = [e for e in ev if e.get('kind') == 'ground_call'][0]['token'].split('"')[1]
            resp[0]['text'] = name + ': heading unavailable\nsize 0.50 x 0.40 x 0.30 m'
        elif how == 'quote_in_question':
            r['question'] = r['question'].replace('the ', 'the "', 1)
        elif how == 'call_token_none':
            [e for e in ev if e.get('kind') == 'ground_call'][0]['token'] = None
        elif how == 'routing_not_dict':
            r['routing'] = 'x'
        return r
    for how in ('drop_last_response', 'operator_fault', 'not_seen_then_gap', 'heading_unavailable_then_gap', 'quote_in_question', 'call_token_none', 'routing_not_dict'):
        c = collections.Counter()
        for r in sample[:100]:
            try:
                c[str(audit_training_contract([mutate(r, how)])[0])] += 1
            except Exception as e:
                c['RAISED ' + type(e).__name__ + ': ' + str(e)[:60]] += 1
        out['corrupt'][how] = dict(c)
print(json.dumps(dict(verdicts=dict(out['verdicts']), roles=dict(out['roles']), corrupt=out['corrupt']), indent=1))
json.dump(dict(verdicts=dict(out['verdicts']), roles=dict(out['roles']), examples=dict(out['examples']), corrupt=out['corrupt'], sample_events_kinds=[e.get('kind') for e in sample[0]['events']] if sample else None), open(sys.argv[2], 'w'), indent=1)
