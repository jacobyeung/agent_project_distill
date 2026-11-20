import sys,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
p=J.load(D/'P_DRY_COUNT.json');n=J.load(D/'N_DRY_COUNT.json');delta=J.load(D/'CONFIG_DELTA.json')
alias={'appearance':'appearance_order','box':'box_3d','camera_absolute_distance':'camera_object_abs_distance','facing':'facing_pairs','first_seen':'first_seen_frame','room':'room_size','route':'route_planning','size':'object_size','camera_obj_rel_dist_v1':'camera_object_rel_distance_v1','camera_obj_rel_dist_v2':'camera_object_rel_distance_v2','camera_obj_rel_dist_v3':'camera_object_rel_distance_v3','obj_obj_relative_pos_lr':'object_object_left_right','obj_obj_relative_pos_nf':'object_object_near_far','obj_obj_relative_pos_ud':'object_object_up_down'}
P={s+'/'+alias.get(k,k):v for name,v in p['counts'].items() for s,k in [name.split('/')]}
N=n['counts'];rows=[]
for c in delta['card_after']['cells']:
 s,k=c['stream'],c['type'];key=s+'/'+k;a=P.get(key,0);b=N.get(key,0)
 reason='Same configured draw rate; no difference.';status='UNCHANGED'
 if k=='room_size':reason='ORCH 0511Z restores P 1.70; ORCH 0418Z item 4 retains SCENE_room 294 + T0_room 65 + T1H1_room 66 = 425 VQA rows.'
 elif k in ('counting','direction'):
  status='ATTRIBUTED'
  reason='K1 union 1c7c930d (includes 43853165): counting population 2617 to 2571; four-repeat cap lowers 10.460 to 10.284 and returns 0.176 to direction. Native 200-step rounding makes the observed difference '+('−' if k=='counting' else '+')+'0.175. ORCH 0511Z returns the 1.70 room allocation from direction.'
 elif a!=b:
  status='UNATTRIBUTED'
  reason='UNATTRIBUTED rate change: existing routing_slices=deferred_first_boundary/card c0167f68 replaces P family quotas with routing_base=64. ORCH 0418Z items 3/5 explain membership, but no supplied ruling fixes the resulting per-type rates. Zero here means no separate allocation cell.'
 rows.append(dict(stream=s,family=k,P_rows_per_step=a/200,N_rows_per_step=b/200,difference=(b-a)/200,P_rows_first_200=a,N_rows_first_200=b,attribution=status,explanation=reason))
assert sum(r['P_rows_first_200'] for r in rows)==sum(r['N_rows_first_200'] for r in rows)==57600
J.write(D/'N_FINAL_CONFIG.json',J.load(kit('n_go')/'k/c.json'));J.write(D/'N_FINAL_CARD.json',delta['card_after'])
for name in ('SELECTION_TABLE.md','SELECTION_TABLE.json'):
 p0=W/'work/sel24'/name;dest=D/'evidence'/name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(p0.read_bytes())
method={
 'steps':'Optimizer steps 1–200, sampler start_step=0, seed=17, world=4; 57,600 global rows per vehicle.',
 'P':'Authenticated config b08fe50c and preparation a5bbef1b/type_mix_population 736344f3; unmodified P type_mix.bound and carrier_c1_data.mixed_indices/type_mix.plans from the packaged P tree.',
 'N':'Final card; unmodified C r1_mix.allocate and r1_mix.plans over card-configured ceiling counts and synthetic disjoint indices. Only validate_binding is replaced with that dry input tuple. No production population or admission receipt is asserted.',
 'N_counts':n['counts_basis'],
 'routing':'Rows are plan allocation families. N routing_base=64 contains native routing types whose post-preparation membership and 200-step split are unknown; separate N routing type cells are zero, not proven zero underlying draws. P units is an admitted 683-row population at 1.00/step; N auxiliary units remains deferred.',
 'room':'room_size is the VQA family name for 425 room_size_estimation rows; SCENE_room/T0_room/T1H1_room partition those same 425 rows and are not an additional population.',
 'limit':'A dry configured-plan count is not a production loader audit. Missing native production rows can change capped allocation or refuse the job; the unchanged row_check still enforces room trace grammar.',
 'six_row_gap':'N relative_distance ceiling implies 19,827 rows versus list census 19,833: UNATTRIBUTED population gap. It does not affect the configured 22.74 rows/step because either capacity exceeds the request.',
 'tool':'No tools/dry_count.py exists in the supplied trees/kits. The scripts execute each plan’s own sampler once through 200 steps.',
}
result=dict(schema='draw-table-24m4i-v1',case='b',steps=200,method=method,rows=rows,total=dict(P_rows_per_step=288,N_rows_per_step=288,difference=0),P_input_config_sha256=p['config_sha256'],N_card_sha256=n['card_sha256'],N_config=J.load(D/'CONFIG_IDENTITIES.json')['n_go']['k/c.json'],raw_counts=dict(P='work/build24m4l/P_DRY_COUNT.json',N='work/build24m4l/N_DRY_COUNT.json'),config_delta='work/build24m4l/CONFIG_DELTA.json')
J.write(L/'out/DRAW_TABLE_24M4I.json',result)
lines=['P and N each draw **340 direct room rows in the first 200 steps: 1.70 rows/step**. These are global counts across four ranks.', '', 'The table reports **plan allocation cells**. N’s `routing_base` contains native routing types; its underlying family split requires production preparation. Zero in a separate N routing cell does not mean that type is absent from `routing_base`.', '', '| Stream / family | P rows/step | N rows/step | N − P | Named ruling or list |','|---|---:|---:|---:|---|']
for r in rows:
 reason=r['explanation']
 if r['family'] in ('counting','direction'):reason='K1 union `1c7c930d` / `43853165`; four-repeat counting cap, direction refill; ORCH 0511Z. See calculation below.'
 elif r['attribution']=='UNATTRIBUTED':reason='**UNATTRIBUTED rate change**; `deferred_first_boundary` groups routing in `routing_base`. ORCH 0418Z governs membership only.'
 lines.append(f"| {r['stream']} / {r['family']} | {r['P_rows_per_step']:.3f} | {r['N_rows_per_step']:.3f} | {r['difference']:+.3f} | {reason} |")
lines.extend(['| **Total** | **288.000** | **288.000** | **0.000** | Same stream quotas |','', 'N’s counting request is 4 × 2,571 / 1,000 = 10.284, compared with P’s 10.460. The 0.176 released rows/step go to direction: 34.990 + 0.176 = 35.166. Over 200 steps the native sampler draws 2,057 counting rows and 7,033 direction rows, giving 10.285 and 35.165.', '', *[f'**{k}:** {v}' for k,v in method.items()], '', 'The JSON contains integer totals, attribution, input identities and paths to all 200 per-step counts. The native code paths are `work/build24m4h/p_tree/student_pilot/type_mix.py:229` (P) and `work/tree_r1c/student_pilot/r1_mix.py:68` (N).'])
(L/'out/DRAW_TABLE_24M4I.md').write_text('\n'.join(lines)+'\n')
case='''CASE b: the input N card requests zero direct-room draws for the whole job; no loader-audit path raises that rate.

The decoded input card sets room_size.rows_per_step=0 at work/build24m4l/N_card.json:102 and room_rows_per_step=0 at work/build24m4l/N_card.json:200. The card hash is c0167f682bd49fce84d1ca447a64131ae1605a345f534ce61ee98aabf7bee9c8; k/c.json binds it as both r1_training.mix and r2_sampling.card (decoded copy work/build24m4l/decoded/c.json:302).

The job calls bind_prepared before production_audit (work/tree_r1c/launch_r1/entry.py:317). bind_prepared passes the same card to produce and binds only the resulting indices/population and row-plan hash (work/tree_r1c/student_pilot/r1_population.py:202). produce keeps card_pin unchanged in the binding (work/tree_r1c/student_pilot/r1_population.py:151).

allocate converts rows_per_step to 1,000-step draw totals and caps them at four repeats (work/tree_r1c/student_pilot/r1_mix.py:24). VQA deficits refill direction alone (work/tree_r1c/student_pilot/r1_mix.py:35); zero room draws cannot increase. plans excludes zero-total cells (work/tree_r1c/student_pilot/r1_mix.py:90). production_audit validates the binding and iterates those same plans; it records draws without editing rates (work/tree_r1c/student_pilot/r1_loader.py:51 and :62). The kit host wrapper only checks that the audit completed (work/build24/kits/n/b/h.py:27).

ORCH 0511Z sets room_size.rows_per_step and room_rows_per_step to 1.70. The compensating direction draw entry changes from 36.866 to 35.166 to preserve 128 VQA rows/step. All other card values remain byte-equivalent as decoded values. The inert room_rule annotation is retained solely to satisfy the requested draw-entry-only config delta; its zero-until-audit statement does not control executable behavior.

The configured room population is 425, so 1,700 draws over 1,000 steps meet the four-repeat cap. The first 200 steps yield 340 room draws. Native admission still applies row_check and room trace grammar (work/tree_r1c/student_pilot/r1_training.py:27). No production audit or training ran.
'''
(L/'out/CASE_24M4I.md').write_text(case)
print('DRAW TABLE',len(rows),'families; case b; room P=N=1.70')
