"""Merge audit results, write the <=80-line report, and package reviewed artifacts."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;O=ROOT/'out';L=ROOT/'out_locate'
def load(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def dump(p,x):p.write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
def main():
 c=load(O/'CHECKS.json');lc=load(L/'CHECKS.json');ind=load(O/'INDEPENDENT_CHECKS.json');li=load(L/'INDEPENDENT_CHECKS.json');tests=load(O/'CONTRACT_TESTS.json')
 assert ind['status']==li['status']==tests['status']=='PASS'
 assert c['eligible_rows']==lc['eligible_rows']==17564
 assert c['eligible_cells']==lc['eligible_cells']=={'single':8404,'multiple':9160}
 assert c['input_sha256']['convert_rows.py']==lc['input_sha256']['convert_rows.py']==sha(ROOT/'convert_rows.py')
 assert tests['input_sha256']['convert_rows.py']==sha(ROOT/'convert_rows.py')
 review=load(O/'READ30_REVIEW.json');assert review['status']=='PASS' and review['rows_reviewed']==30 and review['input_sha256']['READ30.md']==sha(O/'READ30.md')
 c['independent_checks']={'status':'PASS','input_sha256':{'INDEPENDENT_CHECKS.json':sha(O/'INDEPENDENT_CHECKS.json')},'counts':ind['counts']}
 c['contract_tests']={'status':'PASS','input_sha256':{'CONTRACT_TESTS.json':sha(O/'CONTRACT_TESTS.json')},'test_count':len(tests['tests'])}
 c['read30_review']={'status':'PASS','input_sha256':{'READ30_REVIEW.json':sha(O/'READ30_REVIEW.json')},'rows_reviewed':30}
 c['alternate_locate']={'rows':lc['eligible_rows'],'validation':lc['validation'],'counting_admission_errors':lc['counting_admission_errors'],'input_sha256':{'CHECKS.json':sha(L/'CHECKS.json'),'INDEPENDENT_CHECKS.json':sha(L/'INDEPENDENT_CHECKS.json'),'rows.jsonl':sha(L/'rows.jsonl')},'source_reuse':'At most once per invocation/form; both artifacts are alternatives, not a concatenated training set.'}
 c['exact_cell_assertions']={'mechanical':{'single':8678,'multiple':9201},'eligible':{'single':8404,'multiple':9160},'refusals':{'MISSING_independent_instance_annotations':84,'excluded_room_k1_heldout':228,'MISSING_canonical_room_mapping':3}}
 c['required_checks_status']='BLOCKED_UNCHANGED_N_TALLY_GRAMMAR_AND_COUNTING_ADMISSION; arithmetic, provenance, room, field, ID, coverage checks PASS'
 c['input_sha256']['finalize_kit.py']=sha(Path(__file__))
 dump(O/'CHECKS.json',c)
 h=load(O/'TRUTH_HISTOGRAM.json');hist=h['row_truth'];lines=[
 '# Counting conversion kit',
 '',
 'The kit contains 17,564 TALLY rows: 8,404 single-category and 9,160 multiple-category rows. The same sources can be emitted with `--form locate` (17,564 rows). The alternatives must not be concatenated.',
 'All 17,879 removed lists convert mechanically: 8,678 single-category and 9,201 multiple-category. The kit refuses 315 rows: 228 K1 held-out, 84 without independent instance annotations, and 3 without a canonical room mapping. `REFUSALS.jsonl` lists every qid and reason.',
 'Source: pinned store v7, SHA256 210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443; removal reason `count_diag_first_seen_list_form` in z.json. W/w19 is the newer sealed kit; tree seal 8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa.',
 '',
 '| Eligible source pool | Rows |',
 '|---|---:|',
 ]
 for pool,n in sorted(ind['pools'].items()):lines.append(f'| {pool} | {n} |')
 lines+=['','| Final truth | Rows | Single | Multiple |','|---|---:|---:|---:|']
 for key in [str(i) for i in range(10)]+['10+']:lines.append(f'| {key} | {hist[key]} | {h["by_cell"]["single"][key]} | {h["by_cell"]["multiple"][key]} |')
 lines += [
 '',
 f'{sum(v for k,v in hist.items() if k not in ("0","1","2")):,} eligible rows have truth at least 3. Truth means the final stored answer; multi-category rows contribute once. Category totals and frame counts are recorded separately in QID_MAP.jsonl and the target.',
 'Every admitted row passes independent instance-ID/frame recomputation, source-region preservation, ordered frames in 1..32, asked-category coverage, category sums, final sum, field-diff checks, and qid/candidate uniqueness. The kit candidate_identity formula uses the new qid and unchanged question. Each source appears once per form.',
 f'The independent audit covers {ind["counts"]["instances"]:,} annotated instances across {ind["counts"]["category_inventories"]:,} category inventories. {ind["counts"]["region_tagged_rows"]:,} rows retain region tags. No raster or image was read; this checks annotated labels, not visual truth.',
 'Rooms: the pinned K1, R0, withheld-80, dev-S1, and BENCH v2 authorities exclude held-out rooms. Unresolved rooms are refused. Additional aliases come only from stored canonical/raster fields whose native scene reproduces the pinned token hash; `inputs/scene_facts.json` records the source qid and field.',
 'Questions, answers, images, and all source fields except qid, candidate_id, target, and provenance.sb_rowT stay identical. The 30 full rows in READ30.md were read for category coverage, grammar, arithmetic, and region counts; all pass the proposed TALLY specification. Inherited question morphology such as shoes(s) stays unchanged.',
 'Wording: Unicode NFKC + casefold + whitespace normalization; Levenshtein/max length threshold <=0.10. All 117 question/prompt wordings found across 42 sealed-kit/fixture files screen each newly authored trace body; 0 rows removed. No new question wording is generated. This does not certify absent external evaluation corpora; see MISSING.md.',
 '',
 f'Current N validation: all {c["eligible_rows"]:,} source rows pass native direct-row validation and trace grammar; all {c["eligible_rows"]:,} TALLY rows fail that unchanged grammar. `ground_rows.pack` refuses both direct sources and new rows with KeyError suffix; it is a program-only API, not the direct-store packer. No ground_record is fabricated.',
 f'Locate alternative: native passes {lc["validation"].get("new_native_validate_pass",0):,}; lexical grammar passes {lc["validation"].get("new_trace_grammar_pass",0):,}. Counting admission still rejects both alternatives: the gate requires procedure wording and bans totals. No claim that all requested trainer checks pass is made.',
 'TRACE_RULE_AMENDMENT.md supplies the exact proposed rule and required validator/admission changes. The kit keeps the current trainer unchanged. Its status is KIT ONLY, pending the orchestrator amendment and a fresh native admission check.',
 '',
 'Reproduction commands (run from this workspace with local Python >=3.10):',
 '```sh',
 'PY=/scratch/jjyeung/envs/p1cpu/bin/python',
 'gcc -O2 -shared -fPIC ned_filter.c -o ned_filter.so',
 '$PY -B prepare_inputs.py',
 '$PY -B convert_rows.py',
 '$PY -B convert_rows.py --form locate --out out_locate',
 '$PY -B check_rows.py',
 '$PY -B check_rows.py --out out_locate',
 '$PY -B test_contract.py',
 '$PY -B finalize_kit.py',
 'sha256sum out/sb_rowT.tar',
 '```',
 'prepare_inputs.py produces source counts and input hashes; convert_rows.py produces every cell/refusal/histogram/validator count; check_rows.py independently produces the instance, region, source-pool, and coverage counts; test_contract.py produces the 10 mutation/distance checks. Human READ30 review is recorded separately and must be repeated if its bytes change.',
 'The archive includes the extracted source rows and audit inputs. The generator imports the sealed W/w19 tree at the path in inputs/INPUTS.json; rerunning prepare_inputs.py additionally requires the pinned external v7 store. No trainer tree is modified or bundled.',
 'Not done: trainer edits, training, GPU work, image/raster verification, and external evaluation-item staging. No network, SSH, Git, process termination, or file deletion was used.',
 'Writing review: no borderline revision-history sentences retained.',
 ]
 assert len(lines)<=80,len(lines);(O/'REPORT.md').write_text('\n'.join(lines)+'\n')
 (ROOT/'STATUS.md').write_text('Complete as a kit: 17,564 rows per alternative, 315 explicit refusals, independent checks and 30-row review passed. W/w19 native source validation passes; TALLY grammar and counting admission require the amendment in out/TRACE_RULE_AMENDMENT.md. All requested artifacts are under out; no training or trainer changes were made.\n')
 code=['prepare_inputs.py','convert_rows.py','check_rows.py','test_contract.py','finalize_kit.py','ned_filter.c','ned_filter.so','STATUS.md']
 inputs=['INPUTS.json','removed_rows.jsonl','source_ids.json','scene_facts.json','wording_corpus.json','z.json','TREE_SEAL.json','component_rows.json','split.json','reserve.json','aliases.json','build.json','visits.json','withheld.json','dev.json','bench.json','R1_M200_TRACE_ANALYSIS_20261119.md','COVERAGE_V2_PUB.tar','coverage_rows_v2.py','check_cov_v2.py']
 outfiles=['rows.jsonl','QID_MAP.jsonl','REFUSALS.jsonl','CENSUS.json','CHECKS.json','INDEPENDENT_CHECKS.json','CONTRACT_TESTS.json','TRUTH_HISTOGRAM.json','TRUTH_HISTOGRAM.tsv','READ30.md','READ30_REVIEW.json','REPORT.md','TRACE_RULE_AMENDMENT.md','MISSING.md']
 locfiles=['rows.jsonl','QID_MAP.jsonl','REFUSALS.jsonl','CENSUS.json','CHECKS.json','INDEPENDENT_CHECKS.json','TRUTH_HISTOGRAM.json','TRUTH_HISTOGRAM.tsv','READ30.md']
 members=code+['inputs/'+s for s in inputs]+['out/'+s for s in outfiles]+['out_locate/'+s for s in locfiles]
 with tarfile.open(O/'sb_rowT.tar','w') as tar:
  for name in sorted(members):
   info=tar.gettarinfo(str(ROOT/name),arcname=name);info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=''
   with (ROOT/name).open('rb') as f:tar.addfile(info,f)
 digest=sha(O/'sb_rowT.tar');(O/'sb_rowT.tar.sha256').write_text(digest+'  sb_rowT.tar\n')
 dump(O/'DELIVERY.json',{'input_sha256':{name:sha(ROOT/name) for name in members},'archive':{'path':'out/sb_rowT.tar','sha256':digest,'bytes':(O/'sb_rowT.tar').stat().st_size},'report_lines':len(lines),'status':c['status']})
 print(json.dumps({'archive_sha256':digest,'report_lines':len(lines),'rows_per_form':17564,'refused':315}))
if __name__=='__main__':main()
