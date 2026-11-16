# Everything copied off AWS: deduplicated inventory and need verdicts (2026-11-09)

## Question
What did we copy off AWS onto Mind, GCS and Trinity, which bytes are stored more than once, and which of it
do the two projects (main paper campaign, distillation) still need?

## Answer
State at 2026-11-09 23:33Z (fresh listings of Mind and GCS; Trinity from copy-queue receipts and `ls`).
GB = bytes / 1e9.

| Store | Stored GB | Files |
|---|---:|---:|
| Mind `/lab_data/tarrlab/jacoby/agent_project/aws_evac` | 14,528 | 1,710 |
| Mind `/lab_data/tarrlab/jacoby/aws_evac_20261104` (11-04 rescue, mostly other projects) | 519 | 535 |
| Mind `agent_project/distill_publications_20261004` | 46 | not listed |
| GCS `gs://cmu-gpucloud-jjyeung` | 6,918 | 1,938 |
| Trinity (/data2, /data3, node /scratch; present or unconfirmed) | 1,280 | about 330 |
| All | 23,304 | |

Distinct content is about 20.7 TB. Byte-identical duplicates (digest-proven) total 1.78 TB: 1.43 TB of them
are GCS copies of files verified on Mind or /data3, and 0.36 TB are Trinity copies. Mind holds no
byte-identical duplicate of its own.

Verdicts per stored GB (4,078 logical items; every item has one row in `FINAL_VERDICTS.tsv`):

| Verdict | Mind | GCS | Trinity | Meaning |
|---|---:|---:|---:|---|
| KEEP | 8,066 | 0 | 256 | needed, verified copy on a long-term store |
| kept side of a duplicate pair | 1,083 | 0 | 194 | needed; its twin is the extra copy |
| KEEP-AT-RISK | 59 | 2,770 | 122 | needed, but the only copy is in GCS, on /scratch, partial or unverified |
