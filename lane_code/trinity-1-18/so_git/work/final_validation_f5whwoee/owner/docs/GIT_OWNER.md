# Getting lane code into Git

The owner on **trinity-3-30** runs all Git commands in `/scratch/jjyeung/distill_sync/repo`.
Lanes run no Git. The hourly sync and kit command share `/scratch/jjyeung/distill_sync/.sync.lock`.
Nobody checks out another branch, rewrites history, forces a push, or pushes to main.

| Route | Lane supplies | Owner runs | Landing evidence |
|---|---|---|---|
| Reviewed kit | Archive, seal, archive SHA256, review path, unused name | Command below | `kits/<name>/KIT.json`, printed commit, matching origin and home heads |
| Hourly lane snapshot | Source under `/scratch/jjyeung/orch_n30/<lane>/` | Existing `lane_code_sync.sh` loop | `lane_code/<node>/<lane>/…`, `verified GitHub lane-code` in `sync.log` |
| Existing `eff/*` branch | Queue row in `e_*/PUSH_QUEUE.txt` or `eff_*/PUSH_QUEUE.txt` | Existing owner's push-queue step | `$S/PUSH_DONE.txt`; refusal reasons in `$S/PUSH_REFUSED.txt` |

Set `T` to the installed `orch_n30/tools` directory. The owner lands a kit with one command:

```bash
LCS_ENABLE_KIT_LANDING=1 bash "$T/land_kit.sh" kit.tar seal sha256 review.md name
```

Add `--dry` to validate, print the eligible file list and counts, and stop before Git or clone writes.
The review records `Builder: <identity>` and `Reviewer: <identity>`. Accepted verdict lines are
`GO`, `ACCEPT`, `VERDICT: GO`, and `VERDICT: ACCEPT`; Markdown headings/bold are accepted.
The last explicit verdict wins. `GO AFTER FIXES`, even with recorded fixes, requires a later
unconditional `GO`. Unknown explicit verdicts, missing reviews, wrong hashes, secrets in any
archive member, links, unsafe paths, an empty filtered kit, a dirty index/worktree, another branch,
or a conflicting name cause refusal. Optional review `Seal:` and `SHA256:` fields must match.
Identical content and provenance reuse the name and reverify/publish the current head.

The kit command applies the current filter caps and exclusions. It restores eligible duplicate
paths from the filter's manifest to preserve imports. `KIT.json` counts payload files separately
from itself. It records the review digest and a per-file SHA256/size/mode manifest. Both remote
heads must match the printed commit. The lock waits up to 120 seconds; `LCS_LOCK_TIMEOUT` can
set a timeout up to 3600 seconds. Audit directories stay under `$S/land_kit_*`; investigate a
failed/killed command before any restart. No automatic reset, cleanup, rollback, or retry runs.

The hourly route excludes `*_proof`, `runs`, `evidence`, caches, oversized files, and directories
with more than 2000 entries. `in`, `out`, `work/tree`, and `kit` are eligible unless an ancestor
is excluded. The owner checks explicit folders before expanding coverage:

```bash
LCS_ENABLE_DRY_COUNT=1 bash "$T/dry_count.sh" /scratch/jjyeung/orch_n30/swarm_opt
```

Counts deduplicate within each folder; hourly deduplication spans its whole node tree. Root gates
appear separately as `hourly_*` fields. See `COVERAGE.md` for the optional shell-copy extension.

A push-queue row is `<UTC> eff/<slug> <40-hex-sha> [<lane>/clone|<lane>/repo]`.
Only `e_`/`eff_` lane directories qualify. The owner fetches an already committed branch,
checks ancestry and changed-file secrets, then pushes the named commit to origin without force.
This route does not grant lanes permission to create commits; use a kit for uncommitted code.

The owner starts `LCS_ENABLE_SYNC_HEALTH=1 bash "$T/sync_health_loop.sh"` in tmux for a local
check every ten minutes. It writes one stale/failure event per incident and a recovery RESULT;
state lives under `$S/health/`. It makes no SSH or Git calls. A failed monitor stops the loop.
These tools are delivered for owner installation; no production loop was started by this lane.
