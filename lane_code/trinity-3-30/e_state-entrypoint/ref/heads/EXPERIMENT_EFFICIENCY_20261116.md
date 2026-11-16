# Experiment efficiency: where time is lost between "proposed" and "result read", and the eight changes that remove it (2026-11-16)

**Status: DESIGN.** Eight build briefs are ready and nothing is built. No running job, sealed kit, live lane or shared service was changed. Builders append their results under "Build results" at the end.

Paths. B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`. AUD = `/scratch/jjyeung/orch_n30/eff_audit` on trinity-3-30 (five audit notes, the briefs, a tested helper skeleton); the hourly code sync mirrors it to GitHub branch `lane-code` under `lane_code/trinity-3-30/eff_audit/`. Evidence window: 2026-11-15 17:00Z to 2026-11-16 11:00Z, plus the pilots of 11-14 and 11-15.

## Question

USER 2026-11-16: make our experiments efficient and easy. Where do time, GPU hours and agent effort go between "experiment proposed" and "result read", and which code or process changes remove that loss without weakening the cluster IO rules, legality or provenance? The same day the user added: "You should be committing and pushing code frequently so we don't lose history."

## Answer

A new experiment loses most of its time in four places, and none of them is the GPU. Its kit is a fork of an older kit, so it is rebuilt and re-read line by line. The fork is first executed with its production config on the batch host, where it fails. Each fix earns another confirmation round. And the code lives on one node's `/scratch`, so a node failure erases it. Summed over the critical paths of three kits (D0, K1, VSTI), the 18-hour window shows about 9 h of measured delay: 6.3 h from first-launch failures, 2.3 h from confirmation rounds and 0.5 h from input uploads queued behind review. The loss of trinity-2-18 cost a further 30 to 40 agent-hours.

Eight changes remove these losses. Each is one build with its own files, so all eight can be built in parallel. Each lands as branch `eff/<slug>` and takes effect at the next epoch.

| Rank | Change (brief in `AUD/briefs/<slug>.md`) | What it saves | Size | Touches running work |
|---|---|---|---|---|
| 1 | `code-in-git`: trainer tree in the repository, one command to accept a build, the Git owner publishes every queued branch hourly | Measured: 30 to 40 agent-hours and 1.5 to 2 days of wall clock per node loss (two nodes lost in one week); ends tar-and-diff bookkeeping per build | L | no |
| 2 | `kit-dryrun`: the real batch entry with the production config on CPU, plus config and row lints, before any review or submission | Measured: 3 of 3 first-launch failures this session (about 4 h, 1.3 h and 1 h) and 5 of 9 pilots on 11-14/15 (1.5 to 2 h and one allocation each) | M | no |
| 3 | `orchkit-core`: one pin manifest, launcher, stager, return path and ledger; a new job is a config | Estimated 3 to 6 h per new kit (fork, diff table, review that reconstructs it); measured 2 pilots lost to stale pins; ledgers no longer die with a node | L | no |
| 4 | `review-gate`: one review with a machine-readable verdict; a script confirms fixes inside the verdict; rules cited by hash | Measured: 2.3 h of confirmation waits in 18 h and 7 extra reader lanes; estimated 8 h for the contracts chain r1 to r6 | M | no |
| 5 | `reader-harness`: one reader; a read is a config, and a plan of reads shares one job | Estimated 1 to 4 h of queue per read on the one-job partition, and no read-kit fork per read | L | no |
| 6 | `orch-watch`: one watcher that reports state changes; lanes live on a heartbeat lease | 4 of 6 Opus lanes were polling operators (tokens, not measured); measured 29 to 45 min lost to a reviewer that had ended; 14 rotations in 18 h | M | no |
| 7 | `govstream`: one governed-stream launcher and one mirror command | Estimated 15 to 30 agent-minutes per transfer (about 25 hand-written launchers); measured 18 min for one refused stream and 30 min of input upload behind review | S | no |
| 8 | `state-entrypoint`: one current-state page, an index readable in one call, generated briefs | Estimated 60K down to 15K tokens per orchestrator start and 40K per lane that reads the index; no start from a six-day-old handoff | M | no |

Sizes: S up to 3 agent-hours, M 4 to 8, L 10 to 16. The eight total 55 to 75 agent-hours and, built in parallel, about one day of wall clock.

### Steps the orchestrator can take today without a build
