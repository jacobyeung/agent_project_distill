# e_orchkit-core STATUS (2026-11-16T14:50Z, Devin lane on trinity-3-30): BUILD DONE, review loop in progress; ROTATING (context)
Goal: build brief orch_n30/briefs/eff/orchkit-core.md (+ orchkit-core.verdict.md, INTERFACES.md). W = /scratch/jjyeung/orch_n30/e_orchkit-core.
Clone W/repo (W/clone symlink), branch eff/orchkit-core, head 633e3d0b6c0573062a5b0bee0f59c7624e79819b; 14 commits in W/PUSH_QUEUE.txt (never amend; new commits only; git only inside W/repo per the brief's exception).
## In flight
- Codex review round 10 (gpt-6-astra high, read-only) in tmux ock_review10 on trinity-3-30. Brief W/work/review/REVIEW_BRIEF_10.md; log W/work/review/dispatch10.log (line EXIT=N when done); verdict = final_message.md in the newest /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*ock_review10 dir. Check: tmux has-session -t ock_review10. Rounds take about 10 minutes.
## Done
- All modules (pins, ledger, anon, pack, launch, stage, ret, template, schema, example); 108 tests pass on /usr/bin/python3 3.6.8 and under bwrap p1cpu (W/out/test36.txt, test312.txt). Commands in W/REPORT.md "Tests".
- B/ORCHARD_LEDGER.jsonl created from the 151-row import (orchestrator ruling 1305Z). New rows carry payload_sha256; token claims and partition locks in <ledger>.claims/.
- ORCH 1305Z: formats confirmed; review = one Codex review (code by Claude models); no real submission before the review's GO.
- Review rounds 1-9: OC-01..OC-24, OC-26..OC-31 fixed; OC-25 withdrawn (split is a name rule by AGENTS.md). Evidence: W/work/review/VERDICT_N.json.md, FIX_N.diff, REPORT.md "Review". Round 7's Codex run ended on a content flag; the neutral wording of REVIEW_BRIEF_8+ avoids it.
- W/REPORT.md current through 633e3d0b. RECORD block appended once (states e263c512 / 79 tests; the final RESULT gives the new head).
## Next
1. Read round 10's verdict. If GO: write RESULT event "review_go" (head, verdict path, test counts) and stop.
2. If NO_GO: fix each verified finding as a new commit with a regression test that fails on the previous head (copy the old head with git show into W/tmp/oldhead_<sha>/, copy the new tests in, run them there), rerun both suites, write W/work/review/FIX_10.diff and VERDICT_10.json.md, dispatch round 11 from REVIEW_BRIEF_10.md (bump head, lists, reviewer_lane, next OC id): tmux new-session -d -s ock_review11 "cd /home/jjyeung/agent_project_distill && agent/scripts/codex_dispatch.sh review W/repo BRIEF --model gpt-6-astra --effort high --label ock_review11 --skip-git-check > W/work/review/dispatch11.log 2>&1; echo EXIT=\$? >> ...".
3. Answer out-of-spec findings in the brief (deliberate obfuscation, ledger rewriting, split in contents) instead of fixing them. If rounds keep finding only new exotic container or encoding cases, ask the orchestrator in one QUESTION whether to accept with the remaining cases listed (default: keep fixing).
4. Keep REPORT.md "Review" and this file current.
## Removal candidates: W/REMOVAL_CANDIDATES.md (also W/tmp/oldhead_* copies and PREP .check./.submit. dirs from tests).
