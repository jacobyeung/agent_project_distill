# Fix round 1 + two new adapters for the corpus ingest tool (workspace /scratch/jjyeung/orch_n30/corpus/tool)
Read BRIEF_ingest.md (original spec) and SCHEMA.md first. Same hard rules: write only inside /scratch/jjyeung/orch_n30/corpus/tool (tests and fixtures under tool/t/); read the source folders below in place; no network, ssh, git, GPU, deletion; Python 3.6-compatible standard library; RAM under 2 GB. Output roots may be any path under /scratch/ or /dev/shm/ (the operator changed `writable()` on purpose: keep that, and update SCHEMA.md line 4 to say so).
You MAY and MUST run the real-return tests yourself (reads of a few hundred MB on node-local /scratch are approved; no approval question needed).

## A. Fix every defect of the review (receipt: /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/20261119T065234Z_corpus_review/final_message.md), each with a regression test:
1. No streamed source row may disappear: every row of every consumed JSONL/array (item files, report rows, routed manifests/item_mapping, task rows) must land either in an item's raw (matched) or in a per-read `orphans` list kept in the index file (or a sidecar `index/<id>.orphans.jsonl.gz` if large), with a count in the index. Keep joined task rows verbatim (all keys, e.g. room_key).
2. Routed join: when the mapping carries a task hash and the candidate task's hash differs, refuse (exit 2) unless the join is by an explicit, documented rule; never silently join contradictory rows.
3. Kit: all arms of an item must share id and question/truth; mismatched populations or contradictory question/truth across arms -> refuse (partial) with reasons. Per-arm counts must equal the expected counts.
4. Colon-containing IDs: index records by the exact id; never strip prefixes inconsistently.
5. Reserved raw keys must not collide with arm names: put arms under raw.arms.<arm> (update SCHEMA.md).
6. Status checks apply to every consumed row type (supplementary ITEMS.jsonl rows, report rows), not only generation rows.
7. Zero generation rows -> always refuse (exit 2), even with --archive-partial.
8. Routed set extraction: find the task manifest by content, not by the filename 3.json.

## B. New adapters (inspect the real files; do not guess)
- `offread`: official direct reads. /scratch/jjyeung/orch_n30/b07_offread/in/ret_vsi/ (VSI-Bench, 4,008 items, step 544, Orchard 170008; has result.tar.gz, COMPLETE.json, SPEC.json, a0/results/0/{items_a0.jsonl,budget_2048.jsonl,budget_4096.jsonl,...}, a0/results/budget_*/0/items_a0.jsonl, report/) and /scratch/jjyeung/orch_n30/b07_offread/in/ret_revsi/ (ReVSI, 679 items, Orchard 170037). Headline to reproduce from corpus lines: VSI six-task mean B2048 68.77 on 4,008 items (count 63.03, size 72.03); ReVSI five-category mean B2048 64.94 on 679 items (count 58.57, direction 51.19). Find the matching report file in the return and make corpus_score.py able to reproduce these means (a `--mean-of-types` option averaging per-type means).
- `native`: native routed read with in-call heads, Orchard 170056, 636 dev-S1 items: /scratch/jjyeung/orch_n30/b04_e2ehook/work/n13/full_c8r/result.tar.gz (95 MB; unpacked copy in /scratch/jjyeung/orch_n30/b04_e2ehook/work/n13/ret, paired results under native/paired/results). Keep every call and response.
- Also confirm `kit` handles /scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read/readk/kit/build/a4cadd8934b/fetched.

## C. Tests and report
Synthetic regression tests for A1-A8; real ingests (to tool/t/real/) of a8102c3207b, A4/ret (with --inputs /scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4), r1route/out3/B5/ret (--inputs .../out3/B5), ret_vsi, ret_revsi, n13 full_c8r, a4cadd8934b; print item count, bytes, sha256, seconds, max RSS and the reproduced headline numbers next to the reported ones. Final message: what changed per defect, adapter field mapping, test results with numbers, anything doubtful.
