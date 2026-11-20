# Build (run later): BOX dev check — the frozen voted box (vote_10_3_best) against the served rule on the 150 dev items (rank 2 follow-up, CPU)

You are a Codex builder on trinity-2-28. Work only inside `/scratch/jjyeung/orch_n30/lever1_c/boxdev/` (create it). Everything else is read-only. No ssh, git, network, GPU, kill, Slurm, or reads/writes of /home or /data*; reads of this node's local /scratch are approved at any volume (do not stop to ask). Python `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`, nice 10, at most 16 processes.

## Question (registered reading, ORCH ANSWER 1935Z item 3; do not change it)
On K1 held-out the ladder's frozen two-frame vote `vote_10_3_best` (deployed masks, served geometry) scored +5.65 [2.09, 9.62] over the served best-frame rule (`/scratch/jjyeung/orch_n30/lever1_c/r2/out_box/`, built to `/scratch/jjyeung/orch_n30/lever1_c/BRIEF_R2D.md`). It becomes a proposed reader change only if it does not lose on the dev items. "Does not lose" = the paired difference (vote minus served) on the dev items has a paired room-bootstrap upper bound >= 0 (10,000 draws, seed 20261120) — i.e. the interval is not entirely below 0. Report it on all 150 and by dataset (ARKit / ScanNet / ScanNet++).

## Inputs
- The relift harness of rank 1: `/scratch/jjyeung/orch_n30/lever1_c/r1/relift.py` (cell (a) = served masks under the deployed rule on the served depth dump; 150-item parity gate at 0.00 m first). Reuse its loaders, parity gate, item/room table and bootstrap; do not edit r1/ (import or copy into boxdev/).
- The served depth dump does not exist yet (it arrives as `r1/returned/0.gz` with receipt `r1/returned/4.json` after one Orchard job). Build and test now on a synthetic dump in the exact format of `r1/depth_format.py` (and on whatever real T1 capture data relift.py's own tests use), so that the run is one command once the dump lands.
- The vote rule: the exact frozen `vote_10_3_best` implementation and constants used in r2/out_box (find it in r2's code / `/scratch/jjyeung/orch_n30/e3_geom/work/harness`); fit nothing.

## Arms (deployed masks, served geometry, reader guard, deployed selector, own-depth scale; all else as served)
- base: relift cell (a) exactly (must equal relift.py's cell (a) per item, test it).
- vote: base with the box produced by `vote_10_3_best` over the grounded frames.
Score MRA per item against the dev labels relift.py already uses; paired difference, room bootstrap, by dataset.

## Also report (from code and measurement, not guesses)
1. What the vote needs at read time that the served reader does not already compute: frames touched (lifted per object), extra memory, seconds per call (time both arms on CPU per item; state the hardware).
2. Whether training rows' printed responses would need re-rendering under the vote: the distillation training rows carry ground-truth-valued printed responses today; say whether the vote changes what a response prints for a row (the printed fields, their format), from the response renderer you can find on this node (e.g. in the T1 package's serving source under `/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/g3/orchard_t1`), and if you cannot find it, say so.

## Deliver
`boxdev/run.py` (one command: `run.py --depth ../r1/returned/0.gz --receipt ../r1/returned/4.json --out out/BOXDEV.json`; refuses to read any cell if the 150-item parity gate fails, writing STOP), `boxdev/REPORT_TEMPLATE.md`, tests (base == relift cell (a) on the synthetic dump, vote reproduces r2/out_box's vote on a few K1 rows if r2's inputs allow, bootstrap seed), `SHA256SUMS`. Final message: how to run it, test results, what you could and could not verify. Be quick.
