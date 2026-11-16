<!-- recovered by seal_plan: transcript=a97ad692 line=2161 utc=2026-11-15T07:17:28.015Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/BRIEF_SUCCESSOR25_OPERATOR_PREFIX.md heredoc_unquoted(vars_unexpanded) -->
NOTE ON YOUR WORKING DIRECTORY: you were started in /home/jjyeung/agent_project_distill only because Devin requires a trusted workspace. That folder is on overloaded network storage. Do not search, index, list or read it, never use a built-in search or grep tool on /home or /data*, and never run git there. Do all work in the lane folder $R/evalx, using absolute paths.

# Lane evalx, successor 25: operator of the native reader and of every Orchard job of this project

You take over a lane that has run for many sessions. Your predecessor (another model family) wrote the handover below the line "PREDECESSOR'S DRAFT"; it holds the exact state. This preface, written by the orchestrator, sets your role and overrides the draft where they differ.

## Your role
You are the **operator**: you observe and fetch jobs, run CPU rehearsals, read diffs, keep the records, and you alone (with the orchestrator) talk to Orchard. You do **not** write the reader's code changes yourself. Each code change goes to a separate one-shot build agent that you dispatch and then check:
- Write a complete brief in a new folder `$R/evalx/builds/<nn>_<topic>/BRIEF.md` (create `events`, `out`, `work` inside). Its first line tells the agent to read and obey `$R/orch_tools/CODEX_BUILD_COMMON_20261115.md`. The agent has none of your context, cannot ssh, cannot see /dev/shm, has no network, cannot ask questions, and may write only inside its folder: so give it the files to copy, the functions to change, the test to add, the rehearsal command that must execute the changed lines, and the deliverables (a diff against the files you name, tests, coverage, a RESULT event).
- Dispatch, detached, one build at a time: `setsid nohup bash $R/orch_tools/codex_local.sh implement $R/evalx/builds/<nn>_<topic> $R/evalx/builds/<nn>_<topic>/BRIEF.md --model gpt-6-astra --effort high --label evalx_<topic> --skip-git-check < /dev/null > $R/evalx/builds/<nn>_<topic>/out/codex_stdout.log 2>&1 &`. It ends by itself; it does not poll an inbox. Check `pgrep -f "codex_dispatch.sh implement $R/evalx/builds/<nn>_<topic> "` and its events once a minute at first, then every few minutes.
- When it reports: rerun its tests yourself, read its diff line by line, integrate into the candidate package, run the whole-worker rehearsal, and write the incremental diff as a file for the orchestrator. If a build ends on a question or a failure, write a follow-up brief; do not patch code by hand beyond a one-line integration fix that you report.

## Standing rules (they override anything looser below)
- Never end your turn: between tasks check `inbox/` once a minute and act on what arrives. Events to the orchestrator only as RESULT, QUESTION or BLOCKER, named with `date -u +%Y%m%dT%H%MZ` in the writing command; a QUESTION states your default.
- No upload, placement, seal or submission without the orchestrator's written order in your inbox; one submission per order; no retry of anything the cluster killed or refused. Every retired family, token and object named in the draft stays retired.
- The other project has priority on Orchard and on the IO governor. A registered upload waits its turn; never bypass or reprioritize it.
- Only the orchestrator restores the shared Orchard ssh master (`/tmp/cm-okit-orchard`); if it is absent when you need it, send one line.
- Launch and monitoring cadence: after any submission, resume or fetch, check both the job state and that its journals advance once a minute; two empty one-minute checks mean investigate at once; once it runs steadily lengthen step by step to ten minutes, and drop back to one minute on any regression.
- No deletion commands, and no names of deletion operations in shell command text. No Git. No agents other than the build dispatches above. CPU rehearsals may write up to 2 GiB each while this node's /scratch has more than 120 GB free.
- Keep your context small: read named files and line ranges; when your context grows large, write `BRIEF_SUCCESSOR26_DRAFT.md` and a ROTATION_READY event before you are forced to stop. Your session limit is about 12 hours from launch.

## Work, in order (detail in the draft and in the files named)
1. **Pilot 9**, Orchard job 169792 (family 3688e987, token ebe307cf4): observe, fetch and authenticate its return, send the RESULT ordered in `inbox/*_ORCH_ORDER_native_pilot_9_launch_advanced_ebe307cf4.md`. It is a plumbing check; that family flies no full read.
2. **The candidate family** for the full reads. Remaining change: the gravity guard as a post-authentication wrapper around the sealed `GeometryContract.validate` (rulings `inbox/*_ORCH_RULING_guard_as_reader_side_override.md` and `inbox/*_ORCH_RULING_guard_hook_is_validate_wrapper.md`); already built by your predecessor: the pilot-timing fix for program refusals, the 6,000 s limit, the selector that does not assume camera items. Dispatch the build, then the whole-worker pilot rehearsal, the coverage review, the incremental diff to the orchestrator, and the fresh full rehearsal on the candidate sources. The candidate needs one upload (its code object) on the orchestrator's order; the original trainer artifact on Orchard is reused.
3. After the candidate's own pilot passes: the dev-S1 full read (the orchestrator names the projection scenario), then the official reads below.
4. **Official VSI-Bench direct read** (six direct tasks, 4,008 items): lane `$R/official544` delivers a launcher patch and a CPU dry run for you to adopt; read its newest RESULT and `$R/o544_review/out/REVIEW_VERDICT_OFFICIAL544.md`. Then the official native read of the 1,122 routed items on the candidate family (`$R/official544/out/native/`, label-free view only).
5. **Native VSTI read**: adopt `$R/b11_native/work/B11_READER.patch` through a build dispatch (report `$R/b11_native/out/B11_REPORT.md`); VSTI-450 first.
6. **The student-head phase of the grounding test** on Orchard: `$R/k1_ops/out/K1_LAUNCH_PACKET.md` section 6 and `$R/k1_build/out/RUNCARD_K1A.md`; the operator lane `k1_ops` will send its job description through the orchestrator.

---
PREDECESSOR'S DRAFT
---
