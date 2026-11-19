"""Validate train-only outputs and package a bounded report with provenance."""
import gzip,hashlib,json,resource,tarfile,time
from pathlib import Path
from collections import Counter,defaultdict
import serving_reference as R
import math_v2 as M

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()

def main():
    start=time.monotonic();out=R.OUT;root=R.ROOT
    reference=json.loads(R.read(out/'REFERENCE_REBUILD.json'))
    dry=json.loads(R.read(root/'out/DRYRUN.json'))
    decision=json.loads(R.read(out/'DECISION.json'));summary=json.loads(R.read(out/'SUMMARY_TRAIN.json'))
    frozen=decision['freeze'];assert reference['status']=='PASS' and dry['passed']
    train=set(R.read(R.ROWSETS/'K1_TRAIN_1037.txt').decode().splitlines());tables=set(R.read(R.ROWSETS/'K1_TRAIN_TABLES_883.txt').decode().splitlines())
    by=defaultdict(dict);marked=set();sources=set()
    with (out/'PER_ITEM.jsonl').open() as f:
        for line in f:
            r=json.loads(line);assert r['split']=='train' and r['row_id'] in train and not r['arm'].startswith('A6')
            assert r['row_id'] not in by[r['arm']];by[r['arm']][r['row_id']]=r
            sources.update(r['input_sha256'])
            if r['reviewed_guard_refused']:marked.add((r['capture'],r['row_id']))
    for arm,rows in by.items():
        expected=tables if arm.startswith(('A1_','A5_','A8_')) else train
        assert set(rows)==expected,(arm,len(rows))
        got=sum(M.mra(r['prediction'],r['label']) for r in rows.values())/len(rows)*100
        assert abs(got-summary['arms'][arm]['mra'])<1e-9
    assert len(marked)==12 and {c for c,_ in marked}=={'scannetpp/0f69aefe3d','scannetpp/2c7c10379b'}
    restored=json.loads(R.read(out/'RESTORED_CAPTURE_PARITY.json'));assert restored['status']=='PASS' and restored['matched']==12
    ref_sources={str(root/'serving_reference.py'),str(root/'dryrun.py'),str(root/'predicted.py'),str(root/'adapters.py')}
    for rec in reference['captures']:
        assert sha(rec['path'])==rec['sha256']
        table=json.loads(gzip.decompress(Path(rec['path']).read_bytes()))
        assert table['split']=='train'
        for p in ref_sources:assert table['input_sha256'][p]==sha(p),p
    for phase in ['base','extras']:
        for p in (out/phase).glob('*.json'):
            rec=json.loads(p.read_text())
            for dep in ['train_pricing.py','pricing.py','math_v2.py']:
                expected=rec['input_sha256'][str(root/dep)]
                snapshot=root/'out/executed_sources'/(Path(dep).stem+'_'+expected+'.py')
                assert expected==sha(root/dep) or (snapshot.exists() and sha(snapshot)==expected),(p,dep)
    nonull=json.loads(R.read(out/'nonull/TRAIN_OOF.json'))
    assert nonull['seed']==20261116 and len(nonull['records'])==5 and not nonull['deployed_export_created']
    fold_manifest=json.loads(R.read(root/'train_manifest.json'))
    expected_folds=M.folds(c['room'] for c in fold_manifest['captures'] if any(r['id'] in train for r in c['rows']))
    assert nonull['folds']==expected_folds
    assert all(r['fold']==expected_folds[r['room']] for rows in by.values() for r in rows.values())
    srcaudit=json.loads(R.read(out/'SOURCE_AUDIT.json'))
    assert all(r['status']=='MATCH' for r in srcaudit['rows'] if r['role']!='inherited_vendor')
    provenance=json.loads(R.read(out/'SOURCE_PROVENANCE.json'));assert all(r['equal'] for r in provenance['reader_comparisons'])
    manifest=json.loads(R.read(root/'train_manifest.json'))
    excluded={m['capture'] for m in reference['missing']}
    missing=[]
    for c in manifest['captures']:
        if c['canonical'] in excluded:
            p=Path(c['gt']['path']);assert not p.exists()
            missing.append(dict(capture=c['canonical'],status='MISSING',expected_path=str(p),manifest_expected_sha256=c['gt']['sha256'],scope='Reference labels only; excluded by the registered primary rowset'))
    missing_arms=[]
    for arm,rows in by.items():
        codes=Counter(r['refusal_code'] for r in rows.values() if str(r['refusal_code']).startswith('MISSING'))
        if codes:missing_arms.append(dict(arm=arm,missing=dict(codes)))
    R.code_pins()
    R.write(out/'OUTPUT_STATUS.json',dict(status='COMPLETE_TRAIN_ONLY',missing_inputs=missing,missing_arm_inputs=missing_arms,
        heldout=dict(status='DEFERRED',expected_path=str(out/'LADDER_HELDOUT_once.txt'),reason='Orchestrator order 0654Z; no held-out evaluation'),
        A6=dict(status='DEFERRED',reason='Orchestrator order 0654Z; no GT geometry arms executed'),
        deferred_if_no_variant=[] if frozen['frozen_variant'] else ['A5_obj_oracle_seed','A8_nonull_obj','A7_*_frozen','A9_s4_obj']))
    verification=dict(status='PASS',per_item_records=sum(len(v) for v in by.values()),arms=len(by),primary_train_rows=len(train),table_train_rows=len(tables),
        rebuilt_captures=len(reference['captures']),registered_refused_capture_rows=len(marked),nonull_folds=5,
        all_primary_rows_present=True,all_mra_means_recomputed=True,no_heldout=True,no_A6=True,
        commands=['bash run.sh -m unittest -v test_v2','bash run.sh finalize_v2.py'])
    R.write(out/'FINAL_VERIFICATION.json',verification)
    # DRYRUN.json is the immutable pre-pricing gate consumed by the training jobs.
    a=reference['summary']['all'];contrasts=summary['contrasts'];variant=frozen['frozen_variant']
    def delta(key):
        s=contrasts[key];return f'{s["estimate"]:+.2f} [{s["ci95"][0]:+.2f}, {s["ci95"][1]:+.2f}]'
    lines=[
        f'K1 training pricing is complete. Serving-reference replay passes {a["matched"]}/{a["total"]} choices across {a["captures"]} captures ({a["rate"]*100:.2f}%; bar 95%).',
        f'The reference rebuild covers {len(reference["captures"])} training captures; three manifest GT rasters are MISSING and already excluded from the registered pricing set.',
        'A0 uses R1 own-depth median_ratio scale, float32 exp(log(scale)), and checkpoint gravity under the serving guard.',
        f'Both convert-refused captures are accepted and marked: scannetpp/0f69aefe3d and scannetpp/2c7c10379b; direct R1 socket parity is 12/12, with {restored["answered"]} answers.',
        'The replay uses stored step-544 own tensors; it does not rerun a model prefill or claim step-200 numeric equivalence.',
        'All labels were rebuilt from GT rasters with the table producer; isolated features use its unchanged runtime producers. No S4/G1 candidate label was transferred.',
        '',
        '| Dataset | Replay choices | Matched | Exact features |',
        '|---|---:|---:|---:|',
    ]
    for ds in ['arkitscenes','scannet','scannetpp']:
        s=reference['summary'][ds];lines.append(f'| {ds} | {s["total"]} | {s["matched"]} | {s["exact_features"]} |')
    lines+=['','Every primary comparison contains 1,037 train rows / 192 physical rooms; oracle and selector comparisons use the pinned 883 table rows.',
        'Every refusal scores zero. Paired intervals use 10,000 room-bootstrap draws, seed 20261119.', '',
        '| Arm | Train MRA | Rows | Refusals |','|---|---:|---:|---:|']
    for arm in ['A0_deployed','A1_oracle_select','A2_gt_masks','obj_cf','fused_cf','A5_obj_oracle_seed','A8_nonull_best1','A8_nonull_obj','A7_da3_best1','A7_pi3x_best1','A9_s4_today','A9_s4_obj']:
        if arm in summary['arms']:
            s=summary['arms'][arm];lines.append(f'| {arm} | {s["mra"]:.2f} | {s["rows"]} | {s["refusals"]} |')
    lines+=['','| Paired contrast | Gain [95% CI] |','|---|---:|']
    for key in ['object_cf_minus_A0','fused_cf_minus_A2','A1_minus_A0_tables','A2_minus_A0','A8_nonull_minus_A0_tables','size_obj_cf_minus_A0','A9_today_minus_A0','A9_obj_minus_frozen_A4']:
        if key in contrasts:lines.append(f'| {key} | {delta(key)} |')
    lines+=['','| Bar | Verdict |','|---|---|']+[f'| {k} | {v["verdict"]} |' for k,v in decision['bars'].items()]
    lines+=['','| All-train merge eligibility | Precision | Added members |','|---|---:|---:|']
    for tau in M.TAUS:
        p=summary['arms'][f'A4_obj_{tau:.2f}_best1']['precision']
        value='NA' if p['precision'] is None else f'{100*p["precision"]:.2f}%'
        lines.append(f'| tau={tau:.2f} (requires 90%) | {value} | {p["added"]} |')
    lines += [
        '',f'Frozen object variant: {variant["arm"] if variant else "NONE; dependent object arms skipped"}. The replace_box verdict covers part 1 only; tower_frames part 2 remains required.',
        'Object/fusion gains and merge precision use room-cross-fitted predictions. Non-null selection uses five room-held-out fits with the fixed run_iso config and seed 20261116.',
        'The appearance bar uses OOF threshold choices to satisfy the task’s cross-fit requirement; the spec’s all-train frozen-threshold rate remains diagnostic. No source is deployed here.',
        'Dry checks reproduce the copied-reader A0 socket, stored-label S4 predictions, corrected-label scorer targets, one-frame fusion, and tau=1.01 identity. Six math tests pass.',
        'Dry pricing covers A0–A4 and A9; the train pass adds A7 best1 and A8 best1. A5 and frozen-object-dependent arms are skipped because no variant qualifies.',
        f'First-seen ordering is correct for {frozen["first_linker"]["correct"]}/{frozen["first_linker"]["pairs"]} linker pairs ({100*frozen["first_linker"]["rate"]:.2f}%; requires 90%); no object threshold qualifies.',
        'A6 and held-out remain deferred by order 0654Z. The archive remains local under the task’s no-network rule.',
        'LADDER_TRAIN.txt prints all 33 object variants, ten GT fusion variants, paired contrasts, and both-answered diagnostics. SUMMARY_TRAIN.json includes truth/dataset/frame bands.',
        'OBJECT_DIAGNOSTICS.json gives fixed GT full extents, size ratios/MRA, first-seen diagnostics, counts, and added-member precision (GT pixel plurality).',
        'SOURCE_AUDIT.json confirms the active reader/dependencies match the R1 manifest. Unused inherited vendor/stage1.py and grounding.py differ; auxiliary vendor files lack R1 entries.',
        'SCALE_PROVENANCE.md identifies served versus S4/G1 prices; source attribution for the design’s record-only pipeline/selector quotations remains explicitly unverified.',
        '',
        'Commands producing the numbers (logs are in out/):',
        '`bash run.sh prepare.py`; `bash run.sh prepare_pinned.py` — pinned train labels and rowsets.',
        '`bash run.sh serving_reference.py` — rebuilt labels, geometry receipts, and replay.',
        '`bash run.sh run_training_stages.py dry`; `bash run.sh confirm_dry.py` — dry pricing, parity checks and saved-gate verification.',
        '`bash run.sh run_training_stages.py base` — four train shards and cross-fitted FREEZE.json.',
        '`bash run.sh verify_restored.py` — direct R1 socket parity on both convert-refused captures.',
        '`bash run.sh run_training_stages.py extras` — five selector fits, dependent arms, tables and DECISION.json.',
        '`bash run.sh audit_sources.py`; `bash run.sh provenance_v2.py`; `bash run.sh finalize_v2.py` — source audit, provenance, verification and archive.',
        'All Python jobs use p1cpu, nice priority, at most eight cores per job, and a virtual-memory limit below 40 GB; the four pricing shards share eight CPU cores.',
        'No GPU, network, SSH, Git, process termination, tmux change, external write, or deletion ran. No K1 held-out or GT-geometry arm was evaluated.',
        'Every JSON carries input SHA256 values; per-item hashes link to per-capture receipts containing the complete input chain.',
        'Archive: out/sb_kbox4.tar; checksum: out/sb_kbox4.tar.sha256. OUTPUT_STATUS.json records the exact missing input paths and deferred outputs.',
    ]
    assert len(lines)<=80,len(lines)
    (root/'out/REPORT.md').write_text('\n'.join(lines)+'\n')
    (root/'STATUS.md').write_text(f'COMPLETE: serving-reference replay {a["matched"]}/{a["total"]} across {a["captures"]} training captures; CPU pricing covers the pinned 1037/883 train rowsets. Decisions and paired intervals are frozen in out/box_ladder/DECISION.json. Held-out and A6 remain deferred. out/REPORT.md, out/SCALE_PROVENANCE.md, out/DRYRUN.json and out/sb_kbox4.tar with SHA256 contain the deliverables.\n')
    code=sorted(root.glob('*.py'))+[root/'run.sh']+sorted((root/'reader_src/e2e_reader').glob('*.py'))+sorted((root/'vendor').glob('*.py'))
    (out/'CODE_SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(root)}\n' for p in code))
    files=code+[root/'STATUS.md']+sorted((root/'inputs').glob('*'))+sorted((root/'inherited').glob('*.md'))
    files += [root/n for n in ['train_manifest.json','train_labels.json','pinned_train.json','train_boxes.json']]
    files += [p for p in (root/'out').rglob('*') if p.is_file() and p.name not in ['sb_kbox4.tar','sb_kbox4.tar.sha256','SHA256SUMS']]
    files=sorted(set(files))
    (root/'out/SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(root)}\n' for p in files))
    files.append(root/'out/SHA256SUMS')
    archive=root/'out/sb_kbox4.tar'
    with tarfile.open(archive,'w') as tar:
        for p in files:tar.add(p,arcname=str(p.relative_to(root)),recursive=False)
    checksum=sha(archive);(root/'out/sb_kbox4.tar.sha256').write_text(f'{checksum}  sb_kbox4.tar\n')
    print(json.dumps(dict(verification,archive=str(archive),sha256=checksum,bytes=archive.stat().st_size,seconds=time.monotonic()-start),indent=2))

if __name__=='__main__':main()
