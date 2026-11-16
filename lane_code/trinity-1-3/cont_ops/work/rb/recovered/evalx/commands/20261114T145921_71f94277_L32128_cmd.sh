<!-- recovered by seal_plan: transcript=71f94277 line=32128 utc=2026-11-14T14:59:21.122Z kind=commands original_path=(bash command)  -->
fold -w 2500 -s /tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/tasks/b1wcqxqyo.output | tail -n 30 | cut -c1-2500; N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_REVIEW_P1_gate_fix_F1_before_pilot_4.md <<'EOF'
# ORCH: review of the P1/report candidate = ACCEPT AFTER FIXES. Do not submit pilot 4 on seal e58e5a1e

Verdict: `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_NATIVE_P1_GATE.md` (read its Findings section). The P1 gate is correct and passes on pilot 3's real record; the tolerance is judged sound; admission and scope are confirmed; 65 of 65 tests pass in the reviewer's copy.

**F1, blocking: the pilot would fail every time with FileExistsError.** `native_worker.py` line 137 builds the report object before the parity kernel runs; building it creates `native/probe`; the parity kernel then runs its exclusive `mkdir` on the same folder (nomdg line 331). The reviewer reproduced it with the real parity kernel: `/scratch/jjyeung/orch_cd/leg_s1_review/work_p1_gate/repro_mkdir.py`. Your CPU chain missed it because its restoration stub creates the output folder itself.

Fix, worker only, as the reviewer specifies:
1. Keep the report's path. Create the report object and its `loaded` checkpoint inside the `finally` that follows the parity kernel; right after load, print one `pilot_loaded` JSON line (load seconds, peak bytes) to standard output so the worker log holds it if the job dies inside parity.
2. Tests: the restoration stub leaves the output folder absent; add a test that runs the real parity kernel through its `mkdir`, as `repro_mkdir.py` does; the passed and gate-failed publication chains still pass.
3. F2, low, in nomdg's gate: a missing cached record, missing fields or non-finite margins count as a rejected mismatch instead of raising before GPU_PARITY.json is written.
4. F3 needs nothing: one tie in 99 positions passes under the ruled minimum of one.

Then reseal, upload the code object, rebuild the `advanced` pilot packet first, and post one event with the runtime diff and test diff (paths and sha256), the new family sha and the token. I confirm that short diff myself and answer with the control files. The seal e58e5a1e and its two packets (e2daae3c9, e953c2664) are retired; never submit them.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) Independent review of the P1/report candidate (family e58e5a1e): ACCEPT AFTER FIXES (leg_s1_review/REVIEW_VERDICT_NATIVE_P1_GATE.md). BLOCKING F1: the worker creates native/probe (report object) before the parity kernel's exclusive mkdir -> FileExistsError every time (reproduced with the real kernel; author's stub hid it). P1 gate correct on pilot 3's real record; tolerance sound (1 of 126 positions has a margin <= 1.0); digest 4bbcd73f intact. Ordered evalx: worker-only fix + real-kernel test + F2; reseal; I confirm the short diff; seal e58e5a1e and tokens e2daae3c9/e953c2664 retired." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md