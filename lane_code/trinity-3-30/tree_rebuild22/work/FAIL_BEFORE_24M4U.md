# Real-path fail-before / pass-after for the 24m4u helper fixes (assembled by lane tree_rebuild22 from published CPU-job files; values copied from timings.json)

Both runs use the same command on the same Orchard rows: `rcj.sh r` (mode r of rcj/x.py), submitted on the preempt partition with the candidate kit. Only the rcj helpers differ: 173725 ran the 24m4t helpers (before), and 173754 ran the 24m4u helpers (after). The files are under /scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d<job>/<job>/ (timings.json, job.log and the published files).

| Fix (24m4u) | 173725, unfixed helpers (timings.json) | 173754, 24m4u helpers (timings.json) |
|---|---|---|
| Publication budget (5 MB) | aggregate_limit_status "FAIL", aggregate_publication_bytes 8,419,362, publication_errors [{"error": "ValueError", "file": "live"}]; post_returncode 1 | aggregate_limit_status "PASS", aggregate_publication_bytes 3,504,597, publication_errors [] |
| nd / na publication (nsample) | nsample {"reason": "ValueError", "status": "REFUSE"}; nd.json, na.json.gz and n_sample.json are absent from the published list | nsample: files nd.json, na.json.gz, routing_types.json and n_sample.json published; matched 43,101; absent 4,797; task_ii PASS; task_iii PASS |
| routing_types | routing_types "UNAVAILABLE", routing_types_refusal "ValueError" | routing_types "PASS", with all five P quotas inside 10% (routing_types.json) |
| Helper diagnostics (full exception lines) | refusal reasons carry only the class name "ValueError" | refusal reasons carry the full exception line and traceback (see 173796 nd.json "reason": "ValueError: E96:child:1 ... nd.py line 318 ... E96:tree") |

Limit: the unfixed helpers published only the class name, so the original subtype and line of 173725's two ValueErrors cannot be recovered from 173725 itself. The fix makes later runs publish them (173796 shows this). In 173754, nsample's status FAIL comes from task_i, which is the extent refusals that route T addresses, not from a helper error.

The 24m4x2 nd.py tree-pin fix follows the same pattern. Before: 173796 (24m4w helpers), nd.json and timings.json "reason" = ValueError E96:tree at rcj/nd.py:318. After: candidate 173817 (24m4x2 helpers), which runs the same command and is in progress at d173817.
