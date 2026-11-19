"""Seal the fully checked sb_rowB4 kit and verify every archive member."""
import collections as C
import hashlib,json,tarfile
from pathlib import Path
from stage_inputs import sha
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'out'
def read(n):return json.loads((OUT/n).read_text())
def dump(n,x):(OUT/n).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def hs(d):return ', '.join(f'{k}:{v}' for k,v in sorted(d.items()))
def main():
    checks=read('CHECKS.json');ind=read('INDEPENDENT_CHECK.json');review=read('READ30_REVIEW.json');wf=read('WORDING_FILTER_CHECK.json');kit=read('KIT_CHECK.json');gate=read('SCENE_GATE_CHECK.json');retention=read('FAMILY_RETENTION.json');reuse=read('B3_INVARIANTS.json');hist=read('HISTOGRAMS.json');inputs=read('INPUTS.json')
    assert all(d['status']=='PASS' for d in [ind,review,wf,kit,gate,retention,reuse])
    assert ind['false_citations']==gate['refused']==0
    assert review['input_sha256'][str(OUT/'READ30.md')]==sha(OUT/'READ30.md') and len(set(review['reviewed_qids']))==30
    assert ind['input_sha256'][str(OUT/'rows.jsonl')]==sha(OUT/'rows.jsonl')
    assert ind['rows_independently_recomputed']==checks['replacement_native_pack_validate']==gate['native_gate']['admitted']
    for p,h in inputs['input_sha256'].items():
        if str(p).startswith(str(ROOT)):assert sha(p)==h,('input changed after build',p)
    checks.update(status='PASS',ground_truth_independently_recomputed=ind['rows_independently_recomputed'],field_diff_allowed=True,
      candidate_ids_independently_recomputed=True,visibility_independently_checked=True,sighting_references_independently_checked=True,false_citations=0,
      scene_division_gate=gate['native_gate'],scene_division_refused=0,removal_counts=gate['removal_counts'],
      read30='PASS: thirty new distinct source rows reviewed for question, options, trace, answer, and raster evidence',
      wording_distance_tests=wf['comparisons'],required_checks_passed=True,family_retention=retention['families'])
    checked=['INDEPENDENT_CHECK.json','READ30_REVIEW.json','WORDING_FILTER_CHECK.json','KIT_CHECK.json','SCENE_GATE_CHECK.json','FAMILY_RETENTION.json','REMOVE.provenance.json','SAMPLE_SELECTION.json','B3_INVARIANTS.json']
    checks['input_sha256'].update({str(OUT/n):sha(OUT/n) for n in checked})
    checks['input_sha256'][str(Path(__file__))]=sha(Path(__file__))
    checks['output_sha256'].update({n:sha(OUT/n) for n in ['REMOVE_WORDING.json','REMOVE_MISSING_GT.json','READ30.md']})
    dump('CHECKS.json',checks)
    plan=read('PLAN.json')['expected_joint_cells'];families=list(hist['after']);total=checks['replacement_native_pack_validate'];unique=checks['admitted_unique_sources']
    lines=[f'The kit delivers {total:,} frame-k rows from {unique:,} unique store-v7 sources. All required checks pass.',
      f'Independent raster checks find 0 false citations across {sum(ind["sighting_frames"].values()):,} out-of-view citations. N’s scene_division_gate admits all {total:,} rows with 0 refused, filtered, or removed.',
      'The CPU build uses the sealed W19 tree, '+kit['tree_sha256']+'. No training or network access ran.',
      '', '| Family | Census | Eligible sources | Delivered | All out of view | Rows per joint cell by stratum |','|---|---:|---:|---:|---:|---|']
    for f in families:
        a=hist['source_all_before'][f];b=hist['admitted_sources_before'][f];c=hist['after'][f]
        lines.append(f'| {f} | {a["rows"]} | {b["rows"]} | {c["rows"]} | {c["visibility"].get("all_out_of_view",0)} | {hs({k.split("|")[0]:v for k,v in plan[f].items()})} |')
    lines+=['Each cell is a first-seen stratum × rank/semantic answer × answer position. PLAN.json asserts every exact count.',
      'Camera ranks sort by (first_seen, numeric instance id); tied and untied strata stay separate. Pair strata are earlier/later/tied subject sightings.',
      f'Every eligible source is retained, including every eligible all-out-of-view source. Maximum source use: {checks["max_source_uses"]}; use histogram: {hs(checks["source_use_histogram"])}. Repeated sources have distinct answer positions.',
      '', '| Family | Delivered | Old kept if MISSING kept | Old left if MISSING dropped | Total if kept | Total if dropped | Unique sources if dropped | Under 1,000 |','|---|---:|---:|---:|---:|---:|---:|---|']
    for f in families:
        d=retention['families'][f];flag=[]
        if d['under_1000_delivered']:flag.append('DELIVERED')
        if d['under_1000_unique_sources_if_missing_dropped']:flag.append('SOURCES')
        lines.append(f'| {f} | {d["rows_delivered"]} | {d["old_rows_kept_if_missing_kept"]} | {d["old_rows_left_if_missing_dropped"]} | {d["total_rows_if_missing_kept"]} | {d["total_rows_if_missing_dropped"]} | {d["unique_sources_if_missing_dropped"]} | {", ".join(flag)} |')
    lines+=['Old-row counts apply REMOVE.json, REMOVE_WORDING.json, and N’s outside_native_training_division removals. Totals add delivered rows once; duplicate-expanded delivery does not increase unique source coverage.',
      'Camera v1 and v3 have fewer than 1,000 distinct sources without MISSING_GT; camera v3 also delivers fewer than 1,000 rows.',
      '', 'REMOVE.json contains exactly 6,710 replaced sources: REMOVE_PROPOSED.json minus 117 sources from 10 scenes that N marks outside_native_training_division.',
      'REMOVE_WORDING.json contains 679 old rows with reason heldout_wording_distance_le_0.05. REMOVE_MISSING_GT.json contains 4,420 old sources; the orchestrator decides whether to apply it.',
      'All three removal files use compact five-key n.json JSON Lines. REMOVE.provenance.json records input and output SHA256 hashes without adding fields to N’s schema.',
      '', 'An out-of-view citation names the latest raster frame before k with object share ≥0.002. If no such frame precedes k, it says “it first appears in frame f, after frame k”, with f from the raster.',
      f'The independent checker verifies {ind["sighting_frames"].get("last_before",0):,} past citations and {ind["sighting_frames"].get("first_after",0):,} first-appearance citations. It recomputes visibility, answers, geometry_values, and every relation clause on all {total:,} rows using {ind["gt_scenes"]} pinned rasters.',
      'Future sightings occupy a separate step naming the existing object instance, which lets N’s unchanged frame-citation grammar accept the requested two-frame sentence.',
      'Relations use closest OBB point distance, camera-frame bearing, and gravity-aligned height. Each object has one visibility statement and a relation to the frame-k camera; frame numbers are in 1..32.',
      f'N’s native validate_row, direct_row, validate_direct, row_check, and r2_contract.validate pass on all {checks["source_native_pack_validate"]:,} sources and {total:,} delivered rows. Loaded kit modules match TREE_SEAL.json.',
      'The checker recomputes candidate_id with N’s formula and verifies unique qids/candidate_ids, exact cells, source-use bounds, mapping coverage, and field differences.',
      'Permitted edits are qid, candidate_id, answer, target, student_input.question/options, and provenance.sb_rowB4. Option sets, question templates, media, and other source fields remain identical.',
      'The room rule excludes K1 held-out, R0, withheld-80, dev-S1, and BENCH v2. The scene gate also uses N’s complete remove lists and dev/benchmark filter.',
      f'The wording filter compares against {checks["wording_filter"]["unique_heldout_wordings"]:,} wordings from {checks["wording_filter"]["input_files"]:,} pinned inputs and refuses {checks["wording_filter"]["refused_sources"]} sources. Threshold: normalized Levenshtein distance ≤0.05 after NFKC, casefold, and whitespace normalization, divided by maximum codepoint length.',
      f'Every deterministic option permutation is filtered. The distance implementation passes {wf["comparisons"]:,} independent dynamic-program comparisons. Held-out text supplies no template.',
      'HISTOGRAMS.json reports before/after positions, semantics, first-seen ranks, visibility, and earliest-winner frequencies. Each delivered position, semantic/rank, and joint cell is exactly uniform within its stratum.',
      'READ30.md prints thirty complete rows from sources absent from B3’s thirty-row review. READ30_REVIEW.json records the agent’s grammar, answer, and evidence review.',
      'QID_MAP.jsonl maps store-v7 and sb_rowB2 qids to every delivered qid. Use this kit as the replacement frame-k build; do not concatenate B2, B3, and B4 outputs.',
      '', 'Commands producing these numbers (run from this workspace with PYTHONDONTWRITEBYTECODE=1; P=/scratch/jjyeung/envs/p1cpu/bin/python):',
      '`$P build_rows.py` produces census, exact cells, histograms, source-use counts, native checks, wording refusals, and the three removal lists.',
      '`$P verify_rows.py` produces full-row independent GT, visibility, citation, identity, field, balance, and mapping checks.',
      '`$P check_reuse.py` verifies unchanged B3 balance, geometry, wording, permutation, and room algorithms and SHA256-identical staged inputs.',
      '`$P check_gate_removals.py` produces N’s gate counts, exact removal-set checks, and the family retention table.',
      '`$P check_wording_filter.py` produces the edit-distance comparison count. `$P select_samples.py` selects the new thirty-row sample.',
      '`$P record_read30_review.py` records the agent’s completed review. `$P finish_delivery.py` asserts checks, writes this report, seals the tar, and verifies member hashes.',
      '', 'MISSING: 4,420 sources lack 307 exact pinned rasters at the local paths recorded in REFUSALS.json (original paths, expected mirror paths, and hashes). Their absence on this node does not prove the rasters are lost on the source host.',
      'GT rasters and N’s sealed tree remain external read-only inputs. INPUTS.json and the check receipts pin dependencies; removal-list hashes live in their schema-preserving sidecar.',
      'Not done: training and the next-read model gate. That gate requires the top shared object to change on more than the baseline 18 of 59 fixed dev pairs whose true winner changes, with correctness and denominator reported.',
      'Terminology note: “replaced sources” names the removal set required by the trainer; it does not narrate revision history.']
    assert len(lines)<=80,len(lines)
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'STATUS.md').write_text(f'The kit delivers {total:,} rows from {unique:,} sources. All required checks pass, including zero false raster citations and zero N scene-division refusals. The compact replacement, wording, and MISSING_GT lists are separate; the report flags camera v1/v3 source coverage. The tar and SHA256SUMS are in out/.\n')
    code=[p for p in ROOT.glob('*.py') if not p.name.startswith('patch_')]+[ROOT/'wording_filter.cpp',ROOT/'STATUS.md']+list((ROOT/'original').glob('*.py'))
    ins=list((ROOT/'inputs').glob('*'))
    outputs=[p for p in OUT.iterdir() if p.suffix in {'.json','.jsonl','.md'} and p.name not in {'DELIVERY.json','sb_rowB3_REPORT.md','sb_rowB4_REPORT.md'}]
    paths=sorted(code+ins+outputs+[ROOT/'prompts/sb_rowB4.md'])
    assert all(p.is_file() for p in paths)
    archive=OUT/'sb_rowB4.tar'
    with tarfile.open(archive,'w') as tar:
        for p in paths:tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
    expected={str(p.relative_to(ROOT)):sha(p) for p in paths};actual={}
    with tarfile.open(archive) as tar:
        for m in tar:
            h=hashlib.sha256()
            with tar.extractfile(m) as f:
                for b in iter(lambda:f.read(4<<20),b''):h.update(b)
            actual[m.name]=h.hexdigest()
    assert actual==expected
    digest=sha(archive);(OUT/'SHA256SUMS').write_text(digest+'  sb_rowB4.tar\n')
    dump('DELIVERY.json',dict(status='PASS',input_sha256={str(p):sha(p) for p in paths},archive=str(archive),sha256=digest,bytes=archive.stat().st_size,rows=total,archive_members_verified=len(paths),report_lines=len(lines)))
    print(json.dumps({'rows':total,'sha256':digest,'bytes':archive.stat().st_size,'members':len(paths),'report_lines':len(lines)},indent=2))
if __name__=='__main__':main()
