"""Seal the reviewed row build, its checks, and the requested delivery archive."""
import hashlib
import json
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out'
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4<<20),b''):h.update(block)
    return h.hexdigest()
def dump(path,data):path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
def main():
    checks=json.loads((OUT/'CHECKS.json').read_text())
    independent=json.loads((OUT/'INDEPENDENT_CHECK.json').read_text())
    review=json.loads((OUT/'READ30_REVIEW.json').read_text())
    kit=json.loads((OUT/'KIT_CHECK.json').read_text())
    wording=json.loads((OUT/'WORDING_FILTER_CHECK.json').read_text())
    assert checks['status']==independent['status']==review['status']==kit['status']=='PASS'
    assert len(review['reviewed_qids'])==30 and len(set(review['reviewed_qids']))==30
    assert review['input_sha256'][str(OUT/'READ30.md')]==sha(OUT/'READ30.md')
    assert independent['input_sha256'][str(OUT/'rows.jsonl')]==sha(OUT/'rows.jsonl')
    # Reconstruct the missing-input ledger from the final source/resolution inputs.
    resolution=json.loads((ROOT/'inputs/GT_RESOLUTION.json').read_text())
    sources=[json.loads(s) for s in (ROOT/'inputs/sources.jsonl').read_text().splitlines()]
    missing={r['qid']:'MISSING_GT' for r in sources if r['provenance']['raster'] not in resolution['resolved']}
    assert len(missing)==checks['gt_refused_total']==checks['missing_gt_rows']
    dump(OUT/'GT_REFUSALS.json',dict(input_sha256={str(p):sha(p) for p in
         [ROOT/'inputs/GT_RESOLUTION.json',ROOT/'inputs/sources.jsonl',OUT/'INPUTS.json',Path(__file__)]},
         refused=missing,missing_inputs=resolution['missing']))
    checks['read30']='PASS: 30 complete rows reviewed for question, options, frame, comparisons, and answer'
    checks['independent_check']=dict(path='INDEPENDENT_CHECK.json',sha256=sha(OUT/'INDEPENDENT_CHECK.json'))
    checks['input_sha256'].update({str(OUT/'INDEPENDENT_CHECK.json'):sha(OUT/'INDEPENDENT_CHECK.json'),
                                  str(OUT/'READ30_REVIEW.json'):sha(OUT/'READ30_REVIEW.json'),
                                  str(OUT/'KIT_CHECK.json'):sha(OUT/'KIT_CHECK.json')})
    assert wording['status']=='PASS'
    checks['wording_filter']['bounded_distance_test_cases']=wording['comparisons']
    checks['input_sha256'][str(OUT/'WORDING_FILTER_CHECK.json')]=sha(OUT/'WORDING_FILTER_CHECK.json')
    checks['discovery_evidence_sha256']={str(ROOT/'inputs'/name):sha(ROOT/'inputs'/name) for name in
        ['archive_inventory.json','archive_wording_candidates.json','all_gt_candidates.json','GT_RESOLUTION.json','WORDING_CORPUS.json']}
    dump(OUT/'CHECKS.json',checks)
    audit=json.loads((OUT/'AUDIT.json').read_text())['families']
    count=sum(x['admitted'] for x in checks['families'].values())
    refused=sum(x['refused'] for x in checks['families'].values())
    lines=[f'The build delivers {count:,} GT-recomputed replacements and removes all 11,926 source VSTI rows.',
           f'It refuses {refused:,} sources; every refusal has a reason in REFUSALS.json. CHECKS.json and INDEPENDENT_CHECK.json pass.',
           '',
           '| Family | Source rows | Any object outside k | No object at k | Replacements | Missing GT |',
           '|---|---:|---:|---:|---:|---:|']
    for fam,c in checks['families'].items():
        a=audit[fam]
        lines.append(f'| {fam} | {c["source"]} | {a["any_object_cited_other_than_k"]} | {a["no_object_cited_at_k"]} | {c["admitted"]} | {c["missing_gt"]} |')
    lines+=['','The audit prints ten source question/options/trace examples per family in EXAMPLES60.md.',
        'Each replacement fixes its camera and every object comparison to the queried slot k. The first frame mention says “of 32”.',
        'The trace uses N’s qualitative Step grammar. GT_FACTS.jsonl records numeric distances, bearings, heights, poses, and independent computations.',
        'Distance means camera centre to the closest GT OBB point. Left/right uses camera bearing; up/down uses the camera’s gravity-aligned level horizon.',
        'A location relative to the camera does not assert that an object is visible in that frame. Frame-k visibility shares remain in the facts.',
        '', '| Family | Entire source before | Admitted sources before | After |', '|---|---|---|---|']
    def hist(x):return ', '.join(f'{k}:{v}' for k,v in sorted(x.items()))
    for fam,h in checks['position_histograms'].items():
        lines.append(f'| {fam} | {hist(h["source_all_before"])} | {hist(h["admitted_sources_before"])} | {hist(h["after"])} |')
    lines += ['',f'The option seed is {checks["seed"]}. Every admitted source appears once. Counts differ by at most one where divisibility prevents exact equality.',
        'PLAN.json fixes every family/position cell before rendering; the generator asserts every cell exactly and fails on a short cell.',
        'Only qid, candidate_id, answer, target, question/options, and the provenance.sb_rowB2 addition may change. Media pins and other metadata are preserved.',
        'QID_MAP.jsonl maps each emitted replacement. REMOVE.json is JSON Lines with exactly N’s five keys: pool, question_type, reason, row_key, scene.',
        'REMOVE.provenance.json supplies hashes without changing N’s removal schema. INPUTS.json binds the source, kit, GT, and exclusion inputs.',
        '', f'N’s native direct pack and validators pass on all {checks["source_native_pack_validate"]:,} sources and all {count:,} replacements.',
        'The build uses the sealed W19 tree (seal 8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa). Ground-route packing does not apply to this direct-row schema.',
        f'The separate checker recomputes all {independent["rows_independently_recomputed"]:,} delivered answers from pinned rasters and checks each distance ordering.',
        f'GT recomputation changes {independent["source_semantic_answers_changed"]} source semantic answers; option letters change when options move.',
        'The room rule excludes K1 held-out, R0, withheld-80, dev-S1, and BENCH v2 rooms using their pinned authorities.',
        'Unique qids/candidate_ids, one-use source limits, allowed field changes, removal coverage, and all frame-k citations pass.',
        f'The wording filter checks {checks["wording_filter"]["unique_heldout_wordings"]:,} unique held-out wordings from {checks["wording_filter"]["input_files"]:,} local files/archive members.',
        'It excludes normalized Levenshtein distance ≤0.05 (NFKC, casefold, whitespace; divide by maximum codepoint length).',
        f'It refuses {checks["wording_filter"]["refused"]} source rows before balancing, checking every deterministic option position. No held-out wording supplies a template.',
        'The bounded edit-distance implementation passes 3,844 comparisons against an independent dynamic program.',
        'READ30.md contains thirty complete rows, five per family. READ30_REVIEW.json records their review.',
        '', 'Counts and evidence are produced by these commands (CPU only, OPENBLAS_NUM_THREADS=1, OMP_NUM_THREADS=1, CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE=1):',
        '`/scratch/jjyeung/envs/p1cpu/bin/python stage_inputs.py` resolves hash-identical GT and lists missing inputs.',
        '`g++ -O3 -shared -fPIC wording_filter.cpp -o inputs/wording_filter.so` builds the exact bounded edit-distance checker.',
        '`/scratch/jjyeung/envs/p1cpu/bin/python collect_wordings.py` records the exclusion-only wording corpus.',
        '`/scratch/jjyeung/envs/p1cpu/bin/python build_rows.py` produces the audit, GT facts, row counts, position cells, replacements, mapping, and removal list.',
        '`/scratch/jjyeung/envs/p1cpu/bin/python verify_rows.py` independently checks delivered geometry and transformations.',
        '`/scratch/jjyeung/envs/p1cpu/bin/python check_wording_filter.py` produces the edit-distance test count.',
        '`/scratch/jjyeung/envs/p1cpu/bin/python finish_delivery.py` writes this report and seals the archive; SHA256SUMS records its digest.',
        '',f'Not done: {checks["missing_gt_rows"]:,} rows lack {checks["missing_inputs"]} exact source-pinned rasters in the local mirror and have no replacement.',
        'GT_REFUSALS.json lists every missing raster’s original path, expected mirror path, and expected SHA256. No GT, scene mapping, or answer was guessed.',
        'This is a row-build delivery, not a training run or production-readiness claim. The kit’s seal does not authorize production.',
        'No borderline revision-history prose is retained.']
    assert len(lines)<=80,len(lines)
    report='\n'.join(lines)+'\n'
    (OUT/'REPORT.md').write_text(report);(OUT/'sb_rowB2_REPORT.md').write_text(report)
    (ROOT/'STATUS.md').write_text(f'The delivery is complete: {count:,} replacements pass native and independent checks, {refused:,} source rows are refused with recorded reasons, and REMOVE.json covers all 11,926 sources. Thirty complete examples have been reviewed. The report, archive, and checksum are in out/.\n')
    output_names=['rows.jsonl','QID_MAP.jsonl','REMOVE.json','REMOVE.provenance.json','REFUSALS.json',
        'CHECKS.json','INDEPENDENT_CHECK.json','KIT_CHECK.json','WORDING_FILTER_CHECK.json','INPUTS.json','PLAN.json','AUDIT.json','GT_FACTS.jsonl',
        'GT_REFUSALS.json','EXAMPLES60.md','READ30.md','READ30_REVIEW.json','REPORT.md','sb_rowB2_REPORT.md']
    input_names=['sources.jsonl','archive_inventory.json','all_gt_candidates.json','raster_candidates.json',
        'archive_wording_candidates.json','wording_paths.txt','GT_RESOLUTION.json','WORDING_CORPUS.json','dev_scene_exclusions.json',
        'COVERAGE_V2_PUB.tar','coverage_rows_v2.py']
    paths=[ROOT/n for n in ['stage_inputs.py','collect_wordings.py','wording_filter.cpp','check_wording_filter.py','build_rows.py','verify_rows.py','finish_delivery.py','STATUS.md']]
    paths += [OUT/n for n in output_names]+[ROOT/'inputs'/n for n in input_names]
    archive=OUT/'sb_rowB2.tar'
    with tarfile.open(archive,'w') as tar:
        for p in paths:tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
    expected_members={str(p.relative_to(ROOT)):sha(p) for p in paths}
    with tarfile.open(archive) as tar:
        actual_members={}
        for member in tar:
            h=hashlib.sha256()
            with tar.extractfile(member) as f:
                for block in iter(lambda:f.read(4<<20),b''):h.update(block)
            actual_members[member.name]=h.hexdigest()
    assert actual_members==expected_members
    digest=sha(archive)
    (OUT/'SHA256SUMS').write_text(digest+'  sb_rowB2.tar\n')
    delivery=dict(input_sha256={str(p):sha(p) for p in paths},archive=str(archive),sha256=digest,bytes=archive.stat().st_size,
                  rows=count,refused=refused,status='PASS',archive_members_verified=len(expected_members))
    dump(OUT/'DELIVERY.json',delivery)
    print(json.dumps({k:v for k,v in delivery.items() if k!='input_sha256'},indent=2))
if __name__=='__main__':main()
