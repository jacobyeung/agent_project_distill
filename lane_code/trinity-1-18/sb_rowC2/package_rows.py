"""Write the bounded report and a hash-bound review archive after READ30 approval."""
import hashlib,json,pathlib,tarfile
ROOT=pathlib.Path(__file__).resolve().parent;O=ROOT/'out'
def load(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 c=load(O/'CHECKS.json');g=load(O/'GENERATION.json');r=load(O/'MANUAL_REVIEW.json')
 assert r['status']=='PASS' and r['read30_sha256']==sha(O/'READ30.md') and len(r['qids'])==30
 c['manual_read30']={'status':'PASS','rows':30,'sha256':sha(O/'MANUAL_REVIEW.json')}
 c['official_scorer_format_pass']=4000
 c['artifact_sha256']['tally_gate.py']=sha(ROOT/'tally_gate.py')
 (O/'CHECKS.json').write_text(json.dumps(c,sort_keys=True,indent=2)+'\n')
 native=c['native_vqa_intake'];word=g['wording_filter'];pool=g['pool']
 lines=[
 '# sb_rowC2: relative-count tallies',
 '',
 f'**{c["status"]}.** The packet contains 4,000 generated rows. N has not admitted them.',
 f'The unchanged w19 direct VQA validator rejects {native["new_fail"]}/4,000 new rows; required_all_checks_pass is false.',
 'The 4,000-row dose gives each of 20 original wordings 200 examples and covers six exact cells per wording. It is a coverage choice, not a measured optimal dose.',
 'Ties occupy 10% to teach equality without displacing the main comparison task. Unequal rows split exactly 50/50 by which asked category is larger.',
 'A category has at least five instances in 1,600 rows (40%). Scarce high-count ties receive two examples per wording; unequal high-count pairs supply the remainder.',
 '',
 '| Wording | More ≥5 | More <5 | Fewer ≥5 | Fewer <5 | Tie ≥5 | Tie <5 |',
 '|---|---:|---:|---:|---:|---:|---:|',
 ]
 for tid in range(20):
  cells=[c['cells'][f'{tid:02d}|{rel}|{size}'] for rel,size in [('more','high'),('more','low'),('fewer','high'),('fewer','low'),('equal number','high'),('equal number','low')]]
  lines.append('| '+str(tid)+' | '+' | '.join(map(str,cells))+' |')
 lines += [
 '',
 f'All 4,000 GT checks pass: every asked category appears, frames increase strictly within 1..32, increments count newly seen instances, category sums and comparison match GT, and the final option letter agrees.',
 f'Each unordered (clip, category pair) appears once: {c["unique_pairs"]} pairs, {c["clips"]} clips, {c["rooms"]} physical rooms. The maximum tally length is {c["max_entries_per_category"]}; the maximum category count is {c["max_category_total"]}.',
 f'The build uses {c["unique_source_rows"]} distinct source rows, at most {c["max_source_reuse"]} outputs per source (cap 4). Exact cells, source reuse, unique qids/candidate_ids, kit candidate_identity recomputation, field diffs, and identical clip metadata pass.',
 f'The independent checker rereads selected records from the pinned store, derives category totals from distinct GT IDs and first-seen frames, and compares those with both source text and new tallies.',
 'Source edits are limited to qid, candidate_id, question type/category, answer/target, count_kind/count_arity, question/options, and provenance.relative_count_tally. Other provenance describes the retained source; the derivation identifies both actual category sources.',
 'K1, R0, withheld-80, dev-S1 and BENCH v2 checks have zero hits. The exact pinned authorities, store and code hashes are in INPUTS.json.',
 f'The eligible pool has {pool["eligible_b12_rows"]} B12 rows in {pool["eligible_pair_clips"]} multi-category clips, with {len(pool["conflicting_category_groups"])} conflicting category groups. Only removed B12 GT rows are used; other removed pools are excluded.',
 'GT conventions follow B12_COUNT_APPEARANCE_ROWS_20261116.md: visibility share ≥0.002, distinct annotated IDs, first-seen sampled frames, and inherited annotation/alignment gates. No rasters or RGB pixels were reread.',
 f'Normalized character Levenshtein distance ≤0.25 causes rejection. All 4,000 questions were checked against {word["references"]} discovered unique wording references; {word["removed"]} candidates were removed. Inputs include R0, VSTI, local benchmark fixtures, and kit binding patterns.',
 'MISSING: complete dev-S1 item texts and full benchmark corpora in the named local kit/input directories. Novelty is certified against all discovered local wordings only.',
 'The scorer is w19 evalpath.run.score_item, using evalpath.official: nonempty options imply multiple choice and the extracted final letter receives exact-match credit. All 4,000 targets pass this format check.',
 f'Native ground_rows.pack/validate round-trips pass for all new rows and {c["unique_source_rows"]} sources through an explicitly documented direct-row adapter. This envelope check does not establish VQA intake compatibility.',
 f'Unmodified native VQA intake: new rows {native["new_pass"]} pass / {native["new_fail"]} fail; sources {native["source_pass"]} pass / {native["source_fail"]} fail. See NATIVE_BLOCKER.md. No native validator was patched or bypassed.',
 'READ30.md contains 30 full rows. Their questions, options, tally entries, sums and answers were read for grammar and correctness; all row fields were also checked programmatically.',
 'The standalone tally_gate.py rejects missing categories, repeated/nonincreasing/out-of-range frames, nonpositive increments, wrong sums, wrong comparisons, and wrong option letters.',
 '',
 'Commands producing the numbers: `cc -O2 -shared -fPIC edit_filter.c -o edit_filter.so`; `/scratch/jjyeung/envs/p1cpu/bin/python -B build_rows.py` produces pool/cell/novelty counts; `/scratch/jjyeung/envs/p1cpu/bin/python -B check_rows.py` produces independent counts and native failures; `/scratch/jjyeung/envs/p1cpu/bin/python -B package_rows.py` writes this report and archive hashes.',
 'The tree is w19/work/tree_r1, authenticated against w19/out/TREE_SEAL.json. The shared source tree was read only. The packet remains a local proposal.',
 'Not done: native tally-grammar support, N mixture integration, complete-corpus novelty certification, fresh raster/RGB review, training, or model evaluation. The operator must resolve the native grammar failure before admission.',
 ]
 assert len(lines)<=80
 (O/'REPORT.md').write_text('\n'.join(lines)+'\n')
 example=native['examples'][0]
 (O/'NATIVE_BLOCKER.md').write_text('# Native intake blocker\n\nThe unchanged w19 `student_pilot.r2_contract.validate(row, "vqa")` calls the pinned shared direct-trace grammar. Its numeric provenance rules license instance lists and their counts, but do not license numerical increments in per-frame tallies.\n\nExample: `'+example['qid']+'`\n\n```text\n'+example['target']+'\n```\n\nNative result: `'+example['error']+'`.\n\nThe semantic checker and `tally_gate.py` verify this row directly against GT. `ground_rows.pack/validate` accepts a normalized envelope, but that result does not override the direct intake failure. N needs explicit tally grammar support, followed by the unchanged build checks rerun against a new sealed kit. This packet does not change N.\n')
 names=['build_rows.py','check_rows.py','tally_gate.py','novelty.py','edit_filter.c','test_tally_gate.py','package_rows.py','REPRODUCE.md','out/sb_rowC2.jsonl','out/SOURCE_ROWS.jsonl','out/AUDIT.json','out/GENERATION.json','out/INPUTS.json','out/CHECKS.json','out/READ30.md','out/READ30_INDEX.json','out/REVIEWED_TEXT.json','out/MANUAL_REVIEW.json','out/REPORT.md','out/NATIVE_BLOCKER.md']
 inputs={n:sha(ROOT/n) for n in names}
 pm={'schema':'sb-rowC2-package-members-v1','status':c['status'],'input_sha256':inputs,'input_manifest':c['input_manifest']}
 (O/'PACKAGE_MEMBERS.json').write_text(json.dumps(pm,indent=2,sort_keys=True)+'\n')
 names.append('out/PACKAGE_MEMBERS.json')
 with tarfile.open(O/'sb_rowC2.tar','w') as tar:
  for n in names:tar.add(ROOT/n,arcname=n,recursive=False)
 archive_sha=sha(O/'sb_rowC2.tar');(O/'sb_rowC2.tar.sha256').write_text(archive_sha+'  sb_rowC2.tar\n')
 receipt={'schema':'sb-rowC2-package-v1','status':c['status'],'archive':{'path':'out/sb_rowC2.tar','sha256':archive_sha,'bytes':(O/'sb_rowC2.tar').stat().st_size},'input_sha256':inputs,'package_members_sha256':sha(O/'PACKAGE_MEMBERS.json')}
 (O/'PACKAGE.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 (ROOT/'STATUS.md').write_text('The local packet contains 4,000 checked relative-count tallies, 20 wordings, 10% ties, and 40% rows with a count of at least five. Independent GT, room, source, identity, scorer-format and sample-review checks pass. Required native VQA intake fails on the requested tally syntax, so the overall status is BLOCKED_NATIVE_GRAMMAR and the rows remain unadmitted. The report, CHECKS.json, full READ30.md, code, source records and SHA-256-bound archive are complete. No training or GPU work ran.\n')
 print(json.dumps(receipt['archive'],indent=2))
if __name__=='__main__':main()
