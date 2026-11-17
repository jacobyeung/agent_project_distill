# notseen_diag STATUS (Devin lane on trinity-1-3; lane folder /scratch/jjyeung/orch_n30/notseen_diag). Updated 2026-11-17T14:33Z.

## DONE (lane complete, nothing owed)
- **Record.** `DD/H1_0_NOT_SEEN_DIAGNOSIS_20261117.md` (sha256 dad8dfe9), plus one INDEX.md line appended.
- **Briefs (not dispatched)** in `EV/notseen_diag/`:
  - `BRIEF_B1_selector_nonull_diag.md` (reader: drop the selector null when candidates exist, plus per-call stage diagnostics and a 2-rule read kit, about 2.5 H100-h);
  - `BRIEF_B2_real_failure_recovery_rows.md` (rows: recovery rows built on replayed real statuses).
- **Evidence.** `EV/notseen_diag/notseen_evidence_v2_20261117.tgz`, sha256 82c71afd (scripts, per-pair tables, replay outputs, visual-check images).
- **Mirror.** `trinity-0-13:/scratch/jjyeung/n30_mirror/notseen_diag/mirror_notseen_1430Z.tar` equals local `out/mirror_notseen_1430Z.tar` (sha256 b451fe70, matched over IB).
- **Key numbers.**
  - 74/298 (item, name) pairs not seen in H1-0's baseline. By stage: SAM 3 none 6, raster 1, selector null 67; lifting 0; frames 0.
  - CPU stage-1 replay (`work/replay2.py`, own pose plus G3T depth) agrees with H1-0 on 273/294 pairs.
  - Against the tower arm (7 pairs not seen), the extra losses split into selector null +47, own pose +16, own depth +3.
  - Fix (a') leaves 7/294 not seen. Leg R1's claimed reader: 35.8% of reads not seen under the shipped null, 4.7% under (a').
- **Inputs used** (all read-only, small).
  - Orchard: h10sub3 `items.jsonl` 826385c6 and p446 code (about 2 MB over ossh).
  - trinity-1-13 over IB: `masks_4984fac2` tar and 170056 `R1.json`, plus 60 G3T npz from its `result.tar.gz`.
  - trinity-1-18 over IB: selector `run_iso` 6d97c524 and 13 dev-S1 frames.
  - trinity-1-3: build 9 `a0_recovery.jsonl` (copied, untouched).

## Notes for the orchestrator or a successor
- rm_guard queued two lines from this lane in `/home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md`. One is an attempt to delete this lane's own superseded `out/notseen_evidence_20261117.tgz`. The other is a false match on the word in a printf text and deletes nothing. Both can be dismissed; `REMOVAL_CANDIDATES.md` lists the lane's files.
- The replay's selector weights (`run_iso`) were taken from the b04 record, not checked against H1-0's artifact binding. B1's read confirms it.
- No GPU, Orchard job, Git, Codex dispatch or code change was used.
