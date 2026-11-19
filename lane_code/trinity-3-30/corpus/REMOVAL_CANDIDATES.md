# Removal candidates (corpus lane; nothing deleted)
- /scratch/jjyeung/orch_n30/corpus/stage/ : superseded first-tool staging (old schema), incl. empty 0-item aed15a8b7cb file. Never published.
- /scratch/jjyeung/orch_n30/corpus/orchard_in/x/ : extract of orchard_in/r.tar (raw tar published at /data2/.../distill_trace_corpus/raw/orchard_only_cc886a29e4ef.tar, sha256 2660081143f0...).
- /scratch/jjyeung/orch_n30/corpus/tool/t/ : Codex test fixtures and outputs.
- Orchard: /project/community/jjyeung/okh7/cc886a29e4ef/ (r.tar 439 MB, files.txt) after the corpus copy on Mind exists.
- trinity-1-18: /scratch/jjyeung/n30_mirror/corpus_work/*.list (tar listings, 52 MB).
- Leftover working databases from the file-backed tool version (fixed 08:23Z: the database now lives in memory; test tests/test_no_leftovers.py): 505 files tool/t/.corpus-*.sqlite and tool/t/corpus-*.sqlite, 7.78 GB in total. All of tool/t is 7.5 GB.
- Lock files (0 bytes) beside each output: stage2/reads/*.lock, stage2/index/*.lock.
- /dev/shm/noleft-* and /dev/shm/corpus_chk (test outputs, ~100 MB of RAM disk).
Total on trinity-3-30 /scratch from this lane: about 8.7 GB (tool/t 7.5, orchard_in 0.84, stage2 0.21, stage 0.05, pub 0.17).
