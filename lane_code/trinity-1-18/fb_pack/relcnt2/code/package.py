"""Seal the checked packet, report commands, and verify archive members."""
from common import *
import tarfile

def main():
 checks=load(ROOT/'out/CHECKS.json');build=load(ROOT/'out/BUILD.json');dev=load(ROOT/'out/DEV_S1_DIAGNOSTIC.json');extra=load(ROOT/'out/EXTRA_CHECKS.json')
 assert checks['status']=='PASS' and checks['rows']==build['rows']
 n=checks['rows'];prior=checks['name_prior'];cap=checks['chosen_cap'];trials=checks['cap_trials'];auditdir='room_audit_final_v2'
 names=['relative_count.jsonl','BUILD.json','SELECTION_65.json','SELECTION_60.json','ROW_CHECKS.json','CHECKS.json','GT_CHECK.json','WORDING_CHECK.json','NAME_PRIOR.json','RASTER_CHECK.json','DEV_S1_DIAGNOSTIC.json','EXTRA_CHECKS.json','READ40.md','READ40_TEXT.md','READ40_REVIEW.json','CROSS_FAMILY_REVIEW.json',auditdir+'/audit.json',auditdir+'/rows.sqlite']
 files=[Path('out')/name for name in names]
 verified={}
 for rel in files:
  if rel.suffix!='.json':continue
  data=json.loads((ROOT/rel).read_text());pins=data.get('input_sha256',data.get('inputs'));assert isinstance(pins,dict) and pins,rel
  for name,value in pins.items():
   want=value['sha256'] if isinstance(value,dict) else value
   assert name.startswith('/scratch/'),name
   if name not in verified:verified[name]=sha(name)
   assert verified[name]==want,('changed input',str(rel),name,want,verified[name])
   PINS[name]=want
 assert sha(ROOT/'out/relative_count.jsonl')==build['output']['sha256']
 allrows={r['qid']:r for r in rows(ROOT/'out/relative_count.jsonl')}
 examples=[json.loads(s) for s in re.findall(r'```json\n(.*?)\n```',(ROOT/'out/READ40.md').read_text(),re.S)]
 assert len(examples)==40 and all(r==allrows[r['qid']] for r in examples)
 mean=prior['mean_unequal'];pair=prior['pair_majority'];d=dev['selected_packet']['metrics'];q=build['per_template_bucket_quota'];quota=', '.join(f'{k}:{q[k]}' for k in sorted(q,key=int))
 cmd='bash code/run.sh'
 report=f'''The relative-count packet passes the requested CPU data gates at the **{cap:.2f} name-prior cap**. It contains **{n:,} rows** and is not bound to a production store.

`{cmd} code/solve.py` and `{cmd} code/build.py` produce the cap trials below. These are feasible survivors under the declared integer selection constraints, not unrestricted corpus-size bounds.

| Cap | Surviving rows | Rows/template | More/fewer/tie per template | Mean-count LOO | Pair-majority LOO |
|---|---:|---:|---|---:|---:|
| 0.65 | {trials['65']['surviving_rows']} | {trials['65']['rows']//20} | {(trials['65']['rows']-400)//40}/{(trials['65']['rows']-400)//40}/20 | {trials['65']['mean']['correct']}/{trials['65']['mean']['evaluated']} ({trials['65']['mean']['accuracy']:.4%}) | {trials['65']['pair']['correct']}/{trials['65']['pair']['evaluated']} ({trials['65']['pair']['accuracy']:.4%}) |
| 0.60 | {trials['60']['surviving_rows']} | {trials['60']['rows']//20} | {(trials['60']['rows']-400)//40}/{(trials['60']['rows']-400)//40}/20 | {trials['60']['mean']['correct']}/{trials['60']['mean']['evaluated']} ({trials['60']['mean']['accuracy']:.4%}) | {trials['60']['pair']['correct']}/{trials['60']['pair']['evaluated']} ({trials['60']['pair']['accuracy']:.4%}) |
The delivered packet uses 0.60 because at least 3,000 rows survive. The selected means cover every unequal row; pair majority covers every row. Even crediting all tied pair-majority predictions gives {pair['accuracy_tie_upper']:.4%}.
The mean predictor removes the evaluated row from each category's count sum and observation count. The pair predictor removes it from the unordered pair's winner/tie votes. Vote ties use lexical order; the conservative tie upper bound is also checked.
Selection prioritizes direction-matched category pairs, caps each category's majority fraction at {cap:.2f} (larger:smaller and smaller:larger at most {cap/(1-cap):.2f}), and caps each pair's directional majority. A physical room/category pair has only one selected relation across captures.
Every template retains all count buckets. Per-direction max-side bucket quotas are {quota}; the last bucket means ten or more. Quotas shrink uniformly across templates with the survivor count.
No excluded source is recovered. `EXTRA_CHECKS.json` names each missing raster and its expected local location; no delivered row uses one.

`{cmd} code/check.py` produces every row, GT, identity, balance, prior, and wording number below.
The {len(checks['per_template'])} templates each contain {build['per_template_rows']} rows, including ten ascending-order ties and ten reversed ties. Questions, targets, qids, and candidate_ids are rendered together.
Global relations are {checks['relation_counts']['more']} more, {checks['relation_counts']['fewer']} fewer, and {checks['relation_counts']['tie']} ties. Letters are {dict(checks['option_letters'])}; each template has balanced letters, and each relation's letter totals differ by at most one.
The packet uses {checks['source_rows']} b12 sources, {checks['captures']} captures, and {checks['room_audit']['rooms_resolved']} physical rooms. Reuse maxima are source={checks['max_source_reuse']}, unordered pair={checks['max_pair_reuse']}, orientation={checks['max_orientation_reuse']}, capture={checks['max_capture_reuse']}.
Every think block contains two pinned counting-procedure lines and one number-free comparison, followed by a single option letter outside the think block. Instance IDs remain audit metadata.
All {n} rows pass `trace_grammar.validate_trace`, `validate_row`, `r1_counting.admit`, `r1_training.row_check`, and `ground_rows.pack/validate`; packing preserves think bytes and wraps only the answer.
Independent b12 instance-set sizes reproduce every count, comparison, and letter. All identifiers are unique; all candidate identities and exact-match scorer results pass.
The current w24 seal is `{build['tree_seal']['tree_sha256']}`. The validator/scorer files match its pinned `TREE_FILES.sha256`.
Minimum normalized wording distance is {checks['wording']['minimum']:.10f}, above 0.4. The reference contains 139 dev-S1 items and 130 unique relative-count wordings; the distance routine passes 300 scalar-oracle cases.
`{cmd} code/extra_checks.py` checks the wider number-word list, negative-control outcomes, qid regeneration, relation/letter balance, and zero conflicting physical-room/category comparisons.
All five negative controls fail at least one required gate. The synthetic list probe passes generic grammar but fails counting admission.
`{cmd} code/raster_hash_check.py` verifies all {checks['byte_matched_rasters']} selected local rasters against source, census, and raster-audit hashes. Raster arithmetic is inherited by hash; b12 instance arithmetic is fresh.
The native room command below resolves all {n} rows and reports zero R0, dev-S1, BENCH v2, withheld-80, and K1 hits; unresolved rows are zero.
`{cmd} /scratch/jjyeung/orch_n30/sb_auditfix2/store_room_audit.py --store "$PWD/out/relative_count.jsonl" --tree /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1 --lists /scratch/jjyeung/orch_n30/sb_auditfix2/inputs/lists --out "$PWD/out/{auditdir}"`
The room command needs an empty output directory. Its JSON and SQLite receipts, not its abbreviated terminal row summary, carry the row counts.

`{cmd} code/dev_diagnostic.py` produces the following diagnostic after selection; dev-S1 selects nothing and no model runs.
All 139 relative-count questions are parsed in comparison order, including reference-first wording. Frozen packet-trained means score {d['mean_unequal']['correct']}/{d['mean_unequal']['evaluated']} ({d['mean_unequal']['accuracy']:.4%}) on covered unequal items; {d['mean_unequal']['missing_or_abstained']} of {d['mean_unequal']['eligible_items']} unequal items are MISSING or abstained.
Across all items, frozen means score {d['mean_three_way']['correct']}/{d['mean_three_way']['evaluated']} ({d['mean_three_way']['accuracy']:.4%}); {d['mean_three_way']['missing_or_abstained']} predictions are MISSING. Frozen pair majority scores {d['pair_majority']['correct']}/{d['pair_majority']['evaluated']} ({d['pair_majority']['accuracy']:.4%}); {d['pair_majority']['missing_or_abstained']} are MISSING.
Within-dev pair-majority LOO scores {dev['within_dev_pair_loo']['correct']}/{dev['within_dev_pair_loo']['evaluated']} ({dev['within_dev_pair_loo']['accuracy']:.4%}); {dev['within_dev_pair_loo']['missing_pairs']} pairs have no remaining observation.
Within-dev mean-count LOO is **MISSING**: the wording-check `TASKS.jsonl` has comparison labels but no category counts for these 139 items. `DEV_S1_DIAGNOSTIC.json` records its exact path, missing fields, per-item predictions, and coverage. No synonym mapping or counts are invented.
These covered-item diagnostic accuracies are not full-dev accuracy or model results.

I read 40 complete question/option/target/answer/GT summaries: one unequal row and one tie per template, including ten reversed ties. `READ40.md` contains their exact full JSON rows.
Read commands: `sed -n '1,280p' out/READ40_TEXT.md` and `sed -n '281,560p' out/READ40_TEXT.md`.
`{cmd} code/review_binding.py` records the completed read, cross-family procedure check, and consolidated `CHECKS.json`.
`{cmd} code/package.py` checks declared input hashes and sample membership, writes this report, and verifies each archive member. Every output JSON records its input SHA-256 values; each row records its immediate source/code/selection/raster pins.
`code/run.sh` uses the local p1cpu Python, nice 10, and eight-thread OMP/MKL/OpenBLAS limits. No network, GPU, Git, store copy, or external writes are used.
Procedure authentication uses the pinned source example and source packet BUILD receipt. RGB/frame bytes, the production store, and training are outside this CPU packet.
Deliverables are `out/relative_count.jsonl`, its `.sha256`, `out/CHECKS.json`, `out/READ40.md`, `out/REPORT.md`, and `out/fbp_relcnt2.tar` with `.sha256`.
Check file receipts with `sha256sum -c out/relative_count.jsonl.sha256 out/fbp_relcnt2.tar.sha256`.
No-archaeology review: no borderline historical wording is retained; cap trials are the requested controlled comparisons.
'''
 assert len(report.splitlines())<=80
 (ROOT/'out/REPORT.md').write_text(report)
 status(f'The final {n}-row packet passes the 0.60 name-prior gates, all native row/trace/counting/packing checks, GT and identity checks, tie and letter balances, wording distance, and all five room exclusions. The forty-row manual read and frozen dev-S1 diagnostic are recorded; missing dev predictions remain explicit. The final report and verified archive are in out/. No production store is changed.')
 code_pins()
 dump(ROOT/'out/INPUT_CHECK.json',dict(status='PASS',input_sha256=dict(PINS),command='bash code/run.sh code/package.py',declared_input_hashes_verified=len(verified),exact_sample_members_verified=40))
 rowhash=sha(ROOT/'out/relative_count.jsonl');(ROOT/'out/relative_count.jsonl.sha256').write_text(rowhash+'  out/relative_count.jsonl\n')
 files.extend([Path('out/INPUT_CHECK.json'),Path('out/REPORT.md'),Path('out/relative_count.jsonl.sha256'),Path('STATUS.md')])
 files.extend(sorted(p.relative_to(ROOT) for p in (ROOT/'code').rglob('*') if p.is_file() and p.suffix in ('.py','.cpp','.so','.sh')))
 filehashes={str(p):sha(ROOT/p) for p in files}
 manifest=dict(input_sha256={str(ROOT/p):h for p,h in ((Path(k),v) for k,v in filehashes.items())},command='bash code/run.sh code/package.py',members={k:dict(sha256=v,bytes=(ROOT/k).stat().st_size) for k,v in filehashes.items()})
 dump(ROOT/'out/PACKAGE_MANIFEST.json',manifest);files.append(Path('out/PACKAGE_MANIFEST.json'))
 archive=ROOT/'out/fbp_relcnt2.tar'
 with tarfile.open(archive,'w') as tar:
  for rel in files:tar.add(ROOT/rel,arcname=str(rel),recursive=False)
 archivehash=sha(archive)
 with tarfile.open(archive,'r') as tar:
  members=tar.getmembers();assert len(members)==len(files)
  for member in members:assert hashlib.sha256(tar.extractfile(member).read()).hexdigest()==sha(ROOT/member.name),member.name
 result=dict(status='PASS',input_sha256={str(archive):archivehash,str(ROOT/'out/PACKAGE_MANIFEST.json'):sha(ROOT/'out/PACKAGE_MANIFEST.json'),str(ROOT/'code/package.py'):sha(ROOT/'code/package.py')},command='bash code/run.sh code/package.py',archive_bytes=archive.stat().st_size,members_verified=len(files),workspace_bytes=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file()),workspace_byte_cap=150_000_000,report_lines=len(report.splitlines()))
 assert result['workspace_bytes']<149_900_000
 dump(ROOT/'out/PACKAGE_CHECK.json',result)
 sums=archivehash+'  out/fbp_relcnt2.tar\n';(ROOT/'out/fbp_relcnt2.tar.sha256').write_text(sums);(ROOT/'out/SHA256SUMS.txt').write_text(rowhash+'  out/relative_count.jsonl\n'+sums)
 print(json.dumps(result));print('archive_sha256',archivehash)
if __name__=='__main__':main()
