<!-- recovered by seal_plan: transcript=71f94277 line=29942 utc=2026-11-14T08:21:41.924Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd; S=/tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/scratchpad; wc -l -c $C/evalx/BRIEF_SUCCESSOR23_DRAFT.md | head -n 1; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$C" <<'EOF'
import sys
C = sys.argv[1]
b19 = open(C + "/evalx/BRIEF_SUCCESSOR19.md").read()
i = b19.index("## Rules (all binding)"); j = b19.index("## ORCH addendum (2026-11-14T04:03Z)")
rules = b19[i:j].rstrip() + "\n"
draft = open(C + "/evalx/BRIEF_SUCCESSOR23_DRAFT.md").read().rstrip("\n")
head = ("NOTE ON YOUR WORKING DIRECTORY: you were started in /home/jjyeung/agent_project_distill only because Devin requires a trusted workspace. That folder is on overloaded network storage. Do not search, index, list or read it, never use a built-in search or grep tool on /home or /data*, and never run git there. Do all work in the lane folder /scratch/jjyeung/orch_cd/evalx on trinity-2-18, using absolute paths.\n\n"
        "# Evalx successor 23. ORCH (orchestrator orch-home-distill-79) remains the launch authority. You are the only evalx lane; your predecessor was rotated at its own request and has been stopped.\n\n"
        "**Context economy is a binding rule for you.** The last three lanes each lasted about 35 minutes because they read too much into their own context. So: this brief is self-contained (rules, then your predecessor's hand-off, then ORCH's addendum, which wins); read `STATUS.md` and only the inbox notes the addendum names; do NOT open the older briefs. Never print a test log, a diff, a JSON record or a job log into your context: send command output to a file and read only the last lines or the fields you need. Read source files in parts, only the functions you are changing. Keep events short. Aim to last at least three hours.\n\n")
add = """

---

## ORCH addendum (2026-11-14T08:23Z). This wins wherever it differs from the hand-off above.

**Inbox notes to read (only these):** `20261114T0815Z_ORCH_ORDER_native_pilot_launch.md` (what the pilot must report; the step-400 allowlist), and `20261114T0515Z_ORCH_RULING_step200_direct_read.md` items 4 and 5 (what the step-400 packet must add).

**Your work, in order of priority when things collide:**
1. **Step-400 direct read**, when the operator's artifact and attestation arrive (about 08:50Z): one submission on `general` with reader b8ebab38, producer 8365bd3b and the launcher set already bound (say which). If pilot 169477 is still queued or running, use the bounded controller with `ALLOW 169477`, built exactly as my 0736Z answer describes (every accepted validation unchanged; one predicate differs; CPU proof of identical batch bytes and argument list, and of refusal on an unlisted job; report its file and hash with the submission). Build that controller and the step-400 reporting helper now, before the export arrives, as small files with small tests.
2. **Pilot 169477**: one short Orchard observation every ten minutes while it is pending or running (job state, phase, the controller's card evidence). When it ends, fetch and authenticate the bounded return and post the pilot RESULT: load time, P1 to P3 verdicts, peak memory, geometry seconds per capture, seconds per item, compressed return size, the bootstrap's FLA and Triton version and origin lines, and the full read's projections (GPU time for 84 captures and 636 items; return size against the 256 MiB limit). If it failed, post the failure record with the failing phase and the exact error; no second pilot without my word.
3. **Final stop export** (about 14:30Z): the stop route with the bound pins (`work/milestone/stop_bound_s22/BINDING.json`); one submission under the standing authority.
4. After a passed pilot: prepare, but do not submit, the full read's packet for step 200 (it needs my separate order), and add to the worker the runtime fields I asked for earlier (the fast-path flag's value and the per-layer kernel bindings) only if the worker changes anyway.

**First RESULT:** the pilot's first observation that shows it running or finished, or the step-400 submission, whichever comes first.
"""
open(C + "/evalx/BRIEF_SUCCESSOR23.md", "w").write(head + rules + "\n---\n\n" + draft + add)
print("written", len(head + rules + draft + add))
EOF
OLD=2759339; kill $OLD 2>/dev/null; timeout 80 bash -c "while kill -0 $OLD 2>/dev/null; do sleep 3; done"; kill -0 $OLD 2>/dev/null && echo "OLD LANE STILL ALIVE" || echo "old lane stopped"; (cd /home/jjyeung/agent_project_distill && bash $C/orch_tools/devin_bg_acp.sh /home/jjyeung/agent_project_distill $C/evalx/BRIEF_SUCCESSOR23.md gpt-6-astra-max 43200 $C/evalx/out/devin_stdout_23.log) 2>&1 | tail -n 1; sed -i 's#evalx|evalx/BRIEF_SUCCESSOR22.md||#evalx|evalx/BRIEF_SUCCESSOR23.md||#' $S/LANES; sed -i 's#\[evalx\]="evalx/BRIEF_SUCCESSOR22.md"#[evalx]="evalx/BRIEF_SUCCESSOR23.md"#' $S/lanewatch.sh; grep evalx $S/LANES; echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) orch-home-distill-79: evalx(22) asked for rotation at 08:20Z (third lane in a row to last ~35 min). ROTATED to successor 23 (evalx/BRIEF_SUCCESSOR23.md: self-contained, with a binding context-economy rule: no logs/diffs/records printed into context, older briefs not opened); old pid 2759339 stopped; LANES and lanewatch.sh updated. Work: step-400 read (bounded controller ALLOW 169477), pilot 169477 observation and return, final stop export, full-read packet after a passed pilot." >> $C/ORCH_HANDOFF.md