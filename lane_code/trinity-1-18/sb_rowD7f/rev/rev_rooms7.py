"""How N's w20 admits v7 direction sources, whether the same path admits the D7 twins, and which cell each lands in.

No sb_rowD* code is imported. N code runs unmodified from the sealed w20 tree; torch is stubbed inert.
"""
import ast, collections as C, copy, hashlib, json, sqlite3, sys, types
from pathlib import Path

HERE = Path(__file__).resolve().parent; W = HERE / 'work'
B = Path('/scratch/jjyeung/orch_n30/sb_rowD7f/out')  # sb_rowD7f: filtered rows
DB = '/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
TREE = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w20/work/tree_r1')
SEAL = json.load(open(TREE.parents[1] / 'out/TREE_SEAL.json'))
CFG = json.load(open(TREE.parents[0] / 'build20/inputs/config.json'))
ALIAS = '/scratch/jjyeung/orch_n30/sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json'
TEACHER = '/scratch/jjyeung/orch_n30/sb_alias2/work/TEACHER_K1.raw'
LISTS = {'R0': '/scratch/jjyeung/n30_mirror/rows_r1/work/codeB/authority_cache/R0_ROOMS.txt',
         'withheld-80': '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16/fixtures/work/shared/WITHHELD_ROOMS_80.json',
         'dev-S1': '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16/fixtures/work/kit07ca49df_meta/m/k/dev_scene_exclusions.json',
         'BENCH v2': '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16/fixtures/work/kit07ca49df_meta/m/k/benchmark_scene_exclusions.json'}
sys.path.insert(0, str(TREE))


class _Inert(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith('__'): raise AttributeError(name)
        return _Inert(self.__name__ + '.' + name)
    def __call__(self, *a, **k): raise RuntimeError('torch stub called: ' + self.__name__)
for _m in ('torch', 'torch.nn', 'torch.nn.functional', 'torch.distributed', 'torch.utils', 'torch.utils.data'):
    sys.modules.setdefault(_m, _Inert(_m))

from student_pilot import carrier_c1_routing as routing, r1_rooms, r1_population, r1_mix, r1_training, row_text_audit, r0_exclusion
from student_pilot.extent_receipt import Extents
# Filters.reason imports held_row/routed_type/excluded_row from carrier_c1_run, whose module body needs the model stack.
RUN = TREE / 'student_pilot/carrier_c1_run.py'
_tree = ast.parse(RUN.read_text())
_fns = [n for n in _tree.body if isinstance(n, ast.FunctionDef) and n.name in ('held_row', 'routed_type', 'excluded_row', 'row_source')]
assert len(_fns) == 4
_mod = types.ModuleType('student_pilot.carrier_c1_run'); _mod.__package__ = 'student_pilot'; _mod.__dict__.update(routing=routing, json=json)
exec(compile(ast.Module(body=_fns, type_ignores=[]), str(RUN), 'exec'), _mod.__dict__)
sys.modules[_mod.__name__] = _mod
from student_pilot.r1_routing import Filters


def sha(b): return hashlib.sha256(b if isinstance(b, bytes) else b.encode()).hexdigest()
def fsha(p): return sha(Path(p).read_bytes())


def reader_checks(row, extents):
    """carrier_c1_run.Rows.row lines 1119-1128 for stream 'vqa' (r2_admission is None in build20)."""
    row_text_audit.check(row, 'vqa')
    extents.check(row, 'vqa')
    r1_training.row_check(row, 'vqa')
    r0_exclusion.reserve().check(row, 'vqa')


def main():
    out = dict(inputs={}, seal={})
    for mod in list(sys.modules.values()):
        p = getattr(mod, '__file__', None)
        if p and p.startswith(str(TREE)):
            rel = str(Path(p).relative_to(TREE)); out['seal'][rel] = fsha(p) == SEAL['files'].get(rel)
    out['seal']['student_pilot/carrier_c1_run.py'] = fsha(RUN) == SEAL['files']['student_pilot/carrier_c1_run.py']
    assert all(out['seal'].values()), out['seal']
    assert not CFG.get('r2_membership')
    filters = Filters(CFG, CFG['scene_division'])
    extents = Extents(CFG['extent_receipt'])
    native = r1_rooms.Rooms(CFG['r1_training']['room_authority'])
    con = sqlite3.connect('file:' + DB + '?mode=ro&immutable=1', uri=True)
    new = [json.loads(l) for l in open(B / 'NEW_ROWS.jsonl')]
    smap = {m['qid']: m for m in map(json.loads, open(B / 'SOURCE_MAP.jsonl'))}
    src_i = {smap[r['qid']]['source_i'] for r in new}

    # 1. Whole v7 store through N's per-row admission: Filters.reason, then the reader checks, then the cell.
    cells = C.Counter(); refused = C.Counter(); step1_cells = C.Counter(); src_cells = C.Counter()
    status_src = C.Counter()
    for i, raw in con.execute('select i,row from rows order by i'):
        r = json.loads(raw)
        why = filters.reason(r, 'vqa')
        if why is None:
            try: reader_checks(r, extents)
            except (ValueError, KeyError, TypeError) as e: why = 'reader:' + str(e)[:60]
        if why:
            refused[why] += 1
            if i in src_i: status_src['refused:' + why] += 1
            continue
        cell = r1_population.family(r, 'vqa'); cells[cell] += 1
        if r.get('question_type', '').startswith('object_rel_direction_'):
            first = r['target'].removeprefix('<think>\n').split('\n', 1)[0]
            step1_cells[('Seen' if first.startswith('Seen:') else 'Step 1'), r['question_type'].rsplit('_', 1)[1], cell] += 1
        if i in src_i: src_cells[cell] += 1; status_src['admitted'] += 1
    out['v7_admitted_cells'] = dict(cells); out['v7_refused'] = dict(refused)
    out['v7_direction_opening_family_cell'] = {'|'.join(k): v for k, v in sorted(step1_cells.items())}
    out['sources_in_v7_pass'] = dict(status_src); out['source_cells'] = dict(src_cells)

    # 2. Sources and twins: the same per-row path, native strict Rooms, and the cell each lands in.
    per = C.Counter(); examples = []
    for r in new:
        m = smap[r['qid']]
        s = json.loads(con.execute('select row from rows where i=?', (m['source_i'],)).fetchone()[0])
        for name, row in (('source', s), ('twin', r)):
            why = filters.reason(row, 'vqa'); per[name, 'Filters.reason', str(why)] += 1
            try: reader_checks(row, extents); per[name, 'reader_checks', 'PASS'] += 1
            except (ValueError, KeyError, TypeError) as e: per[name, 'reader_checks', str(e)[:80]] += 1
            st, canon, how = native.status(row); per[name, 'Rooms.status', st] += 1
            try: native.admit(row); per[name, 'Rooms.admit', 'PASS'] += 1
            except ValueError as e: per[name, 'Rooms.admit', str(e)] += 1
            per[name, 'cell', r1_population.family(row, 'vqa')] += 1
            per[name, 'pair_id', 'present' if row.get('pair_id') else 'absent'] += 1
            per[name, 'facing', str(row.get('facing'))] += 1
        if len(examples) < 3 and native.status(s)[0] == 'unresolved':
            examples.append(dict(source=s['qid'], twin=r['qid'], token=s['dataset'] + '/' + s['scene']))
    out['sources_and_twins'] = {'|'.join(k): v for k, v in sorted(per.items())}; out['unresolved_examples'] = examples

    # 3. Tiered alias map (sb_rowD2) with the five exclusion lists, as in sb_drev6 rev_balance.
    tiered = r1_rooms.Rooms(CFG['r1_training']['room_authority'])
    tiered.aliases = {k: v['canonical'] for k, v in json.load(open(ALIAS))['aliases'].items()}
    teacher = json.load(open(TEACHER))
    k1 = {tiered.room(c['canonical']) for c in teacher['captures'] if c['k1_split'] == 'heldout'}
    sets = {'K1': k1 | tiered.k1, 'R0': tiered.r0 | set(Path(LISTS['R0']).read_text().split()),
            'withheld-80': set(json.load(open(LISTS['withheld-80']))['rooms']),
            'dev-S1': set(json.load(open(LISTS['dev-S1']))['physical_groups']),
            'BENCH v2': set(json.load(open(LISTS['BENCH v2']))['physical_groups'])}
    th = C.Counter(); unresolved = mism = 0
    for r in new:
        m = smap[r['qid']]
        s = json.loads(con.execute('select row from rows where i=?', (m['source_i'],)).fetchone()[0])
        for row in (s, r):
            canon, _ = tiered.canonical(row)
            if not canon: unresolved += 1; continue
            room = tiered.room(canon); mism += room != m['room']
            for k, v in sets.items(): th[k] += room in v
    out['tiered'] = dict(alias_map_sha256=fsha(ALIAS), unresolved=unresolved, source_map_room_mismatch=mism, hits=dict(th),
                         list_sha8={k: fsha(p)[:8] for k, p in LISTS.items()})

    # 4. verify_audit (called by launch_r1/production_proof.py:75-76): positive control, then an augmented-store fixture.
    audit_pin = CFG['r1_training']['room_audit']
    res = {}
    try: r1_rooms.verify_audit(CFG, audit_pin); res['real_v7_audit'] = 'PASS'
    except Exception as e: res['real_v7_audit'] = type(e).__name__ + ':' + str(e)
    audit = json.load(open(audit_pin['path']))
    receipt = json.load(open(CFG['streams']['vqa']['path']))
    # Test fixture only: a receipt naming a hypothetical v7+D7 database. No such database or manifest exists.
    fake_db = dict(path=str(W / 'FIXTURE_augmented_rows.sqlite'), sha256=sha('FIXTURE: hypothetical v7 + sb_rowD7 store'))
    rec = dict(receipt, database=fake_db, count=receipt['count'] + len(new), fixture='review test only; not a real store')
    rp = W / 'FIXTURE_augmented_receipt.json'; rp.write_text(json.dumps(rec, indent=1))
    cfg2 = copy.deepcopy(CFG); cfg2['streams']['vqa'] = dict(path=str(rp), sha256=fsha(rp))
    twins_unresolved = per['twin', 'Rooms.status', 'unresolved']
    for label, unres in (('augmented_native_unresolved', audit['store']['unresolved'] + twins_unresolved), ('augmented_zero_unresolved', 0)):
        a2 = copy.deepcopy(audit); a2['store'].update(database=fake_db, unresolved=unres, rows=audit['store']['rows'] + len(new))
        ap = W / f'FIXTURE_audit_{label}.json'; ap.write_text(json.dumps(a2, indent=1))
        try: r1_rooms.verify_audit(cfg2, dict(path=str(ap), sha256=fsha(ap))); res[label] = f'PASS (unresolved={unres})'
        except Exception as e: res[label] = f'{type(e).__name__}:{e} (unresolved={unres})'
    out['verify_audit'] = res

    # 5. N's allocation (r1_mix.allocate) and per-row expected draws over the 1,000-step run.
    card = json.load(open(CFG['r1_training']['mix']['path']))
    vqa_cells = [c['type'] for c in card['cells'] if c['stream'] == 'vqa']
    other = {c['type']: 10 ** 6 for c in card['cells'] if c['stream'] != 'vqa'}  # other streams allocate independently
    base = {k: cells.get(k, 0) for k in vqa_cells}
    n_tw = per['twin', 'Filters.reason', 'None']
    TW_CELLS = sorted(k[2] for k in per if k[:2] == ('twin', 'cell'))
    assert TW_CELLS == ['direction'], TW_CELLS
    scen = {'v7_only': base,
            'v7_plus_twins_as_delivered': dict(base, **{c: base[c] + per['twin', 'cell', c] for c in TW_CELLS}),  # sb_rowD7f: twins in their actual N cell
            'v7_plus_twins_with_facing_away(D7)': dict(base, facing_pairs=base['facing_pairs'] + n_tw),
            'v7_plus_twins_without_facing': dict(base, direction=base['direction'] + n_tw)}
    alloc = {}
    for name, cnt in scen.items():
        a = r1_mix.allocate(card, {**cnt, **other})
        rate = {k: a['draws'][k] / cnt[k] for k in ('direction', 'facing_pairs')}
        tw_cell = 'facing_pairs' if 'facing_away' in name else 'direction'
        d = dict(draws={k: a['draws'][k] for k in ('direction', 'facing_pairs')}, counts={k: cnt[k] for k in ('direction', 'facing_pairs')},
                 draws_per_row={k: round(v, 4) for k, v in rate.items()}, cuts=a['cuts'])
        if name != 'v7_only':
            t = n_tw * rate['direction']; aw = n_tw * rate[tw_cell]
            st1 = sum(v for k, v in step1_cells.items() if k[0] == 'Step 1' and k[1] in ('easy', 'hard'))
            d.update(teaching_pairs_expected_draws=dict(toward=round(t), away=round(aw)),
                     teaching_majority_accuracy_as_sampled=round(max(t, aw) / (t + aw), 4),
                     step1_easy_hard_expected_draws=dict(toward=round(st1 * rate['direction']), away=round(aw)))
        alloc[name] = d
    out['allocation'] = alloc
    out['card'] = dict(path=CFG['r1_training']['mix']['path'], sha256=fsha(CFG['r1_training']['mix']['path']),
                       direction=next(c for c in card['cells'] if c['type'] == 'direction'),
                       facing_pairs=next(c for c in card['cells'] if c['type'] == 'facing_pairs'))
    out['inputs'] = {str(p): fsha(p) for p in (B / 'NEW_ROWS.jsonl', B / 'SOURCE_MAP.jsonl', TREE.parents[0] / 'build20/inputs/config.json', audit_pin['path'])}
    out['tree_sha256'] = SEAL['tree_sha256']
    (W / 'ROOMS_REVIEW.json').write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: v for k, v in out.items() if k not in ('seal', 'inputs')}, indent=1, default=str))


if __name__ == '__main__':
    main()
