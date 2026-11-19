The required 8,511-of-8,511 exactness gate FAILED. No new rows were generated; this archive is failure evidence and must not be bound as a row patch.
Only 5,846 pairs have an exact, unique answer mapping. All 2,665 medium pairs have two allowed answers and fail the one-to-one option requirement.
The supplied generator build_away.py rewords admitted v6 away rows and preserves their answers. It does not generate away answers from toward labels.
The supplied check_away.py tests medium answers against sets: left permits right/back, right permits left/back, and back permits left/right. This is consistency, not exact reproduction.
All 8,511 pairs pass that original consistency rule. A literal label flip disagrees with 1,274 stored answers; it is reported only as a diagnostic, not substituted for the original rule.
GATE.json names every pair, all ambiguous failures, and every literal-flip disagreement. EXAMPLES.json contains full source/twin records. Both checks compare option content and then option letters.
Example: toward label left maps to stored back for vsi590k_116616 but to stored right for vsi590k_243209. EXAMPLES_REVIEW.md records the text review of 12 source/twin pairs; no new mapping was inferred from their traces.
Commands: `PYTHONDONTWRITEBYTECODE=1 python build_rows.py` produces every gate, census and exclusion number (expected exit 2); `PYTHONDONTWRITEBYTECODE=1 python verify_outputs.py` independently checks all 8,511 pairs; `PYTHONDONTWRITEBYTECODE=1 python finalize.py` writes this report and archive.
Store v7: `210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443`; 204,413 rows, including 93,370 direction rows.
N uses the newer sealed W/w19 tree: `8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa`. Imported validator and room modules match that seal.

| Family | Exact unique reproduction | Ambiguous |
|---|---:|---:|
| easy | 3664 | 0 |
| medium | 0 | 2665 |
| hard | 2182 | 0 |

Medium transitions below show why a toward answer alone cannot select the away answer.
| Toward label | Stored away label | Rows |
|---|---|---:|
| back | left | 42 |
| back | right | 50 |
| left | back | 597 |
| left | right | 749 |
| right | back | 585 |
| right | left | 642 |

Counts per opening × literal clause × answer label follow. Each entry is `v7 / admitted by N`; before and after are identical because the gate stopped generation.
Easy labels do not identify quadrants; medium back/left/right use the source’s 135-degree rule. The hard labels are quadrants.
| Opening | Clause | left | right | back | front-left | front-right | back-left | back-right |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Step 1 | toward | 14393 / 13797 | 13389 / 12842 | 734 / 696 | 9021 / 8621 | 8537 / 8205 | 1808 / 1739 | 2019 / 1937 |
| Step 1 | away | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| Step 1 | opposite | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| Seen | toward | 6617 / 6454 | 6158 / 5997 | 193 / 187 | 1935 / 1877 | 1903 / 1832 | 311 / 298 | 362 / 353 |
| Seen | away | 5101 / 4962 | 5468 / 5328 | 2399 / 2348 | 362 / 353 | 311 / 298 | 1903 / 1832 | 1935 / 1877 |
| Seen | opposite | 2476 / 2476 | 2671 / 2671 | 1182 / 1182 | 181 / 181 | 158 / 158 | 910 / 910 | 933 / 933 |

Per-clause v7 answer histogram, unchanged after:
toward: left=21010, right=19547, back=927, front-left=10956, front-right=10440, back-left=2119, back-right=2381.
away: left=5101, right=5468, back=2399, front-left=362, front-right=311, back-left=1903, back-right=1935.
opposite: left=2476, right=2671, back=1182, front-left=181, front-right=158, back-left=910, back-right=933.

The split is 0 away and 0 toward additions. The mandatory gate prohibits proceeding with a partial easy/hard build; the 8,000-row allocation and object-name balancing are not attempted.
N’s direct schema and trace validators each pass all 93,370 direction sources. All 8,511 pair identities preserve scene, ordered objects, frame metadata and source provenance; all stored away answers/options equal their admitted v6 away sources.
N’s K1, R0, withheld-80, dev-S1 and BENCH v2 room authorities and n/z/u removal lists were applied to every direction row. Input hashes are in CHECKS.json. Exclusion hits: {"removal:u_union.json": 3026, "room:K1": 3026}.
The admitted direction census contains 90,344 rows. The K1 and u-union hits overlap; their union excludes 3,026 rows.
New-row checks are NOT RUN: exact quotas, source reuse, pack/validate, candidate IDs, field differences, independent truth, removal inheritance, wording-distance clearance and READ60. READ60.md explicitly records the gate stop; no source examples are passed off as generated rows.
No new wording was emitted: wording comparisons and wording removals are 0. No geometry was recovered or inferred. Direct v7 rows lack routed ground_record/events; source validation does not claim routed packing.
VERIFY.json passes failure-evidence integrity only. NEW_ROWS.jsonl and SOURCE_MAP.jsonl are empty. Every output JSON includes input hashes; the tar checksum is in sb_rowD5.tar.sha256.
No GPU, network, SSH, Git, process termination, deletion, training or writes outside this workspace were used. Borderline prose retained: none.
