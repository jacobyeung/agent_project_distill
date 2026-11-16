<!-- recovered by seal_plan: transcript=71f94277 line=28155 utc=2026-11-14T03:31:21.090Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_RULING_export_stream_failure_cause_and_recovery.md heredoc_quoted -->
# ORCH ruling on QUESTION 0328Z: cause, and one recovery with a resumable stream

## Cause (from the record, not a kill)

The governor's notices show it paused your stream at 02:55:50Z at the floor rate of 1,000 B/s because main's transfers needed the budget; your byte receipt at 02:55:28Z was 9,597 MB and the stream died at 9,610 MB. A connection held at 1 KB/s for many minutes was reset by the far end. This is the governor working as intended (we run behind main) meeting a stream that cannot survive a long pause. It is not an administrator kill and not a rate violation; say so in your log.

## Recovery: allowed once, after two things

**1. Make the stream survive pauses.** Change the transfer helper so that when the reader of a part ends early (reset or nonzero exit), it reopens the same generation-pinned object at the byte offset already delivered (a ranged read) and continues feeding the same pipe; the per-part and whole-stream hashes still decide. Wait at least 60 seconds between reopen attempts and stop after 8 attempts on one part with no bytes gained. Add CPU tests: a reset mid-part, a reset at a part boundary, a reset during a governor-style stall, and a wrong-generation refusal. Send me the diff and test result; I confirm by reading it. Do not start the transfer before that.

**2. Choose the node again, with main in mind.** A fresh export plus the depth files needs 24.3 GB; on trinity-0-28 that leaves 129 GB, and main has a run on that disk. Check, within your ssh budget, whether another allowed node (never 0-8, 0-23, 3-23; leave 0-18 free) has an empty large card and at least 300 GB free on `/scratch`. Report the candidates (node, free space, card, who else is on it). If one exists, the runtime and base move there node to node over InfiniBand and the export goes there; trinity-0-28 then gets nothing more. If none exists, we stay on trinity-0-28 with the hold threshold at 126 GB and the floor at 125 GB. Either way I announce the node and the bytes to main BEFORE the first byte moves; wait for my go.

## Housekeeping

- `export_BAD` (9.6 GB) stays where it is; no agent removes it. I am listing it for the user's removal list and telling main it exists.
- The source-side-archive idea is declined: it would leave a 21.6 GB archive on a node with no way for us to remove it.
- CPU preparation with the manifest continues.