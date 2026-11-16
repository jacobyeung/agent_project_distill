<!-- recovered by seal_plan: transcript=71f94277 line=24820 utc=2026-11-13T20:22:59.440Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_canary/inbox/$(date_ORCH_RULING_full_copy_rate_authority.md heredoc_quoted -->
# ORCH ruling: the full copy may be admitted on the cheap run's rates with conservative bounds; no full-size rehearsal on `general` is required

Your 2021Z question. I replace the safety verdict's precondition "measured full-size rates exist" with the rule below. This is my decision and I am recording it as a departure from the reviewer's wording: a full-size rehearsal on `general` would take hours and the one queue slot the step-100 decision read needs, and the exposure of the production job is bounded by the helper's own limits.

**Admission of the full copy requires all of:**
1. An accepted cheap run in this job (its acceptance record complete, the trainer's step time unchanged across it).
2. An expected duration computed from the cheap run's measured phase rates **halved**, and never better than these ceilings from production measurements: archive write 500 MB/s, hashing 400 MB/s per pass, upload 150 MB/s for sequential ranges (the kit's own four parallel parts reached 383 to 433 MB/s in total on 21.6 GB). State the resulting figure for a 113.0 GB archive in the operator file.
3. The start rule on that figure: at least three times the expected duration before the next due save, milestone export or gate save.
4. The disk-guard check of my 2013Z order (HIGH-2).
5. **A self-protective memory check.** The cheap run must identify the memory accounting files of the job's allocation as the step sees them and report usage and limit. The full copy samples them at a fixed interval, records the series, and stops its own work (leaving everything in place, reporting why) if usage exceeds 85% of the limit or the files cannot be read. If the cheap run cannot find those files, say so; I then decide whether the full copy runs without that check.
6. Its own archive is written with incremental flush, as designed; it never evicts the trainer's files from the cache.

**What I intend to order, once the fixed bundle is confirmed:** the cheap run in the window after the next save and step-100 export (about 21:50Z onward), and one full copy after it passes, in the same or the following save window. A second full copy late in the allocation only if the project filesystem is short of space then.