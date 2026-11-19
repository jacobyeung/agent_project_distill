"""Record completed human review and package the checked, unadmitted kit."""
import argparse,collections,hashlib,json,pathlib,tarfile
ROOT=pathlib.Path(__file__).resolve().parent;OUT=ROOT/'out'
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def load(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
ap=argparse.ArgumentParser();ap.add_argument('--reviewed',action='store_true');args=ap.parse_args();assert args.reviewed
c=load(OUT/'CHECKS.json');g=load(OUT/'GENERATION.json');m=load(OUT/'INPUTS.json')
assert c['semantic_checks']=='PASS' and c['rows']==4000
index=load(OUT/'READ30_INDEX.json');assert index['read30_sha256']==sha(OUT/'READ30.md')
review={'status':'PASS','qids':index['qids'],'rows':30,'scope':'Questions, option letters, both category totals, ordinal/frame evidence, comparisons, and source instance metadata. Full store-schema records are published in READ30.md; preserved image/frame metadata is also checked mechanically. RGB images were not inspected.',
 'input_sha256':{str(OUT/'READ30.md'):sha(OUT/'READ30.md'),str(OUT/'READ30_REVIEW.txt'):sha(OUT/'READ30_REVIEW.txt'),str(OUT/'AUDIT.json'):sha(OUT/'AUDIT.json'),str(OUT/'SOURCE_ROWS.jsonl'):sha(OUT/'SOURCE_ROWS.jsonl'),str(ROOT/'review_samples.py'):sha(ROOT/'review_samples.py'),str(ROOT/'finalize.py'):sha(ROOT/'finalize.py')}}
write(OUT/'MANUAL_REVIEW.json',review)
c['manual_read30']='PASS';c['manual_review_sha256']=sha(OUT/'MANUAL_REVIEW.json');c['wording_corpus_completeness']='MISSING complete dev-S1 and benchmark authorities; all discovered local wording records checked'
c['input_sha256'].update({str(OUT/'MANUAL_REVIEW.json'):sha(OUT/'MANUAL_REVIEW.json'),str(ROOT/'finalize.py'):sha(ROOT/'finalize.py')})
write(OUT/'CHECKS.json',c)
lines=[
'# Relative-count row kit',
'',
'Built 4,000 form B rows; `build_rows.py --form A` emits the tally alternative. These forms are alternative versions of the same questions, not additive rows.',
'Admission is BLOCKED: the unchanged w19 direct VQA grammar rejects the requested trace syntax. The orchestrator decides admission; no tree files were changed.',
'W19 is the newer sealed tree: `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1`.',
'Why 4,000: 20 new wording templates × 200 rows give a bounded first dose for a family with no training coverage, while balancing comparison direction and deliberately covering ties and higher counts. This is a coverage choice, not an empirically optimized dose.',
'',
'| Template IDs | First larger ≥5 | First larger <5 | Second larger ≥5 | Second larger <5 | Equal ≥5 | Equal <5 | Total |',
'|---|---:|---:|---:|---:|---:|---:|---:|',
'| Each of 00–19 | 39 | 28 | 39 | 28 | 2 | 64 | 200 |',
'| All templates | 780 | 560 | 780 | 560 | 40 | 1,280 | 4,000 |',
'',
f"The generator asserts all 120 cells exactly. Ties: 1,320 (33%); first/second larger: 1,340 each; either side ≥5: 1,600 (40%). Answer letters: {c['answer_letters']}.",
f"Sources: {g['pool']['eligible_b12_rows']:,} eligible b12 rows on {g['pool']['eligible_pair_clips']:,} pairable clips; {len(g['pool']['conflicting_category_groups'])} inconsistent category groups. The selected rows use {c['unique_source_rows']:,} source rows, {c['clips']:,} clips and {c['rooms']:,} physical rooms; each source appears in at most {c['max_source_reuse']} comparisons.",
'Pairs require identical dataset, scene and all frame metadata, matching instance IDs/first frames for repeated category evidence, disjoint categories and distinct instance IDs. Each unordered category pair appears once.',
f"Unique qids/candidate IDs: 4,000 each. IDs were recomputed with the kit formula; a scan of all {c['store_identity_scan_rows']:,} store rows found no collisions. Only explicitly allowed fields differ from the first source; count_kind is relative and count_arity is 2.",
f"Independent GT checks: {c['ground_truth_independently_recomputed']:,}/{c['rows']:,}. Both forms passed semantic checks on all rows. Frame indices stay within 1..32; form B ordinals run exactly 1..N, and form A frames increase strictly with positive new-instance tallies. Each count equals the distinct GT-instance total.",
'All K1 held-out, R0, withheld-80, dev-S1 and BENCH-v2 room intersections are zero under the pinned room authorities.',
f"Native ground_rows.pack/validate adapter: 4,000 new rows and {c['unique_source_rows']:,} sources pass. This normalizes a direct row to the ground-row envelope and does not establish direct-training compatibility.",
f"Unmodified r2_contract.validate: new rows {c['native_vqa_intake']['new_pass']:,} pass / {c['native_vqa_intake']['new_fail']:,} fail; sources {c['native_vqa_intake']['source_pass']:,} pass / {c['native_vqa_intake']['source_fail']:,} fail. Required all-checks-pass is false; full errors appear in CHECKS.json.",
'The kit type is `relative_count`; bindings.py requires options `more`, `fewer`, `equal number`. evalpath/run.py:score_item uses final-answer extraction and multiple-choice exact match. Every target ends with one correct option letter after </think>; all 4,000 score 1.0 against their GT letters.',
f"Wording filter: NFKC/casefold/alphanumeric normalization; reject character Levenshtein distance/max length ≤0.25. It checked {g['wording_filter']['candidate_questions_tested']:,} candidates against {g['wording_filter']['references']:,} unique local references and removed {g['wording_filter']['removed']}. CHECKS.json lists every wording input and SHA256. Templates were authored independently of evaluation items.",
'Coverage limitation: MISSING complete dev-S1 direct-item and complete benchmark wording authorities. No exact filenames were supplied. The searched w19 kit/input fixtures, sb_callrate source item directory and named mirror row directories provide R0, routed dev-S1, local benchmark fixtures and binding patterns; this cannot certify unseen corpus wordings.',
'All 30 full rows are in READ30.md. Human question/trace/GT review passed, including singular grammar, repeated first frames with distinct ordinals, equality and high counts. Image/frame metadata also passed mechanical comparison.',
'',
'Form B amendment: permit one count-first numbered Step per category in place of one Locate line per instance. Register N only after verifying exactly N unique ordinals 1..N, each tied to a first-seen frame; allow different instances at the same frame. Permit the matching count summary and subsequent comparison of the two registered totals.',
'Form A amendment: permit one Step per category with one positive new-instance tally per first-seen frame, strictly increasing frames, and total equal to their sum. This replaces per-instance Locate evidence with an aggregate; retain the underlying distinct-instance audit. Permit the subsequent comparison of the registered totals. Form A has no checkpoint measurement.',
'Both amendments need an explicit relative-count comparison rule for equals/more/less and option-letter agreement. The standalone checker enforces these properties but does not amend or bypass N’s validator.',
'',
'GT conventions follow B12_COUNT_APPEARANCE_ROWS_20261116.md: visibility floor 0.002 at 240×320, each cited onset has all earlier pins present, distinct instance IDs, and category restrictions. This kit mechanically reuses source evidence; it does not rerasterize or verify RGB pixels.',
'Not done: training, GPU work, force-close/equal-accuracy evaluation, RGB inspection, full missing-corpus filtering, or admission. The evaluation gate should watch force closes and equal accuracy because type accuracy can be inflated by forced answers.',
'',
'Commands producing the reported numbers:',
'```sh',
'g++ -O3 -shared -fPIC edit_distance.cpp -o edit_distance.so',
'/scratch/jjyeung/envs/p1cpu/bin/python -B build_rows.py',
'/scratch/jjyeung/envs/p1cpu/bin/python -B check_rows.py',
'/scratch/jjyeung/envs/p1cpu/bin/python -B review_samples.py',
'/scratch/jjyeung/envs/p1cpu/bin/python -B finalize.py --reviewed',
'# Alternative full build: python -B build_rows.py --form A --out out/formA',
'```',
'GENERATION.json gives generator cell/source/filter counts; CHECKS.json gives independent validation counts; MANUAL_REVIEW.json binds the sample review. INPUTS.json and each row pin computational inputs. PACKAGE.json and sb_rowC3.tar.sha256 bind the archive.',
]
pretty=[];fenced=False
for line in lines:
    if line.startswith('```'):
        if not fenced and pretty and pretty[-1]:pretty.append('')
        fenced=not fenced
    elif line and not fenced and not line.startswith('|') and pretty and pretty[-1] and not pretty[-1].startswith('#'):
        pretty.append('')
    pretty.append(line)
lines=pretty
assert len(lines)<=80,len(lines)
(OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
(ROOT/'STATUS.md').write_text('The 4,000-row form B kit is built and packaged with a form A flag. Independent GT, quota, identity, room, scorer, allowed-field and both-form semantic checks pass; 30 samples were reviewed. Native pack adapters pass, but direct-training grammar rejects the requested form, so admission remains blocked. Complete dev-S1 and benchmark wording authorities are missing. See out/REPORT.md and out/CHECKS.json. No training or GPU work ran.\n')
files=[ROOT/n for n in ['build_rows.py','check_rows.py','trace_forms.py','distance_filter.py','edit_distance.cpp','edit_distance.so','review_samples.py','finalize.py','STATUS.md']]
files += [OUT/n for n in ['sb_rowC3.jsonl','SOURCE_ROWS.jsonl','AUDIT.json','GENERATION.json','INPUTS.json','CHECKS.json','READ30.md','READ30_INDEX.json','READ30_REVIEW.txt','MANUAL_REVIEW.json','REPORT.md']]
files += [ROOT/'in'/n for n in ['B12_COUNT_APPEARANCE_ROWS_20261116.md','coverage_rows_v2.py','check_cov_v2.py','COVERAGE_V2_PUB.tar']]
with tarfile.open(OUT/'sb_rowC3.tar','w') as t:
    for p in files:t.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
archive=sha(OUT/'sb_rowC3.tar');(OUT/'sb_rowC3.tar.sha256').write_text(archive+'  sb_rowC3.tar\n')
write(OUT/'PACKAGE.json',{'schema':'sb-rowC3-package-v1','archive':'sb_rowC3.tar','sha256':archive,'bytes':(OUT/'sb_rowC3.tar').stat().st_size,'input_sha256':{str(p.relative_to(ROOT)):sha(p) for p in files}})
print(json.dumps({'archive':str(OUT/'sb_rowC3.tar'),'sha256':archive,'status':c['status'],'rows':c['rows']}))
