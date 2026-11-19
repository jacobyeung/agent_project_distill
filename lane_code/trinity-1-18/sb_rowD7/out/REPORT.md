# sb_rowD7: clause-only direction half-turn twins

Delivery PASS: 8,000 new away rows use 8,000 distinct Step-1-family easy/hard toward sources. No toward twins or medium rows are emitted.
The best reviewer classifier on clause-masked full question + opening + exact name set scores 50.0% on the 16,000-row teaching subset (required ≤60%). Every source/twin feature pair is identical.

| New answer cell | Rows | Share within difficulty |
|---|---:|---:|
| easy left | 2,000 | 50% |
| easy right | 2,000 | 50% |
| hard front-left | 1,000 | 25% |
| hard front-right | 1,000 | 25% |
| hard back-left | 1,000 | 25% |
| hard back-right | 1,000 | 25% |

Each question preserves its source text, punctuation, names and Cartesian convention outside one recorded facing clause. The codeA/build_away.py single-substitution pattern is reused; its original rule handles away-to-opposite, so substitution.py explicitly handles toward-to-away and refuses unmatched clauses.
The generator attempts 9,474 candidates, refuses 1,474 without one clean substitution, and fills all six quotas exactly. New away rows cover 1,024 names; 951 were absent from admitted Seen/away sources.
The Seen easy/hard population already has 4,360 exact masked-wording pairs with matched names, scene and frames. This delivery adds 0 Seen rows and 0 duplicate toward twins.
The exactness gate passes 5,846/5,846 easy/hard pairs (3,664 easy; 2,182 hard). All 1,274 literal-flip disagreements are medium; all 2,665 medium pairs and 29,124 medium source rows are refused.
For the 3,422 shared D6 away sources, answers, traces, options and frame metadata are identical to D6. Every emitted trace uses D6’s verified half-turn construction and copies its source reference-heading relation.

| Step-1-family source wording population | Toward | Away |
|---|---:|---:|
| Full v7 before | 49,901 | 0 |
| Full v7 plus D7 | 49,901 | 8,000 |
| Admitted v7 before | 47,837 | 0 |
| Admitted v7 plus D7 | 47,837 | 8,000 |
| Selected teaching subset | 8,000 | 8,000 |

TEACHING_SET.json identifies the unchanged source controls. Pair those controls with NEW_ROWS.jsonl for the 50/50 guarantee; full v7 remains imbalanced. LEAK_TEST.json also tests opening, name set, role triples, dataset, frame indices and option order with the reviewer’s majority-per-feature logic.
The leak test reuses rev_balance.bayes and rev_census clause/opening functions. REVIEWER_CHECKS.json reuses rev_verify native packing, field-diff and signed-axis rules. WORDING_REVIEW.json runs rev_wording’s normalized-distance logic.
All 8,000 rows and sources pass N’s packer, schema and trace validators. Independent checks recompute all answers, option bijections, candidate IDs, unique qids, source-use counts, permitted field differences and source preservation. v7 has no candidate IDs; new candidate IDs are mutually unique.
All 8,000 rows and sources pass scene_division_gate with the W20 remove lists and native dev/benchmark scene filter. There are zero removal, lineage, outside-train or held-out hits.
Wording exclusion compares 7,881 distinct new questions against 927 distinct local dev/benchmark wordings (7,305,687 pairs). Normalization is NFKC + casefold + collapsed whitespace; reject Levenshtein/max length ≤0.10. No candidate was removed for wording distance and no delivered question matches.
The C++ distance routine handles Unicode code points; independent DP cases check it. Corpus coverage is limited to the pinned local item/fixture files in WORDING_CORPUS.json. Source questions supply all new wording; no dev/benchmark item supplies text.

Room finding: W20 is the newest intact seal checked: 780ca7b446a578c83a1b1a398a8d54c0503a7cca26309bae6a1b60f85ef2a278 (934/934 files). W21 has nine mismatches against its inherited seal and is not used.
N’s unchanged W20 Rooms, using alias pin c47c5fcd, refuses 7,771 sources and their 7,771 twins as unresolved; 229 per population resolve. ROOM_RESOLUTION.json records exact qids, opaque scene tokens, error strings, file hashes and code-line evidence.
N’s native direct-VQA path nevertheless accepts all 8,000 sources and all 8,000 twins: r1_routing.Filters.reason(row, vqa) returns None, and carrier_c1_run.Rows.row passes its text, extent, R1 and reserve checks. We execute the same sealed functions for both populations.
That path does not resolve the opaque tokens. r1_rooms.py:108–125 grants only the exact pinned v7 database a legacy exception; its audit records 119,375 unresolved store rows. A changed store does not inherit this exception.
Physical-room checks explicitly use sb_rowD2/alias_inputs/out/TIERED_ALIAS_MAP.json, pinned in every row’s provenance and ROOM_RESOLUTION.json. With this map all 16,000 rows resolve, match SOURCE_MAP and have zero K1/R0/withheld-80/dev-S1/BENCH-v2 hits.
Removal authority is w20/work/build20/inputs/config.json, including build18/inputs/u.json (2,637 keys), n.json and z.json, plus the conservative u_union.json (4,959 keys). Every u.json key occurs in u_union. No build17 config supplies removal authority.
Binding is not performed: an augmented store needs N-side room certification carrying the named tiered map. CHECKS.json marks delivery_ready=true and binding_ready=false; no new manifest or room proof is invented.

READ60.md contains 60 complete rows, ten per answer cell; READ30.md contains the first 30. All full records were parsed and compared, and all 60 questions, options and complete traces were read. READ60_REVIEW.json records inherited source agreement/spelling notes in rows 17, 40 and 43. VERIFY.json has a final manual-review result.
Reproduction commands below use prefix: `nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1`.
`python prepare_d7.py` authenticates D6 copies and tree seals; `python survey.py` computes source counts and exclusions; `python wording_corpus.py` collects the local wording corpus.
`g++ -O3 -std=c++17 -shared -fPIC edit_distance.cpp -o edit_distance.so` builds the distance filter; `python build_rows.py` produces rows, gate, quotas, counts, pins and samples.
`python verify_outputs.py` verifies all rows and histograms; `python reviewer_checks.py` checks independent reviewer truth/native rules and D6 equality; `python leak_test.py` produces leak accuracies and before/after clause mixes.
`python room_resolution.py` measures strict Rooms, native admission and tiered exclusions; `python review_wording.py` recomputes wording exclusions; `python record_review.py` records the completed reading; `python finalize.py` seals checks, report, tar and SHA256.
Every output JSON records input hashes. SOURCE_MAP.jsonl binds each new qid to its source index and exact serialized-row hash. External source stores, frame payloads and N’s tree remain read-only dependencies.
Package: out/sb_rowD7.tar; digest: out/sb_rowD7.tar.sha256; verified members: out/PACKAGE.json. The archive contains code, rows, maps and evidence, excluding the large D6 working snapshot.
Not done: training, N binding, frame-image rereads or external benchmark collection. No GPU, network, SSH, Git or process termination was used.
Borderline prose retained: the required before/after clause census and D6 equality comparison directly test the requested fix.
