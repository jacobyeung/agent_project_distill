# C1 train mode, resume rotation and canary

`train()` calls `CarrierC1.train()` before FSDP wrapping. This enables Hugging
Face decoder-layer gradient checkpointing while the override keeps the frozen
base vision tower in eval mode. The pose loss and its arithmetic are unchanged.

The recipe replaces `checkpoint_every` with `resume_every_seconds` (default
1800; any finite positive number is accepted). The loop checks elapsed monotonic
time after each optimizer update. All ranks agree when any rank reaches the
interval. The timer starts at loop entry and resets after each completed save,
so startup and resume-save time do not consume the next interval. Exports do.
Budget, signal, m400-gate and final stops still save full resume states.

States use unique `checkpoint_<step>_<uuid>` directories. Each state contains
trainable weights, AdamW state, every rank's RNG, shard layouts, run binding and
absolute optimizer step; the existing deterministic schedule and batch order
resume from that step. Payloads are fsynced before the completion barrier.
Rank zero writes and fsyncs `complete.json` last, then deletes only this run's
old complete states, retaining the newest two. Selection checks bindings, file
sizes and the exact state directory contents; restoration also checks hashes.
Incomplete states remain untouched and cannot trigger rotation. Two full states
use about 252 GB; completing a third temporarily requires about 378 GB, excluding
exports and any interrupted states.

Use `--resume latest` to select the newest complete state in the configured
output directory, or keep supplying the existing resume-pin JSON file. Resume
still requires the same configuration, source commit, preparation and world size.
After an early crash, a fresh start accepts the existing `binding.json` only if
its contents match the new binding and no complete resume state exists. Partial
states remain untouched. A complete state requires resume; a mismatched binding
still refuses reuse of the output directory.

The export list is now `[100, 200, 400, 800]`. `m100` uses the same weights-only
export function as the other milestones. The m200/m400/m800 behavior, m400 review
gate and 800-step learning-rate horizon are unchanged. A replayed complete
milestone is retained after its identity and manifest/head pins pass validation;
an incomplete milestone refuses replay and remains untouched. This does not
rehash all exported LM weights. Adding 100 and changing the resume interval
fields changes the recipe/configuration identity; regenerate bound preparation
and authorization artifacts for this source and recipe.

The initialized-AdamW CPU fixture writes 3,744,051 payload bytes across native
rank, replicated and RNG files. Its measured full-save times were 0.0512, 0.0500
and 0.0521 seconds, including fsync, completion and rotation (one CPU rank with
mocked collective transport). This small fixture does not predict GPU throughput.
For a 126 GB GPU-run state, assume 0.5–1.0 GB/s aggregate effective storage
throughput: writing alone takes 252–126 seconds (2.1–4.2 minutes). GPU-to-host
copies, serialization, hashing and synchronization can increase that time.
Use roughly 3–5 minutes as a provisional save reserve under that assumption;
replace it with a measured full-size value in `schedule.checkpoint_seconds`.
No GPU save was measured.
