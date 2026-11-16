# Project-space sampling around production checkpoint 269

## Result

The one-session capture passes its integrity and coverage checks. On **2026-11-14**, 52 filesystem samples cover **03:47:40Z–04:03:14Z**. The largest sampling gaps are **15.005 seconds** during the fast interval and **30.002 seconds** during the slow interval.

Free space fell from **434.24 GB** to **363.09 GB** at **04:00:55Z**, then recovered to **512.89 GB** by **04:01:25Z**. The capture ends at **537.86 GB**. The maximum drawdown is **71.14 GB**. The ordinary five-minute samples bracket this fall but do not capture its minimum or its two 400 GB crossings.

## Timing and scope

All four ranks report the step-269 save, with maximum duration **70.9562 seconds**. The trainer's stdout guard has mtime **03:52:03.231Z**. Adding that duration gives a derived end of **03:53:14.187Z**; the metric schema has no native absolute end timestamp. The minimum occurs about **7 minutes 41 seconds** after the derived end.

The sampler uses one existing-master session, writes no files on Orchard and starts no job step. It queries only filesystem space, except for the one authorized top-level metadata listing when the drop exceeds 20 GB.

At **03:59:55Z**, that listing contains four metadata filenames, representing three unique files and **616 bytes** in the production persistent root. It reads no payload, finds no subdirectory and is not truncated. This observation does not identify the writer responsible for the filesystem-wide change.

## Operational consequence

Ordinary five-minute monitoring remains active; the one-shot allowance is consumed. A new floor crossing waits for the next ordinary sample. A recovery produces one nonurgent transient report; confirmed 200/140 GB crossings remain urgent.

Projection inputs wait for the next ordinary sample. A further fall confirms a point; the 20 GB tolerance limits upward recovery, and the applicable floor is the most severe breached floor. The monitor retains the raw series and computes both projections from confirmed points only. It reports a projection below three hours to 150 GB or below 150 GB at the deadline, with urgent severity only when the deadline forecast is below 140 GB. Pending or rejected points can leave the confirmed endpoint more than one interval behind the latest raw observation.

All **39 local tests** and the live **04:34Z** policy check pass. The held replay excludes the unconfirmed 03:59 low. The live check records **587.88 GB** raw free space and a **435.83 GB** deadline forecast from the confirmed endpoint at **04:24Z**. These conditional projections are not storage guarantees.

## Evidence

- Operator verification: `orchard_cp2/out/SAVE_WINDOW_169097_NEXT/VERIFIED.json`, SHA256 **20b5b35378a65ddd2873b54df8371ae109052f5e4bcba2ecf5be13e6c27d36ec**.
- Exact series: `orchard_cp2/out/SAVE_WINDOW_169097_NEXT/series.jsonl`, SHA256 **b96c853c79dbbe9c43f8ed8ceb706dcad7c6fb293693305a745cc2a002e0c370**.
- Durable archive beside this record: `ORCHARD_SAVE_WINDOW_169097_20261114T040853Z.tar.gz`, **55,237 bytes**, SHA256 **d4f95e3580cfacc85b6bced7bcac9bf1e6f4f2fc435e81d365d534db48a9503d**. All copied bytes verify. Its nineteen members include raw transport, the series, timing evidence, controller and probe sources, tests, authority and the verification.
- Monitor-policy archive beside this record: `ORCHARD_SPACE_POLICY_169097_20261114T043702Z.tar.gz`, **12,496 bytes**, SHA256 **6c3e931b1c45ae7266dbf7897022abefac09b099d8f6c103c307a3d641bd5d50**. All copied bytes verify. Its twelve members bind source **c728cde9...**, tests, authority, raw and confirmed series, and the live check.
