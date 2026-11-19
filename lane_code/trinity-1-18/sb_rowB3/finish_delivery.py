"""Seal the checked and reviewed sb_rowB3 row kit."""
import collections as C
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'out'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4<<20),b''):h.update(b)
    return h.hexdigest()
def read(n):return json.loads((OUT/n).read_text())
def dump(n,data):(OUT/n).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
def hs(d):return ', '.join(f'{k}:{v}' for k,v in sorted(d.items()))
def main():
    checks=read('CHECKS.json');ind=read('INDEPENDENT_CHECK.json');review=read('READ30_REVIEW.json');wf=read('WORDING_FILTER_CHECK.json');kit=read('KIT_CHECK.json');hist=read('HISTOGRAMS.json');inputs=read('INPUTS.json')
    assert ind['status']==review['status']==wf['status']==kit['status']=='PASS'
    assert review['input_sha256'][str(OUT/'READ30.md')]==sha(OUT/'READ30.md') and len(set(review['reviewed_qids']))==30
    assert ind['input_sha256'][str(OUT/'rows.jsonl')]==sha(OUT/'rows.jsonl')
    assert ind['rows_independently_recomputed']==checks['replacement_native_pack_validate']
    for p,h in inputs['input_sha256'].items():
        if str(p).startswith(str(ROOT)):assert sha(p)==h,('input changed after build',p)
    checks.update(status='PASS',ground_truth_independently_recomputed=ind['rows_independently_recomputed'],field_diff_allowed=True,
        candidate_ids_independently_recomputed=True,visibility_independently_checked=True,sighting_references_independently_checked=True,
        read30='PASS: all thirty complete question/options/trace/answer renderings and visibility/geometry evidence reviewed',
        wording_distance_tests=wf['comparisons'],required_checks_passed=True)
    checks['input_sha256'].update({str(OUT/n):sha(OUT/n) for n in ['INDEPENDENT_CHECK.json','READ30_REVIEW.json','WORDING_FILTER_CHECK.json','KIT_CHECK.json']})
    dump('CHECKS.json',checks)
    plan=read('PLAN.json')['expected_joint_cells']
    families=list(hist['after']);total=checks['replacement_native_pack_validate'];unique=checks['admitted_unique_sources']
    lines=[f'The kit delivers {total:,} truthful frame-k rows across all six VSTI families, from {unique:,} unique store-v7 sources.',
      'CHECKS.json, INDEPENDENT_CHECK.json, KIT_CHECK.json, and the thirty-row review pass. The build is CPU-only; no training ran.',
      '', '| Family | Source census | Eligible sources | Delivered | All out of view | Per joint cell by stratum |', '|---|---:|---:|---:|---:|---|']
    for f in families:
        a=hist['source_all_before'][f];b=hist['admitted_sources_before'][f];c=hist['after'][f]
        cells={key.split('|')[0]:n for key,n in plan[f].items()}
        lines.append(f'| {f} | {a["rows"]} | {b["rows"]} | {c["rows"]} | {c["visibility"].get("all_out_of_view",0)} | {hs(cells)} |')
    lines += ['Cell counts apply to every rank/semantic-answer × option-position combination within the named first-seen stratum.', '', 'Each queried object has exactly one in-view or out-of-view statement, then a relation to the frame-k camera, then the answer.',
      'The visibility threshold is the source visibility_floor, 0.002. The first frame mention says “of 32”; all frame indices are in 1..32.',
      'For an out-of-view object, use the latest qualifying recorded instance frame strictly before k; otherwise use the nearest recorded frame, preferring the earlier frame on a tie.',
      'The trace labels this as a recorded-sighting reference and explicitly identifies references later in the clip. Source instances record first sightings, not a complete visibility history.',
      'Relations come from geometry_values and are independently checked against pinned GT arrays. Camera distance is to the closest OBB point; left/right compares camera bearings; up/down compares gravity-aligned heights.',
      'Camera geometry_values are sorted distances: the source trace supplies their label order, and independent GT confirms that association. No image region, mask, depth, or pose at k is invented.',
      '', '| Family | Source option histogram before | Eligible-source histogram before | Delivered histogram after |','|---|---|---|---|']
    for f in families:lines.append(f'| {f} | {hs(hist["source_all_before"][f]["position"])} | {hs(hist["admitted_sources_before"][f]["position"])} | {hs(hist["after"][f]["position"])} |')
    lines += ['', '| Camera family | Source rank before | Eligible rank before | Delivered rank after |', '|---|---|---|---|']
    for f in families:
        if not f.startswith('camera_'):continue
        def rankhist(entry):
            c=C.Counter()
            for key,n in entry['first_seen'].items():c[key.split('|')[1]]+=n
            return hs(c)
        lines.append(f'| {f} | {rankhist(hist["source_all_before"][f])} | {rankhist(hist["admitted_sources_before"][f])} | {rankhist(hist["after"][f])} |')
    lines += ['First-seen ranks sort by (first_seen, numeric instance id). Tied and untied rows are balanced separately; ties do not imply temporal precedence.',
      'For untied camera rows, the earliest object wins exactly 1/4, 1/3, and 1/2 of the four-, three-, and two-object families. HISTOGRAMS.json also reports earliest-with-ties counts.',
      'Each camera rank has equal A/B/C/D, A/B/C, or A/B counts within its tie stratum. Pair families balance both semantic directions and A/B within earlier/later/tied subject sightings.',
      '', '| Relation family | Source semantic answers before | Eligible semantic answers before | Delivered semantic answers after |', '|---|---|---|---|']
    for f in families:
        if not f.startswith('camera_'):lines.append(f'| {f} | {hs(hist["source_all_before"][f]["semantic"])} | {hs(hist["admitted_sources_before"][f]["semantic"])} | {hs(hist["after"][f]["semantic"])} |')
    lines += [f'All {unique:,} eligible sources are retained, including every eligible all-out-of-view source. The maximum source use is {checks["max_source_uses"]}; use histogram: {hs(checks["source_use_histogram"])}.',
      'Repeated sources use distinct answer positions. PLAN.json fixes every first-seen/semantic/position cell; the generator and independent checker fail on a short cell.',
      '', f'N’s sealed W19 kit is used: {kit["tree_sha256"]}. Loaded modules match TREE_SEAL.json.',
      f'Native direct pack and validators pass on all {checks["source_native_pack_validate"]:,} sources and all {total:,} new rows. Independent GT checks cover {ind["gt_scenes"]} raster files and every emitted row.',
      'Checks cover unique qids/candidate_ids, N’s candidate-id formula, room exclusions, source-use bounds, complete mapping, and field differences.',
      'Permitted changes: qid, candidate_id, answer, target, student_input.question/options, and provenance.sb_rowB3. All media and remaining source fields stay identical.',
      'The room rule excludes K1 held-out, R0, withheld-80, dev-S1, and BENCH v2 using their pinned authorities in INPUTS.json.',
      f'The wording filter checks {checks["wording_filter"]["unique_heldout_wordings"]:,} unique exclusion-only wordings from {checks["wording_filter"]["input_files"]:,} pinned local inputs; it refuses {checks["wording_filter"]["refused_sources"]} sources.',
      'It rejects normalized Levenshtein distance ≤0.05 after NFKC, casefold, and whitespace normalization, divided by maximum codepoint length. All deterministic option permutations are checked.',
      f'The distance implementation passes {wf["comparisons"]:,} independent dynamic-program comparisons. No held-out wording supplies a template.',
      'QID_MAP.jsonl maps original store qids and sb_rowB2 qids to every new qid. This kit replaces the sb_rowB2 kit; do not concatenate their rows.',
      'REMOVE.json covers all 11,926 original store-v7 qids in N’s five-key JSONL n.json format. REMOVE.provenance.json carries its hashes without changing that schema.',
      '', 'Next-read gate: on the fixed 59 dev camera-item pairs from one room with different k whose true winner changes, the model’s top shared object must change on more than the step-200 baseline of 18 pairs.',
      'Also report answer correctness and the evaluated denominator so random answer changes cannot count as improvement. This build does not measure the next-read gate.',
      '', 'Commands producing the reported counts (from this workspace; CUDA hidden, bytecode disabled, BLAS/OpenMP threads set to 1):',
      '`/scratch/jjyeung/envs/p1cpu/bin/python build_rows.py` produces the census, filters, exact cells, both histograms, rows, mapping, and removal list.',
      '`/scratch/jjyeung/envs/p1cpu/bin/python verify_rows.py` independently checks all geometry, visibility, sighting references, transformations, and identities.',
      '`/scratch/jjyeung/envs/p1cpu/bin/python select_samples.py` selects thirty distinct sources for READ30.md; READ30_REVIEW.json records the agent’s review.',
      '`/scratch/jjyeung/envs/p1cpu/bin/python check_wording_filter.py` produces the edit-distance comparison count.',
      '`/scratch/jjyeung/envs/p1cpu/bin/python finish_delivery.py` asserts checks, writes this report, seals out/sb_rowB3.tar, verifies every archive member, and writes SHA256SUMS.',
      '', f'Not done: {checks["missing_gt_rows"]:,} source rows lack {checks["missing_gt_rasters"]} exact pinned GT rasters. REFUSALS.json marks them MISSING and lists original paths, expected mirror paths, and hashes.',
      'Full GT rasters and the sealed trainer tree remain external read-only inputs; their paths and hashes are recorded. No GT mapping, scene list, or proof was guessed.',
      'The requested before/after histograms describe the build distributions, not model performance. No revision-history prose is retained.']
    assert len(lines)<=80,len(lines)
    report='\n'.join(lines)+'\n';(OUT/'REPORT.md').write_text(report);(OUT/'sb_rowB3_REPORT.md').write_text(report)
    (ROOT/'STATUS.md').write_text(f'The kit delivers {total:,} rows from all {unique:,} eligible sources. All required native, independent GT/visibility, balancing, identity, field, room, wording, and thirty-row review checks pass. The report documents {checks["missing_gt_rows"]:,} sources with missing GT and the next-read gate. The archive and checksum are in out/.\n')
    codes=['build_rows.py','base_rows.py','stage_inputs.py','verify_rows.py','select_samples.py','finish_delivery.py','wording_filter.cpp','check_wording_filter.py','STATUS.md']
    ins=['sources.jsonl','GT_FACTS.jsonl','GT_REFUSALS.json','GT_RESOLUTION.json','WORDING_CORPUS.json','dev_scene_exclusions.json','wording_filter.so','COVERAGE_V2_PUB.tar','coverage_rows_v2.py','check_cov_v2.py']
    outputs=['rows.jsonl','QID_MAP.jsonl','REMOVE.json','REMOVE.provenance.json','REFUSALS.json','CHECKS.json','INDEPENDENT_CHECK.json','KIT_CHECK.json','WORDING_FILTER_CHECK.json','REFERENCE_INPUTS.json','SAMPLE_SELECTION.json','READ30_REVIEW.json','INPUTS.json','PLAN.json','HISTOGRAMS.json','READ30.md','REPORT.md','sb_rowB3_REPORT.md']
    paths=[ROOT/n for n in codes]+[ROOT/'inputs'/n for n in ins]+[OUT/n for n in outputs]+[ROOT/'prompts/sb_rowB3.md']
    archive=OUT/'sb_rowB3.tar'
    with tarfile.open(archive,'w') as t:
        for p in paths:t.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
    expected={str(p.relative_to(ROOT)):sha(p) for p in paths};actual={}
    with tarfile.open(archive) as t:
        for m in t:
            h=hashlib.sha256()
            with t.extractfile(m) as f:
                for b in iter(lambda:f.read(4<<20),b''):h.update(b)
            actual[m.name]=h.hexdigest()
    assert expected==actual
    digest=sha(archive);(OUT/'SHA256SUMS').write_text(digest+'  sb_rowB3.tar\n')
    dump('DELIVERY.json',dict(status='PASS',input_sha256={str(p):sha(p) for p in paths},archive=str(archive),sha256=digest,bytes=archive.stat().st_size,rows=total,archive_members_verified=len(paths),report_lines=len(lines)))
    print(json.dumps(dict(rows=total,sha256=digest,bytes=archive.stat().st_size,members=len(paths),report_lines=len(lines)),indent=2))
if __name__=='__main__':main()
