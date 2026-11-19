"""Print 10 distance traces from raw journals beside the reader's usage category."""
import glob, json, re, sys
IN = '/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/'
READS = {'A4': IN + 'A4/ret/metadata/reads/0', 'b1r1': IN + 'bases/b1/work/ret/metadata/reads/1'}
items = {i['id']: i for i in json.load(open(IN + 'A4/src/items/devs1_routed.json'))['items']}
res = json.load(open('/scratch/jjyeung/orch_n30/sb_crrev2/scratch/out/t0/callrate.json'))['per_item']


def journal(name):
    rows = {}
    for p in sorted(glob.glob(READS[name] + '/metadata/journals/*/*/items.jsonl')):
        for line in open(p):
            r = json.loads(line)
            rows[r['id']] = r
    return rows


PICK = [('A4', 'vsi590k_163095'), ('A4', 'vsi590k_168046')]
J = {k: journal(k) for k in READS}
side = {'A4': 'a', 'b1r1': 'b'}
want = {('A4', 'ft', 'follow_converted'), ('A4', 'm', 'follow_converted'), ('A4', 'cm', 'copied_unconverted'),
        ('A4', 'ft', 'copied_unconverted'), ('A4', 'cm', 'follow_converted'), ('A4', 'in', 'follow_converted'),
        ('b1r1', 'in', 'copied_unconverted'), ('b1r1', 'in', 'follow_converted'), ('b1r1', 'cm', 'copied_unconverted'),
        ('b1r1', 'cm', 'follow_converted')}
picked = []
for read in ('A4', 'b1r1'):
    for k in sorted(J[read]):
        v = res[side[read]].get(k)
        if not v or v['type'] != 'object_abs_distance':
            continue
        key = (read, v['unit'], v['usage_category'])
        if key in want:
            want.discard(key)
            picked.append((read, k))
for read, k in picked:
    r, it, v = J[read][k], items[k], res[side[read]][k]
    o = r['output']
    print('=' * 100)
    print(read, k, '| Q:', it['question'], '| GT:', it['ground_truth'])
    for rec in o['calls'].get('records', []):
        resp = (rec.get('response') or '').replace('\n', ' / ')
        print('  CALL', rec.get('call'), '| served', rec.get('served'), '| RESP', resp[-260:])
    t = o.get('text', '')
    tail = t.rsplit('</think>', 1)[-1] if '</think>' in t else '<no think close>'
    print('  FINAL:', tail.strip()[:200].replace('\n', ' '), '| finish', o.get('finish'))
    print('  READER: cat', v['usage_category'], '| decision', v['response_decision'], '| parsed', v['parsed_answer'],
          '| unit', v['unit'], '| conv_fail', v['conversion_failure'], '| score', v['score'])
