<!-- recovered by seal_plan: transcript=71f94277 line=27314 utc=2026-11-14T01:32:10.619Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_APPROVAL_routed_read_probe_on_0_28_use_step200_export.md heredoc_quoted -->
# ORCH approval on RESULT 0130Z: one restoration and parity probe on trinity-0-28, with the step-200 export

## Approved

1. **Which export: step 200, not step 100.** The registered step-200 rule is the one that tests routed types, the step-200 export is landing now, and one 21.6 GB download serves both the gates and the decision. Start the download as soon as the operator's transport attestation for step 200 is in your inbox (the artifact is already there). A step-100 routed read is optional later, for the trajectory only.
2. **Download:** one stream through the governor into trinity-0-28 `/scratch`, behind main's transfers. Rate 8 MiB/s; you may raise it to 16 MiB/s only while the governor shows main idle, and drop back at once when main starts. Hash every part against the attestation before extraction; extract on `/scratch` only.
3. **GPU:** after CPU admission and a fresh ownership check, ONE production-export restoration and parity probe on trinity-0-28 GPU 3 (GPU 6 if 3 is taken by then), under vnice, hard ten-minute GPU timeout, as you proposed. Record peak memory, the time per item of whatever real items the parity inputs include, and the card's state after exit.
4. **Runtime admission (my ruling):** the tested Trinity runtime (Torch 2.13 / cu130, Transformers 5.19, reference kernels without the fast-path library) is admitted for the routed read if and only if P1 to P3 parity passes on the production export with the registered inputs and assertions. Report the parity numbers. Do not stage the 8 GB production interpreter on Trinity unless parity fails; if it fails, stop and tell me what differs.

## Limits on trinity-0-28

- `/scratch` there must keep at least 150 GB free at all times (it had 201.5 GB): the export, its extraction and your runtime must fit in about 50 GB together. Extract only what the loader needs, or stream members; if it cannot fit, say so before downloading. Do not use the RAM-backed storage for bulk data on a shared node.
- Before staging the cohort's RGB, masks and geometry, post the sizes and their sources (which are on `/data*`, which already on a node), so I can check the read budget. Reads from `/data*` go through the governor at 8 MB/s, one at a time, never while the export download runs.
- Other users' processes and cards are not touched. If the card is taken between your check and your launch, do not wait on it; report and name another.

## Then

Post one RESULT after the probe: parity verdict, memory, per-item time, and your request for the full 636-item routed read (card, expected duration from the measured throughput, what it will print). The step-200 direct read on Orchard proceeds independently and first.