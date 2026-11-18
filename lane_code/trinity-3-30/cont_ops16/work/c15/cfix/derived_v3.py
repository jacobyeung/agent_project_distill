"""DERIVED pooled rule (ORCH AMENDMENT 1108Z item 1; NOT the registered run): the registered tool pooled_harm_rule_v3.py,
imported unchanged, with every runaway counting read of the export scored as step 544 scored that item.
runaway = the B2048 arm force-closed its think at the 2,048-token budget on an object_counting item (lane count_diag's
definition, build_runaway_table.py); single = question without '(s) and ' (one category). No ledger is written.
usage: derived_v3.py --step S [--calibration] --read ITEMS.jsonl --manifest-s1 M --manifest-r0 M --x fetched/x [--export-receipt A] --output OUT.json"""
import argparse, importlib.util, json, re, sys
REG = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/pooled_rule/pooled_harm_rule_v3.py'
spec = importlib.util.spec_from_file_location('ph', REG); ph = importlib.util.module_from_spec(spec); spec.loader.exec_module(ph)
FAM = dict(main='dev-S1', a7='R0-dev')

IDMAP = '/scratch/jjyeung/orch_n30/cont_ops/work/h1read/evidence/ID_MAP.json'

def runaways(x):
    idm = json.load(open(IDMAP)); out = {}
    for fam in FAM:
        rows = [json.loads(l) for l in open('%s/%s/a0/results/budget_2048/0/items_a0.jsonl' % (x, fam)) if l.strip()]
        c = [r for r in rows if r.get('question_type') == 'object_counting']
        dec = lambda i: idm[i]['id'] if fam == 'a7' and i in idm else i
        run = {dec(r['id']): int(bool(re.search(r'\(s\)\s+and\s+', r['question']))) for r in c if r.get('forced_close')}
        out[fam] = dict(ids=run, items=len(c), single_items=sum(1 for r in c if not re.search(r'\(s\)\s+and\s+', r['question'])))
    return out

def main():
    a = argparse.ArgumentParser(); a.add_argument('--step', type=int, required=True); a.add_argument('--calibration', action='store_true')
    a.add_argument('--read', required=True); a.add_argument('--manifest-s1', required=True); a.add_argument('--manifest-r0', required=True)
    a.add_argument('--x', required=True); a.add_argument('--export-receipt'); a.add_argument('--output', required=True); a = a.parse_args()
    RW = runaways(a.x); base_rows = {}; swapped = {}
    orig = ph.load
    def load(path, family, types):
        rows = orig(path, family, types)
        if path == ph.BASE['S' if family == 'main' else 'R']['path']:
            base_rows[family] = rows; return rows
        b = base_rows[family]; n = 0
        for i in RW[family]['ids']:
            if i in rows and rows[i]['task_type'] == 'object_counting':
                rows[i] = dict(rows[i], score=b[i]['score']); n += 1
        swapped[family] = n
        return rows
    ph.load = load
    man = {'S': json.load(open(a.manifest_s1)), 'R': json.load(open(a.manifest_r0))}
    try:
        data = ph.prepare([a.read], man, a.step, a.calibration, export_receipt=a.export_receipt)
    except ph.Refused as e:
        sys.exit('REFUSED: %s' % e)
    res = ph.decide(data, a.step)
    rw = {FAM[f]: dict(runaways=len(v['ids']), single='%d/%d' % (sum(1 for m in v['ids'].values() if m == 0), v['single_items']),
                       multi='%d/%d' % (sum(1 for m in v['ids'].values() if m == 1), v['items'] - v['single_items']),
                       rescored_as_544=swapped.get(f)) for f, v in RW.items()}
    out = dict(rule='DERIVED (amendment 1108Z): registered v3 with runaway counting reads scored as step 544; not the registered run',
               registered_tool=REG, registered_tool_sha256=ph.sha(REG), step=a.step, calibration=a.calibration, read=a.read,
               read_sha256=ph.sha(a.read), runaways=rw, runaway_ids={FAM[f]: sorted(v['ids']) for f, v in RW.items()}, **ph.display(res))
    json.dump(out, open(a.output, 'w'), indent=1)
    f2 = lambda v: '[%+7.2f, %+7.2f]' % (100 * v[0], 100 * v[1])
    print('DERIVED rule (runaways scored as step 544); runaways:', json.dumps(rw))
    for r in res['types']:
        cell = lambda nm: '%+6.2f %s' % (100 * r[nm]['delta'], f2(r[nm]['ci95'])) if nm in r else '-'
        print('%-28s %-26s %-26s %+8.2f  %s   %s' % (r['type'], cell('dev_s1'), cell('r0_dev'), 100 * r['pooled_delta'], f2(r['interval']), 'FIRES' if r['fires'] else ''))
    m = res['mean']; print('%-28s %-26s %-26s %+8.2f  %s   %s' % ('mean of eight (H2 level)', '', '', 100 * m['delta'], f2(m['interval']), 'FIRES' if m['fires'] else ''))
    print('derived H1 fires on:', res['H1'], '| H2 fires:', res['H2'])

if __name__ == '__main__':
    main()
