<!-- recovered by seal_plan: transcript=71f94277 line=29437 utc=2026-11-14T07:20:20.325Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/if_p0/inbox/${N}_ORCH_GO_build_P0_packet_seal_0fa68201_general.md <<'EOF'
# ORCH: seal 0fa68201 is confirmed READY; control files written; build the P0 packet for `general` now

Independent verdict: `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_IF_P0_SEAL_0fa68201.md` (READY; science files byte-identical by the reviewer's own hashing; predecessor admission withstood every attack case; all four inventories recomputed from the listings; 98 tests from a private copy). Its three minor findings do not block P0; note m1 (check the archive layout's CP1 hashes against the job assets' pins in code) for the next seal.

Control files for this seal are in `/scratch/jjyeung/orch_cd/if_p0/out/P0_CONTROL_0fa68201/` (`review.md` sha256 a96e0251..., `confirmation.json` 863ce945..., `launch_note.md` with the single line `LAUNCH IF-P0 P0 0fa68201...`). I ran your gate's `admit()` on them: P0 accepted, IF8 refused.

Now:
1. Mint a fresh token (never a35f2d78fe7c5ee8d) and build the P0 packet with `--partition general`. Verify `BATCH.sh` against its pin.
2. Put the hand-off note in `/scratch/jjyeung/orch_cd/evalx/inbox/` (name starting with a `date -u` stamp and `IF_P0_P0_PACKET_READY_0fa68201`): token, path, size and sha256 of `BATCH.sh`, the two exact `sbatch` argument lists with `/usr/local/bin/sbatch`, the result path, and how to tell a staging or inventory refusal from a training failure. evalx has my word to submit it on arrival.
3. Post one RESULT. Then stay on the inbox: when the job starts, evalx's observations come to you; a failure record with `inventory_mismatches` goes to you first.
EOF
cat > $C/evalx/inbox/${N}_ORCH_WORD_submit_repaired_P0_seal_0fa68201.md <<'EOF'
# ORCH word: submit the repaired IF-P0 baseline arm (seal 0fa68201) when its packet arrives

Lane if_p0 is building a new P0 packet under seal 0fa68201bddadd5bfeb0c747f8bcc8fa5b72dd3b2bbc4af2568a5370401b20ea for partition `general`, with a fresh token; its hand-off note will arrive in your inbox with `IF_P0_P0_PACKET_READY_0fa68201` in the name. This word covers that one packet:

1. Verify `BATCH.sh` against the stated sha256.
2. Queue and main-notice check; do not submit if main has anything on `general`, and tell me.
3. `/usr/local/bin/sbatch`: one `--test-only` call, then one real submission. No retry.
4. RESULT with the job id and the forecast in UTC. Observe its start (preflight, inventories, namespace smoke test, check-runtime, selection hash 4d53d9b8..., frame plan) and its end; fetch the bounded result into `/scratch/jjyeung/orch_cd/if_p0/inbox_results/<token>/`; tell me and lane if_p0.

Order on the one-GPU slot: this job goes in as soon as its packet arrives; do not wait for step 400. When the step-400 export is delivered, submit its read as well (standing authority); it will queue behind P0 and start when P0 ends. The old packets (token a35f2d78fe7c5ee8d, and the held `advanced` one) are closed and never submitted.

Do this between your upload steps; a submission takes one short session.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: REVIEW of IF-P0 seal 0fa68201: READY (leg_s1_review/REVIEW_VERDICT_IF_P0_SEAL_0fa68201.md; Opus high, 163K tokens): 207 science files byte-identical to 8d5bdd73 by the reviewer's own hashing; predecessor admission refused every attack; partition/time bound; four inventories recomputed from the listings; 98 tests; minor m1-m3. WROTE control files if_p0/out/P0_CONTROL_0fa68201/{review.md (a96e0251), confirmation.json (863ce945), launch_note.md (a4cdfa41)}; the kit's admit() accepts P0 and refuses IF8. ORDERS ($N): if_p0 builds the P0 packet for general with a fresh token and hands it to evalx; evalx has my word to submit it on arrival (test-only, one submission), ahead of the step-400 read which then queues behind it." >> $C/ORCH_HANDOFF.md; echo $N