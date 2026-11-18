# Build: the H1-1 Orchard packet (a code-tree kit derivation over D0's kit)

You work only in `/scratch/jjyeung/orch_n30/cont_ops/work/h1/` (write here only; read the paths below). No ssh, no network,
no Git, no GPU, no Slurm, no deletion, no credential use, no session minting. Searches stay inside the named directories.
Python: `/scratch/jjyeung/envs/p1cpu/bin/python`. Keep this folder under 2 GB.

## Goal
(`source/` and `receipts/` may hold a partial extraction from an earlier start of this same task: verify against the pins or redo it.)
H1-1 is D0's job-B leg with a changed trainer tree and config: init step 544 (artifact 1d6eeb28...), D0's rows, seed 17,
world 4 on Orchard `advanced`, two switches on (S1 faithful own camera rows, S2 pose targets on camera routing rows), stopped
after step 200, milestones [100, 200]. Read `in/H1_1_PACKET.md` first; the code, configs and diff are in
`in/h1_1_kit_ready.tar` (sha256 4bce1b7d...; inner sums `in/SHA256SUMS_inner`; inner `h1_1_code.tar` 946b9513...).
Produce everything the operator needs to put H1-1 on Orchard the way D0's job B was put there, without touching D0's run
directory `r/63e57182`, D0's kit `x_f5c353f7`, D0's bundle `i_bb09a77d`, or D0's export sessions.

## How D0 was packaged (read these; they are the template)
- `in/D0_JOB_B_PACKET.md`, `in/PRELAUNCH_CARD_D0.md`, reviews `in/REVIEW_JOB_B_R9.md`, `in/REVIEW_CONFIRMATION_R10..R12.md`.
- Sealed source kit (local copy): `/scratch/jjyeung/orch_n30/cont_ops/work/d0/kitfull/` (SHA256SUMS.txt; trainer tar
  `k/t_b01ce449beffe35b.tar`, code pin `k/7.json`, sealed config `k/b02e4385.json`, `k/0.json` deployment, `b/` gate and job
  scripts `b/r.sh`, `b/c.sh`, `b/g.py`, `b/i.py`, `b/w.py`, `b/v.py`).
- Derivation tool `/scratch/jjyeung/orch_n30/cont_ops/work/d0/tools/derive_kit.py` (sha 4ad1a5ac; docstring lists the
  accepted overrides). It derives DATA-ONLY kits: same trainer tree, b/ gate, job scripts and 7.json. It refuses any other key.
- D0's override builder `/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/make_over_b.py` (tokens `jobB/TOKENS_B.json`),
  local build driver `/scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/build_b.py` and `a2/contract.py`, and D0's actual build
  `/scratch/jjyeung/orch_n30/cont_ops/work/d0/a2/v5b/` (over.json, over_local.json, ids.json, review.json, staging.json, 4.json,
  ANON_OK_B.json, orchard_check.json, fx/ fixture derivation, bundle_tree/b5/ with wrapper jb.sh 3b8f0162, the Orchard-side
  script orch_b.sh and fin_b.sh). Wrapper source `/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/jb.sh`. Export-session
  procedure: `jobB/mint.py` and `jobB/SESS_HOWTO.md` (the operator mints; you only list the 44 object names).

## Deliverables (in this folder)
1. `tools/derive_kit_h1.py`: derive_kit extended with a code-tree override (new trainer tar + its 7.json code pin + whatever
   identity/seal fields depend on the tree) and the config fields H1-1 changes (`configs/diff_against_d0.json`: the `h1` block,
   `milestones`, `recipe.milestones`, `scheduled_sampling`, `recipe.scheduled_sampling`). Everything else stays refused.
   Tests: empty overrides still reproduce the sealed kit byte for byte; D0's own overrides (a2/v5b/over_fx.json) still give
   D0's identity 80f4af94... and contract aaf2d7b0...; the H1 override changes exactly the declared fields; unknown keys refused.
   Report DIFF.md: every changed line of derive_kit with its reason.
2. The trainer tar for the H1 tree, built the way `t_b01ce449beffe35b.tar` is (deterministic; compare member layout and
   ownership/mtime conventions with the sealed tar), and its code pin. State its size and sha256.
3. H1-1 override + fixture derivation: new opaque tokens (run, kit, root, store/bundle dir; lowercase hex like TOKENS_B.json),
   output and preparation_output under the new run (never 469ddece or 359fcc3c paths), the same rows/receipts/init pins as D0,
   the 44 export object names `q8/<kit logical id>/<new run>_<m>.tar.partNN-of-04` for m in m1 m50 m100 m200 m400 m600 m800
   m1000 mstop mstopB mstopC (as D0) or the reduced H1 set if c.sh allows it (say which and why), a fixture derivation that
   passes, the identity and admission contract, and a draft 4.json bound to them (copy D0's 4b.json conventions;
   `production_go_granted` stays false).
4. The Orchard-side script(s) modelled on orch_b.sh / fin_b.sh for the new names, which an operator runs through the Orchard
   wrapper: upload of the small records + code tar (each under 20 MB or say otherwise), derivation on the login node,
   ANON check, inventory/staging check, and the submission line (`sbatch -J a15_cot_ap<hex> ... -p advanced --gres=gpu:4
   -t <wall> --signal=B:USR1@3600 --no-requeue`, wall = 200 steps x 140 s + admission + 2 exports, rounded up honestly).
   Every name on Orchard is opaque: no benchmark, dataset, model, method or project word.
5. A CPU check that the derived H1 kit's first step loads on the tiny fixture the way h1_headsft's first batch did
   (`in/receipt_real_forced.tar` shows the receipts; the H1 tree's own tests live in h1_1_code.tar), or say precisely why it
   cannot run here.
6. `REPORT.md`: what runs, every hash, the operator steps in order (including the faithful gate
   `nice -19 python -B rows/faithful_gate.py <routing receipt> --out gate.json` on the login node, exit 0 submit / 1 stop /
   2 blocker), what is unverified, and a self-review section mapping each review finding of R9-R12 to the H1 packet.

7. USR1 stop path (required by the orchestrator before launch). On 2026-11-16 `scancel --signal=USR1 --batch` on D0's job
   reached jb.sh ("USR1: relayed to job.sh"), r.sh's on_stop wrote `o/<job>.stop`, but the four ranks trained on (steps 232 ->
   237 in 15 min) and no checkpoint or slot was written. Path: jb.sh trap -> job.sh -> r.sh on_stop -> `b/h.py` forward()
   (walks /proc children, matches cmdline `$X/b/i.py $X`) -> `b/i.py` relay() (descendants with LOCAL_RANK in
   /proc/<pid>/environ, inside bwrap `--unshare-user`, no pid namespace) -> torchrun ranks -> `student_pilot/carrier_c1_run.py`
   `stop[0]` checked every optimizer step (run_steps, `request=... stop[0] ...`). Find the cause from the code (candidates:
   jb.sh's `$child` is not r.sh; h.py's match; relay() hitting PermissionError on environ under the user namespace, which it
   does not catch; torchrun forwarding; job.sh exec chain), fix it minimally in the files the H1 kit ships, and PROVE it on CPU:
   run a tiny job through the same r.sh/i.py/torchrun/bwrap-equivalent chain (bwrap if available locally, else say so), send
   USR1 the way Slurm's B: signal does, and show the ranks stop at the next step, a checkpoint is written and jb.sh's slot copy
   runs into a local stand-in slot root. If a faithful proof is impossible here, instead show that `h1.stop_after_step: 200`
   plus the milestone export is a verified fallback that ends the job cleanly before the wall limit with the slot written
   (cite the code path and a CPU run). Either way list the change in DIFF.md with its tests.

## Known hazards
- h1_1.json still names D0's AWS-layout output paths (469ddece). Map stream paths to their Orchard copies as D0 did; sha pins stay.
