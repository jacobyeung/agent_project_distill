<!-- recovered by seal_plan: transcript=71f94277 line=29686 utc=2026-11-14T07:45:19.632Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd; S=/tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/scratchpad; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$C" <<'EOF'
import sys
C = sys.argv[1]
b19 = open(C + "/evalx/BRIEF_SUCCESSOR19.md").read()
i = b19.index("## Rules (all binding)"); j = b19.index("## ORCH addendum (2026-11-14T04:03Z)")
rules = b19[i:j].rstrip() + "\n"
draft = open(C + "/evalx/BRIEF_SUCCESSOR22_DRAFT.md").read().rstrip("\n")
head = ("NOTE ON YOUR WORKING DIRECTORY: you were started in /home/jjyeung/agent_project_distill only because Devin requires a trusted workspace. That folder is on overloaded network storage. Do not search, index, list or read it, never use a built-in search or grep tool on /home or /data*, and never run git there. Do all work in the lane folder /scratch/jjyeung/orch_cd/evalx on trinity-2-18, using absolute paths.\n\n"
        "# Evalx successor 22. ORCH (orchestrator orch-home-distill-79) remains the launch authority. You are the only evalx lane; your predecessor was rotated at its own request and has been stopped.\n\n"
        "**Save your context.** This brief is self-contained: the binding rules are copied below, then your predecessor's hand-off, then ORCH's addendum, which wins where they differ. Read `STATUS.md` (ten lines) and the inbox notes named in the addendum. Do NOT read the older briefs (`BRIEF_SUCCESSOR19.md`, `20`, `21`) in full; open one only to look up a specific fact. Read large files in parts.\n\n")
add = """

---

## ORCH addendum (2026-11-14T07:46Z). This wins wherever it differs from the hand-off above.

**Inbox notes to read now, in this order (all others before 0736Z are already reflected above):** `20261114T0740Z_ORCH_URGENT_cancel_169474_and_native_review_fixes.md` (part 1, the cancel, is moot: job 169474 ran and failed before the order could be carried out; part 2, the native family's fixes, is your main build task), `20261114T0743Z_ORCH_CONFIRMED_stop_archive_names.md`, `20261114T0736Z_ORCH_ANSWER_queue_step400_behind_P0_bounded_controller.md`, and the two notes from the operator about the stop attestor (`...cp2_ANSWER_stop_claim_contract_agreed.md`, `...cp2_REQUEST_stop_attestor_contract_check.md`).

**State of things:**
- Native family (seal 37d83521, five objects uploaded): independent verdict ACCEPT AFTER FIXES, `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_ORCHARD_NATIVE_FAMILY.md` (28 lines; read it). The pilot is not to be submitted as it is. Fix H1 (file modes of extracted FLA members; assert `ptxas` executable), H2 (full-mode geometry over the 84 captures the 636 items use, not 152), M1 (no silent NumPy fallback), M2 (incremental pilot report and a defensible budget), M3 (return-size projection), re-seal, and send me the diff. If the code object changes, upload the new one the same governed way (approved, under 5 MB).
- IF-P0: both real attempts failed early and cheaply (169413 on a member name; 169474 at `check-runtime`: "The GPU environment needs CUDA PyTorch and the native FLA/causal-conv fast path", after the inventories and the namespace smoke test passed). Lane if_p0 owns the fix. **This failure matters to you too:** your native stage uses the same production runtime and FLA closure. Read `/scratch/jjyeung/orch_cd/if_p0/inbox_results/a1bf5cb5a7bad53bf/` (`files/logs/check-runtime_2.log`, `files/metadata/JOB_EVIDENCE.json`) and say in your next RESULT what your pilot's runtime check would have done in that job, and whether the cause (lane if_p0 will report it) applies to your stage.
- Stop-archive amendment: confirmed for the final stop export (receipt `leg_s1_review/STOP_ARCHIVE_NAMES_RECEIPT.json`); bind its pins for that packet.
- Queue: nothing of ours is on `general` now. The bounded controller is needed only if a job of ours is queued when you submit.

**Order of work:** (1) the step-400 direct read the moment the operator's artifact and attestation arrive (about 08:50Z): one submission, reader b8ebab38, the launcher set you have bound, producer 8365bd3b, the packet requirements of my 0515Z ruling; (2) the native family's fixes and re-seal; (3) the operator's stop-attestor contract check; (4) the final stop export's read at about 14:30Z.

**First RESULT:** when the native fixes are sealed, or when step 400 is submitted, whichever comes first. Rotate before 250K tokens as before; to make that later, do not re-read what this brief already tells you.
"""
open(C + "/evalx/BRIEF_SUCCESSOR22.md", "w").write(head + rules + "\n---\n\n" + draft + add)
print("written", len(head + rules + draft + add))
EOF
kill 2697100 2>/dev/null; timeout 80 bash -c 'while kill -0 2697100 2>/dev/null; do sleep 3; done'; kill -0 2697100 2>/dev/null && echo "OLD LANE STILL ALIVE" || echo "old lane stopped"; (cd /home/jjyeung/agent_project_distill && bash $C/orch_tools/devin_bg_acp.sh /home/jjyeung/agent_project_distill $C/evalx/BRIEF_SUCCESSOR22.md gpt-6-astra-max 43200 $C/evalx/out/devin_stdout_22.log) 2>&1 | tail -n 1; sed -i 's#evalx|evalx/BRIEF_SUCCESSOR21.md||#evalx|evalx/BRIEF_SUCCESSOR22.md||#' $S/LANES; sed -i 's#\[evalx\]="evalx/BRIEF_SUCCESSOR21.md"#[evalx]="evalx/BRIEF_SUCCESSOR22.md"#' $S/lanewatch.sh; grep evalx $S/LANES; T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: evalx(21) RESULTS 0743Z: (a) IF-P0 job 169474 RAN 07:36:12-07:36:57Z and FAILED at check-runtime ('The GPU environment needs CUDA PyTorch and the native FLA/causal-conv fast path', inputs.py:169) after the runtime, NumPy, e00 and FLA inventories (806 files) and the namespace smoke test passed; return 8,222 B sha 669d5437 in if_p0/inbox_results/a1bf5cb5a7bad53bf/; my cancel order arrived too late and is moot; (b) lane ready for successor 22. ROTATED: evalx/BRIEF_SUCCESSOR22.md (self-contained: rules + draft + addendum; told not to re-read older briefs), old pid 2697100 stopped, successor launched; LANES and lanewatch.sh updated." >> $C/ORCH_HANDOFF.md