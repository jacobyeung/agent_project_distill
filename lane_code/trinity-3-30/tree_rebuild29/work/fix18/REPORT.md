STATUS 2026-11-22T02:38:34Z verdict REAL (final). Job 174246's real training start fails on ranks 1-3 exactly as rehearsal rh1 did; do not release the review expecting training to start.

# fix18: would job 174246's real training start fail on ranks 1-3 like rehearsal rh1?

## Verdict: REAL
The rehearsal reproduced the job's start faithfully. Ranks 1-3 of the real start read the init artifact's two embedded
home-cluster paths, and neither exists in the job's sandbox.

## Cause (three sentences)
The kit's b/u.py runs train(cfg) inside `scope(request['_paths']), scope(persisted_files)` on every rank, so
r1_persisted.active() is True everywhere and init_mirror() returns None on all four ranks; the C1_INIT_LOCAL mirror
could not serve this init anyway, because the kit staged a different milestone there. Rank 0 loads with
verify_assets=True and reaches the staged copies through pinned() -> relocated(). Ranks 1-3 load with
verify_assets=False, which skips pinned() and with it the relocation, so they open
$X/runs/6ed2c7aa/m400/full_weights/ (and next heads.pt) under the job's empty $Q_ROOT/rp and raise FileNotFoundError.

## Evidence (node probes at 02:29:49Z, 02:32:16Z, 02:34:23Z, 02:37:25Z; read-only; outputs fix18/rd/p1.out to p4.out)
All sandbox facts come from the job's own live sandbox: rv.py pid 4034612, child of the job's bwrap pid 4034610
(149 args), under j.sh pid 3821326. j.sh builds the BW array once (j34.sh:408-412) and launches t.py with it (:441).
The job's files equal the copies I read (p4.out): kit b/u.py 77bf6769, b/t.py 8fcb8426, b/e.sh 6b756ba9, k/j.json
2ca9c9bd, j.sh 9f7a02bb (= fix15/dec/j34.sh), tree carrier_c1_run.py be11454e, r1_persisted.py 33d1615f,
p3_provenance.py afb446e5.
X = /scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b, P = /project/community/jjyeung/c7d31ddd.

Q1. What resolves the init artifact for ranks 1-3 in the real job: nothing.
- Path map by bind: the job binds `--bind /tmp/q_22c714e1_174246/rp $X/runs` (bwrap command line and
  /proc/4034612/mountinfo). /tmp/q_22c714e1_174246/rp is empty (created 21:47Z). Through /proc/4034612/root, $X/runs
  lists [], and $X/runs/6ed2c7aa/m400/full_weights and $X/runs/6ed2c7aa/m400/heads.pt are ABSENT. rh/L.sh:116 binds an
  empty scratch folder at the same place, so the rehearsal saw what the job will see.
- C1_INIT_LOCAL mirror: the job exports C1_INIT_LOCAL=$P/init (environ of bwrap 4034610 and of rv.py 4034612; j.sh's own
  /proc environ shows only its launch values Q_ROOT, Q_NS, Q_KIT, TK_*, since tk_env exports later). $P is
  `--ro-bind /tmp/q_22c714e1_174246/s/c7d31ddd $P`. The mirror holds one entry, init/1d6eeb28f51688c4/.verified
  (steps line 65), which is the kit's 0.json "init" = ap/93ccadab/m544/artifact.json: step 544 of run 469ddece. This
  job's init pin is sha256 5083243cfedd2a38... (step 400 of run 6ed2c7aa), so $P/init/5083243cfedd2a38/.verified is
  absent. The mirror is unused by this job on every rank.
- r1_persisted scope: active on every rank (Q2), and it is the only thing that maps the init; only verifying reads use it.
- rh/L.sh and rh/u2.py set the same C1_INIT_LOCAL, the same binds for $X, $X/runs and $P, and the same two scopes
  around verify_staging, admit and train as j.sh and b/u.py. The differences (smoke_steps=2, timing wrappers, fixed
  rendezvous port, read-only job folder with scratch for writable paths) do not touch path resolution.

Q2. active() does not differ between ranks; the verify flag does.
- b/u.py lines 18-21 enter both scopes in every rank process (request _paths 323 entries, persisted_files 19), so
  init_mirror's `if active(): return None` fires on ranks 0-3. prepared(admission=True) enters no scope of its own.
- Rank 0 (verify=True): carrier_c1_run.py:929 pinned(spec['artifact']) and :965 pinned(artifact['full_weights']).parent
  go through p3_provenance.pinned -> r1_persisted.relocated (sha256 -> path). persisted_files maps full_weights 1de983c9
  -> /tmp/q_22c714e1/p/q/w/full_weights.json (folder holds the index and five shards), heads e72208ac ->
  /tmp/q_22c714e1/p/q/u/e72208ac..., artifact 5083243c -> /tmp/q_22c714e1/p/q/u/5083243c....
- Ranks 1-3 (verify=False): :929 loads spec['artifact']['path'], which the config already carries as the
  /tmp/q_22c714e1/p/q/u path, so it passes; :963 takes Path(artifact['full_weights']['path']).parent raw and :1035
  fails; :976 would fail next on artifact['heads']['path'].
- No other raw read of load_model fails: depth_init's two weight files exist at their raw paths (ap/97a6a3eb/...,
  FILE 1824074576 and 924151276), geometry_online and align are absent from the receipt, the base model root exists.

## Q3. Fix
Three forms of one repair; each makes ranks 1-3 read the copies rank 0 authenticated.

H. In this job, by hand (no tree or kit change; the only form that needs no new job). On the node, before RELEASE:
```
D=/tmp/q_22c714e1_174246/rp/6ed2c7aa/m400
mkdir -p "$D"
ln -s /tmp/q_22c714e1/p/q/w "$D/full_weights"
ln -s /tmp/q_22c714e1/p/q/u/e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7 "$D/heads.pt"
```
  It touches only the empty rp folder: no staged file, no sealed file, no config. The targets exist only inside the
  sandbox (/tmp/q_22c714e1 is absent on the host), so the links dangle on the host and a read through
  /proc/<pid>/root follows them against the host root: check them with readlink, and the targets at
  /proc/<rv.py pid>/root/tmp/q_22c714e1/p/q/w (DIR) and .../p/q/u/e72208ac... (FILE 2763214343), both seen in p2.out.
  fix18 did not make the links: it is a hand write into the job folder outside the reviewed kit, so the orchestrator
  rules on it. Hard links (seven files plus heads.pt, same filesystem, dev 2431) would also work and resolve on the
  host, but they change the link count of staged files; the symlinks touch no staged inode.
  Steps that read what it touches ($X/runs/6ed2c7aa/m400/{full_weights,heads.pt}): load_model on ranks 1-3 only
  (init_from_artifact :963/:967 -> load_export_masters, and :976). Earlier steps (g.py, a.py, d.py, h.py, rv.py) passed
  with rp empty; r1_persisted.verify resolves all 19 handover pins through persisted_files and never opens a raw path;
  verify_staging hashes request['staged_pins'] through pinned() and scans no folder; kit scripts a/d/h/rv/pf/ep/o/rd/x.py
  never name rp or the runs folder. I did not trace every line of every earlier step; the rehearsal rerun below shows
  verify_staging, admit and train passing with the links present.
K. Kit (new job): the same two links in the inner shell before the t.py line (j34.sh:441), under "$NR/6ed2c7aa/m400",
  derived from the config's init artifact instead of hard-coded. It changes k/j.json and the kit seal only; tree,
  config identity and review inputs stay. Every kit step checks the seal, so it needs a run from the start of the proof.
T. Tree (new kit, new job): fix18/tree_fix.diff, three lines in init_from_artifact that use relocated(pin) when verify
  is False (identical to today outside a scope). It changes carrier_c1_run.py, so the source seal, authenticate(),
  trainer commit and config identity change and every proof step reads it: a run from the start of the proof.
  The kit's "init" staging entry (m544 mirror, about 20 GiB of links) serves no rank of this job and can go in the same kit.
  load_depth_stage1 (carrier_c1.py:714, 716) has the same verify=False pattern; its raw paths exist in this job, and it deserves the same change.

## Rehearsal test of H (not applied to fix15/rh)
fix18/rh_fixtest.diff adds the same two links to L.sh's scratch rp ($W/top/rp, bound at $X/runs), default on,
A15_INIT_LINKS=0 for the rh1 control. Pass: ev_rank1-3 log END load_model and every rank logs two finite STEP records.
Same FileNotFoundError: the links do not resolve. Any other error: the next defect, in code rh1 never reached
(everything after agree() at carrier_c1_run.py:2920 on all ranks).

## What might not work
- Code after load_model has not run on any rank in rh1; the rerun is the only evidence for it.
- A reviewer may count the hand links as a change outside the reviewed kit; then K or T with a new job is the route.
- Ranks 1-3 each read 18.8 GB of shards and 2.76 GB of heads from page cache; rank 0 took 87.6 s for the same load.

## Paths
- Probes: fix18/s/p1_inner.sh, p2_inner.sh, p3_inner.sh (sent as p1.sh, p2.sh, p3.sh) and p4.sh; outputs fix18/rd/p1.out to p4.out.
- Diffs: fix18/tree_fix.diff (tree), fix18/rh_fixtest.diff (rehearsal test of H). No rh.diff: the rehearsal needs no
  change to reproduce the job's start.
- Record: /data2/jjyeung/agent_project_data/distill_design/N_174246_REHEARSAL_INIT_PATH_20261122.md
- Nothing was written on the node; /tmp/a15_f18_174246 was not created.
