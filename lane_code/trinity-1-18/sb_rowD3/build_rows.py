"""Census and fail-closed row-build admission for sb_rowD3.
Run: PYTHONDONTWRITEBYTECODE=1 python build_rows.py
Exit 2 reports missing source-bound geometry; it never certifies an empty build.
"""
import collections as C
import hashlib
import json
import math
import re
import sqlite3
import sys
from pathlib import Path
import d2_support as d2

BASE = Path(__file__).resolve().parent
OUT = BASE / 'out'
D2 = Path('/scratch/jjyeung/orch_n30/sb_rowD2')
d2.BASE = D2
TREE, DB = d2.TREE, d2.DB
pin, load, norm = d2.pin, d2.load, d2.norm
COMMAND = 'PYTHONDONTWRITEBYTECODE=1 python build_rows.py'
OPENINGS = ('Step 1', 'Seen')
CLAUSES = ('toward', 'away', 'opposite')
FIELDS = ('question_type', 'pool', 'retrace_rule', 'opening', 'clause')


def dump(name, obj):
    (OUT / name).write_text(json.dumps(dict(command=COMMAND, input_sha256=d2.PINS, **obj), indent=2, sort_keys=True)+'\n')


def cells(c, fields=FIELDS):
    return d2.counter_rows(c, fields)


def cross_counts(c):
    z = C.Counter()
    for k, n in c.items():
        z[k[-2:]] += n
    return [dict(opening=o, clause=c, rows=z[o,c]) for o in OPENINGS for c in CLAUSES]


def bounds(c):
    """Exact integer lower bounds from retained counts; geometry feasibility is separate."""
    b = C.Counter()
    by_family = C.Counter()
    for k, n in c.items():
        group = 'toward' if k[-1] == 'toward' else 'turn'
        b[k[-2], group] += n
        by_family[k[0],k[-2],group] += n
    m = max(b.values())
    per_family = {f:max(by_family[f,o,g] for o in OPENINGS for g in ('toward','turn'))
                  for f in sorted({k[0] for k in c})}
    target = sum(per_family.values())
    required=[]
    for f,mf in per_family.items():
        for o in OPENINGS:
            for g in ('toward','turn'):
                required.append(dict(question_type=f, opening=o, clause_group=g, retained=by_family[f,o,g],
                                     required_additions=mf-by_family[f,o,g], final_count=mf, actual_additions=0))
    return dict(retained_rows=sum(c.values()),
        within_each_opening_binary=sum(abs(b[o,'toward']-b[o,'turn']) for o in OPENINGS),
        opening_parity_per_literal_clause=sum(abs(next(x['rows'] for x in cross_counts(c) if x['opening']=='Step 1' and x['clause']==g)-next(x['rows'] for x in cross_counts(c) if x['opening']=='Seen' and x['clause']==g)) for g in CLAUSES),
        equal_four_binary_cells=4*m-sum(c.values()), equal_six_literal_cells=6*max(cross['rows'] for cross in cross_counts(c))-sum(c.values()),
        equal_four_cells_within_family=sum(x['required_additions'] for x in required), family_quotas=required,
        proposed_binary_final=[dict(opening=o,clause_group=g,rows=target) for o in OPENINGS for g in ('toward','turn')],
        status='COUNT_LOWER_BOUND_ONLY; GT, frame evidence and quadrant feasibility MISSING')


def object_names(row, opening):
    first = row['target'].removeprefix('<think>\n').splitlines()[0]
    if opening == 'Step 1':
        m = re.fullmatch(r'Step 1: (?:find|locate) the (.+?), the (.+?) and the (.+)\.', first)
        if not m:
            m = re.fullmatch(r'Step 1: (?:find|locate) the (.+?) and the (.+?), then the (.+)\.', first)
        return tuple(m.groups()) if m else None
    m = re.fullmatch(r'Seen: (.+?) in frame (\d+); (.+?) in frame (\d+); (.+?) in frame (\d+)\.', first)
    return (m[1],m[3],m[5]) if m else None


def questions(obj):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k in ('question','question_text','query') and isinstance(v,str): yield v
            elif isinstance(v,(dict,list)): yield from questions(v)
    elif isinstance(obj,list):
        for v in obj: yield from questions(v)


def main():
    OUT.mkdir(exist_ok=True)
    pin(__file__); pin(BASE/'d2_support.py'); pin(BASE/'out/SKELETON.md')
    pin(DB,d2.DB_SHA)
    for name in ('BUILD_MANIFEST.json','COUNTS_V7.json','FAMILY_INDEX_RANGES.json','EXCLUSIONS.json'):
        pin(d2.STORE/name)
    seal=load(TREE.parents[1]/'out/TREE_SEAL.json')
    assert seal['tree_sha256'].startswith('8ea1fe6b')
    pin(BASE/'reference/COVERAGE_V2_PUB.tar')
    rooms, excluded = d2.room_authority()
    source_checks = load(D2/'out/CHECKS.json')
    assert source_checks['input_sha256'][str(DB)]['sha256'] == d2.DB_SHA
    assert source_checks['source_native_validator'] == {'pass':93370}
    assert source_checks['source_trace_grammar'] == {'pass':93370}
    assert source_checks['input_sha256'][str(TREE.parents[1]/'out/TREE_SEAL.json')]['sha256'] == pin(TREE.parents[1]/'out/TREE_SEAL.json')['sha256']
    n_format=d2.KIT/'inputs/records/n.json'
    ns=load_n=Path(n_format).read_text();pin(n_format)
    required_remove_keys={'pool','question_type','reason','row_key','scene'}
    assert all(set(json.loads(l))==required_remove_keys for l in ns.splitlines() if l.strip())
    inventory=BASE/'work/LOCAL_FILES.txt';pin(inventory)
    files=inventory.read_text().splitlines()
    by_basename=C.defaultdict(list)
    for p in files:by_basename[Path(p).name].append(p)
    before=C.Counter();allowed=C.Counter();operations=C.Counter();clauses=C.Counter()
    names=C.defaultdict(set);name_fail=[];gtfields=C.Counter();validation=C.Counter();roomhits=C.Counter()
    counts_gt=0;ids=set();source_paths=C.Counter();audit=[];samples={};removals=[]
    allrows=0
    con=sqlite3.connect(DB.as_uri()+'?mode=ro&immutable=1',uri=True)
    for i,raw in con.execute('SELECT i,row FROM rows ORDER BY i'):
        allrows+=1;r=json.loads(raw)
        assert r['qid'] not in ids,r['qid'];ids.add(r['qid'])
        if not r.get('question_type','').startswith('object_rel_direction_'):continue
        opening,subtype,clause=d2.classify(r);assert opening in OPENINGS and clause in CLAUSES
        key=(*d2.family(r),opening,clause);before[key]+=1;clauses[clause]+=1
        canonical,method=rooms.canonical(r);room=rooms.room(canonical) if canonical else None
        assert room,('unresolved_room',r['qid'])
        hits=sorted(k for k,v in excluded.items() if room in v)
        for h in hits:roomhits[h]+=1
        if not hits:allowed[key]+=1
        else:removals.append(dict(pool=r['pool'],question_type=r['question_type'],reason='excluded_room:'+','.join(hits),row_key=r['qid'],scene=r['dataset']+'/'+r['scene']))
        # Reuse D2's full-source validation only for this identical DB and sealed tree.
        validation['native_pass']+=1;validation['trace_grammar_pass']+=1
        body=r['target'].splitlines()
        own_turn=any(('half turn' in line.lower() or 'half-turn' in line.lower()) and line != body[1] for line in body)
        keep=any(re.search(r'keep that heading|keeps? the (?:reference )?heading|no turn applies',line,re.I) for line in body)
        operations[(opening,clause,'own_half_turn' if own_turn else 'no_half_turn','keep_explicit' if keep else 'no_keep_phrase')]+=1
        ns=object_names(r,opening)
        if ns:
            names[(opening,clause)].update(norm(n) for n in ns)
        elif len(name_fail)<30:name_fail.append(dict(qid=r['qid'],first=body[1]))
        present=sorted(set(r)&{'gt','geometry','gt_geometry','roles','ground_record','gt_authority','object_ids'})
        gtfields[','.join(present) or 'none']+=1
        assert not present,('GT-bearing row needs source adapter',r['qid'],present)
        source_paths[r['provenance']['source']]+=1
        samples.setdefault(key,(i,r))
        audit.append(dict(i=i,qid=r['qid'],question_type=r['question_type'],pool=r['pool'],retrace_rule=key[2],
                          opening=opening,clause=clause,room=room,excluded_by=hits,source=r['provenance']['source'],
                          source_row_sha256=hashlib.sha256(raw.encode()).hexdigest(),GT_status='MISSING'))
    con.close()
    assert allrows==204413 and sum(before.values())==93370 and len(before)==30
    assert sum(allowed.values())==90344 and len(removals)==3026
    assert not name_fail,name_fail
    for mod in list(sys.modules.values()):
        path=getattr(mod,'__file__',None)
        if path and str(path).startswith(str(TREE)) and str(path).endswith('.py'):
            pin(path,seal['files'][str(Path(path).relative_to(TREE))])
    for rel in ('student_pilot/ground_rows.py','generator/derivgen_v7/derivgen/ground_v312.py'):
        pin(TREE/rel,seal['files'][rel])
    # No source is replaced without certified geometry. Room removals are separate and unbound.
    for name in ('NEW_ROWS.jsonl','REPLACEMENTS.jsonl','REMOVE.json'):(OUT/name).write_text('')
    with (OUT/'ROOM_EXCLUSIONS.json').open('w') as f:
        for r in removals:f.write(json.dumps(r,sort_keys=True)+'\n')
    rp=pin(OUT/'ROOM_EXCLUSIONS.json')
    parser=d2.row_removals.Removals([dict(path=rp['path'],sha256=rp['sha256'])])
    assert len(parser.keys[0])==len(removals)
    assert all(parser.match(dict(qid=r['row_key']))==[0] for r in removals)
    # Report exact source identities and checked locations; never substitute another scene's geometry.
    missing=[]
    for p,n in sorted(source_paths.items()):
        candidates=[p]
        if p.startswith('/scratch/jjyeung/orch_n30/'):
            candidates.append(p.replace('/scratch/jjyeung/orch_n30/','/scratch/jjyeung/n30_mirror/',1))
        matches=by_basename[Path(p).name]
        existing=[q for q in candidates if Path(q).is_file()]
        assert not existing and not matches,('source arrived: inspect adapter',p,existing,matches)
        missing.append(dict(expected_path=p,rows=n,checked_paths=[dict(path=q,exists=False) for q in candidates],
                            inventory_basename_matches=matches,status='MISSING',
                            required='Source-qid to instance roles; object coordinates; signed-up/frame convention; boundary policy; verified sampled frames for Seen opening.'))
    # Inventory available wording corpora. No template is derived from these wordings.
    corp=[];wordings=set()
    wording_paths=[TREE/'student_pilot/r2_dev_merged.json',
        TREE/'tests/fixtures/benchmark_eval/vsibench/answerable500_gt_canonical.json',
        TREE/'tests/fixtures/benchmark_eval/vstibench/vstibench_repr_450_v2.json']
    for p in wording_paths:
        obj=load(p);qs=list(questions(obj));wordings.update(norm(q) for q in qs)
        corp.append(dict(path=str(p),question_occurrences=len(qs)))
    dump('WORDING_CORPUS.json',dict(status='PARTIAL_INVENTORY',corpora=corp,unique_normalized_questions=len(wordings),
        normalized_questions=sorted(wordings),threshold=0.10,normalization='NFKC, casefold, collapse whitespace',
        metric='Levenshtein / max character length',comparisons=0,removed=0,
        completeness='MISSING: full R0-dev, dev-S1 and all benchmark wording corpora are not bound; no candidates generated.'))
    b0,b1=bounds(before),bounds(allowed)
    assert b0['equal_four_binary_cells']==106234 and b1['equal_four_binary_cells']==101004
    assert b1['within_each_opening_binary']==56348
    assert b1['equal_six_literal_cells']==196678
    dump('COUNTS.json',dict(status='PASS_CENSUS_ONLY',store_rows=allrows,direction_rows=sum(before.values()),
        before=cells(before),room_eligible=cells(allowed),actual_after=cells(before),
        opening_clause_before=cross_counts(before),opening_clause_room_eligible=cross_counts(allowed),
        opening_clause_actual_after=cross_counts(before),
        actual_after_definition='No row changes are bound. ROOM_EXCLUSIONS is a separate proposed N room-rule patch.',
        source_operations=cells(operations,('opening','clause','half_turn','heading_keep')),
        vocabulary=[dict(opening=o,clause=c,distinct_names=len(names[o,c]),names=sorted(names[o,c])) for o in OPENINGS for c in CLAUSES],
        room_exclusions=dict(roomhits)))
    dump('PLAN.json',dict(status='MISSING_GT; NO_ROWS_ADMITTED',
        binding_interpretation='Both clauses means toward versus away/opposite; both openings have equal shares in each group and each opening has equal clause shares (four equal cells). Literal clauses are also reported separately.',
        before_room_rule=b0,after_room_rule=b1,
        cap=30000,cap_feasible_preserving_rows=False,
        size_justification='The largest retained cell fixes the common cell count. Four times that count minus retained total is a sharp count-only lower bound. Geometry and quadrant shortages can increase it.',
        no_drop='Do not remove compliant rows to meet the size cap. Preserve existing away coverage, including the 481 away rows lost to mandatory K1 exclusions, through GT-certified additions.',
        quadrant_policy='Balance all four GT reference quadrants within each family/opening/turn wording; report final answer quadrants separately. Never flip labels. Medium uses its actual angle and question threshold.',
        object_policy='Select from room-eligible Step 1 scenes and object triples, greedily maximize uncovered normalized names within each GT quota, ties by sha256(sb_rowD3|qid); report achieved names, never promise all names before GT admission.',
        source_reuse_limit=6,source_reuse_reason='At most one variant per opening and literal clause; deduplicate unchanged source variant.',
        frame_policy='Step 1 has no frame citation. Seen requires per-object source-bound sampled-frame evidence; never invent a frame for a Step 1 source.',
        actual_new_rows=0,actual_replacements=0,actual_max_source_reuse=0))
    dump('ROW_AUDIT.json',dict(status='MISSING_GT',records=audit))
    dump('MISSING.json',dict(status='MISSING',sources=missing,
        GT='No source-bound numeric coordinates or instance-role mappings occur in the direction store rows. D2 contains no GT recomputation implementation for these rows.',
        additional=['Per-object sampled-frame evidence for the Step 1 sources to support Seen variants.',
                    'Complete dev/benchmark wording corpus with pinned membership.',
                    'A source-bound direct-VQA packing/GT adapter; ground_rows.pack requires ground records/events absent here.']))
    with (OUT/'READ30.md').open('w') as f, (OUT/'READ30_CONTENT.txt').open('w') as t:
        f.write('MISSING: generated rows do not exist. These are 30 complete SOURCE rows, one per occupied family/pool/opening/clause cell.\n\n')
        for j,(_, (i,r)) in enumerate(sorted(samples.items()),1):
            f.write(f'## {j}. Source row {i}\n\n```json\n'+json.dumps(r,ensure_ascii=False,indent=2)+'\n```\n\n')
            t.write(f"{j}. {r['qid']} | {r['question_type']} | {r['pool']}\n{r['student_input']['question']}\n"+' | '.join(r['student_input']['options'])+'\n'+r['target']+'\n\n')
    dump('CHECKS.json',dict(status='MISSING',binding_ready=False,census='PASS',room_rule='PASS_SOURCE_AUDIT',
        source_validation_basis='D2 full-row native/grammar checks reused for identical pinned DB and tree seal',
        direction_rows=93370,source_validation=dict(validation),source_qids_unique=True,source_GT_fields=dict(gtfields),
        retained_rows_after_room_rule=90344,excluded_rows=3026,room_hits={k:roomhits[k] for k in excluded},
        exact_cell_counts=dict(status='FAIL_SHORT_CELLS',required_new_rows_lower_bound=101004,actual_new_rows=0,
            shortages=[x for x in b1['family_quotas'] if x['required_additions']]),
        new_qids_and_candidate_ids='MISSING: no new rows',new_and_source_pack_validate='MISSING: direct sources pass r2_contract/trace_grammar; no GT-bound ground packing record',
        edited_field_diff='MISSING: no generated/source pairs',independent_GT_recomputation='MISSING: no bound geometry',
        clause_driven_skeleton='SPECIFIED in SKELETON.md for both openings and all three wordings; no admitted row tests',
        reference_quadrant_balance='MISSING: labels and traces are not GT geometry',object_coverage='CENSUSED; no generated name expansion',
        source_reuse=dict(actual_max=0,limit=6,status='MISSING generated rows'),
        normalized_edit_distance=dict(threshold=0.10,comparisons=0,removed=0,status='MISSING candidate rows and complete corpus'),
        read30=dict(source_rows=30,generated_rows=0,status='MISSING generated-row review'),
        replacements=0,new_rows=0,removal_records=0,room_exclusion_records=3026,
        removal_format='N n.json five-key JSONL; empty REMOVE.json has no replacement removals; separate ROOM_EXCLUSIONS passes native parser'))
    dump('REMOVE_META.json',dict(status='NO_REPLACEMENTS',REMOVE=pin(OUT/'REMOVE.json'),records=0,
        room_exclusions=rp,room_exclusion_records=3026,bound=False,
        note='Exact n.json records cannot carry extra hash keys; this sidecar pins their complete inputs.'))
    (BASE/'STATUS.md').write_text('The census and native validators cover all 93,370 direction rows. N excludes 3,026 K1 rows, leaving 90,344. Equal shares across the four opening × toward/turn cells require at least 101,004 additions while retaining these rows. All 11 named source packs and source-bound GT geometry are MISSING. The deliverable has zero admitted rows and zero replacement removals; its independent artifact checks and report are pending.\n')
    print(json.dumps(dict(status='MISSING',before=cross_counts(before),room_eligible=cross_counts(allowed),
        vocabulary={f'{o}|{c}':len(v) for (o,c),v in names.items()},operations=cells(operations,('opening','clause','turn','keep')),
        min_four_cell_additions=b1['equal_four_binary_cells'],missing_sources=len(missing)),indent=2))
    return 2

if __name__=='__main__':raise SystemExit(main())
