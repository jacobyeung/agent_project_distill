# Getting lane code into Git

The designated Git owner runs Git on the sync host `LCS_HOST` (now **trinity-2-28**; tools default to trinity-3-30,
so set `LCS_HOST` in every owner command there); lanes supply files and queue rows. The hourly sync, kit command,
and manual owner Git work share that host's `$S/.sync.lock`, where `S=/scratch/jjyeung/distill_sync`. The kit clone is `$S/repo`, on `lane-code`.
Never rewrite history, force a push, or push to main.

| Route | Lane supplies | Owner action and evidence |
|---|---|---|
| Reviewed kit | Archive, seal, SHA256, review path, unused name, identities | Runs kit command; checks `$S/KITS_LANDED.txt`, kit RESULT event, and `kits/<name>/KIT.json` |
| Hourly snapshot | Source under `/scratch/jjyeung/orch_n30/<lane>/` | Runs hourly sync; checks `lane_code/<node>/<lane>/…` and `verified GitHub lane-code` in `sync.log` |
| `eff/*` queue | Queue row for an existing commit | Makes the commit, runs queue publisher; checks `$S/PUSH_DONE.txt` or `$S/PUSH_REFUSED.txt` |

The seven owner tools are installed; the health loop runs every ten minutes with
`LCS_REVIEW2_FIXES=1`. This package replaces only `land_kit.py` against that installed base.
Set `T` to the installed `orch_n30/tools` directory. Python 3.6.8 and 3.12 are supported.
The fixes below require `LCS_REVIEW2_FIXES=1`, default OFF, in each command or loop environment.
With it unset, round-1 behavior remains active, including its documented limitations.
The owner reads the review, confirms that it covers this archive, then runs:

```bash
LCS_REVIEW2_FIXES=1 LCS_ENABLE_KIT_LANDING=1 bash "$T/land_kit.sh" kit.tar seal sha256 review.md name \
  --builder lane_builder --reviewer independent_reviewer --bind-sha sha256
```

Both identities are required and must differ. The review needs no identity lines.
Its first nonempty line must be `VERDICT: GO`, `VERDICT: ACCEPT`, or
`VERDICT: ACCEPT WITH FINDINGS`, without indentation or Markdown. Later unindented
`VERDICT:` lines must also use a supported value; this later-line label is case-sensitive.
Uppercase `NO-GO`, `NO GO`, or `REJECT` tokens and uppercase continuations such as
`NO-GOOD`, `REJECTED`, and `REJECTION` anywhere, including quotes, refuse the file.
Negative `Verdict:` or `Status:` lines refuse regardless of case, including `No-Go`,
`Reject`, `Rejected`, `Rejection`, `Hold`, and `Wait`; a line starting `No-Go` or `No-go`
also refuses. Title-case words in ordinary prose do not refuse: “Rejects symlinks”,
“Hold the lock”, and “Verdict: see above” pass. The first verdict remains case-insensitive.
Any unindented `verdict:` label containing `AFTER FIXES` refuses regardless of case.
`GO AFTER FIXES` needs a separate later GO verdict file;
appending GO to the conditional file does not authorize landing.

A matching `Seal:` or `SHA256:` line must bind the review, or the owner passes
`--bind-sha <archive-sha256>` after reading it. Every supplied binding must match.
Bullets, numbered lists, headings, quotes, `| SHA256 | value |` rows, and labels wrapped in bold,
backticks, or underscores are recognized. Labels can include up to two leading words
(for example `Archive SHA256`); `SHA-256` and `=` separators also qualify.
As an additional refusal check, every 64-hex token must match the archive SHA on a line
naming both SHA256/SHA-256 and an archive, `.tar`, or `.tgz`; `sha256sum:`/`sha256sum=`
lines have the same check. A pipe table naming Archive and SHA256/SHA-256 in its header
gets this check on its subsequent pipe rows until a non-table line. These checks do not
grant binding: unfamiliar formats still need a recognized matching field or `--bind-sha`.
`KIT.json` records the binding, identities, verdict digest, per-file manifest, and skipped files.
`--dry` takes the same lock and creates an audit directory; it stops before Git or clone writes.
Every filtered file prints as `SKIPPED` and refuses
unless the owner passes `--allow-skips`. Eligible duplicate paths are preserved.

Wrong hashes, secrets in any member, links, unsafe paths, empty payloads, conflicting names,
another branch, a changed tracked worktree, or a dirty index refuse. Identical content and
provenance republish the current head. Git disables automatic maintenance and terminal prompts.
Production tool/path overrides require an isolated `LCS_TEST_ROOT`; test destinations cannot
overlap the production state or clone, even through resolved symlinks. Before any clone mutation,
test mode checks every fetch and push URL for both remotes: each must resolve to a filesystem
path inside the test root. Network, SCP-style, `file://`, and leading `~` URLs refuse;
relative local paths such as `./~repo.git` qualify.
Both remotes must verify
before the landing receipt and `<UTC>_RESULT_kit_<name>_landed.md` event are written.
`$S/KITS_LANDED.txt` is local to the sync host; lanes on other nodes read the shared RESULT event.

The lock waits **600 seconds** by default (`LCS_LOCK_TIMEOUT`, maximum 3600). The hourly
uses a nonblocking lock and skips overlapping starts. Land just after `END ok`; stale events
quote the latest lock skip. Audit directories remain under `$S/land_kit_*`. Investigate
failed/killed operations before restarting; remote pushes and receipt writes are separate.
If origin refuses a push, stop and contact the user before the next hourly run: the local commit
can block hourly origin pushes while home advances. No rollback, force, or automatic retry runs.
On add/commit failure, the kit command resets only `kits/<name>` in the index and checks that
the index is clean. Inspect HEAD first because a timeout may follow a completed commit. If the
kit is untracked, move its directory aside before rerunning. Keep that directory and the audit.
If cleanup fails, contact the user before the hourly can commit the staged kit. A killed process
cannot clean its index; its recovery also requires the user. The command does not stop the hourly.
The coordinator's `work/realgit4_by_swarm_opt/` logs prove the successful landing, hourly
kit preservation, failed-commit cleanup, and origin-rejection STOP paths on both interpreters
(3 tests, 0 skips each). The current package's real-Git rerun command is in `HANDOVER.md`.

The hourly excludes proof/run/evidence/cache directories, build by-products (test-run and test-output trees, temporary and 32-hex run directories, payload interpreters, nested lane copies, extracted archives, rehearsals and attics; rules in `lane_code_filter.py`), oversized files, and directories
with more than 2000 entries. `in`, `out`, `work/tree`, and `kit` qualify unless an ancestor
fails a rule. Before expanding coverage, the owner runs:

```bash
LCS_REVIEW2_FIXES=1 LCS_ENABLE_DRY_COUNT=1 bash "$T/dry_count.sh" /scratch/jjyeung/orch_n30/swarm_opt
```

Only existing nonsymlink folders under `/scratch/jjyeung/orch_n30/` qualify. Counts deduplicate
per folder; hourly deduplication spans a node tree. `files` and `bytes` retain the raw filter totals;
`hourly_files` and `hourly_bytes` apply ancestor exclusions, MAXDIR, and substring exclusions
across the folder boundary (including `out/devin_traces`). When no root gate excludes the folder,
the command refuses if any path is pruned and either duplicates are nonzero or their count is unavailable;
pass the containing lane root instead. It does not test whether the pruned path was a duplicate.
`COVERAGE.md` lists the rules.

Queue rows are `<UTC> eff/<slug> <40-hex-sha> [<absolute-clone-path>]` in
`e_*/PUSH_QUEUE.txt` or `eff_*/PUSH_QUEUE.txt` under `/scratch/jjyeung/orch_n30` on the sync host only. An explicit clone path must
be `/scratch/jjyeung/orch_n30/<lane>/clone` or `/scratch/jjyeung/orch_n30/<lane>/repo`; a relative
path is permanently refused. An omitted fourth field selects the lane's clone/repo locally.
**The designated Git owner makes those commits**
in an authorized scratch lane clone under the owner lock and supplies the SHA to the lane.
The publisher fetches, checks ancestry/secrets, and pushes the named commit to origin without force.

The hourly loop runs on trinity-2-28 in tmux `lane_sync`: `LCS_HOST=trinity-2-28 LCS_HEARTBEAT=$B/code_sync_heartbeat/HEARTBEAT.log
nice -n 10 bash $T/lane_code_sync_loop.sh`; each run rewrites that small shared heartbeat (START, verified push, END, HOST lines).
The health loop stays on trinity-3-30 in tmux `sync_health`: `LCS_LOG=$B/code_sync_heartbeat/HEARTBEAT.log LCS_REVIEW2_FIXES=1
LCS_ENABLE_SYNC_HEALTH=1 bash "$T/sync_health_loop.sh"`. Every ten minutes it reads the heartbeat, emits one event per
incident/recovery, and records delivery in its local `$S/health/`. Consumers may move delivered events; only undelivered events replay.
Ordinary errors log to `$S/health.log` and the next tick runs. Signal exits stop for owner
investigation under cluster rules. Replacement Python files load on the next tick.
The owning orchestrator must arrange a restart only when the loop's environment switch changes.
Before installing, run `python3 -I -c 'import lzma'` in the owner's interpreter environment
(or use the configured `LCS_PYTHON`); the unconditional import requires `_lzma` even with the switch off.


### If the sync host fails
1. Copy a surviving clone to an allowed lane node over InfiniBand (`git bundle create - --all` piped through `tools/tssh.sh <new>.ib`, `git clone --branch lane-code` from it, old `.git/config` restored, `refs/remotes/origin/main` set); clone from GitHub only if no clone survives and the user approves a throttled download, without `--single-branch`.
2. Put `LCS_ROBUST_SYNC`, `LCS_ROBUST_BUDGETS`, `KITS_LANDED.txt` and `PUSH_*.txt` into the new `$S`, check `ssh -o BatchMode=yes <new>.ib true` once from each source node, and require `LCS_HOST=<new> bash $T/lane_code_sync.sh --dry` to succeed.
3. Start `LCS_HOST=<new> LCS_HEARTBEAT=$B/code_sync_heartbeat/HEARTBEAT.log bash $T/lane_code_sync_loop.sh` in tmux, verify its first push with `ls-remote`, then stop any old loop; exact commands and the non-fast-forward recovery are in `SYNC_HOST_MOVE.md`.
