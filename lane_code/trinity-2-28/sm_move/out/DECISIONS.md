The package changes three installed tools and adds the hourly wrapper. The default host remains `trinity-3-30`. The robust flag and budgets remain owner-managed state.

Every `3-30` occurrence in the input tools has the following disposition. Line numbers refer to `in/tools/`; the inventory comes from `grep -n 3-30 in/tools/*`.

| Input occurrence | Decision and reason |
|---|---|
| `lane_code_sync.sh:4,6` | Describe robust staging on `LCS_HOST` and retain `trinity-3-30` as its documented default. |
| `lane_code_sync.sh:33` | Validate `LCS_HOST` and compare it with `hostname -s` before taking the sync lock. |
| `lane_code_sync.sh:126,134,155` | Keep the legacy comments, receiver command, source path, and local label unchanged. The driver refuses legacy mode on a different host before any staging or queue work. This preserves the installed legacy command text. |
| `lane_code_stage.sh:96` | Format the receiver as `$LCS_HOST.ib`. The default generated program remains byte-identical. |
| `lane_code_stage.sh:170,172` | Use `LCS_HOST` as the local node label and `$LANES_ROOT` as its source. Node labels remain actual source-node names, including when a node becomes remote. |
| `land_kit.py:420` | Check `hostname -s` against the validated host. Apply this guard in test mode too, so tests must supply a fake hostname rather than bypass the guard. |
| `GIT_OWNER.md:3,65,99` | Supply replacement owner, receipt-location, and queue paragraphs in `GIT_OWNER_patch.md`. The installer does not edit this document. |
| `sync_health.py:214,215` | Keep unchanged: the health process stays on `trinity-3-30`. Its existing `LCS_LOG` setting selects the shared heartbeat. |
| `sync_health_loop.sh:2,6` | Keep unchanged: the health wrapper still starts only on `trinity-3-30`. |

Other implementation decisions:

- Robust staging derives its default remote list from `trinity-1-18 trinity-2-28 trinity-3-30`, omitting the configured host and preserving that order. A nonempty `LCS_REMOTE_NODES` still overrides it. Empty overrides retain the existing fallback behavior. The legacy list stays unchanged.
- Hosts must match `trinity-[0-9]+-[0-9]+` and must not be any of the six prohibited names. A valid host outside the three-node source list stages all three remotely and itself locally. Existing remote-override validation remains unchanged.
- Remote status 66 requires the exact no-source marker before it becomes a SKIP. Silent status 124, 137, or 255 remains a SKIP only for remote `trinity-2-28`; local failures on that host remain failures.
- The heartbeat retains the previous file's last 300 lines and appends this run's evidence and HOST line. A normal verified run therefore leaves at most 304 lines. Evidence comes from the driver's `log()` calls, never from remote output or a reread of a shared log.
- With a heartbeat enabled, early exits emit missing START and END lines to the run log before copying them. The normal default log stays unchanged when no heartbeat is requested. Queue-only, dry, and stage-only runs get terminal END evidence but no fabricated verification.
- The EXIT trap preserves the original return status. Catchable HUP, INT, and TERM exits write failure evidence; SIGKILL, power loss, or a failed filesystem cannot guarantee a final heartbeat. The unchanged health monitor detects the absence of new verified evidence after more than 90 minutes.
- A heartbeat write uses an exclusive temporary in the destination directory, flushes it, and renames it atomically. Failed writes log a warning and preserve the run status. An unsuccessful temporary is retained for inspection rather than deleted.
- The heartbeat directory must already exist. Use one shared file visible to the monitor on `trinity-3-30`; a path under the new host's local `/scratch` is not a cross-host channel. Only the new sync host should write that heartbeat during cutover.
- The new wrapper inherits the caller's environment and adds no exports. It preserves the existing driver invocation and hourly sleep, and stops on status 128 or higher. Ordinary nonzero exits retain hourly scheduling.
- `land_kit.sh` needs no change because it already inherits `LCS_HOST`. The filter, scanner, dry-count tools, SSH helper, and health tools are not delivered as replacements.
- Installation and rollback run on `trinity-3-30` under its existing lock. They do not disable robust mode. Installation checks package/preimage hashes and refuses an existing wrapper; rollback restores verified preimages and renames the wrapper aside. Neither action coordinates an already-running new-host sync, so the owner must schedule rollback while that loop is stopped.
- The failover instructions use `$GITHUB_URL` because no supplied file identifies the origin URL. The owner must use the current repository's configured GitHub URL. A Git clone must follow the cluster's transfer limits; this package performs no live clone or transfer.
- The test harness changes only the copied tssh lock-directory assignment so its writes stay inside the fixture. Fake SSH runs the generated remote program locally, substitutes only its initial source directory, and executes the receiver locally. Recorded commands are compared without path, timestamp, or argument normalization.

The no-archaeology review retained references to preimages, the old running loop, and input line numbers because the owner needs them to install, cut over, and roll back safely. They describe operational state, not a development narrative.
