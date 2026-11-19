R0: 0 / withheld-80: 0 / BENCH v2: 0 / dev-S1: 0 / K1: 4,959; unresolved rows: 0.

The audit covers all 204,413 v7 rows. Every row has a proven scene and a resolved room.
Store SHA256: `210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443`.

| Proof tier | v7 tokens resolved | v7 rows resolved |
|---|---:|---:|
| A | 2,574 | 189,498 |
| B | 308 | 11,842 |
| C | 84 | 3,073 |

Tier A uses explicit source-row canonical witnesses, including v7 row fields. Tier B uses the pinned original rows_a2 archive map. Tier C requires a unique exact printed-token preimage. Assignment is exclusive in A, B, C order.

| List | A rows | B rows | C rows | Total |
|---|---:|---:|---:|---:|
| R0 | 0 | 0 | 0 | 0 |
| withheld-80 | 0 | 0 | 0 | 0 |
| BENCH v2 | 0 | 0 | 0 | 0 |
| dev-S1 | 0 | 0 | 0 | 0 |
| K1 | 110 | 4,770 | 79 | 4,959 |

| K1 stream | Rows | K1 family | Rows |
|---|---:|---|---:|
| MISSING | 69 | box_3d | 69 |
| dose_route_direct | 225 | obj_appearance_order | 336 |
| r1g | 430 | object_counting | 277 |
| rows_rebuild_d0_ARKIT_gaps | 262 | object_rel_direction_easy | 950 |
| rows_rebuild_d0_ARKIT_gen_r2 | 354 | object_rel_direction_hard | 1185 |
| rows_rebuild_d0_T0_gaps | 32 | object_rel_direction_medium | 891 |
| rows_rebuild_d0_T0_gen_r2 | 46 | object_rel_distance | 832 |
| rows_rebuild_d0_T1H1_gaps | 59 | object_size_estimation | 194 |
| rows_rebuild_d0_T1H1_gen_r2 | 80 | route_planning | 225 |
| rows_rebuild_d0_T1H2_gaps | 76 |  |  |
| rows_rebuild_d0_T1H2_gen_r2 | 94 |  |  |
| w1g | 3232 |  |  |

The hash function agrees with 2,569 witnessed tokens and 2,520 hashed archive tokens, with zero disagreements. The archive also has 1,083 literal keys. All 2,571 hashed v7 row-field witnesses agree as well.
The supplied Tier A and Tier B maps agree on all 1,850 overlapping entries.
A_B: 1,858 agreements; 0 disagreements.
A_C: 2,577 agreements; 0 disagreements.
B_C: 2,520 agreements; 0 disagreements.
Preimage collisions: 0; quarantined v7 rows: 0.
Candidate enumeration: 8,357 native scene identifiers and 2,229 other-dataset identifiers. The candidate file records literal origins; the scan manifest records input hashes.
Enumeration covers local metadata, path names, archived member indexes, and rows_a2/v7 SQLite rows; nested archives are not recursively unpacked. Other datasets have no supported carrier token function.
The staged build_a2_other.py is a job-receipt wrapper, not a scene-token builder. sources.py loads existing maps; neither supplies another minting function.

Baseline reproduced on 85,038 already-resolvable rows: 2,637 K1 rows and zero R0 rows. The baseline alias map is used only for this check; final mappings require A, B or C proof.

R0: `bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3`; 372 rooms.
withheld-80: `634820b44927b1a50c18db9b90246b4b99f8954b0d7f5f2893e547f1c92879ed`; 80 rooms.
BENCH v2: `3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970`; 511 rooms.
dev-S1: `969cdb56ce508eff79390d67099c889b92bd360e93dc42ba07f3683ec216a986`; 100 rooms.
K1: `4d4736cf64e496a184d36d74d710e76d1673429e28790613794867ac077048a9`; 50 rooms.

Build 17’s exact Rooms.canonical and Rooms.room methods determine canonical scenes and physical rooms. ARKit captures use the pinned visit metadata; BENCH/dev use physical_groups; withheld-80 uses rooms. K1 uses the pinned split linked to the verified teacher source.
ScanNet++ canonical names use scannetpp; Rooms.room treats scannetpp and scannetppv2 identically. Proof records retain the A/B evidence names.
Streams are row.pool; families are row.question_type. ROOM_AUDIT_TIERED.json gives marginal and joint counts, plus up to 20 example rows per nonempty list/tier cell.

MISSING rebuild inputs (not needed for this proof-tier audit):
`/scratch/jjyeung/n30_mirror/rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite` (expected SHA256 4af43b409969c360d530fde01c044358b6089702a0f5aa8055896276a94deb59).
`/scratch/jjyeung/n30_mirror/rows_a2/work/build_a2.py` (expected SHA256 89b2203f7257ef1a23d3fb4783b142e8b63c3174a47d8dfd8aa8650c2dcdef9b).

Commands, from this workspace:
`python work/enumerate_candidates.py` produces candidate and scan counts and locates exact list pins.
`python work/recover_k1.py` verifies the archived K1 source against its exact hash.
`python work/finish_candidates.py` completes plain-JSON and structured-list candidate enumeration.
`python work/audit.py` produces every mapping, overlap, baseline, tier, room-list, stream and family count above.
`python work/validate.py` replays exported preimages and checks count totals and example rows.
`python work/finalize_report.py` renders the stream/family table from the audit JSON.
`python work/package.py` packages the outputs; `sha256sum out/sb_alias2.tar` verifies the archive digest.
Borderline wording retained: “baseline” identifies the requested independent validation population.
