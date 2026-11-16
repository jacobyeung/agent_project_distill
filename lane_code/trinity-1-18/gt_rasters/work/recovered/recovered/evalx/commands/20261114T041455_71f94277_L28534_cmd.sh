<!-- recovered by seal_plan: transcript=71f94277 line=28534 utc=2026-11-14T04:14:55.966Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/evalx/inbox/${N}_ORCH_AUTHORIZED_orchard_native_routed_family.md <<'EOF'
# ORCH decision on RESULT 0413Z: build the Orchard native routed-read family; Trinity stays on hold

Your report is clear and I am choosing Orchard: Trinity's cards are taken by main's evaluations, and every later checkpoint needs this read. Authorized, in this order. Each numbered stage ends with one RESULT.

## Stage 1: admit the raw geometry cache (CPU, bounded)

- The candidates are on trinity-1-18 at `/scratch/jjyeung/devs1_r2/g3s{32,64}/g3t` (152 NPZ files, 679 MB). Copy them once to this node's `/scratch` under your lane (node to node over InfiniBand, one tar stream, through your rate-limited ssh; if that login drops or is refused, stop and post it). The 1 GB lane limit on this node is raised to 3 GB for this.
- Validate on CPU against what `geometry.py` needs: schema, dense-frame identity per capture, the frames each file was computed from, and the tower's frozen weights and configuration identity. Take provenance from the files' own metadata and from the records of the lane that produced them (`/scratch/jjyeung/orch_cd/devs1_tower/STATUS.md` and its `out/`), read-only. Do not rerun the tower and do not accept a cache whose weights or frames cannot be tied to pins.
- RESULT: admitted or not, with the evidence; if not, exactly what a tower rerun on Orchard would need (weights, config, dense RGB closure: paths, bytes).

## Stage 2: build the native family (CPU)

- A separately sealed job family for the routed read. The accepted direct launcher, its digest and both submitted packets stay untouched; reuse the accepted copy, extraction, storage, card, guard, publication and fetch code byte-identical wherever its contract fits, and list every line that differs.
- Two entry points: **parity-only pilot** (restore the export, run P1 to P3 on the registered first capture, the checkpoint geometry on a handful of captures, about ten real paired items; stop before the scored read; report load time, parity, peak memory, geometry seconds per capture, seconds per item, and the compressed return size) and the **full read** (geometry over all 152 captures, the 636 paired items, merge, R1). Each fits the existing return limits or says what it needs.
- Production runtime with its sealed pins and explicit import paths; never the live trainer's private root; the ordinary loader must not open the training databases.
- As-in-job rehearsal on CPU with fixtures: the whole job script under an empty environment, absolute program paths, a fake private `/tmp`; list what the rehearsal substitutes and cannot exercise. Partition is an explicit argument limited to `general` and `advanced`, bound into the packet.

## Stage 3: the small transfers (after stage 1 passes)

Reader code archive, the metadata closure, the mask cache, the admitted geometry cache and the model manifest: under 1 GB in total. Route: this node to GCS (governed, one stream at a time, behind main), fetched inside the Orchard job like the export. Objects under your existing prefix with generation pins and hashes in the packet. No credential is copied anywhere. Tell me the exact object list and bytes before the first upload; that list is all I need to approve it.

## Stage 4: review and submissions

When the family is sealed I dispatch one scoped independent admission review. Then, each on my separate written word: the parity-only pilot (one job, about fifteen minutes of GPU), and after its numbers the full read for step 200. Slots: `general` after the IF-P0 baseline arm and the step-400 direct read, or `advanced` once the production leg has released it (about 15:00Z), whichever I name.

## Priorities for you, in order

1. The step-200 direct packet when job 169367 returns (with the watch list).
2. The milestone step-set diff (my 0412Z note), needed before the step-400 export at about 08:50Z.
3. Observation of P0 job 169413 when it starts.
4. Stages 1 to 3 above. Target: the pilot's packet ready by about 10:00Z. If that is not realistic, say so in your stage-1 RESULT with the reason.

The Trinity watch from my 0406Z note is cancelled: no more reads of trinity-0-28 for this. Nothing further is written there.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: evalx(19) RESULT 0413Z (Orchard routed feasibility): runtime, base, depth files, export, anchor RGB already on Orchard or GCS; to ship via GCS: reader code 3 MB, metadata closure 57 MB, masks 206 MB (trinity-2-18), raw G3T geometry 679 MB (trinity-1-18; provenance NOT yet admitted), manifest; per-checkpoint geometry pass over 152 captures and per-item time unmeasured; needs a separately sealed native job family + one scoped review; cohort 636 items (150 distance, 36 room, 450 camera). DECISION ($N): BUILD THE ORCHARD NATIVE ROUTED FAMILY; stage 1 raw-cache admission, stage 2 family with a parity-only pilot and the full read, stage 3 small governed transfers via GCS (object list to me first), stage 4 review and submissions on my word; Trinity path cancelled (nothing more on trinity-0-28). Re-armed evwait (bfvybib72)." >> $C/ORCH_HANDOFF.md; echo $N