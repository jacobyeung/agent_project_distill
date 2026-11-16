# E-A frozen-feature probe

The primary readout standardizes each channel using training-only moments and normalizes tokens before and after channel averaging. Every arm uses 1,024 channels, matched heads and fixed optimizer budgets. The card shows standardized final-layer and unstandardized four-tap controls. Extraction reports native and delivered channel energy shares for each tap and split.

R1 compares each arm with A7 under the same head using paired room bootstrap intervals. A deficit interval wholly below −3 points fails; an overlapping interval permits the pilot. T1 selects keys provisionally before teacher labels exist. R3 can veto selection/presence keys; R2 affects mask keys only. Outside arms must beat the own baseline with a paired interval excluding zero to replace its selection keys or supply a mask-only tower.

The real-frame spatial gate compares original and mirrored instance features and rejects shifted/transposed alternatives. Every provider must pass before extraction. SAM must also demonstrate bf16 autocast during its GPU forward. CPU descriptor tests validate fault rejection; real-provider measurements remain pending.

Phase 1 runs A1, A7 and A2 on trinity-1-18 GPU 7, then prints the provisional card. Phase 2 requires completed phase-1 tasks. All runtime environments and both G3T host paths are in the staging inventory. The shared ledger caps GPU work at 240 minutes. Phase-1 planning reserves 165 minutes including calibration and three readouts; measured timing comes from the GPU run.

The CPU tests cover room gates, extraction over all providers, A8 composition, train-only statistics, head scale, real-mask spatial faults, interval-based choices, pending teacher labels, resume behavior and task entry points. `CPU_R3_FINAL.log` and `MUTATIONS_R3.json` record validation. `GPU_COMMAND.md` supplies the executable hand-off. Real-arm channel shares and outside-provider spatial gates are PENDING until their scheduled GPU runs.
