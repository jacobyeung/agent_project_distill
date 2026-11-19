"""Independent review checks for sb_rowD6 (no sb_rowD* code imported)."""
import ast, collections as C, copy, hashlib, json, pickle, random, re, sqlite3, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE / 'work'
B = Path('/scratch/jjyeung/orch_n30/sb_rowD6/out')
DB = '/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
TREE = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
SEAL = json.load(open(TREE.parents[1] / 'out/TREE_SEAL.json'))
CFG = json.load(open(TREE.parents[0] / 'build19/inputs/config.json'))
U_UNION = '/scratch/jjyeung/orch_n30/sb_k1list/out/u_union.json'
LISTS = {'withheld-80': '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16/fixtures/work/shared/WITHHELD_ROOMS_80.json',
         'dev-S1': '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16/fixtures/work/kit07ca49df_meta/m/k/dev_scene_exclusions.json',
         'BENCH v2': '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16/fixtures/work/kit07ca49df_meta/m/k/benchmark_scene_exclusions.json'}
sys.path.insert(0, str(TREE))
import types
class _Inert(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith('__'): raise AttributeError(name)
        return _Inert(self.__name__ + '.' + name)
    def __call__(self, *a, **k): raise RuntimeError('torch stub called: ' + self.__name__)
for _m in ('torch', 'torch.nn', 'torch.nn.functional', 'torch.distributed', 'torch.utils', 'torch.utils.data'):
    sys.modules.setdefault(_m, _Inert(_m))
from student_pilot import r2_contract, trace_grammar, r2_grammar, scene_division_gate, row_removals, r1_rooms, s1_exclusions
from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity

HALF = {'left': 'right', 'right': 'left', 'front-left': 'back-right', 'front-right': 'back-left',
        'back-left': 'front-right', 'back-right': 'front-left'}
# Observer-frame phrase -> (lateral sign, longitudinal sign); +x right, +y front.
PHRASE = {'to my left': (-1, 0), 'to my right': (1, 0), 'in front of me, on my left': (-1, 1),
          'in front of me, on my right': (1, 1), 'behind me, on my left': (-1, -1), 'behind me, on my right': (1, -1)}
QUAD = {(-1, 0): 'left', (1, 0): 'right', (-1, 1): 'front-left', (1, 1): 'front-right', (-1, -1): 'back-left', (1, -1): 'back-right'}
R = C.Counter(); FAIL = C.defaultdict(list)


def sha(b): return hashlib.sha256(b if isinstance(b, bytes) else b.encode()).hexdigest()
def fsha(p): return sha(Path(p).read_bytes())
def check(name, ok, info=None):
    R[name, bool(ok)] += 1
    if not ok and len(FAIL[name]) < 8:
        FAIL[name].append(info)
def opts(r):
    return {m[1]: m[2].strip().lower() for m in (re.fullmatch(r'([A-Z])\.\s*(.+)', s) for s in r['student_input']['options'])}
def body(r):
    t = r['target']; assert t.startswith('<think>\n')
    return t[len('<think>\n'):t.index('\n</think>')].split('\n')


def pack_fn():
    src = (TREE / 'student_pilot/carrier_c1_routing.py').read_text()
    tree = ast.parse(src)
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('require_training_think', 'direct_row')]
    assert len(fns) == 2
    env = {'__name__': 'student_pilot.rev_pack', '__package__': 'student_pilot', 'THINK': '<think>\n'}
    exec(compile(ast.Module(body=fns, type_ignores=[]), 'carrier_c1_routing.py', 'exec'), env)
    return env['direct_row']


def native(r, pack):
    r2_contract.validate(r, 'vqa', require_frames=False)
    v = trace_grammar.validate_row(r)
    assert not v, v
    n = len(r['student_input']['frames'])
    assert r2_grammar.validate_direct(r['target'], r['student_input']['question'], n) == r['answer']
    p = pack(r)
    assert p['target'] == r['target'] and p['routing']['answer'] == r['answer']
    assert p['student_input']['frames'] == r['student_input']['frames']


def diff(a, b, path=''):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            p = f'{path}.{k}' if path else k
            if k not in a: out.append('+' + p)
            elif k not in b: out.append('-' + p)
            else: out += diff(a[k], b[k], p)
    elif a != b:
        out.append(path)
    return out


def main():
    random.seed(20261119)
    # Seal: every TREE module imported here must match the sealed bytes.
    for mod in list(sys.modules.values()):
        p = getattr(mod, '__file__', None)
        if p and p.startswith(str(TREE)):
            rel = str(Path(p).relative_to(TREE))
            check('seal_' + rel, fsha(p) == SEAL['files'].get(rel), rel)
    check('seal_carrier_c1_routing', fsha(TREE / 'student_pilot/carrier_c1_routing.py') == SEAL['files']['student_pilot/carrier_c1_routing.py'])
    pack = pack_fn()
    cen = pickle.load(open(W / 'census.pkl', 'rb')); D = cen['dirrows']; byqid = {m['qid']: m for m in D.values()}
    v7_qids = cen['qids']
    pair_of = C.defaultdict(list)
    for m in D.values():
        if m['pair']: pair_of[m['pair']].append(m)
    con = sqlite3.connect('file:' + DB + '?mode=ro&immutable=1', uri=True)
    def get(i):
        raw = con.execute('select row from rows where i=?', (i,)).fetchone()[0]
        return json.loads(raw), sha(raw)
    new = [json.loads(l) for l in open(B / 'NEW_ROWS.jsonl')]
    smap = {m['qid']: m for m in map(json.loads, open(B / 'SOURCE_MAP.jsonl'))}
    check('count_8000', len(new) == 8000 and len(smap) == 8000)
    sample = set(r['qid'] for r in random.sample(new, 300))
    sources, phrases, cells, teach = [], C.Counter(), C.Counter(), []
    used = C.Counter(); diffs = C.Counter(); qset = set(); cset = set()
    read40 = []
    for r in new:
        m = smap[r['qid']]; branch = m['branch']
        s, ssha = get(m['source_i'])
        check('source_sha', ssha == m['source_row_sha256'] == r['provenance']['sb_rowD6']['source_row_sha256'], r['qid'])
        check('source_qid', s['qid'] == m['source_qid'] and r['qid'] == s['qid'] + '_sb_rowD6_' + branch, r['qid'])
        used[s['qid']] += 1; sources.append(s)
        fam = s['question_type'].rsplit('_', 1)[1]
        check('family_easy_hard', fam in ('easy', 'hard') and r['question_type'] == s['question_type'], r['qid'])
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
        # Roles from the new question.
        q = r['student_input']['question']
        mq = re.fullmatch(r'At the (.+?), face (toward|away from) the (.+?)\. Choose the direction of the (.+?) relative to that heading\.'
                          r'(\nUse the four quadrants around your standing point, with your heading as the forward axis\.)?', q)
        check('question_form', bool(mq) and (mq[5] is not None) == (fam == 'hard'), q)
        X, cl, Y, Z = mq[1], mq[2], mq[3], mq[4]
        check('clause_matches_branch', (cl == 'away from') == (branch == 'a') and r['facing'] == ('away' if branch == 'a' else 'toward'), r['qid'])
        # Source question must name the same roles: Y after a heading phrase, X after a position phrase.
        sq = s['student_input']['question']
        yctx = any(f'{w} the {Y}' in sq for w in ('facing', 'facing toward', 'looking at', 'looking toward', 'look toward', 'face', 'toward',
                   'away from', 'back to', 'looking directly at', 'looking directly toward', 'viewing', 'Facing', 'oriented toward', 'With')) or f'the {Y} ahead' in sq
        xctx = any(f'{w} the {X}' in sq for w in ('by', 'beside', 'next to', 'at', 'near', 'alongside', 'adjacent to', 'from')) or f'the {X} next to me' in sq
        check('source_question_roles', yctx and xctx and f'the {Z}' in sq, (sq, X, Y, Z))
        # Relation in the source trace (observer frame while facing toward Y).
        if branch == 'a':
            line = sb[1]
            mm = (re.fullmatch(rf'Step 2: facing the {re.escape(Y)} from the {re.escape(X)}, I find the {re.escape(Z)} (.+)\.', line)
                  or re.fullmatch(rf'Step 2: standing at the {re.escape(X)} and facing the {re.escape(Y)}, I find the {re.escape(Z)} (.+)\.', line)
                  or re.fullmatch(rf'Step 2: I stand at the {re.escape(X)} facing the {re.escape(Y)}; I find the {re.escape(Z)} (.+)\.', line)
                  or re.fullmatch(rf'Step 2: I find the {re.escape(Z)} (.+) when I stand at the {re.escape(X)} facing the {re.escape(Y)}\.', line))
        else:
            line = sb[1]
            mm = re.fullmatch(rf'If I stood at the {re.escape(X)} facing the {re.escape(Y)}, the {re.escape(Z)} would be (.+)\.', line)
        check('source_relation_parsed', bool(mm), line)
        if not mm: continue
        ph = mm[1]; phrases[ph] += 1
        check('relation_phrase_known', ph in PHRASE, ph)
        if ph not in PHRASE: continue
        x, y = PHRASE[ph]
        toward_label = QUAD[(x, y)]
        check('relation_family_consistent', (y == 0) == (fam == 'easy'), (r['qid'], ph))
        src_from_trace = toward_label if branch == 'a' else QUAD[(-x, -y)]
        check('source_answer_matches_trace', src_from_trace == slab, (r['qid'], ph, slab))
        new_from_trace = QUAD[(-x, -y)] if branch == 'a' else toward_label
        check('new_label_from_trace', no[r['answer']] == new_from_trace, r['qid'])
        # Stored cross-checks: b against the existing toward mate; a has no existing away twin.
        if branch == 'b':
            mates = [t for t in pair_of[s['pair_id']] if t['cl'] == 'toward'] + ([byqid[s['pair_id']]] if s['pair_id'] in byqid else [])
            mates = {t['i']: t for t in mates}.values()
            check('b_toward_mate_exists_one', len(mates) == 1, r['qid'])
            for t in mates:
                check('b_matches_stored_toward_label', t['label'] == no[r['answer']], r['qid'])
                tr, _ = get(t['i'])
                check('b_mate_same_frames_scene', tr['student_input']['frame_indices'] == r['student_input']['frame_indices'] and tr['scene'] == r['scene'], r['qid'])
                check('b_mate_same_option_letter', tr['answer'] == r['answer'] and tr['student_input']['options'] == r['student_input']['options'], r['qid'])
        else:
            check('a_no_existing_away_twin', not pair_of.get(s['qid']) and not s.get('pair_id'), r['qid'])
        # Trace structure.
        lab = no[r['answer']]; prep = 'to' if fam == 'easy' else 'at'
        final = f'So I find the {Z} {prep} my {lab}.'
        check('target_suffix', r['target'].endswith('\n</think>\n\n' + r['answer']), r['qid'])
        check('trace_4_lines', len(nb) == 4, nb)
        if branch == 'a':
            check('a_line1', nb[0] == f'Step 1: find the {X}, the {Y} and the {Z}.', nb[0])
            check('a_line2_is_source_line2', nb[1] == sb[1], r['qid'])
            check('a_half_turn_own_step', nb[2] == f'Step 3: I face away from the {Y} by making a half turn. Front and back swap, and left and right swap.', nb[2])
        else:
            check('b_line1_is_source_line1', nb[0] == sb[0] and nb[0].startswith('Seen: '), r['qid'])
            check('b_line2_relation', nb[1] == f'Standing at the {X} facing the {Y}, I find the {Z} {ph}.', nb[1])
            check('b_heading_kept', nb[2] == f'The question has me face toward the {Y}; I keep that heading.', nb[2])
        check('final_line', nb[3] == final, (nb[3], final))
        nums_new = C.Counter(re.findall(r'\d+', '\n'.join(nb))); nums_src = C.Counter(re.findall(r'\d+', '\n'.join(sb)))
        check('no_new_numbers', all(nums_src[k] >= v - (1 if k in ('1', '2', '3') and branch == 'a' else 0) for k, v in nums_new.items()), (nb, sb))
        # Field diff vs source.
        for p in diff(s, r): diffs[branch, p] += 1
        # Identifiers.
        cid = candidate_identity(dict(qid=r['qid'], scene=r['scene'], frame_indices=r['student_input']['frame_indices'], type=r['question_type'],
                                      question=q, options=r['student_input']['options']))
        check('candidate_id_formula', cid == r['candidate_id'] == m['candidate_id'], r['qid'])
        check('qid_new_unique', r['qid'] not in qset and r['qid'] not in v7_qids, r['qid'])
        check('cid_unique', r['candidate_id'] not in cset and r['candidate_id'] not in cen['cids'], r['qid'])
        qset.add(r['qid']); cset.add(r['candidate_id'])
        cells[branch, fam, lab] += 1
        try:
            native(r, pack); check('native_new', True)
        except Exception as e:
            check('native_new', False, (r['qid'], repr(e)[:200]))
        try:
            native(s, pack); check('native_source', True)
        except Exception as e:
            check('native_source', False, (s['qid'], repr(e)[:200]))
    check('source_used_once', max(used.values()) == 1 and len(used) == 8000)
    # 40 rows for reading: 10 per branch x family.
    by = C.defaultdict(list)
    for r, s in zip(new, sources): by[smap[r['qid']]['branch'], r['question_type']].append((r, s))
    with open(W / 'READ40.md', 'w') as f:
        for k in sorted(by):
            for r, s in random.sample(by[k], 10):
                f.write(f"## {r['qid']}  branch={k[0]} {k[1]} pool={s['pool']}\nSRC Q: {s['student_input']['question']}\nSRC O: {s['student_input']['options']} A={s['answer']}\n"
                        f"SRC T:\n{s['target']}\nNEW Q: {r['student_input']['question']}\nNEW O: {r['student_input']['options']} A={r['answer']}\nNEW T:\n{r['target']}\n\n")
    # Removals, scene division and rooms with N's build19 configuration.
    files = list(CFG['remove_files']); paths = [x['path'] for x in files]
    for p in (U_UNION,):
        files.append(dict(path=p, sha256=fsha(p)))
    for need in ('inputs/records/n.json', 'inputs/records/z.json', 'build18/inputs/u.json'):
        check('remove_list_has_' + need, any(p.endswith(need) for p in paths), need)
    rem = row_removals.Removals(files)
    ukeys = rem.keys[-1]; u18 = rem.keys[[i for i, p in enumerate(paths) if p.endswith('build18/inputs/u.json')][0]]
    R['u18_keys', len(u18)] += 1; R['u_union_keys', len(ukeys)] += 1; R['u18_minus_union', len(u18 - ukeys)] += 1
    lineage_hits = 0
    for r, s in zip(new, sources):
        check('removal_new_clean', not rem.match(r), r['qid'])
        check('removal_source_clean', not rem.match(s), s['qid'])
        keys = set(r.get('label_row_keys', [])) | {s['qid'], s.get('pair_id') or ''} | {t['qid'] for t in pair_of.get(s.get('pair_id') or '-', [])}
        lineage_hits += bool(any(k in ks for k in keys for ks in rem.keys))
        check('lineage_in_label_row_keys', {s['qid']} | ({s['pair_id']} if s.get('pair_id') else set()) <= set(r['label_row_keys']), r['qid'])
    R['lineage_family_removal_hits', lineage_hits] += 1
    excl = s1_exclusions.Exclusions(CFG['dev_scene_exclusions'], CFG['benchmark_scene_exclusions'])
    for name, rows in (('new', new), ('sources', sources)):
        try:
            g = scene_division_gate.check_rows(rows, CFG['scene_division'], removals=row_removals.Removals(files), scene_filter=excl)
            R['scene_gate_' + name, json.dumps(g)] += 1
        except Exception as e:
            check('scene_gate_' + name, False, repr(e)[:300])
    rooms = r1_rooms.Rooms(CFG['r1_training']['room_authority'])
    sets = {'withheld-80': set(json.load(open(LISTS['withheld-80']))['rooms']),
            'dev-S1': set(json.load(open(LISTS['dev-S1']))['physical_groups']),
            'BENCH v2': set(json.load(open(LISTS['BENCH v2']))['physical_groups'])}
    R['list_sizes', json.dumps({k: len(v) for k, v in sets.items()}) + ' ' + json.dumps({k: fsha(p)[:8] for k, p in LISTS.items()})] += 1
    how = C.Counter()
    for name, rows in (('new', new), ('sources', sources)):
        for r in rows:
            st, canon, h = rooms.status(r); how[name, st, h] += 1
            room = rooms.room(canon) if canon else None
            hits = [k for k, v in sets.items() if room in v or canon in v or f"{r['dataset']}/{r['scene']}" in v]
            check('room_ok_' + name, st == 'ok' and not hits, (r['qid'], st, canon, hits))
    R['room_status', json.dumps({str(k): v for k, v in how.items()})] += 1
    out = dict(results={f'{k[0]}|{k[1]}': v for k, v in sorted(R.items(), key=str)}, failures=dict(FAIL),
               phrases=dict(phrases), cells={'|'.join(k): v for k, v in sorted(cells.items())},
               field_diff={f'{k[0]}|{k[1]}': v for k, v in sorted(diffs.items())},
               inputs={str(p): fsha(p) for p in (B / 'NEW_ROWS.jsonl', B / 'SOURCE_MAP.jsonl', DB)})
    (W / 'VERIFY_REVIEW.json').write_text(json.dumps(out, indent=1))
    bad = {k: v for k, v in R.items() if k[1] is False}
    print(json.dumps(out['results'], indent=0)[:6000]); print('FAILS', bad); print(json.dumps(out['field_diff'], indent=0)); print(dict(phrases))


if __name__ == '__main__':
    main()
