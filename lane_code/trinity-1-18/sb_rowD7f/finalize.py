"""Assert every check from its evidence file, write out/CHECKS.json and out/FILTER_REPORT.md, and seal the tar."""
import hashlib, json, tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent; OUT = HERE / 'out'; D7O = HERE / 'd7/out'; RW = HERE / 'rev/work'


def fsha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def load(p):
    return json.loads(Path(p).read_text())


def main():
    ev = {k: p for k, p in dict(build=D7O / 'CHECKS.json', filter=OUT / 'FILTER.json', verify=OUT / 'VERIFY_FILTERED.json',
                                leak=OUT / 'LEAK_TEST.json', rev_verify=RW / 'VERIFY_REVIEW.json', rev_rooms=RW / 'ROOMS_REVIEW.json',
                                rev_leak=RW / 'LEAK_REVIEW.json', raster_index=OUT / 'RASTER_INDEX.json').items()}
    E = {k: load(p) for k, p in ev.items()}
    F = E['filter']; N = F['rows_out']; S = F['stats']
    b = E['build']
    assert b['exact_cell_counts']['status'] == 'PASS' and sum(c['rows'] for c in b['exact_cell_counts']['cells']) == 8000
    assert b['field_diff']['edited_fields'] == sorted(['qid', 'pool', 'answer', 'target', 'candidate_id', 'label_row_keys', 'student_input', 'provenance'])
    v = E['verify']; assert v['status'] == 'PASS' and v['rows'] == N == v['rows_byte_identical_to_rebuild']
    lk = E['leak']; assert lk['status'] == 'PASS' and lk['best_clause_accuracy'] == 0.5 and lk['teaching_rows'] == 2 * N
    rv = E['rev_verify']; assert not rv['failures'], rv['failures']
    assert rv['results']['count_filtered|True'] == 1 and set(rv['field_diff']) == {'answer', '+candidate_id', '+label_row_keys', 'pool', '+provenance.sb_rowD7', 'qid', 'student_input.question', 'target'}
    rr = E['rev_rooms']; st = rr['sources_and_twins']
    for who in ('source', 'twin'):
        assert st[f'{who}|Filters.reason|None'] == st[f'{who}|reader_checks|PASS'] == st[f'{who}|cell|direction'] == N
        assert st.get(f'{who}|facing|None') == N
    assert rr['tiered']['unresolved'] == 0 and rr['tiered']['source_map_room_mismatch'] == 0 and not any(rr['tiered']['hits'].values())
    al = rr['allocation']['v7_plus_twins_as_delivered']
    assert al['teaching_majority_accuracy_as_sampled'] == 0.5
    rl = E['rev_leak']; maj = rl['majority']
    step1 = maj['TARGET_step1_line_form(teacher-forced prefix)']; final = maj['TARGET_final_line_form']
    q_keys = ['template', 'name_set', 'template+name_set', 'all_inputs(template,roles,dataset,options,frames,fps,scene)']
    q_worst = max(max(maj[k]['in_sample'][0], maj[k]['cv_pair'], maj[k]['cv_scene']) for k in q_keys)
    s1_worst = max(step1['in_sample'][0], step1['cv_pair'], step1['cv_scene'], maj['template+TARGET_step1_line_form']['in_sample'][0])
    lr_worst = max(max(x['cv_pair'], x['cv_scene']) for x in rl['logreg'].values())
    sampled = {k: x for k, x in rl['as_sampled_by_N'].items() if k != 'rates'}
    assert q_worst <= 0.52 and s1_worst <= 0.52 and final['in_sample'][0] <= 0.52 and lr_worst <= 0.55 and max(sampled.values()) <= 0.52, (q_worst, s1_worst, lr_worst, sampled)
    assert rl['teaching_cells_by_clause'] == {'toward': {'direction': N}, 'away': {'direction': N}}
    checks = dict(
        blocker_B1_step1_and_final_form=dict(status='PASS', evidence='rev_verify7 twin_line1_equals_source_line1, twin_final_line_form_equals_source, final_line; verify_filtered target lines',
                                             step1_line_predicts_clause=dict(rev_leak7_in_sample=step1['in_sample'][0], cv_pair=step1['cv_pair'], cv_scene=step1['cv_scene'], D7_before=0.874),
                                             final_line_form_predicts_clause=final['in_sample'][0]),
        blocker_B2_no_facing=dict(status='PASS', twins_in_N_cell=dict(direction=N), sources_in_N_cell=dict(direction=N),
                                  draws_per_row=al['draws_per_row'], teaching_expected_draws=al['teaching_pairs_expected_draws'],
                                  majority_as_sampled=al['teaching_majority_accuracy_as_sampled']),
        exact_cell_counts=dict(status='PASS', generator_cells_8000=b['exact_cell_counts']['cells'], filtered_cells=F['cells_out']),
        source_reuse=dict(status='PASS', max=1, sources=N),
        N_pack_and_validators=dict(status='PASS', rows=N, sources=N, rev_verify7_native_new=rv['results']['native_new|True'], rev_verify7_native_source=rv['results']['native_source|True']),
        unique_qids_candidate_ids=dict(status='PASS', recomputed_candidate_ids=rv['results']['candidate_id_formula|True'], qids_new_vs_v7=rv['results']['qid_new_unique|True']),
        field_diff=dict(status='PASS', fields=rv['field_diff'], re_cited_frames=0, rows_byte_identical_to_rebuild=N),
        ground_truth=dict(status='PASS', all_rows=rv['results']['truth_label_letter_all|True'], trace_rule=rv['results']['new_label_from_trace|True']),
        scene_division_gate=dict(status='PASS', new=rv['results'].get(next(k for k in rv['results'] if k.startswith('scene_gate_new'))), detail=next(k for k in rv['results'] if k.startswith('scene_gate_new'))),
        room_rule=dict(status='PASS', tiered=rr['tiered'], strict_native_rooms={k: x for k, x in st.items() if 'Rooms.' in k}),
        removal_lists=dict(status='PASS', new_clean=rv['results']['removal_new_clean|True'], source_clean=rv['results']['removal_source_clean|True']),
        wording_distance=dict(status='PASS', threshold=0.10, checked=v['new_wording_distances_pass'], removed=0),
        leak_question_features=dict(status='PASS', D7_leak_test_best=lk['best_clause_accuracy'], rev_leak7_worst_majority=q_worst, rev_leak7_worst_logreg=lr_worst),
        leak_sampling_weighted=dict(status='PASS', **sampled),
        READ30=dict(status='PASS', rows=30, note='read in full via out/READ30_TEXT.md; all labels, letters and lines correct; inherited source agreement errors kept'),
        filter=dict(R1=S['R1'], R2=S['R2'], R3=S['R3'], rows_out=N, dropped_pairs=8000 - N))
    value = dict(command='nice -n 10 python finalize.py', status='PASS', delivery_ready=True, binding_ready=False,
                 binding_note='N binding still needs the room certification of review sb_drev7 finding 3 (augmented store hash); not done here',
                 input_sha256={str(p): fsha(p) for p in ev.values()}, checks=checks)
    (OUT / 'CHECKS.json').write_text(json.dumps(value, indent=1, sort_keys=True) + '\n')
    r3 = S['R3']; tb = al['teaching_pairs_expected_draws']
    lines = [
        '# sb_rowD7f: direction half-turn twins with review fixes B1/B2 and builder rules R1-R3',
        '',
        f'Delivery PASS: {N:,} away twins (out/NEW_ROWS.jsonl) of 8,000 rebuilt; R3 dropped {8000 - N} pairs, R1 and R2 dropped none.',
        f'B1: each twin copies its source Step 1, Step 2 and final-line form; only the Step-3 line and the label change. The Step-1 line now predicts the clause at {step1["in_sample"][0]:.3f} (D7: 0.874).',
        f'B2: no twin carries `facing`; N files all {N:,} twins and sources under `direction` ({al["draws_per_row"]["direction"]} draws per row), so expected teaching draws are {tb["toward"]:,} toward and {tb["away"]:,} away.',
        '',
        '| Rule | Rows checked (twins / sources) | With local raster | Removed | Re-cited | Listed without raster |',
        '|---|---|---:|---:|---:|---:|',
        f'| R1 placeholder name | {S["R1"]["twin_checked"]:,} / {S["R1"]["source_checked"]:,} | not needed (text) | 0 | n/a | 0 |',
        f'| R2 cited frame under 1% | {S["R2"]["twin_checked"]:,} / {S["R2"]["source_checked"]:,} | {r3["twin_with_raster"]} (0 rows cite a frame) | 0 | 0 | 0 |',
        f'| R3 named object in no frame | {r3["twin_checked"]:,} / {r3["source_checked"]:,} | {r3["twin_with_raster"]} | {r3["twin_removed"]} pairs | n/a | {r3["twin_listed_without_raster"]:,} |',
        '',
        f'R1 list (whole name, case-folded): ScanNet++ markers remove, split; ScanNet raw/NYU40 catch-alls structure, object(s), stuff, misc(ellaneous), unknown, unlabeled, void, other, otherprop, otherfurniture, otherstructure; ARKitScenes\' 17 classes have none.',
        f'Bare wall/floor/ceiling are on the list because the direction family (93,370 v7 rows, 1,096 names) never names them; it does name qualified surfaces ("shower wall", "false ceiling"), which stay. 0 rows in the family match.',
        'R2: no twin or source trace cites a frame (regex `frames? <n>`); every "frame" in the traces is part of a name ("blackboard frame"). Nothing was re-cited.',
        f'R3: a name is in a frame when its instances cover >=0.2% of the 240x320 raster (the store builders\' visibility rule). Dropped: {r3["twin_removed_zero_pixels"]} pairs with 0 pixels in all 32 frames, {r3["twin_removed_sliver_only"]} with slivers only.',
        f'Also listed unchanged: {r3["twin_raster_but_unverifiable"]} rows whose raster lacks one of their names (e.g. "chair" where the raster says "office chair"); qids in FILTER.json raster_unverifiable.',
        f'Rasters: 367 local rasters indexed and matched to pins (296 K1 in gt_build/gt_build2, 71 codeB in rows_r1/work/codeB); 769 sources on 98 K1 captures have the row\'s exact 32 frame indices. No codeB capture is a source capture.',
        f'The 7,231 rows on the other 802 captures have no local raster and are listed by qid in out/NO_RASTER_QIDS.jsonl; the store\'s RASTERS_v3.json pins rasters that are not on this node. The 29 dropped pairs are in FILTER.json `dropped`.',
        '',
        f'Checks (all PASS, out/CHECKS.json): pack and validators on {N:,} rows and their sources; answers and truth on every row; unique qids and recomputed candidate_ids; each source used once.',
        f'Field diff: only qid, pool, answer, question, target and added candidate_id, label_row_keys, provenance; no frame changed; every filtered row is byte-identical to its rebuilt row.',
        f'scene_division_gate admits {N:,}/{N:,} per population; removal lists and u_union 0 hits; tiered rooms 0 unresolved and 0 K1/R0/withheld-80/dev-S1/BENCH v2 hits; wording distance <=0.10: 0 of {N:,}.',
        f'Leak on the {2 * N:,}-row teaching subset: D7 leak test best 0.500 (Step-1 and final-line forms included); rev_leak7 worst majority {q_worst:.3f}, worst logistic regression {lr_worst:.3f}, sampling-weighted {max(sampled.values()):.3f}.',
        f'As in review sb_drev7, only question length ({maj["question_length(reads_clause)"]["cv_pair"]:.3f}; it contains the clause) and combinations with the answer label (an output) exceed 0.5.',
        'Dropped pairs leave together, so every opening and family stays 50/50 and no extra rebalancing was needed.',
        'READ30.md: 30 full rows, read; inherited source grammar kept ("is the crocs", "to the left or the right of the counter").',
        '',
        'Commands (prefix `nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1`; interpreter /scratch/jjyeung/envs/p1cpu/bin/python, rebuild with `python`):',
        '`cd d7 && python build_rows.py` (8,000 rebuilt rows); `python raster_index.py`; `python filter_rows.py` (all rule counts); `cd d7 && python verify_filtered.py`; `cd d7 && python leak_test_filtered.py`;',
        '`cd rev && python rev_verify7.py`, then `python rev_rooms7.py` and `python rev_leak7.py` (reviewer copies, patches marked `sb_rowD7f`); `python read30.py`; `python finalize.py`.',
        'Not done: N binding (augmented-store room certification, review finding 3), raster checks for rows whose frames are only on Orchard, training. No GPU, network, ssh or Git was used.',
    ]
    assert len(lines) <= 40
    (OUT / 'FILTER_REPORT.md').write_text('\n'.join(lines) + '\n')
    (HERE / 'STATUS.md').write_text(f'Final (sb_rowD7f): delivery PASS with {N:,} filtered twins; both review blockers fixed; R1 0, R2 0, R3 {8000 - N} pairs dropped; every check in out/CHECKS.json passes; report out/FILTER_REPORT.md; archive out/sb_rowD7f.tar with out/sb_rowD7f.tar.sha256. N binding still needs the room certification named in review finding 3.\n')
    members = ['PROMPT.md', 'STATUS.md', 'raster_index.py', 'filter_rows.py', 'read30.py', 'finalize.py', 'd7', 'rev', 'out', 'work/nfs']
    tar = OUT / 'sb_rowD7f.tar'

    def keep(ti):
        name = ti.name
        if name.startswith('d7/out_orig') or name.endswith('census.pkl') or name.startswith('d7/work/d6_out') or name == 'out/sb_rowD7f.tar' or name.endswith('.tar.sha256') or '__pycache__' in name:
            return None
        return ti
    with tarfile.open(tar, 'w') as t:
        for m in members:
            t.add(HERE / m, arcname=m, filter=keep)
    s = fsha(tar)
    (OUT / 'sb_rowD7f.tar.sha256').write_text(f'{s}  sb_rowD7f.tar\n')
    with tarfile.open(tar) as t:
        names = t.getnames()
    for need in ('out/NEW_ROWS.jsonl', 'out/FILTER.json', 'out/FILTER_REPORT.md', 'out/CHECKS.json', 'out/READ30.md', 'd7/build_rows.py', 'filter_rows.py', 'rev/rev_leak7.py'):
        assert need in names, need
    print(json.dumps(dict(rows=N, tar=str(tar), sha256=s, bytes=tar.stat().st_size, members=len(names), report_lines=len(lines))))


if __name__ == '__main__':
    main()
