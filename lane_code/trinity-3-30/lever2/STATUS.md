# lever2 STATUS (trinity-3-30; started 20:06Z 11-20; 6 h timeout ~02:06Z 11-21 -> write B/briefs/lever3.md and start lever3 by ~01:35Z)
Lane dir /scratch/jjyeung/orch_n30/lever2 (work/, out/); 2-28 work dir /scratch/jjyeung/orch_n30/lever1_c (shared with lever1); poll: work/poll228.sh via tssh.
Inherits lever1 (B/briefs/lever1.md, lever2.md); lever1 history: /scratch/jjyeung/orch_n30/lever1/STATUS.md.
## Running (2-28; reviews auto-start after fixes)
- ORDER (ORCH 2337Z): rank 4 first; rank 1 submits only after rank 4's jobs have left general; never both. /project floor 15 GiB (ORCH 2329Z); kits state ext4 staging + <= 50 MB /project.
- Rank 4: preflight 173952 (token e71c940a6b283) died at launch, returned cause: job Python lacks stdlib 'keyword' (RESULT ~2352Z). Guard fix done (FIX6, token eb331eb9af6a4: memory.current minus file cache). Cause: path translator renamed stdlib keyword.py (deny word 'word'); FIX7 fixed it (token f68a2d7c903be), review 8 GO. ORCH NOTE 2351Z: boot worker + import closure BEFORE bulk staging in every lever job -> tmux l2_r4boot (BRIEF_R4BOOT.md) then l2_r4bootrev (auto). On GO: upload delivery (ossh, set -C cat) to PLACE.md D path, place body + `3.py cpu` (ONE preflight resubmission allowed under 2244Z), fetch c, if pass `3.py submit` (GPU read, 30 min, no further ANSWER), monitor/min, fetch g, score.py on 2-28 (out/return.tgz). A death with no return -> BLOCKER.
- Rank 1: review 12 GO (token a6f198d3c7b20, sha 9ac72506...). Boot-first order (ORCH 2351Z): tmux l2_r1boot then l2_r1bootrev (auto). On GO and after rank 4 leaves general: fetch orchard/ (tar cf - orchard SHA256SUMS PLACE.md) to /dev/shm, o_place, o_cpu, o_sub_hand (pre-approved: general, 1 H100, 50 min), monitor/min, o_fetch, o_get, pull (work/pull_tpl.sh on 2-28), relift.py, boxdev/run.py. Death with no return -> BLOCKER; death returning cause -> RESULT, fix, one more resubmission.
- Old placed packages (removal candidates, ~15 MB + ~23 MB): okh7/a15_cot_apd93a17be024f5, okh7/add93a17be024f5, okh7/a15_cot_ape71c940a6b283, okh7/ade71c940a6b283, a784b94c2e6af, a99a83187be42.
## Done
- Rank 5 ARKit: 21/22 pass, 22 built; RESULT posted; archive nogt_arkit7_20261120.tar.zst (sha b904ed67...) + mirror 1-18 (tar 84098c02...); INDEX + plan updated.
- Rank 5 archive (15 NPZs): /data3/jjyeung/distill_archives/lever1/nogt_gt15_20261120.tar.zst (121,289,552 B, sha c5d0c5ed..., readback ok); INDEX line added.
- Rank 5 mirror: trinity-1-18 /scratch/jjyeung/n30_mirror/lever1/nogt_gt15_20261120.tar (+ extracted nogt_gt15/), sha256 9287ce41... equal to 2-28 lever1_c/arch5/nogt_gt15_20261120.tar.
## Queued
- Rank 5 optional: ARKit restage in timestamp order (~10 MB governed) + rebuild.
- Removal candidate: 3-30 lever1/work/r6in.tar (8 GB; in lever1/REMOVAL_CANDIDATES.md).

## ROTATION (2026-11-21 ~00:15Z, exact)
- lever2 hands off to lever3 (brief B/briefs/lever3.md, started on trinity-3-30). Nothing of lever2's runs on Orchard or GPUs; no governed stream open (lever2_ark_ref, lever2_nogt_archive, lever2_nogt_ark_archive all .done). On 2-28: tmux l2_r4boot -> l2_r4bootrev, l2_r1boot -> l2_r1bootrev (Codex; reviews auto-start). Orchard ledger: lever2/work/ORCHARD_LEDGER.jsonl. Removal candidates: lever2/REMOVAL_CANDIDATES.md.
