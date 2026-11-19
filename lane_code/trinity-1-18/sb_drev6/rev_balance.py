"""Teaching-subset predictability of the clause, and room recheck through the tiered alias map."""
import collections as C, json, pickle, re, sqlite3, sys, types
from pathlib import Path

HERE = Path(__file__).resolve().parent; W = HERE / 'work'
B = Path('/scratch/jjyeung/orch_n30/sb_rowD6/out')
DB = '/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
TREE = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
CFG = json.load(open(TREE.parents[0] / 'build19/inputs/config.json'))
ALIAS = '/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json'
TEACHER = '/scratch/jjyeung/orch_n30/sb_alias2/work/TEACHER_K1.raw'
LISTS = {'R0': '/scratch/jjyeung/n30_mirror/rows_r1/work/codeB/authority_cache/R0_ROOMS.txt',
         'withheld-80': '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16/fixtures/work/shared/WITHHELD_ROOMS_80.json',
         'dev-S1': '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16/fixtures/work/kit07ca49df_meta/m/k/dev_scene_exclusions.json',
         'BENCH v2': '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16/fixtures/work/kit07ca49df_meta/m/k/benchmark_scene_exclusions.json'}
sys.path.insert(0, str(TREE))
from student_pilot import r1_rooms


def opts(r):
    return {m[1]: m[2].strip().lower() for m in (re.fullmatch(r'([A-Z])\.\s*(.+)', s) for s in r['student_input']['options'])}


def bayes(rows, f):
    """Accuracy of the best clause guess given feature f (majority class per feature value)."""
    tab = C.defaultdict(C.Counter)
    for r in rows: tab[f(r)][r['cl']] += 1
    return round(sum(max(c.values()) for c in tab.values()) / len(rows), 4), len(tab)


def main():
    cen = pickle.load(open(W / 'census.pkl', 'rb')); D = cen['dirrows']
    con = sqlite3.connect('file:' + DB + '?mode=ro&immutable=1', uri=True)
    new = [json.loads(l) for l in open(B / 'NEW_ROWS.jsonl')]
    smap = {m['qid']: m for m in map(json.loads, open(B / 'SOURCE_MAP.jsonl'))}
    src = [json.loads(con.execute('select row from rows where i=?', (smap[r['qid']]['source_i'],)).fetchone()[0]) for r in new]
    out = {}
    # Rooms: N's Rooms class, tiered alias map substituted for the alias lookup.
    rooms = r1_rooms.Rooms(CFG['r1_training']['room_authority'])
    rooms.aliases = {k: v['canonical'] for k, v in json.load(open(ALIAS))['aliases'].items()}
    teacher = json.load(open(TEACHER))
    k1 = {rooms.room(c['canonical']) for c in teacher['captures'] if c['k1_split'] == 'heldout'}
    sets = {'K1': k1 | rooms.k1, 'R0': rooms.r0 | set(Path(LISTS['R0']).read_text().split()),
            'withheld-80': set(json.load(open(LISTS['withheld-80']))['rooms']),
            'dev-S1': set(json.load(open(LISTS['dev-S1']))['physical_groups']),
            'BENCH v2': set(json.load(open(LISTS['BENCH v2']))['physical_groups'])}
    hits = C.Counter(); unresolved = 0; mismatch = 0
    for r in new + src:
        canon, how = rooms.canonical(r)
        if not canon: unresolved += 1; continue
        room = rooms.room(canon)
        if room != smap.get(r['qid'], {}).get('room', room): mismatch += 1
        for k, v in sets.items():
            if room in v: hits[k] += 1
    out['rooms_tiered'] = dict(rows=len(new) + len(src), unresolved=unresolved, hits=dict(hits), source_map_room_mismatch=mismatch,
                               list_sizes={k: len(v) for k, v in sets.items()})
    # Teaching subset: sources + new rows.
    names_seen = set(); names_step = set()
    for m in D.values():
        if m['fam'] == 'medium': continue
        r = None
    teach = []
    for r, s in zip(new, src):
        for row, isnew in ((s, False), (r, True)):
            q = row['student_input']['question']
            first = row['target'][len('<think>\n'):].split('\n', 1)[0]
            op = 'Seen' if first.startswith('Seen:') else 'Step 1'
            cl = row.get('facing') or 'toward'
            mq = smap[r['qid']]['objects']
            masked = q
            for n in sorted(set(mq), key=len, reverse=True): masked = masked.replace(n, '<N>')
            masked = re.sub(r'\b(facing away from|turned away from|with my back to|face away from|face toward|facing toward|facing|looking at|looking toward|look toward|toward|face|ahead)\b', '<C>', masked)
            teach.append(dict(cl=cl, op=op, new=isnew, fam=row['question_type'].rsplit('_', 1)[1], letter=row['answer'],
                              label=opts(row)[row['answer']], dataset=row['dataset'], nopt=len(row['student_input']['options']),
                              order=tuple(row['student_input']['options']), names=tuple(mq), masked=masked.split('\n')[0],
                              fps=row['student_input'].get('fps'), nfr=len(row['student_input']['frames']), pool=s['pool']))
    out['teaching_rows'] = len(teach)
    cells = C.Counter((t['op'], t['cl']) for t in teach); out['opening_clause'] = {'|'.join(k): v for k, v in cells.items()}
    for key in ('label', 'letter', 'dataset', 'nfr', 'fps'):
        out['by_' + key] = {f'{o}|{c}': dict(C.Counter(t[key] for t in teach if (t['op'], t['cl']) == (o, c)).most_common(8)) for o, c in sorted(cells)}
    # Names of each opening family across the whole admitted v7 easy/hard population.
    fam_names = C.defaultdict(set)
    for t in teach: fam_names[t['op'] if not t['new'] else ('Step 1' if t['cl'] == 'away' else 'Seen')].update(t['names'])
    seen_only = fam_names['Seen']; step_only = fam_names['Step 1'] - fam_names['Seen']
    out['name_sets'] = dict(seen_family=len(fam_names['Seen']), step_family=len(fam_names['Step 1']), overlap=len(fam_names['Seen'] & fam_names['Step 1']))
    tmpl = lambda t: 'new' if t['masked'].startswith('At the <N>') else 'old'
    family_by_names = lambda t: all(n in fam_names['Seen'] for n in t['names'])
    feats = {
        'opening': lambda t: t['op'],
        'template': tmpl,
        'answer_letter': lambda t: t['letter'],
        'answer_label': lambda t: t['label'],
        'dataset': lambda t: t['dataset'],
        'names_all_in_Seen_family_set': family_by_names,
        'masked_question_wording': lambda t: t['masked'],
        'template+dataset': lambda t: (tmpl(t), t['dataset']),
        'template+names_all_in_Seen_family_set': lambda t: (tmpl(t), family_by_names(t)),
        'template+frames_fps': lambda t: (tmpl(t), t['nfr'], t['fps']),
        'template+answer_letter': lambda t: (tmpl(t), t['letter']),
        'template+option_order': lambda t: (tmpl(t), t['order']),
        'opening+answer_letter': lambda t: (t['op'], t['letter']),
        'opening+answer_label': lambda t: (t['op'], t['label']),
    }
    out['clause_bayes_accuracy'] = {k: bayes(teach, f) for k, f in feats.items()}
    # Old-template (benchmark-style) rows only: does the opening family still fix the clause?
    old = [t for t in teach if tmpl(t) == 'old']
    out['old_template_only'] = dict(rows=len(old), by_opening_clause=dict(C.Counter(f"{t['op']}|{t['cl']}" for t in old)),
                                    names_family_acc=bayes(old, family_by_names), dataset_acc=bayes(old, lambda t: t['dataset']))
    newr = [t for t in teach if tmpl(t) == 'new']
    out['new_template_only'] = dict(rows=len(newr), by_opening_clause=dict(C.Counter(f"{t['op']}|{t['cl']}" for t in newr)),
                                    names_family_acc=bayes(newr, family_by_names), dataset_acc=bayes(newr, lambda t: t['dataset']))
    out['source_pools'] = {f'{o}|{c}': dict(C.Counter(t['pool'] for t in teach if (t['op'], t['cl']) == (o, c)).most_common(6)) for o, c in sorted(cells)}
    (W / 'BALANCE_REVIEW.json').write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


if __name__ == '__main__':
    main()


def wording_only():
    """Old-template rows: clause predicted from the clause-masked wording."""
    import sqlite3
    con = sqlite3.connect('file:' + DB + '?mode=ro&immutable=1', uri=True)
    smap = [json.loads(l) for l in open(B / 'SOURCE_MAP.jsonl')]
    tab = C.defaultdict(C.Counter)
    for m in smap:
        s = json.loads(con.execute('select row from rows where i=?', (m['source_i'],)).fetchone()[0])
        q = s['student_input']['question'].split('\n')[0]
        for n in sorted(set(m['objects']), key=len, reverse=True): q = q.replace(n, '<N>')
        q = re.sub(r'\b(facing away from|turned away from|with my back to|facing toward|facing|looking at|looking toward|look toward|toward|face|ahead)\b', '<C>', q)
        tab[q][m['source_clause']] += 1
    acc = sum(max(c.values()) for c in tab.values()) / len(smap)
    both = {k: dict(v) for k, v in tab.items() if len(v) > 1}
    print(json.dumps(dict(old_template_rows=len(smap), wordings=len(tab), clause_acc_from_masked_wording=round(acc, 4), wordings_with_both_clauses=both), indent=1))
