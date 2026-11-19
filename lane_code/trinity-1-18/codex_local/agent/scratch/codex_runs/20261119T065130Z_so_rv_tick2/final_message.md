VERDICT: NO-GO

Items 1–14 correspond to the first review. Items 15–16 identify additional v2 defects.

1. **HIGH — First finding partially fixed: write confinement is still not guaranteed.**  
   [tick.sh:16](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:16) rejects an explicit tools directory and existing leaf symlinks. However, the default path’s ancestors are unchecked, and validation precedes pathname-based opens and replacements ([44–47](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:44)). Replacing the checked state directory with a symlink to `tools` before those operations can overwrite evwait’s `seen.txt`. Ordinary operation keeps the files separate; “can never” is false.  
   **Smallest fix:** validate ancestors, open a private state directory once, and perform lock creation, temporary-file creation, and replacements relative to its directory descriptor.

2. **INFO — First finding 2 resolved by the accepted specification change.**  
   [tick.sh:73–75](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:73) excludes events whose mtimes exceed one hour and reports their count. This also hides them during a fresh-state `--peek`, without persisting state.  
   **Fix:** none under the revised specification.

3. **MEDIUM — First finding 3 partially fixed: event reads are bounded, but previews can silently omit requested lines.**  
   [tick.sh:68–92](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:68) rejects observed nonregular files and reads at most 8,192 bytes. A first line longer than that prevents lines 2–4 from appearing, yet the event becomes seen without a truncation notice. The `lstat`/`open` race also permits a replacement symlink or FIFO. Reading happens before the budget check.  
   **Smallest fix:** open with no-follow/nonblocking flags, verify the opened descriptor with `fstat`, report byte-limit truncation, and stop opening candidates when the budget is exhausted.

4. **HIGH — First finding 4 remains: the five-second limit is not enforced.**  
   Every tick lists every event directory; initialization additionally stats every matching event ([62–74](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:62)). Every registered lane incurs status lookups before filtering, including remote lanes ([136–146](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:136)). Four sequential subprocess calls each allow three seconds, while NFS operations have no deadline. Governor reads can consume arbitrarily long lines. Shell-pipeline descendants are not explicitly terminated on timeout.  
   **Smallest fix:** apply one shared deadline, skip unnecessary status lookups, bound reads, and terminate subprocess groups. A strict response deadline during NFS stalls requires a local cached snapshot.

5. **INFO — First finding 5 resolved by the revised specification.**  
   [tick.sh:141–152](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:141) implements running local lanes plus one recent-gone summary, using the last 40 accepted rows and successor suppression. Remote processes remain unchecked as accepted; `--all` labels them `remote?`.  
   **Fix:** none to the selection policy; process detection remains defective below.

6. **MEDIUM — First finding 6 partially fixed: all three process checks remain fallible.**  
   [tick.sh:119–134](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:119) avoids the old Devin prefix match and Devin/Claude timeout-supervisor matches, but:
   - **Devin:** matching only executable basename and brief can attribute one process to multiple lanes sharing a brief. Whitespace splitting loses argument boundaries. An interpreter-based entry point can fail the basename check. See [devin_bg.sh:13](/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/devin_bg.sh:13).
   - **Claude:** any Claude process containing the lane phrase qualifies, without checking its brief or working directory. An interpreter or rewritten process title can cause a false negative. See [claude_bg.sh:14](/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/claude_bg.sh:14).
   - **Codex:** `--label` remains optional, so unlabelled launches are missed. A labelled dispatcher itself qualifies without proving a live agent child. See [codex_local.sh:3–15](/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/codex_local.sh:3).

   The named launchers do not establish the eventual children’s argv. Additionally, failed `ps` becomes **“no proc”** under `--all` ([148](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:148)).  
   **Smallest reliable fix:** record and validate agent PID, start time, and lane identity; report `unknown` when process inspection fails.

7. **INFO — First finding 7 fixed.**  
   [tick.sh:119](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:119) collects `ps` inside Python rather than exporting the process table.  
   **Fix:** none.

8. **MEDIUM — First finding 8 partially fixed: most missing inputs are isolated, but some failures remain hidden or fatal.**  
   Empty event folders work. Missing roots, missing `LANES.txt`, vanished events, and unreadable individual events no longer abort subsequent sections. However, unreadable lane directories disappear silently ([63–64](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:63)); invalid UTF-8 in `LANES.txt` or state raises an uncaught decoding error. Basename deduplication tries only the first copy, so an unreadable first copy prevents showing readable copies ([85–95](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:85)).  
   **Smallest fix:** count skipped directories, handle decoding errors explicitly, and try another copy before declaring a group unreadable.

9. **MEDIUM — First finding 9 partially fixed: body sanitization improves, but paths remain unsafe.**  
   Binary event bytes receive replacement decoding, and ordinary body control characters are sanitized ([90–92](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:90)). Event paths and folder names remain unescaped in headers and diagnostics ([95–99](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:95)). Embedded newlines break header/cap accounting and the newline-delimited seen-state format. Selection still requires timestamp-prefixed files directly beneath lane folders ([38](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:38), [58–67](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:58)).  
   **Smallest fix:** escape displayed paths, encode state keys safely, and explicitly document the accepted event naming/layout convention.

10. **MEDIUM — First finding 10 partially fixed, with a concrete regression: valid lanes are rejected.**  
    Field trimming, malformed-row counting, and accepted last-row-wins behavior work. However, [tick.sh:114](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:114) rejects hyphens, excluding `e_state-entrypoint` and `e_code-in-git` from [LANES.txt:63–64](/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANES.txt:63). The inspected registry contains **183 rows and 178 distinct names**; rejecting those two leaves 176.  
    **Smallest fix:** permit hyphens in otherwise safe lane names.

11. **MEDIUM — First finding 11 partially fixed: fallback works, but status ownership remains ambiguous.**  
    [tick.sh:136–139](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:136) correctly tries the unnumbered folder when the numbered folder lacks `STATUS.md`. Multiple generations can still inherit the same status, affecting the gone summary, and the output does not identify the source folder.  
    **Smallest fix:** display the status source and mark shared fallback status as ambiguous; use an explicit mapping when status must identify a particular generation.

12. **INFO — First finding 12 fixed for ordinary operation.**  
    [tick.sh:22](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:22) acquires a nonblocking lock. With a stable lock inode, concurrent runs exit immediately, and a leftover lock file does not block future runs. Output is flushed before atomically replacing each state file ([172–176](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:172)). Cap-excluded eligible events remain new. `--peek` leaves seen/last-tick contents unchanged, although it can create the directory and lock.  
    **Fix:** retain this behavior while addressing confinement and cap accounting.

13. **MEDIUM — First finding 13 mostly passes, but governor output is now truncated.**  
    The embedded code uses Python 3.6-compatible syntax and APIs. Node metrics request free `/scratch`, load, and available RAM ([157–163](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:157)); there are no SSH or Git commands. Governor decoding now tolerates invalid bytes and missing/short files. However, [168](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:168) applies the event-specific 200-character limit to governor line 4, contrary to the unchanged requirement to print that line.  
    **Smallest fix:** separate governor rendering from event-width truncation, with an explicit notice if a safety read limit is reached.

14. **INFO — First finding 14 repeated: validation remained read-only.**  
    The script matches [SHA256](/scratch/jjyeung/orch_n30/so_rv_tick2/SHA256): `b3ef8d143be91473def19257c71dcecedf79925acf6ab4e58e4e84398331a1e2`. `bash -n` and embedded-Python syntax parsing pass. I did not execute the digest, create state, reproduce timing claims, or test under Python 3.6.8.  
    **Fix:** none.

15. **MEDIUM — New: error output bypasses the event cap.**  
    [tick.sh:94–97](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:94) prints unreadable/nonregular-file diagnostics without decrementing the budget. Hundreds of such candidates produce hundreds of lines, even with `--max 0`. Section and remainder lines also sit outside the budget.  
    **Smallest fix:** charge event diagnostics against the cap and aggregate remaining failures into one bounded summary.

16. **MEDIUM — New: ORCH filtering differs from the revised instruction and consumes skipped events.**  
    [ORCH_NOTE.md:2](/scratch/jjyeung/orch_n30/so_rv_tick2/ORCH_NOTE.md:2) says to skip any basename containing `_ORCH_`; [tick.sh:78](/scratch/jjyeung/orch_n30/so_rv_tick2/tick.sh:78) checks only the parsed kind. Thus `…_NOTE_ORCH_…` still prints. Skipped ORCH files also enter `shown` and become seen, so a later `--orch` cannot reveal them.  
    **Smallest fix:** test the basename for `_ORCH_` and leave filtered events unseen, or track their acknowledgement separately.