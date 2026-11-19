# Independent review: sb_rowD7f and sb_d7bind
**ACCEPT WITH FINDINGS. No BLOCKER found in the rows or binding record.**
The binding supplies the per-twin evidence required by path (b); this verdict does not certify an augmented database or N's build-22 admission implementation.

1. **minor — Raster coverage is partial.** Of 7,971 retained twins, 695 pass all named-object raster checks; 7,231 lack local rasters and 45 have unmatched raster labels. Both unchecked groups are explicitly listed, without inferred mappings. Do not describe all rows as visually certified.
2. **minor — N must still enforce path (b).** Strict Rooms resolves 229 source/twin pairs and leaves 7,742 unresolved. The binding discloses the pinned tiered map used for those rooms. N must pin the augmented hash and binding, reject missing/mismatched sources or rooms, and run `unremoved_hits` with `u_union` through source keys. The record alone does not implement these checks.
3. **minor — The balance guarantee has a defined scope.** Clause-masked question features and Step-1 forms score 50% on the teaching subset. Raw question length scores 65.18% by scene because it includes the edited clause; the full admitted Step-1 population remains 80.7% toward. Both limits are disclosed in the delivered evidence.

Commands below run from `/scratch/jjyeung/orch_n30/sb_drev8`.
`P = nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python`
Every evidence JSON records its input SHA256 hashes and exact command. Local adaptations of the six prior scripts are recorded in `work/SCRIPT_ADAPTATIONS.diff`; no builder code is imported.

`P run_review.py rev_census.py`: v7 contains 204,413 unique qids and 93,370 direction rows. The 5,846 easy/hard opposite pairs and 12,023 easy/hard away pairs have zero half-turn disagreements. No medium twin is delivered.
`P run_review.py rev_verify7.py`: all 7,971 answers match the half turn and unique option mapping, including 300 random twins (seed 20261119). Source trace relations independently give the same labels.
The same command confirms exact source Steps 1 and 2, exact final-line form with only its label replaced, and the required Step-3 half turn. Options and frames are unchanged; no `facing` field exists.
N's r2_contract, trace_grammar, r2_grammar and direct_row packer pass on every twin and source. The 20 imported modules and packer file match the sealed tree. scene_division_gate admits 7,971/7,971 in each population; all removal and lineage checks pass.
Qids and candidate_ids are unique and new; N's candidate formula reproduces every ID. Field differences are exactly qid, pool, answer, question and target, plus candidate_id, label_row_keys and provenance.sb_rowD7. Each source is used once.
`P run_review.py rev_fixcheck7.py`: all 7,971 fixed rows still pass native validation and occupy `direction`.

`P run_review.py rev_rooms7.py`: N's family function assigns every source and twin to `direction`. Build-20 allocates 36,690 draws across 56,411 direction rows: 0.6504 per row and 5,184 expected draws per teaching clause.
The same command finds matching tiered rooms and zero K1/R0/withheld-80/dev-S1/BENCH-v2 hits. The unmodified N audit accepts v7 and rejects the deliberately hypothetical augmented unresolved-store fixture; fixtures are tests, not certification records.
`P run_review.py rev_leak7.py`: on 15,942 teaching rows, Step-1/final forms and clause-masked templates, names, role triples, dataset and combined inputs score exactly 50% in-sample and when held out by pair or scene. Input-only logistic regressions also score 50%; sampling-weighted features score 50%.
All 36 templates, 4,045 name sets and 1,024 names balance exactly. Predictors that include answer outputs are not question-input leak tests.
`P run_review.py rev_wording7.py`: zero normalized edit-distance hits at <=0.10 among 7,852 distinct questions against 927 reference wordings.

`P run_review.py rev_pilot8.py`: all 367 indexed raster pins reproduce and the bounded directory inventory matches. R1 removes zero pairs. R2 has zero frame citations; every trace occurrence of “frame” belongs to an object name.
For 769 pairs on 98 raster-backed captures, independent integer-pixel counts reproduce R3: 16 pairs have zero pixels and 13 have only sub-0.2% slivers. Exactly these 29 pairs are dropped. The no-raster list covers all 7,231 rows on 802 captures; the 45 unmatched-name rows are separately listed.
`P run_review.py rev_binding8.py`: all 7,971 records reproduce N's row keys and parsed-row digests; every source occurs once in v7 `210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443`. Source indices, raw source hashes, rooms and authority tags agree.
The same command finds zero source-key or twin-key hits in u_union/u/n/z (4,959/2,637/601/17,879 keys), zero twin-key collisions with v7, and zero hits across all build-20 removal files. The tiered census finds 4,959 held-out v7 rows, all removed; the augmented population has zero unremoved hits.
Strict census counts reproduce audit dd60517b. All 15 current out/ archive members checked match their files, and every binding input pin reproduces. N's digest differs from raw JSONL-line hashing for 100 Unicode-bearing twins, as the binding report states.
`P run_review.py rev_claims8.py`: no checked claim or producer input-pin mismatch. Teaching references match exactly; the family survey covers all v7 direction rows, with 1,096 names and zero placeholder-name rows.
`P run_review.py finalize_review8.py`: consolidates these checks in `out/FINAL_CHECKS.json`, including explicit zero unremoved counts and the 100 digest-encoding differences.

Recomputed delivery SHA256: `a0381ea08a018ef97ef0193b8817f45cc82a680f3b940164e605a484e237d186`.
Recomputed binding SHA256: `d8c3837019d29e9c8b7916a7e8b3c3d595890b6cad32c7dc72ba5f871a0a5108`.
