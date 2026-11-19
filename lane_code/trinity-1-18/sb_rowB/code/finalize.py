"""Summarize checks and package the partial, explicitly unadmitted deliverable."""
import argparse,tarfile
from common import *

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--reviewed-read30',action='store_true',required=True);args=parser.parse_args()
 b=load(ROOT/'out/BUILD_COUNTS.json');c=load(ROOT/'out/CENSUS.json');checks=load(ROOT/'out/CHECKS.json');scope=load(ROOT/'out/STORE_SCOPE.json')
 assert checks['status']=='PARTIAL_BLOCKED'
 checks['tests']['read30']='PASS_AGENT_READ_30_QUESTIONS_OPTIONS_TRACES_AND_GT'
 checks['read30_review']=dict(rows=30,scope='All 30 complete serialized rows are printed in READ30.md; the agent read each question, options, trace, GT distances/order and camera-relative coordinates. No RGB pixels were read.',findings='All references use k, comparisons follow GT, answer letters match options. Behind-camera positions are expressed relative to the queried pose without asserting visibility. Numeric drafts remain unadmitted.',read30_sha256=sha(ROOT/'out/READ30.md'))
 checks['input_sha256'][str(ROOT/'out/READ30.md')]=sha(ROOT/'out/READ30.md');checks['input_sha256'][str(ROOT/'code/finalize.py')]=sha(ROOT/'code/finalize.py')
 dump(ROOT/'out/CHECKS.json',checks)
 missing=lines(ROOT/'out/MISSING_GT.jsonl');by={}
 for r in missing:
  h=r['expected_sha256'];v=by.setdefault(h,dict(original_path=r['original_path'],expected_mirror_path=r['expected_mirror_path'],expected_sha256=h,rows=0,status='MISSING'))
  v['rows']+=1
 dump(ROOT/'out/MISSING_RASTERS.json',dict(input_sha256={str(ROOT/'out/MISSING_GT.jsonl'):sha(ROOT/'out/MISSING_GT.jsonl')},rasters=list(by.values()),count=len(by)))
 report=['# sb_rowB: camera-object distance at frame k',
 '**PARTIAL — no replacement satisfies both the requested numeric trace and N’s pinned direct grammar.**',
 'REPLACEMENTS.jsonl is empty. REBUILT_NUMERIC_UNADMITTED.jsonl contains 4,667 requested numeric reconstructions; every one fails N’s direct grammar.',
 'GRAMMAR_COMPATIBLE_ALTERNATIVE.jsonl contains 4,667 distinct-qid alternatives that reason at k, express position and distance comparisons in words, and preserve numeric GT in provenance. They require a choice to relax the numeric-trace requirement.',
 'The sealed w19 tree is used: 8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa. Used validator files match TREE_SEAL.json.',
 '',
 '| Family | Rows | Any object outside k | Any object at k | No object at k | All objects at k |',
 '|---|---:|---:|---:|---:|---:|']
 for f,wordings in c['families'].items():
  v=next(iter(wordings.values()));report.append('| '+f+' | '+' | '.join(str(v[k]) for k in ['rows','cites_other','cites_k','none_at_k','all_at_k'])+' |')
 report += [
 '“Any at k” and “outside k” overlap on mixed rows. The camera sentence does not count as an object citation.',
 'Each camera family has one wording: “Measuring from the closest point of each object, which of these objects ({objects}) is the closest to the camera in frame {k} of 32?”',
 'The near/far wording is “In frame {k} of 32, relative to the camera, is {a} [Near/Far] compared to {b}?”',
 'CENSUS.json gives each wording’s counts and object-citation counts. EXAMPLES.md prints 20 examples per nonempty large class; all-at-k classes have only 1, 3, 15 and 15 examples, respectively.',
 'STORE_SCOPE.json scans all 204,413 rows. Its two extra lexical matches name a physical camera and a window frame; neither asks about the camera at k.',
 '',
 '| Family | GT recomputed | GT missing | Defective rows with missing GT | Existing N exclusion | Numeric drafts / qualitative alternatives |',
 '|---|---:|---:|---:|---:|---:|']
 for f,v in b['cells'].items():report.append('| '+f+' | '+' | '.join(str(v[k]) for k in ['gt_recomputed','gt_missing','needs_retrace_gt_missing','already_in_n_removal','numeric_drafts'])+' |')
 report += [
 'All 4,781 recomputed answers and stored distance values agree with GT. The evidence establishes a trace-location problem; it does not establish incorrect training labels.',
 'The generator uses camera-centre-to-closest-GT-OBB distance, not object-centre distance. Pose index k−1 maps to the store’s one-based frame k; source frame_indices are checked exactly.',
 'GT matches 693 of 1,000 source raster hashes in B12_MIRROR_20261116T1631Z.tar and old_lanes_3_30_a.tar. The mirror’s 96 archives and extracted NPZ names were searched.',
 'MISSING_RASTERS.json names all 307 missing rasters and exact expected hashes; MISSING_GT.jsonl names all 3,151 affected source rows, including 3,146 needing retracing. No missing geometry was inferred.',
 'No selected source hits K1-heldout, R0, withheld-80, dev-S1 or BENCH v2 rooms. The 85 existing n.json removals remain excluded; no new qid bypasses that filter.',
 '',
 'CHECKS.json records independent recomputation from original archive arrays, exact family capacities, unique qids/candidate_ids, unchanged questions, restricted field diffs, room rules and removal consumption.',
 'Native direct intake uses r2_adapters.normalize + r2_contract.validate(vqa), plus trace_grammar.validate_row: all 7,932 sources and 4,667 alternatives pass. ground_rows.pack is for routed event rows, not this direct schema.',
 'Numeric drafts fail number_not_allowed, unit_quantity, angle_or_coordinate and number_word. No validator was edited, no tool response was fabricated, and no numeric draft was admitted.',
 'Each source appears once per variant; the two variants are mutually exclusive. Candidate IDs use N’s candidate_identity formula with the new qid and unchanged question. QID_MAP.jsonl maps both variants to each source.',
 'New question wordings: 0. Normalized edit-distance filtering is not applicable (threshold N/A; removed 0) because every question and option is unchanged; no dev/benchmark wording supplied a new question.',
 'REMOVE.json uses exactly n.json’s five-field JSONL schema: pool, question_type, reason, row_key, scene. Its 7,898 keys cover every defective source, including missing-GT rows; removal alone therefore shrinks the population.',
 'REMOVE.json stores input hashes inside reason to retain the exact schema. Other JSON/JSONL outputs carry input hashes or bound provenance.',
 'READ30.md prints 30 complete alternative rows. The agent checked all 30 questions, options, traces and GT values. RGB images were not read.',
 '',
 'Commands (run from the workspace with /scratch/jjyeung/envs/p1cpu/bin/python -B and OPENBLAS_NUM_THREADS=1):',
 '- code/inventory.py: store hash, family/wording/citation counts, examples and GT candidate inventory.',
 '- code/audit_store_scope.py: full-store search and family scope.',
 '- code/prepare_gt.py: archive/source hashes and raw GT-array extraction.',
 '- code/build_rows.py: all per-cell generation/refusal counts, variants, qid mapping and REMOVE.json.',
 '- code/check_rows.py: independent raw-GT recomputation, adapter/validator checks and CHECKS.json.',
 '- code/finalize.py --reviewed-read30: report, manifest, tar and SHA256SUMS.',
 '',
 'Not done: numeric traces cannot pass the unchanged direct grammar; 307 GT rasters are missing; no training, GPU, network, RGB loading or external writes ran.',
 'The viable choices are to accept the qualitative alternatives or authorize a compatible grammar/routed-family change in N. The present package changes neither N’s tree nor its binding.',
 'Reader-first report review: no revision-history sentences were retained.'
 ]
 assert len(report)<=80
 (ROOT/'out/REPORT.md').write_text('\n'.join(report)+'\n')
 (ROOT/'STATUS.md').write_text('Final stage: The package contains the census, full examples, exact-schema removal list, independently verified GT evidence, 4,667 unadmitted numeric drafts and 4,667 grammar-compatible qualitative alternatives. All 30 review rows were read. CHECKS.json reports PARTIAL_BLOCKED: no numeric replacement can pass the pinned direct grammar, and 307 rasters are missing. REPLACEMENTS.jsonl is intentionally empty. REPORT.md documents the exact counts, commands and remaining decisions.\n')
 included=[p for directory in ['code','inputs','out'] for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.tar'] and p.name not in ['ARTIFACT_MANIFEST.json','SHA256SUMS']]
 included += [ROOT/'STATUS.md',ROOT/'reference/coverage_rows_v2.py',ROOT/'reference/check_cov_v2.py']
 manifest=dict(input_sha256={str(ROOT/'out/CHECKS.json'):sha(ROOT/'out/CHECKS.json'),str(ROOT/'out/BUILD_COUNTS.json'):sha(ROOT/'out/BUILD_COUNTS.json'),str(ROOT/'code/finalize.py'):sha(ROOT/'code/finalize.py')},status='PARTIAL_BLOCKED',files={str(p.relative_to(ROOT)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(included)})
 dump(ROOT/'out/ARTIFACT_MANIFEST.json',manifest);included.append(ROOT/'out/ARTIFACT_MANIFEST.json')
 archive=ROOT/'out/sb_rowB.tar'
 with tarfile.open(archive,'w') as t:
  for p in sorted(included):t.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
 h=sha(archive);(ROOT/'out/SHA256SUMS').write_text(h+'  sb_rowB.tar\n')
 print(json.dumps(dict(archive=str(archive),sha256=h,bytes=archive.stat().st_size,report_lines=len(report)),indent=2))
if __name__=='__main__':main()
