<!-- recovered by seal_plan: transcript=71f94277 line=29437 utc=2026-11-14T07:20:20.325Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_WORD_submit_repaired_P0_seal_0fa68201.md heredoc_quoted -->
# ORCH word: submit the repaired IF-P0 baseline arm (seal 0fa68201) when its packet arrives

Lane if_p0 is building a new P0 packet under seal 0fa68201bddadd5bfeb0c747f8bcc8fa5b72dd3b2bbc4af2568a5370401b20ea for partition `general`, with a fresh token; its hand-off note will arrive in your inbox with `IF_P0_P0_PACKET_READY_0fa68201` in the name. This word covers that one packet:

1. Verify `BATCH.sh` against the stated sha256.
2. Queue and main-notice check; do not submit if main has anything on `general`, and tell me.
3. `/usr/local/bin/sbatch`: one `--test-only` call, then one real submission. No retry.
4. RESULT with the job id and the forecast in UTC. Observe its start (preflight, inventories, namespace smoke test, check-runtime, selection hash 4d53d9b8..., frame plan) and its end; fetch the bounded result into `/scratch/jjyeung/orch_cd/if_p0/inbox_results/<token>/`; tell me and lane if_p0.

Order on the one-GPU slot: this job goes in as soon as its packet arrives; do not wait for step 400. When the step-400 export is delivered, submit its read as well (standing authority); it will queue behind P0 and start when P0 ends. The old packets (token a35f2d78fe7c5ee8d, and the held `advanced` one) are closed and never submitted.

Do this between your upload steps; a submission takes one short session.