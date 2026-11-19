"""ORCH ORDER 0351Z item 4: in every bound N recovery row (760 of recovery_v3 58389a67), does the trace show the failed tool call
before the answer? Lists any row that answers without a call line, with a gap call, or without a failed status first."""
import json, re, sys
from collections import Counter
W = '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16b/work/build16'
P = '/scratch/jjyeung/n30_mirror/rows_r1/out/recovery_v3/rows.jsonl'
bound = set(json.load(open(W + '/proofs/census/membership.json'))['sources']['recovery']['rows'])
c = Counter(); bad = []; phr = Counter()
for line in open(P):
    if not line.strip(): continue
    r = json.loads(line)
    if r['qid'] not in bound: continue
    t = r['target']; c['rows'] += 1
    calls = [(m.start(), m.group(1)) for m in re.finditer(r'<(ground|gap|move|turn)\b', t)]
    fail = [m.start() for m in re.finditer(r'<tool_response>\n[^\n]*: (?:not seen|box unavailable)\n?</tool_response>', t)]
    ans = t.rfind('<answer>'); stop = t.find('do not call it again')
    kinds = Counter(k for _, k in calls)
    c['first_call_is_ground'] += bool(calls and calls[0][1] == 'ground')
    c['has_failed_status'] += bool(fail)
    c['failed_before_answer'] += bool(fail and min(fail) < ans)
    c['stop_sentence_after_failure'] += bool(fail and stop > min(fail))
    c['gap_calls'] += kinds['gap']
    c['ground_calls_%d' % kinds['ground']] += 1
    c['answer_after_all_calls'] += bool(calls and ans > max(p for p, _ in calls))
    phr['sighting_lines'] += len(re.findall(r'\bI (?:can )?see the [^\n]+ in frame \d+', t))
    if not calls or not fail or kinds['gap'] or ans < (min(fail) if fail else 0): bad.append(r['qid'])
json.dump(dict(counts=c, phrases=phr, rows_without_call_or_failure=bad), open(sys.argv[1], 'w'), indent=1)
print(dict(c)); print('rows answering without a call line or failed status first:', len(bad), bad[:10]); print(dict(phr))
