The row build is MISSING. No new row or replacement has passed GT admission; this archive must not be bound as a completed row patch.
All 11 named source packs are absent at their recorded paths and checked local mirrors. MISSING.json gives each exact location and required fields.
The direction rows contain no source-bound coordinates or instance roles. D2 supplies classification and room/validator checks, but no GT recomputation code for these rows.
Command for all census, vocabulary, room, operation and lower-bound numbers: `PYTHONDONTWRITEBYTECODE=1 python build_rows.py` (exit 2 means MISSING).
Independent recount: `PYTHONDONTWRITEBYTECODE=1 python verify_outputs.py`. Vocabulary: `PYTHONDONTWRITEBYTECODE=1 python vocabulary_check.py`. Report/archive: `PYTHONDONTWRITEBYTECODE=1 python finalize.py`.
N tree: W/w19, seal `8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa`; imported kit files match the seal.
Store v7: sha256 `210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443`; 204,413 total rows, 93,370 direction rows.

| Opening | Clause | Before | Room-eligible | Actual after |
|---|---|---:|---:|---:|
| Step 1 | toward | 49901 | 47837 | 49901 |
| Step 1 | away | 0 | 0 | 0 |
| Step 1 | opposite | 0 | 0 | 0 |
| Seen | toward | 17479 | 16998 | 17479 |
| Seen | away | 17479 | 16998 | 17479 |
| Seen | opposite | 8511 | 8511 | 8511 |

Actual after equals before because no change is bound. The room-eligible column applies N’s five exclusion lists; 3,026 rows hit K1, and none hits R0, withheld-80, dev-S1 or BENCH v2.

| Family | Pool | Rule | Opening | Clause | Before | Room-eligible |
|---|---|---|---|---|---:|---:|
| easy | r1_away_opp | none | Seen | opposite | 3664 | 3664 |
| easy | rows_rebuild_d0_ARKIT_gaps | none | Seen | away | 1421 | 1301 |
| easy | rows_rebuild_d0_ARKIT_gaps | none | Seen | toward | 1421 | 1301 |
| easy | rows_rebuild_d0_T0_gaps | none | Seen | away | 3214 | 3202 |
| easy | rows_rebuild_d0_T0_gaps | none | Seen | toward | 3214 | 3202 |
| easy | rows_rebuild_d0_T1H1_gaps | none | Seen | away | 1506 | 1480 |
| easy | rows_rebuild_d0_T1H1_gaps | none | Seen | toward | 1506 | 1480 |
| easy | rows_rebuild_d0_T1H2_gaps | none | Seen | away | 1371 | 1335 |
| easy | rows_rebuild_d0_T1H2_gaps | none | Seen | toward | 1371 | 1335 |
| easy | w1g | rows_rebuild_d0_v1 | Step 1 | toward | 12969 | 12407 |
| hard | r1_away_opp | none | Seen | opposite | 2182 | 2182 |
| hard | rows_rebuild_d0_ARKIT_gen_r2 | none | Seen | away | 1160 | 1065 |
| hard | rows_rebuild_d0_ARKIT_gen_r2 | none | Seen | toward | 1160 | 1065 |
| hard | rows_rebuild_d0_T0_gen_r2 | none | Seen | away | 1647 | 1634 |
| hard | rows_rebuild_d0_T0_gen_r2 | none | Seen | toward | 1647 | 1634 |
| hard | rows_rebuild_d0_T1H1_gen_r2 | none | Seen | away | 887 | 868 |
| hard | rows_rebuild_d0_T1H1_gen_r2 | none | Seen | toward | 887 | 868 |
| hard | rows_rebuild_d0_T1H2_gen_r2 | none | Seen | away | 817 | 793 |
| hard | rows_rebuild_d0_T1H2_gen_r2 | none | Seen | toward | 817 | 793 |
| hard | w1g | rows_rebuild_d0_v1 | Step 1 | toward | 21385 | 20502 |
| medium | r1_away_opp | none | Seen | opposite | 2665 | 2665 |
| medium | rows_rebuild_d0_ARKIT_gen_r2 | none | Seen | away | 1037 | 955 |
| medium | rows_rebuild_d0_ARKIT_gen_r2 | none | Seen | toward | 1037 | 955 |
| medium | rows_rebuild_d0_T0_gen_r2 | none | Seen | away | 2291 | 2281 |
| medium | rows_rebuild_d0_T0_gen_r2 | none | Seen | toward | 2291 | 2281 |
| medium | rows_rebuild_d0_T1H1_gen_r2 | none | Seen | away | 1129 | 1108 |
| medium | rows_rebuild_d0_T1H1_gen_r2 | none | Seen | toward | 1129 | 1108 |
| medium | rows_rebuild_d0_T1H2_gen_r2 | none | Seen | away | 999 | 976 |
| medium | rows_rebuild_d0_T1H2_gen_r2 | none | Seen | toward | 999 | 976 |
| medium | w1g | rows_rebuild_d0_v1 | Step 1 | toward | 15547 | 14928 |

Equal shares means the two openings × two clause groups (toward and away/opposite) have equal counts. Retaining all eligible rows gives a count-only minimum of 101,004 additions: 47,837 per final cell, minus 90,344 retained rows. This also permits equal cells within each difficulty family; PLAN.json lists the exact shortages.
The 30,000 cap cannot meet this requirement while preserving compliant rows. Even equal toward/turn shares only within each opening need 56,348 additions; equal shares across all six literal opening/clause cells need 196,678. Before room exclusions, these minima are 106,234, 58,412 and 206,036 respectively.
These are count lower bounds, not achieved quotas: GT reference-quadrant and object-frame availability may require more rows. No compliant row is removed to force balance; new rows must restore at least today’s 25,990 away/opposite coverage after the 481 K1 away exclusions.
The opening text contains 1096 normalized object names in Step 1 rows and 73 in Seen rows. Room-eligible Step 1 rows contain 1,080 names. The full-store count of 1,096 differs from the prompt’s 1,089; VOCABULARY_CHECK.json independently reproduces the literal-name count without alias merging. Generated coverage is zero.
SKELETON.md retains both openings. The quoted question clause selects a separate keep-heading step or half-turn step for toward, away and opposite. Seen variants require verified sampled-frame citations, which the Step 1 sources do not provide.
D2’s pinned full-source checks pass N’s direct VQA validator and trace grammar (93,370 each) for this identical DB/tree; the recount verifies unique source qids. The source schema has no ground_record/events, so routed ground_rows.pack cannot certify these direct rows.
New-row pack/validate, candidate IDs, edited-field diffs, independent GT, quadrant counts and generated-row source-reuse checks are MISSING. Every required addition cell is short; CHECKS.json is not PASS.
NEW_ROWS.jsonl and REPLACEMENTS.jsonl are empty. REMOVE.json is empty because no source is replaced. ROOM_EXCLUSIONS.json separately lists 3,026 exact n.json-format records and passes N’s Removals parser; REMOVE_META.json pins its inputs. Neither patch is bound.
The wording filter threshold is 0.10 normalized Levenshtein distance (NFKC, casefold, whitespace collapse). Comparisons: 0; removals: 0. WORDING_CORPUS.json inventories available kit wordings; full corpus coverage and generated-wording clearance remain MISSING.
READ30.md prints 30 full source rows, one per occupied census cell. READ30_REVIEW.md records the text review; no generated-row correctness review is possible without GT.
VERIFY.json passes artifact integrity only: it independently recounts the store, matches source hashes and 30 samples, checks removal identities and size arithmetic, and confirms that no rows were admitted.
No training, GPU, network, SSH, Git, process termination, deletion or writes outside this workspace were performed. Borderline prose retained: none.
