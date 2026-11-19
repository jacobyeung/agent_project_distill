# Getting lane code into Git

The designated Git owner on **trinity-3-30** runs Git; lanes supply files and queue rows.
The hourly sync, kit command, and manual owner Git work share `$S/.sync.lock`, where
`S=/scratch/jjyeung/distill_sync`. The kit clone is `$S/repo`, already on `lane-code`.
Never rewrite history, force a push, or push to main.

| Route | Lane supplies | Owner action and evidence |
|---|---|---|
| Reviewed kit | Archive, seal, SHA256, review path, unused name, identities | Runs kit command; checks `$S/KITS_LANDED.txt`, kit RESULT event, and `kits/<name>/KIT.json` |
| Hourly snapshot | Source under `/scratch/jjyeung/orch_n30/<lane>/` | Runs hourly sync; checks `lane_code/<node>/<lane>/…` and `verified GitHub lane-code` in `sync.log` |
| `eff/*` queue | Queue row for an existing commit | Makes the commit, runs queue publisher; checks `$S/PUSH_DONE.txt` or `$S/PUSH_REFUSED.txt` |

The seven owner tools are installed; the health loop runs every ten minutes, as reported
in the supplied review. This package is a replacement for selected installed files.
Set `T` to the installed `orch_n30/tools` directory. Python 3.6.8 and 3.12 are supported.
The fixes below require `LCS_REVIEW2_FIXES=1`, default OFF, in each command or loop environment.
With it unset, the installed behavior remains active, including its documented limitations.
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
Ordinary prose such as “rejects symlinks” does not. The first verdict remains
case-insensitive. Any unindented `verdict:` label containing `AFTER FIXES` refuses regardless
of case. `GO AFTER FIXES` needs a separate later GO verdict file;
appending GO to the conditional file does not authorize landing.

A matching `Seal:` or `SHA256:` line must bind the review, or the owner passes
`--bind-sha <archive-sha256>` after reading it. Every supplied binding must match.
Bullets, numbered lists, headings, quotes, table rows, and labels wrapped in bold,
backticks, or underscores are recognized. Labels can include up to two leading words
(for example `Archive SHA256`); `SHA-256` and `=` separators also qualify.
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
path inside the test root. Network, SCP-style, and `file://` URLs refuse; relative local paths qualify.
Both remotes must verify
before the landing receipt and `<UTC>_RESULT_kit_<name>_landed.md` event are written.
`$S/KITS_LANDED.txt` is local to trinity-3-30; lanes on other nodes read the shared RESULT event.

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

The hourly excludes proof/run/evidence/cache directories, oversized files, and directories
with more than 2000 entries. `in`, `out`, `work/tree`, and `kit` qualify unless an ancestor
fails a rule. Before expanding coverage, the owner runs:

```bash
LCS_REVIEW2_FIXES=1 LCS_ENABLE_DRY_COUNT=1 bash "$T/dry_count.sh" /scratch/jjyeung/orch_n30/swarm_opt
```

Only existing nonsymlink folders under `/scratch/jjyeung/orch_n30/` qualify. Counts deduplicate
per folder; hourly deduplication spans a node tree. `files` and `bytes` retain the raw filter totals;
`hourly_files` and `hourly_bytes` apply ancestor exclusions, MAXDIR, and substring exclusions
across the folder boundary (including `out/devin_traces`). If that pruning overlaps deduplicated
output, the command refuses an ambiguous count; pass the containing lane root instead.
`COVERAGE.md` lists the rules.

Queue rows are `<UTC> eff/<slug> <40-hex-sha> [<absolute-clone-path>]` in
`e_*/PUSH_QUEUE.txt` or `eff_*/PUSH_QUEUE.txt` on trinity-3-30 only. An explicit clone path must
be `/scratch/jjyeung/orch_n30/<lane>/clone` or `/scratch/jjyeung/orch_n30/<lane>/repo`; a relative
path is permanently refused. An omitted fourth field selects the lane's clone/repo locally.
**The designated Git owner makes those commits**
in an authorized scratch lane clone under the owner lock and supplies the SHA to the lane.
The publisher fetches, checks ancestry/secrets, and pushes the named commit to origin without force.

The owner starts `LCS_REVIEW2_FIXES=1 LCS_ENABLE_SYNC_HEALTH=1 bash "$T/sync_health_loop.sh"` in tmux.
Every ten minutes it checks local evidence, emits one event per incident/recovery, and records
delivery in `$S/health/`. Consumers may move delivered events; only undelivered events replay.
Ordinary errors log to `$S/health.log` and the next tick runs. Signal exits stop for owner
investigation under cluster rules. Replacement Python files load on the next tick.
The owning orchestrator must arrange a restart only when the loop's environment switch changes.
