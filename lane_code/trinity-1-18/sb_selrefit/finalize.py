"""Assemble the requested internal report and verifiable local archive."""
import collections, hashlib, json, tarfile
from pathlib import Path
import selrefit as S


def main():
    root,out=S.ROOT,S.OUT
    train=S.js(out/'TRAIN_DATA.json');cv=S.js(out/'CV_FROZEN.json');held=S.js(out/'HELDOUT.json');fit=S.js(out/'FIT.json')
    meta=S.js(out/'selector_head_refit.json')
    S.read(root/'heldout.py');S.read(root/'finalize.py');S.read(root/'verify.py')
    # Include every consumed leaf and intermediate, using recorded hashes rather than re-reading raw arrays.
    pins=dict(S.PINS)
    for obj in [train,cv,held,fit,meta]:pins.update(obj['input_sha256'])
    fold_models=[]
    for k in range(5):
        m=S.js(out/f'fold_{k}.json')
        fold_models.append(dict(fold=k,weights_sha256=m['weights_sha256'],coefficients=m['coefficients']))
        pins.update(m['input_sha256'])
    recs=[]
    for folder in ['cv_captures','heldout_captures']:
        for path in sorted((out/folder).glob('*.json')):
            rec=S.js(path);pins.update(rec['input_sha256']);recs.append((folder,rec))
    S.PINS.update(pins)
    # Conventional loader-compatible deployment directory, with the same coefficient bytes.
    deploy=out/'refit_head';deploy.mkdir(exist_ok=True)
    (deploy/'selector_head.safetensors').write_bytes(S.read(out/'selector_head_refit.safetensors'))
    deploy_meta=dict(meta,weights_file='selector_head.safetensors')
    S.write(deploy/'selector_head.json',deploy_meta)
    assert hashlib.sha256((deploy/'selector_head.safetensors').read_bytes()).hexdigest()==meta['weights_sha256']
    slot_counts={}
    for split in ['cv_captures','heldout_captures']:
        slot_counts[split]={}
        for arm in ['old','refit']:
            rr=[r for folder,rec in recs if folder==split for a in rec['arms'] if a['arm']==arm for r in a['items']]
            cc=[r for folder,rec in recs if folder==split for a in rec['arms'] if a['arm']==arm for r in a['choices']]
            slot_counts[split][arm]=dict(distance_rows=len(rr),gap_mra=float(S.np.mean([r['mra'] for r in rr])),objects=len(cc),choice_accuracy=float(S.np.mean([r['correct'] for r in cc])))
    metrics_spread={}
    for arm in ['old','refit']:
        metrics_spread[arm]={metric:dict(mean=float(S.np.mean([f[arm][metric] for f in cv['folds']])),sd=float(S.np.std([f[arm][metric] for f in cv['folds']],ddof=1))) for metric in ['gap_mra','choice_accuracy']}
    same_members_flips=sum(c.get('same_member_annotations',False) for c in train['label_change_list'] if c.get('kind')=='label_flip_at_common_id')
    checks=dict(physical_room_folds=5,all_datasets_every_fold=all(len(f['datasets'])==3 for f in cv['folds']),
        exact_serving_feature_checks=sum(len(a['checks']) for _,rec in recs for a in rec['arms'])//2,
        same_member_annotation_label_flips=same_members_flips,
        recorded_recipe_hashes_match={n:S.META['code_sha256'][n]==hashlib.sha256(S.read(S.SEL/n)).hexdigest() for n in S.META['code_sha256']},
        final_weights_match_frozen=meta['weights_sha256']==cv['final_weights_sha256'])
    assert all(checks['recorded_recipe_hashes_match'].values()) and checks['final_weights_match_frozen']
    S.pin_code()
    report=dict(status='COMPLETE',decision=cv['rule'],fold_table=cv['folds'],mean_paired_gain=cv['mean_paired_gain'],paired_gain_sd=cv['paired_gain_sd'],spread_2sd=cv['spread_2sd'],
        refit_wins=cv['refit_wins'],cv_frozen_at_utc=cv['frozen_at_utc'],seed=S.SEED,fold_assignment=train['folds'],
        label_change_counts=train['label_change_counts'],label_change_list=train['label_change_list'],label_comparison=train['label_comparison'],
        old_model_choice_changes=train['choice_changes'],coverage=train['coverage'],missing_registered_gt=train['missing_registered_gt'],
        config=S.CFG,coefficients=dict(old=cv['coefficients_old'],refit=cv['coefficients_refit'],folds=fold_models),
        weights_sha256=dict(old=S.META['weights_sha256'],refit=meta['weights_sha256']),heldout=held,pooled=slot_counts,fold_metric_spread=metrics_spread,checks=checks,
        metric_definition='MRA = mean of strict |printed_distance-target|/|target| < 1-t for t=np.arange(.5,.96,.05); printed distance has two decimals; refusals score zero.',
        choice_definition='Serving argmax over candidates plus null; a chosen candidate is correct when y=1; null is correct when no candidate is positive. Evaluated on annotated object groups with candidates, as in the recorded recipe.',
        limitations=['Fixed old coefficients were trained on K1 training captures; only refit validation predictions are out of fold.',
            'Serving rebuild adds 24 captures absent from caps_iso; the refit includes the complete registered 239-capture training set.',
            'Candidate IDs can change membership with geometry. Common-ID label flips compare table cells, not physical candidate identity.',
            'Cached tower, SAM and own-depth/gravity outputs replay the serving socket; this is not a new routed language-model read.'],
        commands=['bash run.sh selrefit.py prepare','bash run.sh selrefit.py train','bash run.sh selrefit.py score','bash run.sh heldout.py','bash run.sh finalize.py'])
    S.write(out/'SELREFIT.json',report)
    if cv['refit_wins']:
        text=(f'QUESTION for the coordinator to post: Run one paired routed read on the registered K1 held-out distance items in `{S.ROWSETS}/K1_HELDOUT_216.txt` '
              f'(SHA256 `{S.PINS[str(S.ROWSETS/"K1_HELDOUT_216.txt")]}`), with both arms on the identical rows and identical R1 checkpoint, prompt, frame, geometry, SAM, decoder and seed pins. '
              f'Keep serving null-argmax, own-depth median-ratio scale with float32 exp rounding, serving gravity, and the serving guard behavior. '
              f'Change only the selector coefficients: old `{S.SEL}/work/run_iso` (`{S.META["weights_sha256"]}`), '
              f'refit `{deploy}` (`{meta["weights_sha256"]}`). Report paired distance-item correctness/MRA and the paired difference for both arms. '
              'Use the coordinator’s existing routed-read pins; do not tune or change them from these report-only results.\n')
        (out/'READ_REQUEST.md').write_text(text)
    c=train['label_change_counts'];f=cv['folds'];h=held['metrics']
    lines=[
        'The selector refit '+('WINS' if cv['refit_wins'] else 'DOES NOT WIN')+' the frozen training decision.',
        cv['rule'],
        f'Mean paired gap-MRA gain: {cv["mean_paired_gain"]:.6f}; fold SD: {cv["paired_gain_sd"]:.6f}; 2 x SD: {cv["spread_2sd"]:.6f}.',
        '',
        f'Serving tables: 239 registered training captures, 219 physical rooms, {len(train["rows"])} candidates, 760 object groups; all three datasets.',
        f'Label cells changed: {c["label_flips_at_common_ids"]}/{c["common_id_rows"]} common IDs; {c["serving_added"]} added and {c["s4_removed"]} removed IDs across {c["compared_captures"]} comparable captures.',
        f'Among common IDs, {c["changed_member_annotations"]} have changed member annotations; {same_members_flips} label flips have identical annotations.',
        'These are table-cell differences: candidate IDs do not establish the same candidate across geometries. All serving labels were freshly computed from GT.',
        f'The S4/G1 table is MISSING for {c["old_tables_missing"]} captures; exact paths appear in SELREFIT.json. Three unregistered-GT captures remain excluded by the official rowsets.',
        f'Null targets change for {c["null_target_flips"]}/{c["common_objects"]} common objects. Fixed-old choice IDs change for {c["old_model_choice_id_changes"]}/{c["common_objects"]}; this differs from the 17/149 replay statistic.',
        'The serving rebuild replays 149/149 sampled choices and includes both convert-guard-refused captures.',
        '',
        'Recipe: unchanged 58-feature DeepSets, hidden=32, name_mode=none; candidate/null BCE; AdamW lr=.003, weight_decay=.001; 15 epochs; object batch size 16.',
        'Five physical-room folds use seed 20261116. Each refit uses the other four folds; final coefficients use all training captures. No hyperparameter search ran.',
        'The serving socket uses null-argmax, own-depth median-ratio scale with float32 exp rounding, and serving gravity.',
        'Gap MRA scores the actual two-decimal printed distance against corrected labels; strict relative-error thresholds .50 through .05; refusals score zero.',
        'Choice accuracy includes the null slot on annotated groups with candidates. Fold means weight folds equally; pooled results weight rows/objects equally.',
        '',
        '| Fold | Distance rows | Old choice | Refit choice | Old gap MRA | Refit gap MRA | Paired gain |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for r in f:lines.append(f'| {r["fold"]} | {r["old"]["distance_rows"]} | {r["old"]["choice_accuracy"]:.4f} | {r["refit"]["choice_accuracy"]:.4f} | {r["old"]["gap_mra"]:.4f} | {r["refit"]["gap_mra"]:.4f} | {r["paired_gain"]:+.4f} |')
    lines+=['',f'Fold SD, old/refit: gap MRA {metrics_spread["old"]["gap_mra"]["sd"]:.6f}/{metrics_spread["refit"]["gap_mra"]["sd"]:.6f}; choice accuracy {metrics_spread["old"]["choice_accuracy"]["sd"]:.6f}/{metrics_spread["refit"]["choice_accuracy"]["sd"]:.6f}.',
        f'Held-out, report-only after CV freeze: {held["captures"]} captures; {h["old"]["distance_rows"]} distance rows; {h["old"]["objects"]} object groups.',
        f'Held-out old/refit: gap MRA {h["old"]["gap_mra"]:.6f}/{h["refit"]["gap_mra"]:.6f}; choice accuracy {h["old"]["choice_accuracy"]:.6f}/{h["refit"]["choice_accuracy"]:.6f}; refusals {h["old"]["refused"]}/{h["refit"]["refused"]}.',
        'The fixed old model saw training captures; its fold scores are descriptive, not an out-of-fold estimate of its training procedure. The refit also uses 24 additional registered captures.',
        'Cached-output serving replay does not measure a new language-model routed read.',
        'The coordinator request is in READ_REQUEST.md.' if cv['refit_wins'] else 'No routed-read request is warranted by the frozen rule; READ_REQUEST.md was not created.',
        '',
        'Commands producing the numbers above:',
        '`bash run.sh serving_reference.py` in sb_kbox4: the supplied 149/149 reference replay and registered-table coverage.',
        '`bash run.sh selrefit.py prepare`: table coverage, label changes, feature and room counts.',
        '`bash run.sh selrefit.py train`: five fold fits and final coefficients using the recorded recipe.',
        '`bash run.sh selrefit.py score`: serving parity, fold choice accuracy, printed-distance MRA, spread and frozen decision.',
        '`bash run.sh heldout.py`: the single held-out report-only pass.',
        '`bash run.sh finalize.py`: pooled summaries, recipe hash checks, report, JSON and archive.',
        '`bash run.sh verify.py`: paired row coverage, physical-room isolation, frozen coefficients, input consistency and archive integrity.',
        f'Old weights SHA256: `{S.META["weights_sha256"]}`.',
        f'Refit weights SHA256: `{meta["weights_sha256"]}`.',
        'SELREFIT.json includes the complete fold table, label-change list, coefficients, limitations, and input SHA256 values.',
        'Archive: out/sb_selrefit.tar; checksum: out/sb_selrefit.tar.sha256.',
        'The S4/G1 and serving comparison is retained as a requested experiment, not revision history.']
    assert len(lines)<=60
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    S.status('Complete: the report, label audit, frozen CV, one held-out pass, refit coefficients and loader-compatible head are validated. The archive and its SHA256 are in out/.')
    paths=[root/'run.sh',root/'selrefit.py',root/'heldout.py',root/'finalize.py',root/'verify.py',root/'STATUS.md']
    paths+=sorted(p for p in out.rglob('*') if p.is_file() and p.name not in ['sb_selrefit.tar','sb_selrefit.tar.sha256','finalize.log'])
    with tarfile.open(out/'sb_selrefit.tar','w') as tar:
        for p in paths:tar.add(p,arcname=str(p.relative_to(root)),recursive=False)
    sha=hashlib.file_digest((out/'sb_selrefit.tar').open('rb'),'sha256').hexdigest()
    (out/'sb_selrefit.tar.sha256').write_text(sha+'  sb_selrefit.tar\n')
    print(json.dumps(dict(decision=cv['refit_wins'],gain=cv['mean_paired_gain'],spread=cv['spread_2sd'],heldout=held['metrics'],archive_sha256=sha,report_lines=len(lines))))


if __name__=='__main__':main()
