# AWS copy-off manifest (2026-11-09)

## Question
Which of our files on code-aws (`ap/` = /scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/) must leave AWS before access ends? The user ruled on 11-09 that AWS is for copying only and that every model weight and everything else we need must be copied off. A 21:40Z ruling adds that public raw data is skipped and that GPU-computed features are copied.

## Answer
- Manifest v2 TSV: /scratch/jjyeung/orch_cd/aws_copyoff/COPYOFF_MANIFEST_v2.tsv, with a summary at COPYOFF_MANIFEST_v2.md in the same folder. /scratch is cleared after 7 days, so a copy of the TSV sits beside this record as AWS_COPYOFF_MANIFEST_20261109.tsv.
- 205 rows. Classes: A = needs for continuing on Trinity/Orchard; B = all other weights; C = records, prep outputs, GPU features; D = raw or rebuildable.
- Totals (rows / known GB; unknown sizes count 0):
  - A: COPY 34 / 279.9, VERIFY 4 / 7.6, LIST 3, DONE 24 / 1,770.2, SKIP-REBUILD 5 / 36.2, NOT-ON-AWS 2.
  - B: COPY 40 / 7,180.2, VERIFY 1 / 897.0, LIST 5 / 3,818.0, DONE 17 / 5,113.2, SKIP-REBUILD 2 / 709.0, NOT-ON-AWS 5 (GCS-only sizes, 4,131.0).
  - C: COPY 25 / 55.8, VERIFY 4 / 6,868.5 (GCS feature units), LIST 1, DONE 6 / 0.5.
  - D: COPY 1 / 282.3 (partner tars, last), LIST 2, DONE 4 / 65.0, SKIP-REBUILD 19 / 2,667.0, NOT-ON-AWS 1.
- The copy lane's sender (job 137901, AWS -> Mind at 50 MB/s) already queues 53 COPY rows (5,880 GB known). Another 40 COPY or LIST rows (>= 1,833 GB known) are absent from its queue and must be added.
- Class A copy order (open rows, v2 order numbers):
  1. CP1 checkpoint_000346 (116.1 GB)
  2. CP1 m100
  3. CP1 m50
  4. f2ad01ad/.in (slice and kit tars)
  5. A4 rows r_val/r_s/r_spp/division
  6. r_s24/mr1 (not queued)
  7. G3T weights with SHA256SUMS
  8. closure c_ tar
  9. e_ tar (not queued)
  10. art and bwrap
  11. venv
  12. bc67ca08
  13. T0 prep arms 13e69a8d/4df58a04 (not queued)
  14. CP1-R o8 with f482b3e8/80
  15. 9281911f kit
