# Draft registration card: RL kit dry run (not registered; needs ORCH GO)
- What: rlkit-v1 sampler, 200 R0-rl prompts x 8 draws (half forced: head/direct alternating), temperature 0.7, top-p 0.95, seed 17, 4,096 sampled-token budget, 32 frames (64 as a second arm only if ORCH asks; about twice the prefill cost).
- Export: <bound by ORCH>; tree b01ce449 reader; head path served by the reader's s1_grounding backend (SAM 3 + G3T frozen, mask_source mdg).
- Hardware: one 48 GB card (Trinity under vnice, or trinity-0-13 at normal priority), at most one hour (3,300 s cap), resumable per draw. Data and outputs on that node's /scratch; no /data* traffic during the run.
- Measures: seconds per rollout per path, own tokens per path, calls per rollout, g rate and reward per type, budget hits, tower errors, unforced head-call rate.
- Not measured or claimed: any benchmark score. ReVSI, VSI-Bench, VSTI and dev-S1 items are refused by the sampler.
- Stop: any FAILED_shard file, a tower error rate above 20%, or card contention; no automatic retry.
- Outputs: RUN_DIR (draw commits, progress, DRYRUN_MEASURE.json); a RESULT event with the measured rates.
