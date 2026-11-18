"""Per-read runaway classification of every counting item, per export and set (lane count_diag).
Reads the scored B2048 items and the 16k generations of each export (paths in cd_load.SOURCES); writes RUNAWAY_BY_ITEM.tsv.
runaway = the B2048 arm force-closed the think at its 2,048-token budget (forced_close); cap16k = the 16k generation hit 16,384 tokens.
form: S544_DETECT_MATCH, V5_PROC, FS_LIST, TOTALS, OTHER (first match in the order TOTALS, FS_LIST, V5_PROC, S544_DETECT_MATCH)."""
import json, re, hashlib
from cd_load import load, load_on16k, as_num
D, SH1 = load(); O, SH2 = load_on16k()
def form(g):
    h = g[:600]
    if re.search(r'add them|in total|\d+ \+ \d+ =', g): return 'TOTALS'
    if re.search(r'at its first appearance|by the frame where it first appears|first appears?:|first seen:|by first appearance:|using its first-seen frame:', h): return 'FS_LIST'
    if re.search(r'across the frames, and count it once|count each once across the frames', h): return 'V5_PROC'
    if re.search(r'find the frames that show|detections across those frames', h): return 'S544_DETECT_MATCH'
    return 'OTHER'
LIST_CAP = re.compile(r'(?:at its first appearance|by the frame where it first appears|by first appearance|using its first-seen frame|first appears?|first seen)\s*:\s*([^\n]*)')
def list_stats(g):
    m = LIST_CAP.search(g)
    if not m: return 0, 0, ''
    ents = [e.strip(' .') for e in m.group(1).split(';') if e.strip(' .')]
    start = ''
    for j in range(max(0, len(ents) - 9)):
        if len(set(ents[j:j + 10])) == 1: start = j + 1; break
    return len(ents), len(ents) - len(set(ents)), start
cols = ['export', 'set', 'item_id', 'room', 'multi_category', 'truth', 'answer_b2048', 'score_b2048', 'score_step544_b2048',
        'forced_close_b2048', 'cap16k', 'output_tokens_16k', 'form_16k', 'list_entries_16k', 'list_repeats_16k', 'loop_start_entry']
out = ['\t'.join(cols)]
for ex in D:
    for s in D[ex]:
        for i in sorted(D[ex][s]):
            b = D[ex][s][i]; o = O[ex][s][i]; g = o['raw_generation'] or ''
            n, rep, st = list_stats(g)
            out.append('\t'.join(str(v) for v in [ex, s, i, b['room'], int(bool(re.search(r'\(s\)\s+and\s+', b['question']))), b['ground_truth'],
                       (b['extracted_answer'] or '').replace('\t', ' '), b['score'], D['S544'][s][i]['score'], int(bool(b['forced_close'])),
                       int(bool(o['hit_token_cap'])), o['output_tokens'], form(g), n, rep, st]))
open('RUNAWAY_BY_ITEM.tsv', 'w').write('\n'.join(out) + '\n')
json.dump({**SH1, **SH2}, open('RUNAWAY_SOURCES_SHA256.json', 'w'), indent=1)
print(len(out) - 1, 'rows', hashlib.sha256(open('RUNAWAY_BY_ITEM.tsv', 'rb').read()).hexdigest())
