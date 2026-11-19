NO-GO

1. **HIGH — Writes are not confined; `tools/seen.txt` can be overwritten.**  
   Evidence: `tick.sh:12–15,21,111–114`. Setting `TICK_STATE` to `$B/tools` makes the final replacement overwrite evwait’s actual seen file (`evwait.sh:5`). Symlinks at `lock`, `seen.txt.tmp`, or `last_tick` can redirect truncating writes outside the state directory. Even `--peek` creates the directory and truncates `lock`.  
   **Smallest fix:** restrict state locations, reject symlink traversal, open files relative to a validated private directory, create temporary files exclusively, and atomically replace state files. Open the lock without truncation.

2. **HIGH — First run silently discards unseen events.**  
   Evidence: `tick.sh:41–45,109–113`. Every matching event with an mtime older than one hour becomes seen without being printed. A newly delivered file preserving an old mtime is also discarded. With fresh state, `--peek` hides those events too.  
   **Smallest fix:** start with an empty seen set; make any historical cutoff an explicit option.

3. **HIGH — Event reads can hang or consume unbounded memory and NFS bandwidth.**  
   Evidence: `tick.sh:34–43,51–54`. The script never verifies that candidates are regular files. A timestamp-named FIFO can block indefinitely; directories become “unreadable” events. Python reads an entire line before applying `[:220]`, so a huge first line is fully fetched and allocated. It also reads the next candidate before checking whether the remaining budget can accommodate it.  
   **Smallest fix:** reject nonregular files and symlinks, bound bytes read per event, report truncation explicitly, and stop reading when the output budget is exhausted.

4. **HIGH — The five-second requirement is not enforced.**  
   Evidence: `tick.sh:15,34–43,77–79,95–104`. Lock acquisition alone permits ten seconds. Three sequential subprocess calls each allow four seconds. Directory listings, event reads, metadata requests and governor reads have no deadline. Every tick lists every event directory; first run additionally stats every matching event. The output cap does not cap this NFS work. Pipeline descendants can also outlive the shell killed by a subprocess timeout.  
   **Smallest fix:** use a nonblocking lock and one overall deadline, bound scan work, and terminate subprocess groups. A strict response deadline during an NFS stall requires serving a local cached snapshot with its age displayed.

5. **MEDIUM — The default command does not print every lane.**  
   Evidence: `tick.sh:19,81–91`. Quiet lanes disappear unless `--all` is supplied. Remote lanes show `remote`, which conveys location but not whether their process runs. The quiet-lane summary also describes missing statuses as “older than 24 h.”  
   **Smallest fix:** print all lanes by default, distinguish missing status, and label remote process state `unknown (remote)`. Remote liveness requires a receipt or heartbeat if SSH remains prohibited.

6. **MEDIUM — Process matching can misclassify all three lane types.**  
   Evidence: `tick.sh:68–72`.
   - **Devin:** the launcher uses `timeout … devin … --prompt-file "$BRIEF"` (`devin_bg.sh:13`). The match accepts a longer filename sharing the brief’s prefix, another lane using the same brief, or an unrelated command containing that text. It can return the timeout supervisor’s PID.
   - **Claude:** the expected prompt matches the launcher (`claude_bg.sh:14`), but any command containing `claude` and that prompt fragment qualifies, including the supervisor. The match does not establish that a Claude executable is alive.
   - **Codex:** `--label` is optional (`codex_local.sh:3`), yet detection requires it. Unlabelled launches are missed. The launcher executes a dispatcher (`codex_local.sh:15`), so a dispatcher containing the label can qualify without proving a live Codex child. The named files do not establish the eventual child’s argv.
   
   Failed or truncated `ps` output and processes changing after the snapshot introduce further false negatives or stale positives (`tick.sh:16,67`).  
   **Smallest fix:** record agent PID, start time, lane and executable at launch; validate those locally. For a minimal interim improvement, match executable identity and exact argv tokens, not flattened substrings.

7. **MEDIUM — Exporting the whole process table can prevent Python from starting.**  
   Evidence: `tick.sh:16,67`. `PS_SNAPSHOT` becomes one environment entry. On Linux, a sufficiently large entry can exceed the per-string exec limit and produce “Argument list too long”; total argv/environment limits also apply. Long agent prompts make this plausible.  
   **Smallest fix:** collect `ps` inside Python through a pipe instead of passing it through the environment.

8. **MEDIUM — Missing or unreadable inputs can abort the entire digest.**  
   Evidence: `tick.sh:25–29,34–43,51–55,61,103–107`. An empty events root works, and unreadable individual lane directories are silently skipped. A missing/unreadable events root or `LANES.txt` aborts before node and governor output. A vanished or dangling event during first-run `getmtime` also aborts. An unreadable event instead prints a placeholder and becomes seen, preventing a later retry.  
   **Smallest fix:** isolate failures by section and file, report skipped inputs, catch metadata races, and leave unreadable events unseen. Handle state-file read errors explicitly.

9. **MEDIUM — Event selection and rendering do not fully satisfy “every event, first ten lines.”**  
   Evidence: `tick.sh:22,32–39,51–55`. Only files directly under `events/<lane>/` with the timestamp prefix qualify. Other event names are silently omitted. Lines are truncated to 220 characters. Invalid encoded bytes are replaced, but binary NULs and terminal escape sequences remain unsanitized; filenames containing newlines also defeat line accounting.  
   **Smallest fix:** explicitly define the accepted event naming convention, escape unsafe filename/content characters, and display a clear marker for bounded or binary previews.

10. **MEDIUM — Lane parsing silently accepts malformed records and replaces duplicates.**  
    Evidence: `tick.sh:61–66`. Rows with other than three fields disappear without a warning. Three-field rows with empty fields, whitespace around fields, or path traversal are accepted. Duplicate names use the last row and move to its position. Actual examples are `h1_headsft` (`LANES.txt:69,72`), `h10_stage` (`82,85`), and `review_treen1` (`124,133,142,149`). The reviewed file has 182 rows and 177 distinct names, rather than the author’s earlier 176. A changed brief can also hide an older Devin process still running.  
    **Smallest fix:** trim and validate fields, reject unsafe lane names, report malformed rows, and explicitly document or reject duplicate replacement.

11. **MEDIUM — The unnumbered-folder fallback can miss or misattribute status.**  
    Evidence: `tick.sh:76–80`. Trailing digits and an optional underscore are removed only when the numbered **directory** does not exist. An existing numbered directory without `STATUS.md` prevents fallback. Multiple numbered lanes can inherit one unnumbered status and appear active together.  
    **Smallest fix:** prefer an explicit events-directory mapping. At minimum, fall back based on the status file’s absence and display the directory actually used.

12. **INFO — Ordinary concurrency and cap carryover mostly work.**  
    Evidence: `tick.sh:15,47–57,109–114`. With one stable state directory and lock inode, `flock` serializes runs, survives the exec into Python, and releases on process exit; a leftover lock file does not itself block later runs. Only printed candidates enter `shown`, so cap-excluded events remain new after a successful normal run. `--peek` leaves seen/last-tick contents unchanged.  
    **Remaining fix:** flush stdout successfully before committing seen state. Currently buffered output can fail after events have been marked seen. Replace `last_tick` atomically too; it currently can be truncated independently of `seen.txt`.

13. **INFO — Python 3.6 syntax and the normal metrics/governor paths pass static review.**  
    Evidence: `tick.sh:17–114` uses Python 3.6-compatible APIs and syntax. Lines `98–100` request free `/scratch`, load and available RAM; lines `103–107` print governor line four and handle missing/short files. Invalid text encoding in the governor is not caught. The script invokes no SSH or Git commands. With an ordinary default state directory, its seen file is separate from evwait’s.  
    **Smallest fix:** handle governor decoding errors; retain the stronger confinement changes above.

14. **INFO — Review validation was read-only.**  
    The [reviewed script](/scratch/jjyeung/orch_n30/so_rv_tick/tick.sh) matches `SHA256` (`8dc3ce63141c1256e3502408bd3d28879cf2e943fe11c3294b78ed86d8456667`), and `bash -n` passes. I did not execute the script, create temporary state, or reproduce the author’s timing tests.