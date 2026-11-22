# n_review1l: my reading of the disk plan of kit 7e23bbdd (written 2026-11-22 03:53Z, before reading tree_rebuild29's)

Sources (I opened each): tree t_e047002134f979bd.tar (sha 5f2d77c4) from n_review1k/work/k34/n_go/k, extracted at
n_review1l/work/t34; kit config k/c.json and k/n.json decoded at n_review1l/work/kd; kit b/ decoded at n_review1l/work/kb;
174246 o.tar extract n_ops12/work/fail_174246/x (j2.log, t.log); P-era config r1_ops6/cp/out/proof/local_config.json.

## The formula (tree student_pilot/checkpoint_space.py)
- plan() :11-21: planned_full_states = ceil((wall-stop_before)/resume_every)+2; extra_full_states = 2;
  planned_weight_exports = |set(milestones)| + export_at_stop; reserve_bytes default 200e9; retained_archive_copies passed in.
- check() :106-120, at every checkpoint/export save, with completed saves subtracted (Budget.remaining :41-49):
  S = 1.25*measured_state + 64 MiB, measured_state = sum over ranks of trainable weights + buffers + own optimizer state (all fp32);
  E = 2.5*exported + 64 MiB, exported = sum over ranks of model.named_parameters() at element_size (fp32) + buffers;
  required = states*S + exports*E + copies*(states*(S+10240) + exports*(E+10240)) + reserve; free = min statvfs over ranks.
- Callers: carrier_c1_run.checkpoint :1961 and export :2084 (both via run_steps' one Budget :2355); the step-1 save is due because
  first_step_admission is set (:2433-2434). The configured policy must equal plan(recipe, reserve, copies): carrier_c1_run.py:92,
  launch_r1/entry.py:165 (R1_DISK_PLAN_DIFFERS, copies=1 hard-coded), launch_r2/persistence.py:14 (copies=1), r2_config.py:71 writes it.

## The terms of 6,027,674,886,604 B (174246, first save, completed = 0)
- Policy in kit c.json/n.json: planned 14 (= ceil(82800/7200)=12 +2), extra 2 -> 16 states; exports 7 (milestones 100,200,400,600,800,1000 + stop);
  reserve 200,000,000,000; retained_archive_copies 1.
- Hence 32*S + 14*E + 235,520 + 200e9 = 6,027,674,886,604, i.e. 32*S + 14*E = 5,827,674,651,084 B.
- Split (ESTIMATE: assumes exported = fp32 of the staged 19.33 GB bf16 model, j2.log "model staged 18876304 KiB"):
  E ~ 96.7 GB, S ~ 139.8 GB (measured state ~111.8 GB). Native states 16S ~2,237 GB; their archive copies ~2,237 GB;
  native exports 7E ~677 GB; archive copies ~677 GB; reserve 200 GB. Exact split needs the measured state/export tensor bytes.
- Where set: 86400/3600 from the tree RECIPE (carrier_c1_sweep.recipe_for), 7200 and milestones from the kit config;
  +2, extra 2, reserve 200 GB, factors 5/4 and 10/4, 64 MiB, 10240 in the tree (checkpoint_space.py); copies=1 in the tree (r2_config.py:71).
- P-era plan (r1_ops6 local_config.json; I believe it is P's): planned 14, extra 2, exports 3, reserve 200e9, NO retained_archive_copies
  -> 16S + 3E + 200e9 ~ 2,727 GB under the same S, E. N's plan is 2.2x P's: the archive copy (x2) and 4 more exports.

## Which terms are real and which are inflated
- Real: the archive copy. cfg has r2_identity and r1_training but no r2_persistence, so persistence.upload (local_only) tars every
  checkpoint and export into runs/r/persist and keeps it; kit b/pc.py:390-402 uploads that same tar; nothing in tree or kit deletes
  native states or tars. A full leg holds native + tar of every save.
- Inflated 1 (largest): exports are written BF16 (full_ft.save_export :660-693, "dtype bfloat16") but estimated at fp32 element size
  and then x2.5: E ~96.7 GB planned against ~20 GB written (19.33 GB weights + heads.pt). 14 export slots overstate by ~1.07 TB.
- Inflated 2: the count of states assumes the whole 82,800 s span, but the trainer's clock starts at job start (j.sh:410 TK_JOB_START,
  carrier_c1_run.py:2879-2882). 174246 began training at 5h42m: window ~62,250 s -> step-1 save + 8 periodic + stop = 10 states, not 14.
  Whether all 7 exports occur depends on 1000 steps fitting in that window (step time not read by me).
- Margins I would keep: 1.25 on states, 2 extra states, 200 GB reserve.

## Arithmetic for a clean orchard-community node (corrected 04:04Z with tree_rebuild29's survey, RESULT 0400Z)
- A clean node's /tmp: 6,388.3 GB, 6,379.7 GB free; no leftovers of ours were on community-3 at 174246's save.
- 174246 after staging and proof held ~662 GB: free 5,717,540,712,448 B at the first save is what a clean node has.
- The old plan (6,027.7 GB) is short by 310.1 GB on every clean node of this type: it can never pass.
- RULING 0357Z plan (resume_every 10,800 s): 24S + 14E + 200 GB ~4,909 GB (S ~139.8 GB); preflight bar +300 GB ~5,209 GB; margin ~508 GB.
  The new bytes depend on S alone (old - 8S): S = 120 GB would give ~5,067 GB, bar ~5,367 GB, margin ~350 GB.
- Later saves do not fail first: each completed state lowers the requirement by ~2S (~280 GB) while it uses ~224 GB; each export lowers
  it by ~2E (~194 GB) while it uses ~41 GB. The first save is the binding one.
- What a 24-hour leg really needs (native + tar, real sizes, 200 GB reserve): 10 states + 7 exports ~2.72 TB; even 16 states ~4.06 TB.
  Both fit in the 5.72 TB that 174246 had.

## Identities a change would move (for review item 2f)
- c.json/n.json checkpoint_disk_guard is part of the configuration (config 76de3706) and is pinned = plan(recipe, copies=1) in three
  tree places; changing plan() constants or the policy moves the configuration identity and needs the tree change in all three.
- Fixing the estimator in check() (export at its written dtype) changes the tree (gate pins TREE) but not the config policy dict.
