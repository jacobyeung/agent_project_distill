"""Audit v7 direction sources and refuse output without source-bound GT geometry.

Run: PYTHONDONTWRITEBYTECODE=1 python build_rows.py
Exit 2 means the requested row build remains MISSING, not a successful empty build.
Only local scratch inputs are read. No frame payloads or NFS paths are opened.
"""
import ast
import collections
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import sys
import unicodedata

os.environ.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', CUDA_VISIBLE_DEVICES='')
sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
OUT = BASE / 'out'
TREE = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
KIT = TREE.parents[2]
STORE = Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7')
DB = STORE / 'vqa/rows.sqlite'
DB_SHA = '210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443'
sys.path.insert(0, str(TREE))
from student_pilot import r1_rooms, r2_contract, trace_grammar, row_removals
from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity

PINS = {}


def pin(path, expected=None):
    path = Path(path).resolve()
    if str(path) in PINS:
        result = PINS[str(path)]
    else:
        h = hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda: f.read(4 << 20), b''):
                h.update(block)
        result = dict(sha256=h.hexdigest(), bytes=path.stat().st_size)
        PINS[str(path)] = result
    if expected:
        assert result['sha256'] == expected, (path, 'hash mismatch')
    return dict(path=str(path), **result)


def load(path, expected=None):
    pin(path, expected)
    return json.loads(Path(path).read_text())


def dump(name, value):
    (OUT / name).write_text(json.dumps(dict(command='PYTHONDONTWRITEBYTECODE=1 python build_rows.py',
        input_sha256=PINS, **value), indent=2, sort_keys=True) + '\n')


def norm(text):
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())


def classify(row):
    q = row['student_input']['question']
    if re.search(r'\bopposite\b', q, re.I):
        clause = 'opposite'
    elif re.search(r'\b(?:away from|with my back to)\b', q, re.I):
        clause = 'away'
    elif (re.search(r'\b(?:facing|face|look|looking|oriented|directed|aiming|viewing|directing my view|gazing|turned)(?: directly| straight)?(?: towards?| at)? the\b', q, re.I)
          or re.search(r'with my gaze fixed on the\b', q, re.I)
          or re.search(r'^With the .+ next to me and the .+ ahead,', q)
          or re.search(r'\bwith the .+ ahead of (?:me|you)\b', q, re.I)):
        clause = 'toward'
    else:
        clause = 'UNKNOWN'
    first = row['target'].removeprefix('<think>\n').splitlines()[0]
    if first.startswith('Seen:'):
        opening = 'Seen'
        subtype = 'Seen'
    elif first.startswith('Step 1:'):
        opening = 'Step 1'
        subtype = re.match(r'Step 1:\s*(\w+)', first)[1]
    else:
        opening = 'OTHER'
        subtype = first
    return opening, subtype, clause


def family(row):
    return (row['question_type'], row['pool'], row.get('retrace', {}).get('rule', 'none'))


def counter_rows(counter, fields):
    return [dict(zip(fields, key), rows=n) for key, n in sorted(counter.items())]


def room_authority():
    audit = load(BASE / 'alias_inputs/out/ROOM_AUDIT_TIERED.json')
    alias = load(BASE / 'alias_inputs/out/TIERED_ALIAS_MAP.json')
    assert not alias['conflicts'] and not alias['quarantined_tokens']
    prior = load(KIT / 'w17b/work/build17/proofs/rooms/RESULT.json')['audit']
    auth = prior['authority']
    for p in auth.values():
        pin(p['path'], p['sha256'])
    rooms = r1_rooms.Rooms(auth)
    # These are proof-bearing aliases from the supplied local archive, not inferred names.
    rooms.aliases = {key: value['canonical'] for key, value in alias['aliases'].items()}
    teacher = load(BASE / 'alias_inputs/work/TEACHER_K1.raw', r1_rooms.TEACHER)
    assert {rooms.room(c['canonical']) for c in teacher['captures'] if c['k1_split']=='heldout'} == rooms.k1
    sets = {'K1': rooms.k1}
    for name in ('R0', 'withheld-80', 'BENCH v2', 'dev-S1'):
        p = audit['list_checks'][name]['pin']
        pin(p['path'], p['sha256'])
        raw = Path(p['path']).read_text()
        sets[name] = set(raw.split()) if name == 'R0' else set(json.loads(raw)['rooms' if name == 'withheld-80' else 'physical_groups'])
    assert {k:len(v) for k,v in sets.items()} == {'K1':50,'R0':372,'withheld-80':80,'BENCH v2':511,'dev-S1':100}
    return rooms, sets


def main():
    OUT.mkdir(exist_ok=True)
    pin(__file__)
    pin(DB, DB_SHA)
    pin(STORE / 'BUILD_MANIFEST.json')
    pin(STORE / 'COUNTS_V7.json')
    pin(STORE / 'FAMILY_INDEX_RANGES.json')
    pin(STORE / 'EXCLUSIONS.json')
    pin(BASE / 'COVERAGE_V2_PUB.tar')
    seal = load(TREE.parents[1] / 'out/TREE_SEAL.json')
    assert seal['tree_sha256'].startswith('8ea1fe6b')
    for rel in ('student_pilot/r1_rooms.py', 'student_pilot/r2_contract.py',
                'student_pilot/r2_grammar.py', 'student_pilot/trace_grammar.py',
                'student_pilot/row_removals.py', 'student_pilot/ground_rows.py',
                'generator/derivgen_v7/derivgen/ground_v312_quality.py'):
        pin(TREE / rel, seal['files'][rel])
    n_format = KIT / 'inputs/records/n.json'
    pin(n_format)
    n_records = [json.loads(line) for line in n_format.read_text().splitlines() if line.strip()]
    assert all(set(r)=={'pool','question_type','reason','row_key','scene'} for r in n_records)
    rooms, excluded = room_authority()
    fields = ('question_type','pool','retrace_rule','opening','clause')
    counts = collections.Counter()
    subtypes = collections.Counter()
    room_counts = collections.Counter()
    clauses = collections.Counter()
    source_paths = collections.Counter()
    missing_gt_keys = collections.Counter()
    native = collections.Counter()
    grammar = collections.Counter()
    cell_examples = {}
    ids = set()
    metadata = []
    total = 0
    all_ids = set()
    removals = []
    source_failures = []
    source_wording = collections.Counter()
    with sqlite3.connect(DB.as_uri()+'?mode=ro&immutable=1',uri=True) as con, (OUT/'REFUSED.jsonl').open('w') as refused:
        for i, raw in con.execute('SELECT i,row FROM rows ORDER BY i'):
            total += 1
            r = json.loads(raw)
            assert r['qid'] not in all_ids
            all_ids.add(r['qid'])
            if not r.get('question_type','').startswith('object_rel_direction_'):
                continue
            assert r['question_type'] in {'object_rel_direction_easy','object_rel_direction_medium','object_rel_direction_hard'}
            opening, subtype, clause = classify(r)
            key = (*family(r), opening, clause)
            counts[key] += 1
            subtypes[(r['question_type'], opening, subtype, clause)] += 1
            clauses[clause] += 1
            assert clause != 'UNKNOWN', r['qid']
            ids.add(r['qid'])
            cell_examples.setdefault(key, (i,r))
            source = r['provenance']['source']
            source_paths[source] += 1
            # Answers and old trace relations are deliberately not geometry authorities.
            present = sorted(set(r) & {'gt','geometry','gt_geometry','roles','ground_record','gt_authority','object_ids'})
            missing_gt_keys[','.join(present) or 'none'] += 1
            assert not present, ('New GT-bearing input requires a real source adapter',r['qid'],present)
            canonical, method = rooms.canonical(r)
            room = rooms.room(canonical) if canonical else None
            hits = sorted(name for name, values in excluded.items() if room in values)
            room_counts[('resolved' if room else 'unresolved',)] += 1
            for hit in hits:
                room_counts[(hit,)] += 1
            if not hits:
                room_counts[('allowed',)] += 1
            if hits:
                removals.append(dict(pool=r['pool'], question_type=r['question_type'],
                    reason='excluded_room:'+','.join(hits), row_key=r['qid'], scene=r['dataset']+'/'+r['scene']))
            try:
                r2_contract.validate(r,'vqa',require_frames=False)
                native['pass'] += 1
            except Exception as exc:
                native['fail'] += 1
                if len(source_failures)<30:
                    source_failures.append(dict(qid=r['qid'],check='N_native_direct',error=str(exc)))
            violations = trace_grammar.validate_row(r)
            grammar['fail' if violations else 'pass'] += 1
            if violations and len(source_failures)<30:
                source_failures.append(dict(qid=r['qid'],check='N_trace_grammar',error=str(violations)))
            first = r['target'].splitlines()[1]
            source_wording[(opening,'frames' if re.search(r'\bframe\s+\d+',first) else 'no_frames')] += 1
            meta = dict(store_i=i, qid=r['qid'], source=source, question_type=r['question_type'],pool=r['pool'],
                        opening=opening,clause=clause,canonical=canonical,room=room,excluded_by=hits,
                        status='MISSING',reason='MISSING_source_bound_GT_geometry_and_instance_roles')
            metadata.append(meta)
            record = dict(meta, input_sha256={str(DB):DB_SHA},
                source_row_sha256=hashlib.sha256(raw.encode()).hexdigest())
            refused.write(json.dumps(record,sort_keys=True,separators=(',',':'))+'\n')
    assert total==204413
    n = sum(counts.values())
    assert n == len(ids) == len(metadata) == 93370
    step = sum(v for k,v in counts.items() if k[-2]=='Step 1')
    assert step == 49901
    assert all(k[-1]=='toward' for k in counts if k[-2]=='Step 1')
    assert sum(v for k,v in counts.items() if k[-2]=='Seen') == n-step
    (BASE/'STATUS.md').write_text(f'The census covers {n:,} direction rows and reproduces the 49,901 Step 1 toward rows. All {n:,} lack source-bound GT geometry. The five room lists are applied independently; {len(removals):,} rows are excluded. The build remains MISSING while output reports are assembled.\n')
    # Original source paths and their same-relative-path local mirrors are checked exactly.
    missing = []
    for source, count in sorted(source_paths.items()):
        candidates = [source]
        if source.startswith('/scratch/jjyeung/orch_n30/'):
            candidates.append(source.replace('/scratch/jjyeung/orch_n30/','/scratch/jjyeung/n30_mirror/',1))
        missing.append(dict(expected_path=source,rows=count,
            checked_paths=[dict(path=p,exists=Path(p).is_file()) for p in candidates],
            status='MISSING',needed='Question-to-instance roles, GT object geometry, and coordinate/up convention.'))
    assert all(not p['exists'] for item in missing for p in item['checked_paths'])
    # 25% is a proposal, contingent on GT availability and all admission checks.
    # Exact quadrant quotas total 12,468 source triples; each contributes one away and one opposite twin.
    proposed = []
    for level in ('easy','medium','hard'):
        population = sum(v for k,v in counts.items() if k[0].endswith('_'+level) and k[-2]=='Step 1')
        per_quad = population // 16
        for quadrant in ('front-left','front-right','back-left','back-right'):
            for clause in ('away','opposite'):
                proposed.append(dict(question_type='object_rel_direction_'+level,reference_quadrant=quadrant,
                    clause=clause,required=per_quad,actual=0,status='MISSING'))
    assert sum(x['required'] for x in proposed)==24936
    (OUT/'REPLACEMENTS.jsonl').write_text('')
    (OUT/'TWINS.jsonl').write_text('')
    with (OUT/'REMOVE.json').open('w') as f:
        for item in removals:
            assert set(item)==set(n_records[0])
            f.write(json.dumps(item,sort_keys=True,separators=(',',':'))+'\n')
    remove_pin = pin(OUT/'REMOVE.json')
    removal_check = row_removals.Removals([dict(path=remove_pin['path'],sha256=remove_pin['sha256'])])
    assert len(removal_check.keys[0]) == len(removals)
    assert all(removal_check.match(dict(qid=x['row_key']))==[0] for x in removals)
    # Select all family/clause/opening cells, then fill deterministically if necessary.
    selected = [value for _,value in sorted(cell_examples.items())]
    assert len(selected)>=30, len(selected)
    selected = selected[:30]
    with (OUT/'READ30.md').open('w') as f:
        f.write('MISSING: no generated rows passed GT admission. These are 30 complete SOURCE rows for inspection, not replacements.\n\n')
        for number,(i,r) in enumerate(selected,1):
            f.write(f'## {number}. Source store row {i}\n\n```json\n'+json.dumps(r,ensure_ascii=False,indent=2)+'\n```\n\n')
    with (BASE/'work/READ30_CONTENT.txt').open('w') as f:
        for number,(i,r) in enumerate(selected,1):
            f.write(f'{number}. {r["qid"]} | {r["question_type"]} | {r["pool"]}\n'+r['student_input']['question']+'\n'+' | '.join(r['student_input']['options'])+'\n'+r['target']+'\n\n')
    # Pin every imported local kit source actually used; no code writes in the live kit.
    for module in list(sys.modules.values()):
        p = getattr(module,'__file__',None)
        if p and str(p).startswith(str(TREE)) and str(p).endswith('.py'):
            rel = str(Path(p).relative_to(TREE))
            pin(p,seal['files'][rel])
    pin(OUT/'REFUSED.jsonl')
    pin(OUT/'READ30.md')
    pin(OUT/'REPLACEMENTS.jsonl')
    pin(OUT/'TWINS.jsonl')
    checks = dict(status='MISSING',binding_ready=False,store_rows=total,direction_rows=n,
        classification='PASS',classification_cells=len(counts),source_qids_unique=True,
        source_native_validator=dict(native),source_trace_grammar=dict(grammar),
        source_validation_examples=source_failures,source_GT_fields=dict(missing_gt_keys),
        room_rule=dict(counts={k[0]:v for k,v in room_counts.items()},new_rows=0,new_row_hits=0),
        exact_cell_counts=dict(status='FAIL_SHORT_CELLS',cells=len(proposed),required=24936,actual=0),
        replacement_rows=0,twin_rows=0,refused_GT_rows=n,
        source_reuse=dict(actual_max=0,proposed_max=3,scope='one replacement plus away and opposite twins'),
        pack_and_validate_new_rows='MISSING: no GT-admitted rows; not a vacuous pass',
        independent_GT_recomputation='MISSING: no geometry/instance-role authority for these qids',
        field_diff='MISSING: no new rows',candidate_ids='MISSING: no new rows',
        candidate_formula=str(TREE/'generator/derivgen_v7/derivgen/ground_v312_quality.py')+':candidate_identity',
        normalized_edit_distance=dict(status='MISSING: no candidate wordings generated or compared',
            normalization='Unicode NFKC, casefold, collapse whitespace',metric='Levenshtein / max character length',
            proposed_reject_threshold=0.10,removed=0,comparison_count=0,
            limitation='No complete dev/benchmark wording corpus bound; do not interpret zero removals as clearance.'),
        read30=dict(source_rows=30,generated_rows=0,status='MISSING generated-row review; source text inspected separately'),
        removal=dict(records=len(removals),format='PASS: exactly N n.json JSONL keys; native Removals parser passes',
            scope='Only proven excluded rooms. Missing GT alone does not remove an existing source row.',
            provenance='Input hashes are in REMOVE_META.json because exact N records have only five fields.'))
    dump('COUNTS.json',dict(status='PASS',store_rows=total,direction_rows=n,clauses=dict(clauses),
         cells=counter_rows(counts,fields),opening_variants=counter_rows(subtypes,('question_type','opening','verb','clause')),
         frame_citations=counter_rows(source_wording,('opening','citations'))))
    dump('MISSING.json',dict(status='MISSING',sources=missing,refused_rows=n,
        explanation='No source-bound numeric GT or instance roles exist in the store rows. Named source packs are absent. Available R0-dev rasters cannot supply admissible training GT.'))
    dump('TWIN_PLAN.json',dict(status='MISSING',proposed_share=12468/49901,source_count=12468,
        twins=24936,quota_cells=proposed,selection='Lowest sha256(sb_rowD2|qid) among GT-admitted sources within family and reference quadrant; paired variants; no replacement reuse.',
        rationale='Toward rows dominate the census. A quarter of Step 1 sources adds both turn wordings while keeping toward rows largest. Each family balances all four reference quadrants; hard twins are exactly half front and half back. This does not fit R0-dev labels.',
        reference_quadrant='Must come from GT coordinates, including easy/medium rows; old answer labels cannot establish this cell.',
        required_assertion='Every one of the 24 cells must meet required; no silently reduced quota.'))
    dump('CHECKS.json',checks)
    dump('REMOVE_META.json',dict(status='PASS',records=len(removals),output=remove_pin,
        reason='Pinned physical-room exclusions, independent of missing GT.',bound=False))
    lines=['| Family | Pool | Opening | Clause | Rows |','|---|---|---|---|---:|']
    for k,v in sorted(counts.items()):
        lines.append(f'| {k[0]} | {k[1]} | {k[-2]} | {k[-1]} | {v} |')
    (OUT/'COUNTS.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(status='MISSING',direction_rows=n,clauses=clauses,counts_cells=len(counts),
        room_counts={k[0]:v for k,v in room_counts.items()},native=native,grammar=grammar,
        proposed_twins=24936,actual_twins=0,missing_sources=len(missing)),indent=2))
    return 2


if __name__=='__main__':
    raise SystemExit(main())
