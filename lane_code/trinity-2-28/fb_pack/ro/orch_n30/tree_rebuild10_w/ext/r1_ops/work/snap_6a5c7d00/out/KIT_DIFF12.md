Packet `p_9dd2fbb7.tar` differs from the scanned `p_69d2930d.tar` in exactly 3 of 37 archive members. The fixture-derived kits have 99 files and 0 differences. Findings outside the proof, gate and sums/authority records: 0.

The table lists every changed archive member, every changed derived-kit file (none), and the resealed authority. `KIT_INVENTORY12.json` lists old/new SHA256 for every archive member and every derived-kit file, including unchanged files.

| File | Old SHA256 | New SHA256 | Reason |
|---|---|---|---|
| archive/p_673bc60f.sh | fbff32efdc981a46290590fdbc51cc19ba75ec550025864111b40186487bce26 | b3c6c2317fb98132f6b0ed2d8419d0f3fb51fa94802ea868f1ddfcb633843a6d | Fix-11 proof caller environment (unchanged in fix 12) |
| archive/s.sh | 6fac31e33a7ba701f504c5b6a70b5d2d64da8e18007e87189ce7fefc2c137530 | fbcbb76c43a3307a846eb2c73171dd3ae4f99da7ad273328ce3a1a2e53e7b847 | CANARY branch; original PASS checks and sbatch line retained |
| archive/sums.txt | 036d6738c9c79fc9dfda2beb24e5fc7bcaeec2baeb943ad07e4d671644be9708 | 23eb51a0f6863e1086365acb4b542b3f62d4e8c3ba15dbf0bae6890cfad37bd8 | Binds the two changed script hashes |
| authority.json (same-path fixture) | dc5b22dee322c0c2cdf380cf1fb122a2c6ce5281e725586b03b53d25501450ea | 8f0ec8e14c5e32f45d07bb4311597bd4709ffe5028b2436035613255255dbe69 | Only bundle_files.s.sh and bundle_files.p_673bc60f.sh |

Both kits derive from `/scratch/jjyeung/orch_n30/cont_ops/work/h1/build/fx` using the same source manifest and logical deployment paths. The two absent inherited archives are `['k/np226_5204b3a0.tar', 'k/t_e6456bcecb8d4a8f4f68158eb68275f8befff128.tar']`; these are fixture derivations, not Orchard attestations. The fixture seal uses a production-form READY kit and one stable bundle path for both versions; only the two script pins differ in its authority. The proof driver must reseal the actual deployed bundle.

| Visible surface | Comparison |
|---|---|
| Archive member names and paths | 37 names; byte-equal |
| Derived kit names and file bytes | 99 files; byte-equal |
| Trainer archive, jb.sh, c.sh, r.sh, p0.sh, a.py, config and admission predicates | Byte-equal |
| Training sbatch argv and proof submission prefix | Byte-equal |
| srun argv outside changed scripts | Byte-equal (all containing files identical) |
| Environment names outside changed scripts | Byte-equal |
| Log line formats outside changed scripts | Byte-equal |
| New gate input environment name | ADMISSION_JOB (PROOF_JOB retained) |
| New gate paths | /project/community/jjyeung/okh7/x_69d2930d.f170956/o/170956.proof.{json,log}; old manifest/config/0.json; BUN/job.id; KH/o/<PROOF_JOB>.canary.json |
| New gate queue argv | TZ=UTC squeue --noheader --jobs <PROOF_JOB> --format=%i\|%T\|%j |
| Proof additions | TK_RUNS_DIR, TK_JOBDIR, R1_RUNTIME_RECORD exports; private .proof directory and pinned runtime-record path |
| Complete visible surface | Not byte-equal; quick scan required for the additions inside s.sh/proof |

Outside `s.sh`, the proof contents, and their sums/authority values, the visible surface is byte-equal. The full surface is not byte-equal because those scripts introduce the listed names, paths and commands. This report does not certify a reused content scan. `PROOF_DIFF12.diff` exposes the decoded proof change; the embedded proof is byte-equal to fix 11.

Scanned archive SHA256: `a99ab475f602c63332d4faaa4bf20f9d75e604cb973a80a041338b03a7d5f589`. New archive SHA256: `9dd2fbb77503ecee875d538ebaed933cc95ff286f76e5955fc2591f63e3f0192`. Config identity: `fac0705214fdecb53561c633d7d94642cd469b50b662c5de81f09d11891d115f` (unchanged).
