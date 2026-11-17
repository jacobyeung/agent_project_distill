# Brief 04 (operator): package leg R1 on Orchard, prove it with the production config, hold it ready for the slot

Carrier: Devin Opus, medium effort, on trinity-1-3; either lane cont_ops (its owner already holds the H1-1 deployment) or a new lane `r1_ops` in `/scratch/jjyeung/orch_n30/r1_ops` (cap 4 GB). Codex gpt-6-astra, effort high, for any fix build. First read `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md`. Orchard only through `tools/ossh.sh`; every stream above 20 MB through the IO governor; job names `a15_cot_ap` plus hex, meanings in the lane's `work/ORCHARD_LEDGER.jsonl`. **Submit nothing that uses a GPU, and no training job, without the orchestrator's GO.** Before every submit read the newest `INBOX_TO_DISTILL_ORCH_*.md` in `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/`: main has priority, and distillation holds one Orchard job at a time.

## Goal
When main returns Orchard advanced (about 16:15Z on 2026-11-18; as early as 02:15Z), leg R1 submits within minutes on a deployment whose production-config proof has passed. Design record: `/data2/jjyeung/agent_project_data/distill_design/NEXT_LEG_DECISION_20261117.md` (sections 2.2, 3.2, 3.3, 5).

## Inputs
- Brief 01's packet: trinity-1-3 `/scratch/jjyeung/orch_n30/r1_pkt/out/` (`R1P_PACKET.md`, `r1p_code.tar`, `proof/`, `ADMISSION_BY_TYPE.json`).
- The H1-1 deployment and how it was derived: Orchard `/project/community/jjyeung/okh7/x_3fdda0fb`; `/scratch/jjyeung/orch_n30/cont_ops/work/h1/REPORT.md`; `events/cont_ops/STATUS.md` (cont_ops9 and cont_ops10 entries: derive, certify, proof, submit, babysit).
- Row store: v6 now (`/scratch/jjyeung/orch_n30/rows_a2/out/a2_vqa_v6/vqa/`, 1.6 GB), v7 from brief 03 after its review.
- S2's value: the orchestrator sets it from the H1-1 m100 reads (design record, table 2.3) at about 18:00Z. Until then prepare both.

## Steps
1. **Upload the row store** to Orchard through the governor as one archive (register it with the priority the orchestrator gives; `--writes-nfs` does not apply on Orchard's side). Verify sha256 there.
2. **Derive and certify** R1's deployment from brief 01's packet the way x_3fdda0fb was derived (new deployment root, new run key, new persistent root; never H1-1's or D0's). Run the content scan for visible names.
3. **Production proof.** Submit the proof script as a CPU-only job on a compute node (48 cores, 800 GB node-local disk, 4 h limit), from an empty root. It must reach the first-batch boundary of every rank through `s1_admission.admit(prepare_only=True)` with the exact config identity, and its receipt must show the five assertions (disk plan, selection pin, no assumed path, binaries resolved at run time, directory modes). Ask the orchestrator to ask main whether this job may run beside the one GPU read; if not, it goes ahead of every read except the two H1-1 m100 reads. Submit the first proof by 19:30Z. One fix round per failure (Codex), then the whole proof again; a second failure of the same check is a BLOCKER event.
4. **Any change reruns the proof:** a new store sha (v7), S2's final value, a new selection pin.
5. **Five rows per type.** From the files as staged on Orchard (`rows.sqlite` and the routing receipts), write `PRELAUNCH_ROWS_R1.md`: five random rows per question type and per routing family, full target text, with the seed. The orchestrator and the user read it before GO.
6. **Registration card.** Write `PRELAUNCH_CARD_R1.md` from the design record's sections 2.2 and 5 with the final config identity, store sha, mix and the admitted row counts per type from the proof.
7. **Vehicle gate, two hours before the slot.** Report which vehicle is proven: this deployment, or the new tree's kit (brief 02) if its seal, review, records, frame-host job and production proof have all passed. The orchestrator chooses.
8. **On GO:** submit, then babysit as for 170710 (first-steps RESULT with `early_loss_check_d0.py`, each export verified on pool and GCS, the in-process stop at step 200). After the m100 and m200 exports, run the h1read direct read and the evaluator's routed read on the general job place.

## Gates
Proof receipt PASS on the final config identity; sha256 of every uploaded input equal on both ends; scan CLEAN; the card and the row sheet written. No training submit without GO.

## Outputs
Lane `STATUS.md`, `work/ORCHARD_LEDGER.jsonl`, the proof receipt, `PRELAUNCH_CARD_R1.md`, `PRELAUNCH_ROWS_R1.md`, RESULT events for: proof verdict, vehicle gate, submit, first steps, each export.
