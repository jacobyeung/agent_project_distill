"""Publish an explicit blocked delta and concise report; no tree/config mutation."""
import json,hashlib,csv
from pathlib import Path
W=Path(__file__).resolve().parent;O=W/'out'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):return dict(path=str(p),sha256=sha(p))
c=json.loads((O/'CENSUS.json').read_text());b=json.loads((O/'LOADER_BOUNDARY.json').read_text())
review=json.loads((O/'MANUAL_REVIEW.json').read_text())
assert review['checked']==40 and review['disagreements']==0
inputs={i['path']:i for i in c['inputs']}
for p in [O/'CENSUS.json',O/'READ40.md',O/'MANUAL_REVIEW.json',W/'finalize.py',W/'loader_boundary.py']:
 i=pin(p);inputs[i['path']]=i
chosen=c['analytical_options'][c['chosen_option']]
policy=dict(name=c['chosen_option'],status='PROPOSAL_ONLY_REQUIRES_TREE_CHANGE',
 scope='Within each direction or facing_pairs cell, reweight only toward-hard rows; keep all rows eligible.',
 weights=c['chosen_relative_weights'],other_rows_weight='1',normalization='Preserve each cell quota and its toward-hard total expected draws.',
 maximum_actual_draws_per_qid_per_1000_steps=4,
 target_toward_hard_back_share=.5,expected_away_hard_back_share=chosen['away_hard_back_share'],
 note='Weights describe an expectation. A finite schedule must enforce the hard repetition ceiling; random weighted sampling alone is insufficient.')
encoded=json.dumps(policy,sort_keys=True,separators=(',',':')).encode()
proposal_sha=hashlib.sha256(encoded).hexdigest()
missing=[dict(name='complete prepared draw population',expected_location='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24/inputs/population.json',status='MISSING: existing file has complete=false, after_all_filters=false and zero counts'),
 dict(name='complete prepared draw indices',expected_location='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24/inputs/indices.json',status='MISSING: bound indices are empty'),
 dict(name='production preparation receipt',expected_location='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/469ddece/receipt.json',status='MISSING: not supplied in the named local launch inputs; not searched elsewhere')]
delta=dict(schema='fbp-prior-delta-v1',status='TREE_CHANGE_REQUIRED',runnable=False,inputs=list(inputs.values()),tree_seal=c['tree_seal'],
 executable_delta='MISSING',config_fields_to_set='MISSING: no existing field expresses selective per-row weights or repeats',
 proposal=policy,proposal_sha256=proposal_sha,sha256_scope='Canonical sorted compact JSON serialization of proposal; full-file digest is in PRIOR_DELTA.json.sha256.',
 native_before_replay='MISSING',native_after_replay='MISSING',native_refusal=b['native_error'],missing_inputs=missing,
 smallest_change=[
  dict(file='student_pilot/r1_mix.py',lines='68-86, 95-97',change='Add an optional pinned finite per-cell draw-order input. Authenticate its population/index/card pins; verify every offset belongs to its existing eligible cell, each schedule length equals the allocated cell draws, and each (stream, offset) occurs at most four times across the whole schedule. Keep unique exhaustive population indices unchanged. At line 96 select the validated finite schedule entry rather than cycling the uniform pool.'),
  dict(file='student_pilot/r1_population.py',lines='120-130, 148-156',change='For an integrated producer, resolve the policy against actual filtered native rows and offsets, then pin the finite schedule into the returned sampling binding. This integration is needed if normal preparation would otherwise replace an externally prepared binding.'),
  dict(file='student_pilot/r1_loader.py',lines='55-59, 66-70, 101-105',change='Audit both direction and facing_pairs and retain separate cell identifiers; emit front/back shares per clause and difficulty from actual draws.'),
  dict(file='student_pilot/r1_direction_twins.py',lines='136-143',change='Correct the clause parser to recognize opposite-direction, back-to, turned-away, oriented/directed-toward, gaze/viewing, and ahead-reference phrasings. Do not infer clause from the answer.')],
 changes_applied=False,stopped_at_task_step=3)
(O/'PRIOR_DELTA.json').write_text(json.dumps(delta,indent=2)+'\n')
for name in ['PRIOR_DELTA.json','CENSUS.json']:
 (O/(name+'.sha256')).write_text(sha(O/name)+'  '+name+'\n')
base=c['expected_before'];opts=c['analytical_options']
pop={(g['clause'],g['difficulty']):g for g in c['source_population']}
exp={(g['clause'],g['difficulty']):g for g in base['clause_difficulty']}
lines=[
'# Vehicle N hard-direction prior',
'',
'**BLOCKED at task step 3.** The sealed loader cannot express selective row weights or repeats. No tree or launch config changed. `PRIOR_DELTA.json` is an explicit non-runnable proposal; native before/after draws are `MISSING`.',
'',
f"Tree seal: `{c['tree_seal']['tree_sha256']}`. The native sampler refuses N’s actual binding with `{b['native_error']}`. The bound population has `complete=false`, `after_all_filters=false`, and zero counts.",
'',
'Commands (run from this workspace; all numerical tables come from these scripts):',
'```bash',
'export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1',
'nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python census_source.py',
'nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python loader_boundary.py',
'nice -n 10 python analyze_prior.py',
'python manual_review.py',
'nice -n 10 python finalize.py',
'```',
'',
f"The source scan authenticated 204,413 v7 rows and 7,971 twins. All 12 launch removal lists apply, including n, z, the K1 union, and the 109-row naming list. It removed {c['source_counts']['removed']:,} rows; six additional relative-distance rows failed native text checks. Direction retains {c['direction_row_count']:,} rows: 55,808 in `direction` and 42,507 in `facing_pairs`.",
'',
'`READ40.md` contains 40 manually checked question/trace/option examples; all agree with the parser. Every hard forward relation also agrees with its clause/answer transform, and every twin preserves its source forward line and applies the expected answer half-turn. Source and code hashes appear in every output JSON.',
'',
'Row census and expected draws per 1,000 steps (expectations over the native shuffle, **not realized seed-17 loader counts**):',
'',
'| Clause / difficulty | Rows | Front % | Back % | Expected draws | Draw back % |',
'|---|---:|---:|---:|---:|---:|']
for key,g in sorted(pop.items()):
 e=exp[key];s=g['answer_sides'];es=e['answer_sides']
 lines.append(f"| {key[0]} / {key[1]} | {g['amount']:,.0f} | {100*s.get('front',{}).get('share',0):.3f} | {100*s.get('back',{}).get('share',0):.3f} | {e['amount']:,.3f} | {100*es.get('back',{}).get('share',0):.3f} |")
lines += ['',
'Easy rows are lateral; medium rows also carry lateral relations. `CENSUS.json` includes all answer labels and stated forward relations. The card allocates 36,866 direction draws and 18,170 facing-pair draws, within 128,000 VQA and 288,000 total draws. Other-stream quota feasibility is not newly proven here.',
'',
'Options keep every row eligible and preserve card-cell quotas. (a)/(b) assign the stated actual draw counts to selected rows and distribute the remaining quota uniformly. (c) and the chosen policy normalize relative weights within each cell. These are analytical expectations; a finite sampler must enforce the hard cap.',
'',
'| Option | Toward-hard back % | Away-hard back % | Total draws |',
'|---|---:|---:|---:|']
labels={'baseline':'Before','a_cap4':'(a) Behind rows: four actual draws','b_sources_twice':'(b) 2,000 source rows: two actual draws','b_sources_cap4':'2,000 source rows: four actual draws','a_plus_b_cap4':'(a)+(b), capped at 4','c_front_downweight':'(c) Down-weight front to balance','chosen_balance_preserve_mass':'Chosen: balanced, same toward-hard mass'}
for key,label in labels.items():
 o=opts[key];lines.append(f"| {label} | {100*o['toward_hard_back_share']:.3f} | {100*o['away_hard_back_share']:.3f} | {o['total_draws_per_1000_steps']:,} |")
lines += ['',
'For the chosen option, back/front weights are '+ '; '.join(f"`{f}`: `{v['back']}` / `{v['front']}`" for f,v in c['chosen_relative_weights'].items())+'. Other rows retain weight 1. Each cell’s toward-hard mass stays constant, so every other clause/difficulty draw total and answer share stays unchanged. The target is 50%, independent of dev truth shares.',
f"The largest modeled direction-row expected draw count is {chosen['max_expected_draws_per_row']:.6f}, below four. This is not a realized-cap proof. `CENSUS.json` lists every option’s effects on all six clause/difficulty groups and every card cell. (a)+(b) cannot add copies beyond four: the 2,000 sources are a subset of (a).",
'',
'Drawing the 2,000 sources twice means two actual draws per source, not multiplying their baseline expected dose by two. This distinction supports the analyst’s roughly 30% estimate. The quoted 71.8% away-hard share precedes removals and ignores the two cell draw rates.',
'',
'Exact ceiling and selection code:', '',
'- `student_pilot/r1_mix.py:27`: `totals = {k: min(n, 4*counts[k]) for k, n in requested.items()}`.',
'- `student_pilot/r1_loader.py:92-93`: `if max(repeats.values(), default=0) > 4:` then `raise ValueError(\'R1_REPEAT_LIMIT_EXCEEDED\')`.',
'- `r1_mix.py:76-79` rejects duplicate population offsets; `83-84` requires full coverage. `81-82` shuffles once, and `96` selects `pool[consumed[kind] % len(pool)]`. No per-row weight is read.',
'',
'The smallest sampler change is an authenticated finite per-cell draw schedule in `r1_mix.py:68-86,95-97`, with unchanged eligible indices, exact cell quotas, and a per-row cap of four. Normal preparation also needs to bind it at `r1_population.py:148-156`. `PRIOR_DELTA.json` identifies those edits; none were applied.',
'',
f"The loader audit omits `facing_pairs` and its clause parser disagrees on {sum(c['native_clause_disagreements'].values()):,} source rows. Fix `r1_loader.py:55-70,101-105` and `r1_direction_twins.py:136-143` before reporting a balanced result.",
'',
'`MISSING`: complete `w24/work/build24/inputs/population.json` and matching `indices.json` (the supplied files are placeholders), plus production `.../ap/8865619b/f/469ddece/receipt.json`. Exact absolute paths appear in `PRIOR_DELTA.json`. No mappings, manifests, scene lists, or production proofs were invented.',
'',
'Artifacts: `CENSUS.json`, `PRIOR_DELTA.json`, `READ40.md`, source evidence, scripts, and input hashes are packaged by `python package_outputs.py` into `fbp_prior.tar`; `fbp_prior.tar.sha256` records its digest.']
assert len(lines)<=80,len(lines)
(O/'REPORT.md').write_text('\n'.join(lines)+'\n')
(W/'STATUS.md').write_text('Final stage: Completed the authenticated source census, 40-row manual parser review, and ceiling-bounded analytical option comparison. The mass-preserving proposal targets 50% toward-hard back answers while preserving all other draw totals and shares. The native loader refused its actual incomplete launch population and has no per-row weight/repeat interface, so the requested production before/after verification and executable delta are MISSING. Stopped at task step 3 without changing the tree, as instructed; report and non-runnable delta are ready for packaging.\n')
print('REPORT lines',len(lines),'proposal sha256',proposal_sha)
