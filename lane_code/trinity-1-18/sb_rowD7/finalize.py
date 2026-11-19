"""Seal the verified row delivery, report, archive and member hashes."""
import hashlib,json,tarfile
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'out'
PREFIX='nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 '
def pin(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(4<<20),b''):h.update(block)
 return dict(sha256=h.hexdigest(),bytes=p.stat().st_size)
def load(n):return json.loads((O/n).read_text())
def main():
 c=load('CHECKS.json');v=load('VERIFY.json');l=load('LEAK_TEST.json');r=load('ROOM_RESOLUTION.json');h=load('HISTOGRAMS.json');w=load('WORDING_REVIEW.json');rv=load('READ60_REVIEW.json');a=load('INPUT_AUDIT.json');ind=load('REVIEWER_CHECKS.json');ref=load('REFUSALS.json')
 assert all(x['status']=='PASS' for x in (v,l,w,rv,a,ind)) and r['status']=='PASS_WITH_NATIVE_ROOM_LIMITATION'
 assert 'PENDING' not in json.dumps(v) and l['best_clause_accuracy']<=0.60
 deps=['VERIFY.json','LEAK_TEST.json','ROOM_RESOLUTION.json','READ60_REVIEW.json','INPUT_AUDIT.json','REVIEWER_CHECKS.json','WORDING_REVIEW.json','HISTOGRAMS.json','REFUSALS.json']
 c.update(status='PASS',delivery_ready=True,binding_ready=False,binding_limitation=r['binding_limitation'],
  READ60=dict(status='PASS',rows=60,review=pin(O/'READ60_REVIEW.json'),inherited_wording_notes=rv['inherited_wording_notes']),
  leak_test=dict(status='PASS',teaching_rows=16000,threshold=0.60,best_clause_accuracy=l['best_clause_accuracy'],pin=pin(O/'LEAK_TEST.json')),
  native_room_resolution=dict(strict_refused_sources=7771,strict_refused_new=7771,direct_VQA_filter_and_reader_pass_sources=8000,direct_VQA_filter_and_reader_pass_new=8000,tiered_alias_map=r['tiered_alias_map'],pin=pin(O/'ROOM_RESOLUTION.json')),
  independent_reviewer=dict(status='PASS',truth_rows=ind['independent_signed_axis_truth'],native_checks=ind['native_rows_and_sources'],wording_questions=w['questions'],wording_hits=len(w['hits']),D6_overlap=ind['D6_away_source_overlap']),
  clause_only_substitution=dict(status='PASS',rows=8000,masked_pair_mismatches=0,source_question_unchanged_outside_recorded_clause=True))
 # Numbers above must agree with the independently computed room evidence.
 assert c['native_room_resolution']['strict_refused_sources']==r['counts']['source|Rooms.status|unresolved']
 assert c['native_room_resolution']['strict_refused_new']==r['counts']['new|Rooms.status|unresolved']
 c['input_sha256'].update({str(O/n):pin(O/n) for n in deps});c['input_sha256'][str(Path(__file__))]=pin(Path(__file__))
 c['command']+='; '+PREFIX+'python finalize.py'
 (O/'CHECKS.json').write_text(json.dumps(c,indent=2,sort_keys=True)+'\n')
 before=l['Step1_wording_clause_mix'];seen=l['Seen'];names=h['new_away_names'];new_names=len(h['new_away_names_absent_from_old_away'])
 lines=[
 '# sb_rowD7: clause-only direction half-turn twins',
 '',
 'Delivery PASS: 8,000 new away rows use 8,000 distinct Step-1-family easy/hard toward sources. No toward twins or medium rows are emitted.',
 'The best reviewer classifier on clause-masked full question + opening + exact name set scores 50.0% on the 16,000-row teaching subset (required ≤60%). Every source/twin feature pair is identical.',
 '',
 '| New answer cell | Rows | Share within difficulty |',
 '|---|---:|---:|',
 '| easy left | 2,000 | 50% |','| easy right | 2,000 | 50% |',
 '| hard front-left | 1,000 | 25% |','| hard front-right | 1,000 | 25% |',
 '| hard back-left | 1,000 | 25% |','| hard back-right | 1,000 | 25% |',
 '',
 'Each question preserves its source text, punctuation, names and Cartesian convention outside one recorded facing clause. The codeA/build_away.py single-substitution pattern is reused; its original rule handles away-to-opposite, so substitution.py explicitly handles toward-to-away and refuses unmatched clauses.',
 f'The generator attempts {ref["attempted"]:,} candidates, refuses {sum(ref["candidate_refusals"].values()):,} without one clean substitution, and fills all six quotas exactly. New away rows cover {names:,} names; {new_names:,} were absent from admitted Seen/away sources.',
 f'The Seen easy/hard population already has {seen["exact_masked_wording_source_pairs"]:,} exact masked-wording pairs with matched names, scene and frames. This delivery adds 0 Seen rows and 0 duplicate toward twins.',
 f'The exactness gate passes 5,846/5,846 easy/hard pairs (3,664 easy; 2,182 hard). All 1,274 literal-flip disagreements are medium; all 2,665 medium pairs and {ref["medium_direction_rows_refused"]:,} medium source rows are refused.',
 f'For the {ind["D6_away_source_overlap"]:,} shared D6 away sources, answers, traces, options and frame metadata are identical to D6. Every emitted trace uses D6’s verified half-turn construction and copies its source reference-heading relation.',
 '',
 '| Step-1-family source wording population | Toward | Away |',
 '|---|---:|---:|',
 f'| Full v7 before | {before["v7_before"]["toward"]:,} | 0 |',
 f'| Full v7 plus D7 | {before["v7_plus_new_after"]["toward"]:,} | 8,000 |',
 f'| Admitted v7 before | {before["admitted_before"]["toward"]:,} | 0 |',
 f'| Admitted v7 plus D7 | {before["admitted_after"]["toward"]:,} | 8,000 |',
 '| Selected teaching subset | 8,000 | 8,000 |',
 '',
 'TEACHING_SET.json identifies the unchanged source controls. Pair those controls with NEW_ROWS.jsonl for the 50/50 guarantee; full v7 remains imbalanced. LEAK_TEST.json also tests opening, name set, role triples, dataset, frame indices and option order with the reviewer’s majority-per-feature logic.',
 'The leak test reuses rev_balance.bayes and rev_census clause/opening functions. REVIEWER_CHECKS.json reuses rev_verify native packing, field-diff and signed-axis rules. WORDING_REVIEW.json runs rev_wording’s normalized-distance logic.',
 'All 8,000 rows and sources pass N’s packer, schema and trace validators. Independent checks recompute all answers, option bijections, candidate IDs, unique qids, source-use counts, permitted field differences and source preservation. v7 has no candidate IDs; new candidate IDs are mutually unique.',
 'All 8,000 rows and sources pass scene_division_gate with the W20 remove lists and native dev/benchmark scene filter. There are zero removal, lineage, outside-train or held-out hits.',
 f'Wording exclusion compares {w["questions"]:,} distinct new questions against {w["wordings"]:,} distinct local dev/benchmark wordings ({w["pairs"]:,} pairs). Normalization is NFKC + casefold + collapsed whitespace; reject Levenshtein/max length ≤0.10. No candidate was removed for wording distance and no delivered question matches.',
 'The C++ distance routine handles Unicode code points; independent DP cases check it. Corpus coverage is limited to the pinned local item/fixture files in WORDING_CORPUS.json. Source questions supply all new wording; no dev/benchmark item supplies text.',
 '',
 'Room finding: W20 is the newest intact seal checked: 780ca7b446a578c83a1b1a398a8d54c0503a7cca26309bae6a1b60f85ef2a278 (934/934 files). W21 has nine mismatches against its inherited seal and is not used.',
 'N’s unchanged W20 Rooms, using alias pin c47c5fcd, refuses 7,771 sources and their 7,771 twins as unresolved; 229 per population resolve. ROOM_RESOLUTION.json records exact qids, opaque scene tokens, error strings, file hashes and code-line evidence.',
 'N’s native direct-VQA path nevertheless accepts all 8,000 sources and all 8,000 twins: r1_routing.Filters.reason(row, vqa) returns None, and carrier_c1_run.Rows.row passes its text, extent, R1 and reserve checks. We execute the same sealed functions for both populations.',
 'That path does not resolve the opaque tokens. r1_rooms.py:108–125 grants only the exact pinned v7 database a legacy exception; its audit records 119,375 unresolved store rows. A changed store does not inherit this exception.',
 'Physical-room checks explicitly use sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json, pinned in every row’s provenance and ROOM_RESOLUTION.json. With this map all 16,000 rows resolve, match SOURCE_MAP and have zero K1/R0/withheld-80/dev-S1/BENCH-v2 hits.',
 'Removal authority is w20/work/build20/inputs/config.json, including build18/inputs/u.json (2,637 keys), n.json and z.json, plus the conservative u_union.json (4,959 keys). Every u.json key occurs in u_union. No build17 config supplies removal authority.',
 'Binding is not performed: an augmented store needs N-side room certification carrying the named tiered map. CHECKS.json marks delivery_ready=true and binding_ready=false; no new manifest or room proof is invented.',
 '',
 'READ60.md contains 60 complete rows, ten per answer cell; READ30.md contains the first 30. All full records were parsed and compared, and all 60 questions, options and complete traces were read. READ60_REVIEW.json records inherited source agreement/spelling notes in rows 17, 40 and 43. VERIFY.json has a final manual-review result.',
 'Reproduction commands below use prefix: `'+PREFIX.strip()+'`.',
 '`python prepare_d7.py` authenticates D6 copies and tree seals; `python survey.py` computes source counts and exclusions; `python wording_corpus.py` collects the local wording corpus.',
 '`g++ -O3 -std=c++17 -shared -fPIC edit_distance.cpp -o edit_distance.so` builds the distance filter; `python build_rows.py` produces rows, gate, quotas, counts, pins and samples.',
 '`python verify_outputs.py` verifies all rows and histograms; `python reviewer_checks.py` checks independent reviewer truth/native rules and D6 equality; `python leak_test.py` produces leak accuracies and before/after clause mixes.',
 '`python room_resolution.py` measures strict Rooms, native admission and tiered exclusions; `python review_wording.py` recomputes wording exclusions; `python record_review.py` records the completed reading; `python finalize.py` seals checks, report, tar and SHA256.',
 'Every output JSON records input hashes. SOURCE_MAP.jsonl binds each new qid to its source index and exact serialized-row hash. External source stores, frame payloads and N’s tree remain read-only dependencies.',
 'Package: out/sb_rowD7.tar; digest: out/sb_rowD7.tar.sha256; verified members: out/PACKAGE.json. The archive contains code, rows, maps and evidence, excluding the large D6 working snapshot.',
 'Not done: training, N binding, frame-image rereads or external benchmark collection. No GPU, network, SSH, Git or process termination was used.',
 'Borderline prose retained: the required before/after clause census and D6 equality comparison directly test the requested fix.',
 ]
 assert len(lines)<=80,len(lines)
 (O/'REPORT.md').write_text('\n'.join(lines)+'\n')
 (B/'STATUS.md').write_text('Delivery PASS: 8,000 clause-only away twins are complete, with exact answer quotas, unique sources and a 50.0% leak score on 16,000 paired teaching rows. The 5,846-pair gate, native validation, scene gate, independent truth, wording filter and 60-row review pass. Strict native Rooms refuses 7,771 sources and twins; the native direct-row path accepts all, and the explicitly pinned tiered map passes every physical-room exclusion. N binding requires separate certification. The archive and SHA256 are sealed in out/.\n')
 includes=[B/n for n in ('prepare_d7.py','build_rows.py','substitution.py','cpu_native.py','survey.py','wording_corpus.py','verify_outputs.py','reviewer_checks.py','leak_test.py','room_resolution.py','review_wording.py','record_review.py','finalize.py','edit_distance.cpp','edit_distance.so','wording_paths.txt','STATUS.md')]
 includes+=sorted(p for p in (B/'reference').glob('*.py'))
 includes+=sorted((B/'reference/reviewer').glob('*.py'))
 includes+=[B/'reference/COVERAGE_V2_PUB.tar']
 names=['NEW_ROWS.jsonl','SOURCE_MAP.jsonl','CHECKS.json','VERIFY.json','LEAK_TEST.json','ROOM_RESOLUTION.json','INPUT_AUDIT.json','REVIEWER_CHECKS.json','WORDING_REVIEW.json','GATE.json','PREFLIGHT.json','SURVEY.json','WORDING_CORPUS.json','TEACHING_SET.json','HISTOGRAMS.json','REFUSALS.json','READ60.md','READ30.md','REVIEW_TEXT60.md','READ60_REVIEW.json','REPORT.md']
 includes+=[O/n for n in names]
 members={str(p.relative_to(B)):pin(p) for p in includes}
 archive=O/'sb_rowD7.tar'
 with tarfile.open(archive,'w') as tar:
  for p in includes:tar.add(p,arcname=str(p.relative_to(B)),recursive=False)
 with tarfile.open(archive,'r') as tar:
  assert set(tar.getnames())==set(members)
  for m in tar:
   hsh=hashlib.sha256()
   with tar.extractfile(m) as stream:
    for block in iter(lambda:stream.read(4<<20),b''):hsh.update(block)
   assert hsh.hexdigest()==members[m.name]['sha256'],m.name
 ap=pin(archive);(O/'sb_rowD7.tar.sha256').write_text(ap['sha256']+'  sb_rowD7.tar\n')
 package=dict(command=PREFIX+'python finalize.py',input_sha256=members,status='PASS',archive=dict(path=str(archive),**ap),member_count=len(members),all_member_hashes_verified=True,new_rows=8000,report_lines=len(lines),binding_ready=False)
 (O/'PACKAGE.json').write_text(json.dumps(package,indent=2,sort_keys=True)+'\n')
 print(json.dumps(dict(status='PASS',archive=package['archive'],members=len(members),report_lines=len(lines))))
if __name__=='__main__':main()
