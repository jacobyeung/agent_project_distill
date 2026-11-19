"""Independent review checks for sb_rowD7 (no sb_rowD* code imported); adapted from sb_drev6 rev_verify.py to w20/build20."""
import ast, collections as C, difflib, hashlib, json, pickle, random, re, sqlite3, sys, types
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE / 'work'
B = Path('/scratch/jjyeung/orch_n30/sb_rowD7/out')
DB = '/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
TREE = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w20/work/tree_r1')
SEAL = json.load(open(TREE.parents[1] / 'out/TREE_SEAL.json'))
CFG = json.load(open(TREE.parents[0] / 'build20/inputs/config.json'))
U_UNION = '/scratch/jjyeung/orch_n30/sb_k1list/out/u_union.json'
sys.path.insert(0, str(TREE))
class _Inert(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith('__'): raise AttributeError(name)
        return _Inert(self.__name__ + '.' + name)
    def __call__(self, *a, **k): raise RuntimeError('torch stub called: ' + self.__name__)
for _m in ('torch', 'torch.nn', 'torch.nn.functional', 'torch.distributed', 'torch.utils', 'torch.utils.data'):
    sys.modules.setdefault(_m, _Inert(_m))
from student_pilot import r2_contract, trace_grammar, r2_grammar, scene_division_gate, row_removals, s1_exclusions
from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity

HALF = {'left': 'right', 'right': 'left', 'front-left': 'back-right', 'front-right': 'back-left',
        'back-left': 'front-right', 'back-right': 'front-left'}
PHRASE = {'to my left': (-1, 0), 'to my right': (1, 0), 'in front of me, on my left': (-1, 1),
          'in front of me, on my right': (1, 1), 'behind me, on my left': (-1, -1), 'behind me, on my right': (1, -1)}
QUAD = {(-1, 0): 'left', (1, 0): 'right', (-1, 1): 'front-left', (1, 1): 'front-right', (-1, -1): 'back-left', (1, -1): 'back-right'}
TOWARD = ('facing', 'looking at', 'look toward', 'face', 'facing toward', 'looking toward', 'face toward')
AWAY = ('facing away from', 'face away from')
R = C.Counter(); FAIL = C.defaultdict(list)


def sha(b): return hashlib.sha256(b if isinstance(b, bytes) else b.encode()).hexdigest()
def fsha(p): return sha(Path(p).read_bytes())
def check(name, ok, info=None):
    R[name, bool(ok)] += 1
    if not ok and len(FAIL[name]) < 8: FAIL[name].append(info)
def opts(r): return {m[1]: m[2].strip().lower() for m in (re.fullmatch(r'([A-Z])\.\s*(.+)', s) for s in r['student_input']['options'])}
def body(r):
    t = r['target']; assert t.startswith('<think>\n')
    return t[len('<think>\n'):t.index('\n</think>')].split('\n')


def pack_fn():
    tree = ast.parse((TREE / 'student_pilot/carrier_c1_routing.py').read_text())
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('require_training_think', 'direct_row')]
    assert len(fns) == 2
    env = {'__name__': 'student_pilot.rev_pack', '__package__': 'student_pilot', 'THINK': '<think>\n'}
    exec(compile(ast.Module(body=fns, type_ignores=[]), 'carrier_c1_routing.py', 'exec'), env)
    return env['direct_row']


def native(r, pack):
    r2_contract.validate(r, 'vqa', require_frames=False)
    v = trace_grammar.validate_row(r); assert not v, v
    assert r2_grammar.validate_direct(r['target'], r['student_input']['question'], len(r['student_input']['frames'])) == r['answer']
    p = pack(r)
    assert p['target'] == r['target'] and p['routing']['answer'] == r['answer'] and p['student_input']['frames'] == r['student_input']['frames']


def diff(a, b, path=''):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            p = f'{path}.{k}' if path else k
            if k not in a: out.append('+' + p)
            elif k not in b: out.append('-' + p)
            else: out += diff(a[k], b[k], p)
    elif a != b: out.append(path)
    return out


def roles(line, names):
    """Assign standing X, heading Y, target Z from the source's Step 2 line; returns (X, Y, Z, phrase) or None."""
    import itertools
    hits = set()
    for X, Y, Z in itertools.permutations(names):
        e = {k: re.escape(v) for k, v in dict(X=X, Y=Y, Z=Z).items()}
        for pat in (rf'Step 2: facing the {e["Y"]} from the {e["X"]}, I find the {e["Z"]} (.+)\.',
                    rf'Step 2: standing at the {e["X"]} and facing the {e["Y"]}, I find the {e["Z"]} (.+)\.',
                    rf'Step 2: I stand at the {e["X"]} facing the {e["Y"]}; I find the {e["Z"]} (.+)\.',
                    rf'Step 2: I find the {e["Z"]} (.+) when I stand at the {e["X"]} facing the {e["Y"]}\.'):
            m = re.fullmatch(pat, line)
            if m and m[1] in PHRASE: hits.add((X, Y, Z, m[1]))
    return next(iter(hits)) if len(hits) == 1 else None


def main():
    random.seed(20261119)
    for mod in list(sys.modules.values()):
        p = getattr(mod, '__file__', None)
        if p and p.startswith(str(TREE)):
            rel = str(Path(p).relative_to(TREE)); check('seal_imported_module', fsha(p) == SEAL['files'].get(rel), rel)
    check('seal_carrier_c1_routing', fsha(TREE / 'student_pilot/carrier_c1_routing.py') == SEAL['files']['student_pilot/carrier_c1_routing.py'])
    pack = pack_fn()
    cen = pickle.load(open(W / 'census.pkl', 'rb')); D = cen['dirrows']; v7_qids = cen['qids']
    con = sqlite3.connect('file:' + DB + '?mode=ro&immutable=1', uri=True)
    def get(i):
        raw = con.execute('select row from rows where i=?', (i,)).fetchone()[0]
        return json.loads(raw), sha(raw)
    new = [json.loads(l) for l in open(B / 'NEW_ROWS.jsonl')]
    smap = {m['qid']: m for m in map(json.loads, open(B / 'SOURCE_MAP.jsonl'))}
    check('count_8000', len(new) == 8000 and len(smap) == 8000)
    sample = set(r['qid'] for r in random.sample(new, 300))
    sources, phrases, cells, used, diffs = [], C.Counter(), C.Counter(), C.Counter(), C.Counter()
    qset, cset, edits, s1forms, s3forms = set(), set(), C.Counter(), C.Counter(), C.Counter()
    for r in new:
        m = smap[r['qid']]
        s, ssha = get(m['source_i'])
        check('source_sha', ssha == m['source_row_sha256'] == r['provenance']['sb_rowD7']['source_row_sha256'], r['qid'])
        check('source_qid', s['qid'] == m['source_qid'] and r['qid'] == s['qid'] + '_sb_rowD7_a', r['qid'])
        used[s['qid']] += 1; sources.append(s)
        fam = s['question_type'].rsplit('_', 1)[1]
        check('family_easy_hard', fam in ('easy', 'hard') and r['question_type'] == s['question_type'], r['qid'])
        dm = D[m['source_i']]
        check('source_is_step1_toward_v7', dm['op'] == 'Step 1' and dm['cl'] == 'toward' and not s.get('pair_id') and not s.get('facing'), r['qid'])
        so, no = opts(s), opts(r)
        check('options_identical', s['student_input']['options'] == r['student_input']['options'], r['qid'])
        slab = so[s['answer']]; want = HALF[slab]
        letters = [k for k, v in no.items() if v == want]
        inj = len(set(so.values())) == len(so) and all(HALF.get(v) in so.values() for v in so.values())
        check('option_map_bijective', inj and len(letters) == 1, r['qid'])
        ok = len(letters) == 1 and r['answer'] == letters[0]
        check('truth_label_letter_all', ok, (r['qid'], slab, r['answer'], letters))
        if r['qid'] in sample: check('truth_label_letter_sample300', ok, r['qid'])
        sb, nb = body(s), body(r)
        rl = roles(sb[1], m['objects'])
        check('roles_from_source_trace', rl is not None and list(rl[:3]) == list(m['objects']), (sb[1], m['objects']))
        if rl is None: continue
        X, Y, Z, ph = rl; phrases[ph] += 1
        x, y = PHRASE[ph]
        check('relation_family_consistent', (y == 0) == (fam == 'easy'), (r['qid'], ph))
        check('source_answer_matches_trace', QUAD[(x, y)] == slab, (r['qid'], ph, slab))
        check('new_label_from_trace', no[r['answer']] == QUAD[(-x, -y)], r['qid'])
        if r['qid'] in sample: check('trace_truth_sample300', no[r['answer']] == QUAD[(-x, -y)] == HALF[slab], r['qid'])
        # Question: the source's own text with exactly one clause substituted, bound to the heading Y.
        sq, q = s['student_input']['question'], r['student_input']['question']
        e = r['provenance']['sb_rowD7']['clause_edit']
        rebuilt = sq[:e['start']] + e['new_clause'] + sq[e['end']:]
        check('question_is_source_with_one_edit', rebuilt == q and sq[e['start']:e['end']] == e['source_clause'], r['qid'])
        ops = [o for o in difflib.SequenceMatcher(None, sq.split(' '), q.split(' '), autojunk=False).get_opcodes() if o[0] != 'equal']
        check('word_diff_one_block', len(ops) == 1, (sq, q))
        check('edit_bound_to_heading', sq[e['end']:].startswith(' the ' + Y) and e['source_clause'] in TOWARD and e['new_clause'] in AWAY
              and (e['start'] == 0 or not sq[e['start'] - 1].isalnum()), (r['qid'], e, Y))
        edits[e['source_clause'], e['new_clause']] += 1
        rest = q[:e['start']] + '<EDIT>' + q[e['start'] + len(e['new_clause']):]
        resid = re.findall(rf'\b(?:toward|towards|facing|face|faces|looking at|look at|looking|look|ahead of|in front of)\s+(?:the\s+)?{re.escape(Y)}\b', rest, re.I)
        resid += re.findall(rf'\b{re.escape(Y)}\s+(?:ahead|in front)\b', rest, re.I)
        check('no_residual_toward_heading_clause', not resid, (q, resid))
        check('twin_clause_away_by_rev_census', 'away from' in q.lower(), r['qid'])
        for n in (X, Y, Z): check('names_in_question', n in q, (q, n))
        if fam == 'hard':
            check('hard_cartesian_sentence_kept', q.endswith('\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).') == sq.endswith('\nThe directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).'), q)
        # Trace: source lines copied, half turn as its own step, final line from the mapped label.
        check('source_trace_4_lines', len(sb) == 4, sb)
        check('twin_trace_4_lines', len(nb) == 4, nb)
        prep = 'to' if fam == 'easy' else 'at'
        check('source_final_line', re.fullmatch(rf'So I find (?:the position of )?the {re.escape(Z)} {prep} my {re.escape(slab)}\.', sb[-1]) is not None, sb[-1])
        check('twin_final_line_form_equals_source', sb[-1].startswith('So I find the position of ') == nb[3].startswith('So I find the position of '), (sb[-1], nb[3]))
        check('twin_line1_equals_source_line1', nb[0] == sb[0], (sb[0], nb[0]))
        check('twin_line1_lists_same_three_names', nb[0] == f'Step 1: find the {X}, the {Y} and the {Z}.', nb[0])
        s1forms[re.sub('|'.join(map(re.escape, sorted((X, Y, Z), key=len, reverse=True))), '<N>', sb[0])] += 1
        s3forms[re.sub(re.escape(Y), '<Y>', sb[2])] += 1
        check('twin_line2_is_source_step2', nb[1] == sb[1], r['qid'])
        check('half_turn_own_step', nb[2] == f'Step 3: I face away from the {Y} by making a half turn. Front and back swap, and left and right swap.', nb[2])
        check('final_line', nb[3] == f'So I find the {Z} {prep} my {no[r["answer"]]}.', nb[3])
        check('target_suffix', r['target'].endswith('\n</think>\n\n' + r['answer']), r['qid'])
        nn, ns = C.Counter(re.findall(r'\d+', '\n'.join(nb))), C.Counter(re.findall(r'\d+', '\n'.join(sb)))
        check('no_new_numbers', all(ns[k] >= v - (1 if k == '3' else 0) for k, v in nn.items()), (nb, sb))
        for p in diff(s, r): diffs[p] += 1
        cid = candidate_identity(dict(qid=r['qid'], scene=r['scene'], frame_indices=r['student_input']['frame_indices'], type=r['question_type'],
                                      question=q, options=r['student_input']['options']))
        check('candidate_id_formula', cid == r['candidate_id'] == m['candidate_id'], r['qid'])
        check('qid_new_unique', r['qid'] not in qset and r['qid'] not in v7_qids, r['qid'])
        check('cid_unique', r['candidate_id'] not in cset and r['candidate_id'] not in cen['cids'], r['qid'])
        qset.add(r['qid']); cset.add(r['candidate_id'])
        cells[fam, no[r['answer']]] += 1
        for name, row in (('native_new', r), ('native_source', s)):
            try: native(row, pack); check(name, True)
            except Exception as ex: check(name, False, (row['qid'], repr(ex)[:200]))
    check('source_used_once', max(used.values()) == 1 and len(used) == 8000)
    # 40 rows to read: 10 per easy label pair cell, 5 per hard quadrant.
    by = C.defaultdict(list)
    for r, s in zip(new, sources): by[r['question_type'], opts(r)[r['answer']]].append((r, s))
    with open(W / 'READ40.md', 'w') as f:
        for k in sorted(by):
            for r, s in random.sample(by[k], 10 if k[0].endswith('easy') else 5):
                f.write(f"## {r['qid']} {k[0]} new={k[1]} pool={s['pool']}\nSRC Q: {s['student_input']['question']}\nSRC O: {s['student_input']['options']} A={s['answer']}\n"
                        f"SRC T:\n{s['target']}\nNEW Q: {r['student_input']['question']}\nNEW O: {r['student_input']['options']} A={r['answer']}\nNEW T:\n{r['target']}\n\n")
    # Removals and scene division with N's build20 configuration (plus u_union as in sb_drev6).
    files = list(CFG['remove_files']); paths = [x['path'] for x in files]
    files.append(dict(path=U_UNION, sha256=fsha(U_UNION)))
    for need in ('inputs/records/n.json', 'inputs/records/z.json', 'build18/inputs/u.json'):
        check('remove_list_has_' + need, any(p.endswith(need) for p in paths), need)
    rem = row_removals.Removals(files)
    u18 = rem.keys[[i for i, p in enumerate(paths) if p.endswith('build18/inputs/u.json')][0]]
    R['u18_keys', len(u18)] += 1; R['u_union_keys', len(rem.keys[-1])] += 1; R['u18_minus_union', len(u18 - rem.keys[-1])] += 1
    lineage = 0
    for r, s in zip(new, sources):
        check('removal_new_clean', not rem.match(r), r['qid']); check('removal_source_clean', not rem.match(s), s['qid'])
        lineage += any(k in ks for k in set(r.get('label_row_keys', [])) | {s['qid']} for ks in rem.keys)
        check('label_row_keys_is_source', r.get('label_row_keys') == [s['qid']], r['qid'])
    R['lineage_removal_hits', lineage] += 1
    excl = s1_exclusions.Exclusions(CFG['dev_scene_exclusions'], CFG['benchmark_scene_exclusions'])
    for name, rows in (('new', new), ('sources', sources)):
        try:
            g = scene_division_gate.check_rows(rows, CFG['scene_division'], removals=row_removals.Removals(files), scene_filter=excl)
            R['scene_gate_' + name, json.dumps(g)] += 1
        except Exception as ex: check('scene_gate_' + name, False, repr(ex)[:300])
    out = dict(results={f'{k[0]}|{k[1]}': v for k, v in sorted(R.items(), key=str)}, failures=dict(FAIL),
               phrases=dict(phrases), cells={'|'.join(k): v for k, v in sorted(cells.items())}, field_diff=dict(diffs),
               clause_edits={'->'.join(k): v for k, v in edits.most_common()}, source_step1_forms=dict(s1forms.most_common(10)),
               source_line3_forms=dict(s3forms.most_common(10)),
               inputs={str(p): fsha(p) for p in (B / 'NEW_ROWS.jsonl', B / 'SOURCE_MAP.jsonl', TREE.parents[0] / 'build20/inputs/config.json')})
    (W / 'VERIFY_REVIEW.json').write_text(json.dumps(out, indent=1))
    print(json.dumps(out['results'], indent=0)); print('FAILS', dict(FAIL))
    for k in ('field_diff', 'phrases', 'cells', 'clause_edits', 'source_step1_forms', 'source_line3_forms'): print(k, json.dumps(out[k]))


if __name__ == '__main__':
    main()
