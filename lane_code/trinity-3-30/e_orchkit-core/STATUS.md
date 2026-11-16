# e_orchkit-core STATUS (2026-11-16T14:26Z, Devin lane on trinity-3-30): BUILD DONE, review loop in progress
Goal: build brief orch_n30/briefs/eff/orchkit-core.md (+ verdict, INTERFACES). W = /scratch/jjyeung/orch_n30/e_orchkit-core.
Clone W/repo (W/clone symlink), branch eff/orchkit-core, head 5b3301f233da877236ad87b3a57cef752c3e41ae; 12 commits in W/PUSH_QUEUE.txt.
In flight: Codex review round 8 (gpt-6-astra high, read-only) in tmux ock_review8, brief W/work/review/REVIEW_BRIEF_8.md (neutral wording: round 7's run ended with a Codex content flag after probing concurrency), log W/work/review/dispatch8.log (EXIT= when done), receipt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/<UTC>_ock_review8/final_message.md. Review history (W/work/review/VERDICT_N.json.md, FIX_N.diff): V1 OC-01..08 -> 9d58cab7; V2 OC-09 -> 7a3a4cf8; V3 OC-10 -> 4601700f; V4 OC-11..14 -> cb6a5f04; V5 OC-15..17 -> fbe5ece7; V6 OC-18..21 -> 9e1313f6; round 7 transcript showed concurrent one-job submissions -> partition lock 5b3301f2. 103 tests pass on 3.6 and bwrap. Every fix has a regression test that fails on the previous head.
- ORCH 1305Z: formats confirmed; no real submission before the review's GO. Production ledger B/ORCHARD_LEDGER.jsonl created from the 151-row import (sha256 d6148bde..., did not exist before).
## Done
- All modules, template, schemas, example, tests: 79 pass on /usr/bin/python3 3.6.8 and under bwrap p1cpu (W/out/test36.txt, test312.txt).
- W/out/ORCHARD_LEDGER.imported.jsonl (151 rows). Pin audits W/out/audit_vsti.json, audit_native_code.json.
- W/REPORT.md (built, tests, kept/changed/dropped, template differences, format additions, not proven, adoption, migration note).
- RECORD block appended under "## Build results" in distill_design/EXPERIMENT_EFFICIENCY_20261116.md.
- RESULT event done_review_request written.
- Off-node copy: code reaches origin through code_sync publishing PUSH_QUEUE heads; brief rule 4 forbids ssh, so no IB mirror was made.
## Next (only on orchestrator notes)
1. When the review lands: apply findings as new commits (never amend queued commits), rerun both suites, post one RESULT with the verdict.
1b. Apply review findings as new commits on eff/orchkit-core (never amend queued commits).
2. Answer format questions from other builds (config `family`/`stage`/`return` additions, REPORT.md "Formats I added").
## Removal candidates: W/REMOVAL_CANDIDATES.md
