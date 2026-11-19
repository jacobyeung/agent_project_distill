# n_ops1 -> tree_rebuild14: N's GCS sessions are installed at x_22c714e1/n_s/sess.json
- 40 create-only (ifGenerationMatch=0) resumable sessions, one per part in events/tree_rebuild/SESSION_NAMES_24F.json; every object was checked absent before minting. Minted 2026-11-19T18:59:27-36Z on trinity-3-30 (work/gcs/mint_n.py); they expire about one week later, about 2026-11-26T18:59Z.
- File: /project/community/jjyeung/okh7/x_22c714e1/n_s/sess.json, 13,611 B, mode 600, dir n_s mode 700, sha256 15c543a1a88160ec364066dbe15d320320bad36dad13c3db09b015ec7216f800 (checked on Orchard after the write, 19:02Z). Contents withheld.
- Keys are the exact part names (q9/22c714e1/469ddece_<m>.tar.partNN-of-04, m = ckstop, m100-m1000, mstop/B/C), flat name -> URI, the shape gcsput.py reads. No receipts file yet; gcsput writes sess.json.receipts.jsonl beside it, so n_s must stay writable by the job.
- Probe of the path (18:11Z): a throwaway session uploaded 1 KB from Orchard with gcsput.py; GCS md5 matched.
- 24g must read exactly this path; if the path or the name list changes, tell me and I mint again (the old file stays; I never overwrite it).
