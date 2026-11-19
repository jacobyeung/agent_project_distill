"""Publish the geometry blocker and the completed training-only evidence."""
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
from adapters import ROOT, READER, TREE
from dryrun import PINS, read, write, OUT

PACK=Path('/scratch/jjyeung/n30_mirror/sb_headacc2/pack')
BARS=['replace_box','fused_path','merge_safe','selector_worth','selector_adopt','size_screen','first_seen_screen','tower_challenger']


def main():
    results={}
    for name in ['REPLAY_EXPANDED','GEOMETRY_PROVENANCE','SERVING_SCALE_AUDIT','SERVING_GUARD_AUDIT','SOURCE_AUDIT','REPLAY_SAMPLE']:
        d=json.loads(read(OUT/(name+'.json')))
        PINS.update(d['input_sha256']);results[name]=d
    for p in sorted(ROOT.glob('*.py'))+[ROOT/'run.sh',ROOT/'KIT_SPEC_box_ladder_k1_v2.md']:
        read(p)
    for p in sorted((ROOT/'reader_src/e2e_reader').glob('*.py'))+sorted((ROOT/'vendor').glob('*.py')):
        read(p)
    for rel in ['K1_TRAIN_1037.txt','K1_HELDOUT_216.txt','K1_TRAIN_TABLES_883.txt','K1_HELDOUT_TABLES_194.txt']:
        read(PACK.parent/'K1_ROWSETS'/rel)
    convert_source=Path('/scratch/jjyeung/orch_cd/evalx/work/milestone/native_package_s24_05/sources/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py')
    read(convert_source)
    replay=results['REPLAY_EXPANDED']; provenance=results['GEOMETRY_PROVENANCE']['captures']
    guard=results['SERVING_GUARD_AUDIT']['captures'];scale=results['SERVING_SCALE_AUDIT']['summary']
    assert len(guard)==2 and all(c['reader_from_tower']=='ACCEPTED' and c['reviewed_loader'].startswith('GeometryError:') for c in guard)
    total_rows=sum(c['primary_train_rows'] for c in guard);answered=sum(c['reader_answered'] for c in guard)
    sample=replay['summary']['table_S4_G1']['all']
    assert sample['total']>=100 and sample['captures']>=20
    checks=results['SOURCE_AUDIT']['rows']
    assert all(c['status']=='MATCH' for c in checks if c['role']!='inherited_vendor')
    # Verify the raw and isolated table metadata describe the same original geometry.
    rawpath=READER/'heads/selector/data/caps_raw/arkitscenes__41048124.json.gz'
    raw=json.loads(gzip.decompress(read(rawpath)))
    first=next(c for c in provenance if c['capture']=='arkitscenes/41048124')
    assert raw['scale']==first['table_scale'] and raw['geometry_sha256']==first['table_geometry_sha256']
    meta=json.loads(read(READER/'heads/selector/work/run_iso/selector_head.json'))
    blocker='A0 serving mismatch: GD_reviewed rejects two registered train captures accepted by the R1 reader; reconcile the gravity contract before rebuilding references or pricing.'
    write(ROOT/'out/DRYRUN.json',dict(status='BLOCKED',reason=blocker,minimum_replay_agreement=.95,
        replay=replay['summary'],serving_scale_audit=scale,serving_guard_audit=guard,
        train_pricing='MISSING',heldout_evaluation='MISSING: not run',heldout_reads=0,
        table_reference_rebuilt=False,reference_rebuild_reason='Deferred because GD is not serving-equivalent',
        seconds=replay['seconds'],peak_rss_mib=replay['peak_rss_mib']))
    write(OUT/'DECISION.json',dict(status='BLOCKED',reason=blocker,split='train',frozen_variant='MISSING',
        bars={bar:dict(verdict='MISSING',reason=blocker) for bar in BARS},
        heldout_read_permitted=False))
    missing=['PER_ITEM.jsonl','LADDER_TRAIN.txt','LADDER_HELDOUT_once.txt']
    write(OUT/'OUTPUT_STATUS.json',dict(status='BLOCKED',missing={name:dict(status='MISSING',expected_location=str(OUT/name),reason=blocker) for name in missing},
        missing_inputs=[c['missing_geometry'] for c in guard],
        no_archive_transfer='User prohibits SSH and network; local archive only'))
    write(OUT/'TABLE_ORIGIN.json',dict(capture=first['capture'],raw_table=str(rawpath),
        raw_table_geometry_sha256=raw['geometry_sha256'],table_scale=raw['scale'],
        exact_table_producer=str(PACK/'r1_src/b/heads/selector/sl118/sl_tables.py'),
        table_export_origin='sl_tables.geometry_npz, exported per-capture under out/geo; not run_convert_1 or run_convert_2',
        isolated_table_producer=str(PACK/'r1_src/b/heads/selector/isolate_tables.py'),
        selector_training=meta['train'],selector_weights_sha256=meta['weights_sha256']))
    # Include the source of the sample policy in its provenance without changing membership.
    sample_doc=results['REPLAY_SAMPLE'];sample_doc.pop('input_sha256',None)
    write(OUT/'REPLAY_SAMPLE.json',sample_doc)
    gd=replay['summary']['GD_convert2']['all'];tab=replay['summary']['table_S4_G1']['all'];live=replay['summary']['reader_own_ungated']['all']
    bytes_match=sum(p['table_export_bytes_match'] for p in provenance)
    tv=[r for r in replay['rows'] if r['capture']=='arkitscenes/41048124' and r['name']=='tv']
    tvgd=next(r for r in tv if r['geometry']=='GD_convert2');tvt=next(r for r in tv if r['geometry']=='table_S4_G1')
    validgd=[r for r in replay['rows'] if r['geometry']=='GD_convert2' and not r['refusal_code']]
    strict={}
    for geometry in ['GD_convert2','table_S4_G1','reader_own_ungated']:
        subset=[r for r in replay['rows'] if r['geometry']==geometry]
        hits=sum(r['passed'] and r['selected_frames']==sorted(m['slot']+1 for m in r['table_selected_members']) for r in subset)
        strict[geometry]=dict(matched=hits,total=len(subset),rate=hits/len(subset),passed=hits/len(subset)>=.95)
    live_by={(r['capture'],r['name']):r for r in replay['rows'] if r['geometry']=='reader_own_ungated'}
    live_equal=sum(r['got']==live_by[(r['capture'],r['name'])]['got'] and r['selected_frames']==live_by[(r['capture'],r['name'])]['selected_frames'] for r in validgd)
    write(OUT/'REPLAY_COMPARISONS.json',dict(candidate_and_frame_agreement=strict,
        reader_vs_GD_available=dict(matched=live_equal,total=len(validgd)),
        max_camera_array_difference=max(p['gd_reader_camera_max_error'] or 0 for p in provenance)))
    debug=[
        'BLOCKER: the spec’s A0 is not the R1 serving reader.',
        f'The reviewed convert guard rejects two captures covering {total_rows} registered training rows; R1 accepts both and answers {answered} rows.',
        'The labelled table is also the wrong reference for GD: it uses S4 scale and G1 tower-pose gravity.',
        '',
        f'Expanded replay: {tab["total"]} operand choices in {tab["captures"]} training captures, with 15 captures per dataset.',
        f'Against the original isolated table: GD {gd["matched"]}/{gd["total"]} ({100*gd["rate"]:.2f}%); table geometry {tab["matched"]}/{tab["total"]} ({100*tab["rate"]:.2f}%).',
        f'GD on available exports only: {sum(r["passed"] for r in validgd)}/{len(validgd)}. Missing exports count as failed replays.',
        f'Requiring the same ID and member frames: GD {strict["GD_convert2"]["matched"]}/{gd["total"]}; table {strict["table_S4_G1"]["matched"]}/{tab["total"]}.',
        f'Table geometry gives exact candidate sets and feature vectors for {tab["exact_feature_objects"]}/{tab["total"]} objects.',
        f'The unmodified table geometry producer reproduces {bytes_match}/{len(provenance)} recorded geometry SHA256 values byte for byte.',
        'Command: bash run.sh debug_geometry.py > out/box_ladder/replay_expanded.log 2>&1',
        '',
        f'ARKitScenes 41048124: table scale {first["table_scale"]:.10f}; convert scale {first["gd_scale"]:.10f}.',
        f'Table choice {tvt["got"]} has {len(tvt["selected_frames"])} frames; GD choice {tvgd["got"]} has {len(tvgd["selected_frames"])} frames.',
        f'Table geometry SHA256: {first["table_geometry_sha256"]}.',
        f'The failing capture’s run_convert_1 and run_convert_2 exports are byte-identical: {first.get("convert1_equals_convert2")}.',
        'Table origin: PACK/r1_src/b/heads/selector/sl118/sl_tables.py:71–87,129–166; isolation: isolate_tables.py:25–35.',
        'The table uses no own-depth scale: SCALES_S4.json supplies exp(b0 + b1 log(h_raw) + b2 log(span)).',
        'Coefficients: '+json.dumps(results['GEOMETRY_PROVENANCE']['coefficients'])+'.',
        'run_iso/selector_head.json records caps_iso as the training input and weights 6d97c52407b7e106a7b475040558ba313589514c23c33b6994f4e7a0bb1df6c1.',
        '',
        f'Convert and serving median scales agree on {scale["available"]}/{scale["available"]} available training exports; the range-gate difference has no effect here.',
        'Command: bash run.sh audit_serving_scale.py > out/box_ladder/serving_scale_audit.log 2>&1',
        'Convert uses own_170235/native/probe/<digest>/own.npz and tower_scale_rule.estimate; OwnDepthScale uses stage1.median_ratio.',
        'Serving also rounds exp(log(scale)) through float32; replay records this separately.',
        '',
        'Missing exports: /scratch/jjyeung/k1/run_convert_2/{45511ef70c22b11e,9baa923934276385}/geometry.npz.',
        'Their CACHE_COMPLETE.json files record reference_camera_up_opposes_gravity and retain REFUSED_GEOMETRY.npz.',
        'Captures: scannetpp/0f69aefe3d and scannetpp/2c7c10379b.',
        'R1 geometry.py:22–39 removes the terminal up-axis check; both from_npz and from_tower accept these arrays.',
        'Command: bash run.sh audit_guard.py > out/box_ladder/serving_guard_audit.log 2>&1',
        'The serving replay uses stored checkpoint own outputs; it does not claim to rerun the current language-model prefill.',
        '',
        'Required orchestrator action: reconcile the registered A0 gravity contract with R1 serving; the reference rebuild must use the same contract.',
        'Rebuild candidate labels and isolated features through the table producer on that geometry; candidate IDs cannot carry labels across geometries.',
        'The 95% replay bar is unchanged. No training pricing, rule fitting, or held-out evaluation ran.',
        'All evidence JSON files record input SHA256 values; commands above produced every numerical comparison.',
    ]
    assert len(debug)<=40
    (ROOT/'out/DEBUG.md').write_text('\n'.join(debug)+'\n')
    report=[
        'K1 box-ladder pricing is BLOCKED because the registered A0 geometry differs from R1 serving.',
        f'The convert guard refuses {total_rows} registered training rows in two captures; the serving reader answers {answered} of those rows.',
        'The table-reference mismatch is independently explained by S4 scale plus G1 gravity. It is not an adapter feature bug.',
        '',
        '| Geometry replay against original table | Matched / choices | Agreement | >=95% |',
        '|---|---:|---:|---|',
    ]
    for title,r in [('GD reviewed convert',gd),('Original table S4/G1',tab),('R1 serving rule on cached own outputs',live)]:
        report.append(f'| {title} | {r["matched"]}/{r["total"]} | {100*r["rate"]:.2f}% | {"PASS" if r["passed"] else "FAIL"} |')
    report+=['', '| Dataset | Captures | Choices | GD matches | Table matches |', '|---|---:|---:|---:|---:|']
    for ds in ['arkitscenes','scannet','scannetpp']:
        t=replay['summary']['table_S4_G1'][ds];g=replay['summary']['GD_convert2'][ds]
        report.append(f'| {ds} | {t["captures"]} | {t["total"]} | {g["matched"]} | {t["matched"]} |')
    report += [
        '',
        f'The sample was fixed before replay: the first 15 canonical-sorted eligible train captures per dataset, all registered operand names with table inputs.',
        f'Table exports match their recorded hashes for {bytes_match}/{len(provenance)} captures; exact features and candidate sets match for {tab["exact_feature_objects"]}/{tab["total"]} objects.',
        f'The convert and serving median scales match on all {scale["available"]} available training exports. The two missing exports are explicit gravity refusals.',
        f'Requiring matching IDs and member frames gives GD {strict["GD_convert2"]["matched"]}/{gd["total"]} and table geometry {strict["table_S4_G1"]["matched"]}/{tab["total"]}.',
        f'On available sample exports, R1 and GD choose the same IDs and member frames on {live_equal}/{len(validgd)} operands.',
        'The table producer uses S4 from SCALES_S4.json, not an own-depth scale or another convert run.',
        'The serving reader removes an up-axis rejection that the spec’s reviewed loader retains. This changes accepted inputs and answers.',
        'Serving-rule replay uses stored cp2 checkpoint own tensors; a fresh serving prefill was not run.',
        '',
        '| Decision bar | Verdict |', '|---|---|',
    ]
    report += [f'| {bar} | MISSING |' for bar in BARS]
    report += [
        '',
        'No variant is frozen. Full train pricing, selector retraining, cross-fitting, bootstrap contrasts, and held-out evaluation are MISSING.',
        'PER_ITEM.jsonl, LADDER_TRAIN.txt, and LADDER_HELDOUT_once.txt were not produced; OUTPUT_STATUS.json records their expected paths.',
        'DECISION.json records the blocker and every missing bar. DRYRUN.json records the expanded replay and serving checks.',
        'No reference rebuild ran: the task requires a BLOCKER when GD differs from serving. Relabelling under GD would preserve the wrong A0 contract.',
        '',
        'Commands and evidence:',
        '',
        '- bash run.sh debug_geometry.py > out/box_ladder/replay_expanded.log 2>&1 — replay counts, features, geometry hashes, scales, TV membership.',
        '- bash run.sh audit_serving_scale.py > out/box_ladder/serving_scale_audit.log 2>&1 — full training scale audit.',
        '- bash run.sh audit_guard.py > out/box_ladder/serving_guard_audit.log 2>&1 — acceptance and answers on both refused captures.',
        '- bash run.sh audit_sources.py > out/box_ladder/source_audit.log 2>&1 — source identity.',
        '- bash run.sh finalize_debug.py — report, decisions, provenance, local archive, and SHA256.',
        '',
        'The replay’s R1 reader copies and checked dependencies match R1_A4_SRC_SHA256.txt. SOURCE_AUDIT.json lists every check.',
        'Inherited vendor/stage1.py and vendor/grounding.py differ from R1 and were not used as the replay reader; auxiliary harness files lack R1 manifest entries.',
        'The table geometry function is AST-loaded unchanged with a capture-scoped loader binding. Refused GD exports remain refusals.',
        'The dry run did not execute the full v2 all-arm parity suite because A0 serving equivalence failed.',
        f'Replay elapsed {replay["seconds"]:.3f} seconds; peak RSS {replay["peak_rss_mib"]:.3f} MiB (reported by debug_geometry.py).',
        'All executed Python jobs used p1cpu, nice 10, at most eight numerical threads, and a virtual-memory limit below 40 GB.',
        'No GPU, network, SSH, Git, tmux, process termination, deletion, or external write ran. No held-out capture was evaluated.',
        'The spec was copied once from its named NFS path; remaining task inputs were read from local scratch.',
        'The requested local archive is out/sb_kbox3.tar; its checksum is out/sb_kbox3.tar.sha256. Network transfer is prohibited by the task.',
        'No borderline revision-history prose was kept. Internal diagnostic identifiers are retained because the user explicitly requested a root-cause report.',
    ]
    assert len(report)<=80
    (ROOT/'out/REPORT.md').write_text('\n'.join(report)+'\n')
    (OUT/'dryrun.log').write_text('BLOCKED before the all-arm v2 dry run: '+blocker+'\n'
        +'Expanded replay command: bash run.sh debug_geometry.py\n'
        +'Expanded replay log: replay_expanded.log\n'
        +'Scale check: serving_scale_audit.log\n'
        +'Serving acceptance check: serving_guard_audit.log\n'
        +'Source identity check: source_audit.log\n'
        +f'Choices per geometry: {tab["total"]}; train captures: {tab["captures"]}; held-out evaluations: 0.\n')
    (ROOT/'STATUS.md').write_text(f'Geometry diagnosis is complete and K1 pricing remains BLOCKED: R1 serving accepts two captures that GD_reviewed refuses, affecting {total_rows} registered training rows. Expanded replay covers {tab["total"]} choices in {tab["captures"]} training captures across all three datasets. The table mismatch is traced to byte-reproduced S4/G1 exports. The deliverables contain hashed evidence and missing-output declarations; no rules were fitted and no held-out evaluation ran.\n')
    codefiles=sorted(ROOT.glob('*.py'))+[ROOT/'run.sh',ROOT/'KIT_SPEC_box_ladder_k1_v2.md']+sorted((ROOT/'vendor').glob('*.py'))+sorted((ROOT/'reader_src/e2e_reader').glob('*.py'))
    (OUT/'CODE_SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(ROOT))+'\n' for p in codefiles))
    files=codefiles+[ROOT/'STATUS.md',ROOT/'train_manifest.json',ROOT/'out/DEBUG.md',ROOT/'out/REPORT.md',ROOT/'out/DRYRUN.json']+sorted(OUT.glob('*'))
    archive=ROOT/'out/sb_kbox3.tar'
    with tarfile.open(archive,'w') as tar:
        for p in sorted(set(files)):
            if p.is_file():tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
    sha=hashlib.sha256(archive.read_bytes()).hexdigest()
    (ROOT/'out/sb_kbox3.tar.sha256').write_text(sha+'  sb_kbox3.tar\n')
    print(json.dumps(dict(status='BLOCKED',archive=str(archive),sha256=sha,debug_lines=len(debug),report_lines=len(report),replay=replay['summary'])))


if __name__=='__main__':main()
