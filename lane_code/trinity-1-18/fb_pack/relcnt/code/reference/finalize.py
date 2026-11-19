"""Finalize the audited packet; a grammar failure always blocks acceptance."""
from common import *
import tarfile,collections

def main():
 cp=ROOT/'out/CHECKS.json';check=json.loads(cp.read_text());rows=ROOT/'out/relative_count.jsonl';build=jload(ROOT/'out/BUILD.json')
 sums={}
 for line in (ROOT/'in/INPUT_SHA256SUMS.txt').read_text().splitlines():
  h,p=line.split(None,1);p=str(Path(p).resolve());sums[p]=h
 store='/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
 assert sums[store]=='210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443'
 corpus=jload(ROOT/'in/WORDING_CORPUS.json');census=jload(ROOT/'in/CENSUS.json')
 read=ROOT/'out/READ30.md';samples=[json.loads(s) for s in re.findall(r'```json\n(.*?)\n```',read.read_text(),re.S)]
 assert len(samples)==30
 review=dict(input_sha256={str(read):sha(read),str(rows):sha(rows)},reviewer='Codex primary agent',rows=30,qids=[r['qid'] for r in samples],language_and_count_comparison='PASS',scope='Read all 30 complete questions, options, procedure traces, final answers and GT count/room summaries. Full JSON rows are printed in READ30.md; metadata and frame bindings are checked by code/check.py.',rgb_visual_audit='NOT_RUN')
 dump(ROOT/'out/READ30_REVIEW.json',review)
 check['manual_read']='PASS: 30 question/option/trace/answer and GT-summary reviews; full JSON printed'
 check['required_checks']='FAIL: sealed shared direct grammar rejects numeric procedure counts'
 check['status']='BLOCKED_GRAMMAR'
 check['training_admitted']=False
 check['wording_filter']['metric']='UTF-8 byte Levenshtein / maximum normalized UTF-8 byte length'
 check['counts']['shared_direct_grammar_failed_rows']=4000
 check['native_validation_scope']={'direct_trace_grammar':'FAIL','ground_pack_and_validate_through_serialization_adapter':'PASS','r1_counting_admit':'PASS','r1_training_row_check':'PASS','full_trainer_preparation':'NOT_RUN'}
 check['input_sha256'].update(sums)
 check['input_sha256'].update({str(ROOT/'out/READ30_REVIEW.json'):sha(ROOT/'out/READ30_REVIEW.json'),str(ROOT/'code/finalize.py'):sha(__file__)})
 dump(cp,check)
 conflict='''The 4,000 direct rows state each category's GT count after the store's counting procedure, then compare the categories. All fail the sealed shared direct-trace grammar with `number_not_allowed` on each of the two counts (8,000 violations).

The conflict is in w19 `student_pilot/trace_grammar.py`, `validate_trace`: a numeric count must match an earlier explicit list. The store's procedure-only single-count example avoids this rule by placing its number only after `</think>`. Relative count needs the two intermediate numbers before its final option letter. Repeating instance lists would violate this task.

N's `r1_counting.admit` recognizes these rows as PROC, and `r1_training.row_check` passes them. `ground_rows.pack` and `ground_rows.validate` also pass through the documented no-call serialization adapter. These narrower passes do not override the shared grammar failure or establish trainer readiness.

Resolution needed: the owner of N's sealed validator must reconcile numerical procedure counts with the grammar contract, or the row requirement must change. This workspace changes neither the sealed tree nor the task requirement. The packet is BLOCKED_GRAMMAR and must not be represented as fully validated.
'''
 (ROOT/'out/GRAMMAR_CONFLICT.md').write_text(conflict)
 c=check['counts'];a=check['answer_letters'];ds=check['datasets'];m=json.loads((ROOT/'out/MISSING_RASTERS.json').read_text())
 report=f'''The packet contains 4,000 procedure-only relative-count rows. Status: **BLOCKED_GRAMMAR; do not admit as fully validated**.
The sealed shared direct grammar rejects the required intermediate numerical counts. All other listed data checks pass.

Build: w19 tree `8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa`; relevant validator files match its frozen copy.
Source: b12 v4 totals and byte-matched local GT rasters. Store v7 verifies as `210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443`.
Size rationale: 4,000 is 200 examples for each of 20 new wordings, about 1.96% of the 204,413-row store.
Ties occupy 10% so equality is learned without dominating comparison; unequal rows split 1,800/1,800 by which side is larger.
Every trace counts each category once across frames, states both counts, and compares them; no instance enumeration appears.
The wording corpus has 139 relative-count items (130 unique wordings), all using multiple-choice exact match. No numeric-difference format was observed.
Answers use the benchmark's final single option letter; options contain more, fewer, and equal number in balanced positions.
The scorer is w19 `evalpath/run.py:score_item`, with extraction and exact match in `evalpath/official.py`.

The following cells apply separately to EACH template 00–19; CHECKS.json enumerates all 380 cells.
| Maximum side count | First larger per template | Second larger per template | Ties per template |
|---|---:|---:|---:|
| 2 | 28 | 28 | 0 |
| 3 | 18 | 18 | 0 |
| 4 | 12 | 12 | 0 |
| 5 | 10 | 10 | 0 |
| 6 | 8 | 8 | 0 |
| 7 | 4 | 4 | 0 |
| 8 | 4 | 4 | 0 |
| 9 | 3 | 3 | 0 |
| 10+ | 3 | 3 | 0 |
| Equal counts | 0 | 0 | 20 |
Counts range from 1 to 25 on both sides, with every value 1–10 represented. {c['at_least_one_side_ge_5']} rows (32%) have a side with at least 5 instances.
Final letters: A={a['A']}, B={a['B']}, C={a['C']}. Data: ScanNet={ds.get('d1',0)}, ARKitScenes={ds.get('d3',0)}, ScanNet++=0.
There are {check['training_scenes']} captures in {check['physical_rooms']} physical rooms and {check['source_count']} distinct source rows.
Observed reuse maxima/caps: source 8/8, unordered category pair 4/4, oriented pair 2/2, capture 24/24. This bounds reuse while filling rare high-count cells.

Checks: exact cells, unique qids/candidate_ids, kit candidate formula, limited field diffs, and unchanged source frames all pass on 4,000 rows.
GT: independent raster recomputation passes on 4,000 rows and all 1,803 sources; annotated category instances must each reach pixel share 0.002 at the source pins.
ARKit alignment entries are checked for every selected capture. Counts remain annotation-based and were not visually audited against RGB.
Rooms: zero K1-heldout, R0, withheld-80, dev-S1, or BENCH-v2 hits; all canonical rooms resolve through pinned N authorities.
Native pack/validate passes on 4,000 outputs and 1,803 sources through an explicit direct-to-ground serialization adapter, preserving thought bytes and using no calls.
N procedure admission and row_check pass for all outputs. Source direct grammar passes for all 1,803 sources.
Shared direct grammar: FAIL on all 4,000 outputs, with 8,000 `number_not_allowed` violations. See GRAMMAR_CONFLICT.md; no validator was altered.
Scorer: all 4,000 GT traces score 1.0. This checks answer serialization, not model accuracy.
Wording: compare each rendered question against all 4,265 discovered kit/item question strings; reject normalized edit distance <=0.25; removed 0, skipped files 0.
Normalization: NFKC, casefold, word-token extraction and whitespace collapse; distance is Levenshtein over UTF-8 bytes divided by maximum byte length.
The corpus includes all discovered JSON/JSONL questions in w19 TREE/fixtures and the routed-read source package, plus Python question literals. The C++ matcher passes 300 Python-oracle cases.
I read 30 complete question/option/trace/answer samples with their GT summaries. READ30.md prints full JSON, and READ30_REVIEW.json records the review scope.
Missing inputs: {len(m['missing_rasters'])} b12 rasters, named with expected digests/collection in MISSING_RASTERS.json, exclude 5,779 source rows. No delivered row depends on one.

Commands (run from this workspace; CPU environment /scratch/jjyeung/envs/p1cpu/bin/python):
`python code/census.py` produces available-source counts, raster facts and candidate count bins.
`python code/corpus.py` produces wording-file counts and hashes; `g++ -O3 -shared -fPIC code/editdistance.cpp -o code/editdistance.so` builds the filter.
`python code/generate.py` asserts every cell and reuse cap and writes out/relative_count.jsonl and BUILD.json.
`python code/check.py` produces all validation counts, histograms and READ30.md using independent raster arithmetic.
`python code/finalize.py` records the manual review, combines the checks, and packages out/sb_rowC.tar with SHA256SUMS.txt.
`sha256sum` on the four paths in in/INPUT_SHA256SUMS.txt produced the store/archive input identities. All JSON audit outputs bind their inputs by SHA256.
Use `PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`; raster workers are capped at 8.
Not done: sealed grammar reconciliation, full trainer preparation, RGB review, training, GPU work, numeric-difference supervision, or an accuracy claim.
No-archaeology review: no borderline historical wording was retained. This is an internal build report.
'''
 assert len(report.splitlines())<=80
 (ROOT/'out/REPORT.md').write_text(report);(ROOT/'sb_rowC_REPORT.md').write_text(report)
 status('The 4,000-row packet is built and audited, with 20 new wordings, 1,800/1,800 unequal comparisons, 400 ties, and 32% high-count rows. Independent GT, rooms, IDs, field diffs, scorer, native serialization-adapter validation and 30 language reviews pass. Overall status is BLOCKED_GRAMMAR: the sealed shared direct grammar rejects the two required numerical procedure counts in each row. Reports and the archive identify this unresolved compatibility issue; no training ran.')
 # Package the runnable code, selected row artifact, reports, compact audit inputs, and original source rows.
 # Raw GT remains local and is pinned in CENSUS/CHECKS; it is not copied into the output packet.
 files=[p for p in (ROOT/'code').iterdir() if p.is_file() and p.suffix in ('.py','.cpp','.so')]
 files += [ROOT/'STATUS.md',ROOT/'sb_rowC_REPORT.md',ROOT/'in/CENSUS.json',ROOT/'in/WORDING_CORPUS.json',ROOT/'in/procedure_source.json',ROOT/'in/INPUT_SHA256SUMS.txt',SRC]
 files += [p for p in (ROOT/'out').iterdir() if p.is_file() and p.suffix in ('.json','.jsonl','.md')]
 manifest=dict(input_sha256={str(p):sha(p) for p in files},status='BLOCKED_GRAMMAR',raw_gt_included=False,raw_gt_location='Paths and sha256 in in/CENSUS.json and out/CHECKS.json',commands=['census.py','corpus.py','generate.py','check.py','finalize.py'])
 dump(ROOT/'out/PACKAGE_MANIFEST.json',manifest)
 # A repeated finalization must list the manifest once, without a self-hash dependency.
 files=[p for p in files if p.name!='PACKAGE_MANIFEST.json']+[ROOT/'out/PACKAGE_MANIFEST.json']
 archive=ROOT/'out/sb_rowC.tar'
 with tarfile.open(archive,'w') as tf:
  for p in sorted(set(files)):tf.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
 h=sha(archive);(ROOT/'out/SHA256SUMS.txt').write_text(f'{h}  sb_rowC.tar\n{sha(rows)}  relative_count.jsonl\n')
 print(json.dumps(dict(status='BLOCKED_GRAMMAR',archive=str(archive),sha256=h,rows=4000,report_lines=len(report.splitlines()))))
if __name__=='__main__':main()
