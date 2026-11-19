"""Local provenance, explicit pending bindings, and GPU requirements."""
from common import *
import budget,difflib

def main():
 pins();spec=ROOT/'inputs/KIT_SPEC_object_route_r0dev_v2.md';sha(spec)
 pack=Path('/scratch/jjyeung/n30_mirror/sb_headacc2/pack')
 manifest={n.removeprefix('./'):h for h,n in (line.split() for line in read(ROOT/'inputs/pack/MANIFEST.sha256').decode().splitlines())}
 checked=[];edits=[];patch=[]
 for rel,h in manifest.items():
  if rel.startswith('r1_src/b/e2e_reader/') or rel.startswith('r1_src/tree/'):
   source=pack/rel;assert sha(source)==h
   target=ROOT/'code/vendor'/rel.removeprefix('r1_src/b/').removeprefix('r1_src/tree/')
   if not target.exists():continue
   before=read(source).decode().splitlines(True);after=read(target).decode().splitlines(True)
   spans=[]
   for tag,i,j,a,b in difflib.SequenceMatcher(a=before,b=after).get_opcodes():
    if tag!='equal':spans.append(dict(kind=tag,original_lines=[i+1,j],copied_lines=[a+1,b]))
   checked.append(dict(source=str(source),source_sha256=h,copy=str(target),copy_sha256=sha(target),equal=before==after))
   if spans:edits.append(dict(path=str(target.relative_to(ROOT)),spans=spans));patch+=list(difflib.unified_diff(before,after,fromfile=str(source),tofile=str(target)))
 tree=Path('/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449')
 for name in ('scene_state.py','geometry_profiles.py','tower_read.py'):
  source=tree/'student_pilot'/name;target=ROOT/'code/vendor/student_pilot'/name
  before=read(source).decode().splitlines(True);after=read(target).decode().splitlines(True);spans=[]
  for tag,i,j,a,b in difflib.SequenceMatcher(a=before,b=after).get_opcodes():
   if tag!='equal':spans.append(dict(kind=tag,original_lines=[i+1,j],copied_lines=[a+1,b]))
  if spans:edits.append(dict(path=str(target.relative_to(ROOT)),spans=spans));patch+=list(difflib.unified_diff(before,after,fromfile=str(source),tofile=str(target)))
  checked.append(dict(source=str(source),source_sha256=sha(source),copy=str(target),copy_sha256=sha(target),equal=before==after))
 write(ROOT/'out/SOURCE_VERIFICATION.json',dict(status='PASS',files=checked))
 write(ROOT/'out/EDITED_LINES.json',dict(comparison='Pinned R1 pack source to copied tree',files=edits));(ROOT/'out/EDITED_LINES.patch').write_text(''.join(patch))
 hook_path=ROOT/'config/KBOX_RULES_HOOK.json'
 sibling=Path('/scratch/jjyeung/orch_n30/sb_kbox2')
 decision=sibling/'out/box_ladder/DECISION.json';d=js(decision)
 write(hook_path,dict(status='MISSING',module_path=str(sibling/'box_math.py'),module_sha256=sha(sibling/'box_math.py'),receipt_path=str(decision),receipt_sha256=sha(decision),replay_path=str(sibling/'out/box_ladder/REPLAY_CHECK.json'),required_interface=['gather','fusion_box','count_objects','object_source','stage1_replay','price_k1_tracks'],reason='Sibling training rule/screens are MISSING; its deployed replay gate has not passed',expected_normalized_decision=str(ROOT/'inputs/KBOX_DECISION.json')))
 bars={typ:dict(type_points=v,ci95_lower_gt=0) for typ,v in __import__('registration').CATEGORIES.items()}
 write(ROOT/'config/BARS.json',dict(version=2,selection_split='K1-train',heldout='report-only',R0_comparisons_per_category=1,form='fallback',geometry='g3t_s4',treatment='S4 treatment',bars=bars,gates={'object_abs_distance':['replace_box_both_parts'],'object_size_estimation':['replace_box_both_parts','size_screen','s4_size_treatment_ci95_lower_gt_minus_2'],'object_rel_distance':['replace_box_both_parts'],'obj_appearance_order':['K1_first_seen_pair_rate_ge_0.90']},track='K1 only: paired lower bound >0 under the same box rule',T94='K1 tower views_pay only; R0 absolute distance only',counting='dev-S1 diagnostic only',context='none',bootstrap=dict(draws=10000,seed=20261119,unit='room',estimate='item weighted')))
 steps=[]
 for group in budget.BUDGETS:
  steps.append(dict(part=group,cards=1,memory_gib=48,estimated_gpu_hours=budget.ESTIMATES[group],hard_stop_hours=budget.BUDGETS[group]/3600,commands=['bash scripts/gpu_'+s+'.sh' for s,g in budget.GROUPS.items() if g==group],cumulative_shared_between_commands=True,measured_peak_memory='MISSING'))
 write(ROOT/'out/GPU_NEED.json',dict(status='NOT_RUN',cards=1,memory_gib=48,steps=steps,order=list(budget.BUDGETS),total_three_kit_cap_gpu_hours=16,admission='other kits seconds + local used + remaining part stop <=16h; pinned exclusive ledger lease',ledger_path=str(budget.LEDGER),cut_order=['dev-S1 diagnostics including its tracker','track size/relative work only before primary freeze','94-frame work only before primary freeze'],frozen_arm_policy='Do not alter frozen arms to fit a budget; skip the complete category and keep its look unspent',resume='Skip DONE units only after validating binding and every output SHA256; interrupted budget needs review',GPU_hours_used=0))
 blockers=[dict(path=str(hook_path),why='Box rule, screens, object grouping and stage-1 sibling parity are unbound'),dict(path=str(ROOT/'inputs/TOWER_DECISION.json'),why='K1 32-frame treatment/replace_box and views_pay decision not supplied'),dict(path=str(ROOT/'out/object_route/K1_TRACK_CHOICE.json'),why='K1 GPU track pass and paired pricing have not run'),dict(path=str(ROOT/'inputs/K1_TRACK_EVIDENCE.json'),why='Paired 1037-row track/linker evidence and first-seen GT pairs require the sibling geometry/object adapter'),dict(path=str(ROOT/'inputs/DEVS1_STAGING_PLAN.json'),why='REQUEST.json pins a plan hash but names no plan; no item/frame binding may be inferred'),dict(path=str(budget.LEDGER),why='Shared 16h ledger and exclusive launch lease not staged; no GPU work authorized in this task')]
 write(ROOT/'out/READINESS.json',dict(status='MISSING',blockers=blockers,CPU_dry_run_separate=True))
 write(ROOT/'out/object_route/K1_TRACK_CHOICE.json',dict(status='MISSING',selection_split='K1-train',reason='K1 tracker pass not run',box_source=None,expected_evidence_path=str(ROOT/'inputs/K1_TRACK_EVIDENCE.json')))
 write(ROOT/'out/object_route/ROUTE_TABLE.json',dict(status='MISSING',rows=[dict(category=t,status='MISSING',reason='PRIMARY_ARMS awaits completed K1 decisions',treatment='S4 treatment',read_spent=False) for t in bars]))
 (ROOT/'out/object_route/ROUTE_TABLE.txt').write_text('All four category reads remain unspent; PRIMARY_ARMS awaits completed K1 decisions.\n')
 status('Stage 2 complete: v2 source joins, scorer, frozen-arm and one-look enforcement, K1 tracker job selection, budgeted GPU scripts and explicit sibling hooks are prepared. Inputs and missing evidence are recorded in out/READINESS.json; no GPU ran.')
if __name__=='__main__':main()
