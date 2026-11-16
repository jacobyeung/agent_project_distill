# Build brief 15: recover the VLA kits (LIBERO few-demo test, navigation runner) and prove them on CPU

Builder: Claude Opus, medium effort. Written by lane queue_synth, 2026-11-16. CPU only. No VLA GPU run starts before the spatial model is strong (user, 2026-11-11); this brief keeps the code ready.

## Rules
Read `/home/jjyeung/.claude/CLAUDE.md` section "Key Trinity Cluster Rules", then `B/tools/CLAUDE_LANE_RULES.md` and `B/tools/LANE_RULES.md` (B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`). No Git, no deletion, no GPU, no Orchard job. Orchard only through `B/tools/ossh.sh`, one batched listing. Downloads only as governed streams, and only after asking ORCH. Lane folder `/scratch/jjyeung/orch_n30/vla_kits` (cap 20 GB); events `B/events/vla_kits/`.

## Why
The user's second goal: a strong spatial model should make VLA fine-tuning cheaper (fewer demonstrations) and better. The tests are designed (`distill_design/VLA_ACTION_HEAD_DESIGN_20261111.md` sections 4.1, 4.2, 4.4, 5) and the kits were built and CPU-tested on trinity-2-18, which is down. `RECOVERY_MAP_2_18_OUTAGE_20261115.md` row 8c lists them as lost. The LIBERO kit's record says an Orchard copy with environments and data exists.

## Inputs
- Records: `VLA_LIBERO_KIT_20261111.md` (StarVLA 985c2238 overlay, LIBERO and LIBERO-Plus, recipe schema 10, trainer wrapper, head hook, 5-demo subset `d5_s0` with 50 demonstrations and 6,281 frames, blind priors: demo replay 54.2% on LIBERO-Spatial, so the validity bar is about 64%), `VLA_NAV_RUNNER_20261111.md` (package navrun, R2R-CE in habitat-sim 0.2.4, lists and blind priors, oracle-click ceiling 0.802), `VLA_WHERE_PROVIDER_20261111.md`, `VLA_ACTION_HEAD_DESIGN_20261111.md`, `DYN_PROBE_KIT_20261111.md`.
- Possible survivors: Orchard `/project/community/jjyeung/vla_libero` (kit copy, environments, data; unverified since 2026-11-11); trinity-0-13 `envs/nav_habitat024` and older `nav_build` copies (2026-11-06) on trinity-0-13, 1-8 and 3-30 (recovery map row 8c).

## What to do
1. One Orchard listing of `/project/community/jjyeung/vla_libero` with sizes and the kit's `KIT_SHA256`; one listing of the navigation survivors on trinity-3-30. Report what exists before rebuilding anything.
2. Restore or rebuild, in this order: the LIBERO kit's code (trainer wrapper, data patch, head hook, policy server, launch and readout scripts, compare tool), then navrun (episode loop, metrics, five policy formats, lists, row builder). Rebuild from the records where no copy survives; keep interfaces and config keys as recorded.
3. Re-run the CPU proofs the records name: hook parity with StarVLA's head at step 0, exact resume, repeat equality, parity of eval and training images, the conformance tests T-3 to T-6, random and demo-replay priors on ten episodes, navrun's 58 CPU tests and the shortest-path oracle on rand100.
4. Bind the student: the action head attaches to an export of the current lineage (step 544 today; the A2 export later) with its heads dropped (arm B1) and with the where input (arm U1). Under the end-to-end ruling U1's where input must come from heads inside the artifact (briefs 04 and 05), not from the old runtime: mark U1 blocked until then.
5. Costs for the queue, from the records: shake-down about 3.6 H100-hours plus 2 GPU-hours; decisive Test L 2 x 18 H100-hours plus 30 to 60 GPU-hours of evaluation; Test N 2 x 27 H100-hours plus about 36 GPU-hours. The base-model arm B0 is approved by the user as the base comparison.

## Tests
As in step 3; plus the first training batch of arm B1 through the full forward on CPU with a tiny model and with the real step-544 export's config (no weights loaded on CPU if memory forbids: say so).

## Do not touch
D0 job 170111, the VSTI read, K1, Orchard queues. Nothing is installed into /home.

## Deliver
`out/VLA_KITS_STATUS.md` (what survived, what was rebuilt, tests, hashes), mirror on a second node, STATUS.md, one RESULT event. Review: none until a GPU run is proposed.
