<!-- recovered by seal_plan: transcript=71f94277 line=1990 utc=2026-11-11T13:12:10.855Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd && mkdir -p revsi999_review && NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ) && T=$(date -u +%Y%m%dT%H%MZ) && cat > revsi999_review/BRIEF.md <<'EOF'
# revsi999_review (Codex Astra, read-only): independent review of the kit that scores our model on ReVSI's official 999 items
Your folder: /scratch/jjyeung/orch_cd/revsi999_review. Review the evaluation kit /scratch/jjyeung/orch_cd/evalx/work/aws_vl64r (read-only), which is a copy of /scratch/jjyeung/orch_cd/evalx/work/aws_vl64o with these changes: local/build_revsi999.py builds the 999 official rows from the official parquets (ground_truth_metadata/{32,64}_frame.parquet); binding takes --revsi-set official999 --revsi-tier {32,64}; each tier reads its own video at that frame count; ground truth is the pinned official parquet; tests/test_revsi999.py. Its notes are aws_vl64r/BUILD_NOTES.md. This change touches scoring and admission (the ground-truth source and the gate), so one independent review is required before any number from it counts. You are a second model family: find what is wrong; do not rewrite the kit.

## Standing answers (the orchestrator cannot answer a running Codex session)
- You may read this node's local disk (/scratch and the kit's inputs) with one serial process. You write nothing. No GPU, no ssh, no git, no network. /home and /data* are overloaded network storage: open named files only (the benchmark-scoring authority is /home/jjyeung/agent_project/AGENTS.md section 3; the kit's BUILD_NOTES name the parquet paths), never search or list recursively there.
- Never hold on a question: decide and say what you assumed.

## Check
1. Item set: are the 999 ids exactly the benchmark's official set, with no duplicates and none missing, and do the 32-tier rows reproduce the 452 rows of inputs/revsi_rows.json byte for byte where they overlap, as the notes claim?
2. Ground truth: does each tier's answer come from that tier's official parquet, with no fallback to another tier or to a sidecar; are the 11 items whose 64-tier answer differs from the 32-tier answer handled by tier and not averaged or overwritten; can a row ever be scored against the wrong tier's answer?
3. Scoring: is the scorer the one the project's scoring authority prescribes for ReVSI (metric per task, task averaging, treatment of unparseable answers), unchanged from aws_vl64o apart from the item set and tier; diff the scoring and gate code between the two kits and list every changed line with its effect.
4. Admission and leakage: can any ground-truth field, tier label or answer reach the model's prompt or the frame selection; does the gate refuse a mixed-tier or partial run; are unscored items reported and never silently dropped?
5. Frames: does each tier read the exact frames the official tier defines (count, order, source video), and does the kit record frames, resolution and tokens per frame beside the score?
6. Tests: do tests/test_revsi999.py's seven tests exercise items 1 to 4, and what is untested?

## Deliver (as your final message; you cannot write files)
A verdict of at most 30 lines: "COUNTS", "COUNTS AFTER FIXES" or "DOES NOT COUNT"; then findings ranked by their effect on a reported score, each with file and line and the smallest fix; then what you checked and found correct, in one line.
EOF
tmux new-session -d -s cx_revsi999_review "bash /scratch/jjyeung/orch_cd/orch_tools/codex_local.sh review /scratch/jjyeung/orch_cd/revsi999_review /scratch/jjyeung/orch_cd/revsi999_review/BRIEF.md --skip-git-check --label revsi999_review > /scratch/jjyeung/orch_cd/revsi999_review/dispatch.out 2>&1"
printf 'revsi999_review|tmux:cx_revsi999_review||\n' >> /tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/scratchpad/LANES
cat > evalx/inbox/${T}_ORCH_ANSWER_revsi999.md <<EOF
# ORCH ANSWER ($NOW) to your 1311Z QUESTION (aws_vl64r and the 513 MB stream)
- Stream: yes. One governed stream of the 391 files (513 MB) as a single tar stream at 8 MB/s or less, tier 2, priority 180, after rv64 ends, into 2-18 /dev/shm/jjyeung_revsi999 (check free space first; /dev/shm was 86% full this morning). It stays behind main's copies. This is within my standing rule: one throttled transfer under 2 GB at a time; anything larger waits for the user.
- Review: a Codex Astra read-only review of aws_vl64r is running now (tmux cx_revsi999_review on 2-18; brief /scratch/jjyeung/orch_cd/revsi999_review/BRIEF.md). No ReVSI 999 number counts before its verdict; I post it here. You may stage and dry-bind in the meantime.
EOF
echo "$NOW orch-home-distill-79: evalx Q 1311Z: kit aws_vl64r (ReVSI official 999, tiers 32 and 64; 7/7 tests; 11 of 999 GTs differ at tier 64) built; needs 391 files / 513 MB from /data2. ANSWER: stream approved (one governed tar stream <= 8 MB/s after rv64); dispatched Codex Astra review revsi999_review (tmux cx_revsi999_review) since the kit touches scoring and admission; no ReVSI 999 number counts before its verdict." >> ORCH_HANDOFF.md; tmux has-session -t cx_revsi999_review && echo "review alive"