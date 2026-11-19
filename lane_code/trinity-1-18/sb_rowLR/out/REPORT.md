# sb_rowLR: traced large-room rows

Built 72 checked rows: 24 at ≥40 m², including 12 at ≥60 m², plus 48 controls at 10–40 m².
The requested 600 large rows are short by 576. The local pool has only six eligible captures at ≥60 m².
Two rows per capture and the 50% ≥60 requirement cap this pool at 24 large rows; no scene was repeated more than twice.

| Dataset | Local GT captures | Pass exclusions | ≥40 m² | ≥60 m² | New rows |
|---|---:|---:|---:|---:|---:|
| ScanNet | 69 | 35 | 2 | 1 | 24 |
| ScanNet++ | 102 | 71 | 17 | 5 | 48 |
| ARKitScenes | 0 | 0 | 0 | 0 | 0 |

These are counts in the discovered local pool, not totals for the datasets. ARKitScenes training GT is MISSING in that pool.
The 35 eligible ScanNet captures cover 28 physical rooms; the 71 ScanNet++ captures cover 71 rooms.
All 19 eligible large captures have exact-pin store image bindings and qualifying landmark traces.
The build selects 12 large captures (six in each large band) and 24 controls, with two question variants per physical room.

| Dataset | 10–20 | 20–40 | 40–60 | 60–100 | ≥100 m² |
|---|---:|---:|---:|---:|---:|
| ScanNet | 12 | 8 | 2 | 2 | 0 |
| ScanNet++ | 12 | 16 | 10 | 8 | 2 |

| Room area (m²) | Store v7 before | Added | Hypothetical after |
|---|---:|---:|---:|
| <20 | 315 | 24 | 339 |
| 20-40 | 100 | 24 | 124 |
| 40-60 | 11 | 12 | 23 |
| 60-100 | 5 | 10 | 15 |
| >=100 | 0 | 2 | 2 |

The room family grows from 431 to 503 rows. Its median moves from 15.96 to 16.84 m²; its mean moves from 17.70 to 20.21 m².
The ≥40 share rises from 3.7% to 8.0%. The controls limit the median change to 0.88 m²; the area prior is not unchanged.
Square-foot labels are converted to m² for the histogram. The source family contains 357 square-metre rows and 74 square-foot rows.

The build uses w19’s newer sealed tree_r1 (8ea1fe6bd032c9cc49f5974279a18e211b0d55e3f615fc083fb1acc678689caa).
The trace follows rows_r1/work/codeF/build_room.py: unique-label, disjoint-stem landmarks, best-view pixel share ≥0.01, and the farthest horizontal pair.
The third landmark is between the pair only at projection 0.25–0.75 and perpendicular distance <0.35 times the pair length.
The label follows room_v314 sensor geometry: stride-four depth pixels, native z-up poses and per-frame intrinsics; 5 cm XY cells above percentile-1 height minus 0.1 m; 0.2 m disk closing and hole filling.
The trace stays qualitative and gives the rounded square-metre label after </think>. It contains no routed room call.
GT lives at /scratch/jjyeung/orch_cd/dose_pool/out/t1_gt/gt, a path cited by the kit’s pool_room fixture.
New rows derive room labels from that GT and retain exact image pins and licenses from checked store-v7 scene rows; sources need not already be room questions.

Checks: exact nine-cell counts; 72 unique qids and formula-derived candidate_ids; zero store identity collisions; 36 sources and physical rooms, each used twice.
Checks: independent per-row back-projection, occupancy area, landmark visibility/ranking, relation and target reconstruction pass on all 72 rows.
Checks: 44 exact-pin room_v4 metric labels agree with room_v314; five-way room exclusions have zero output hits; no unlisted field changes.
N validation passes for all new rows and source uses through r2_adapters.normalize and r2_contract.validate(vqa); the shared trace grammar also passes.
ground_rows.pack/validate is NOT_APPLICABLE to the required direct form: that API requires a routed room computation. The native direct intake branch is the relevant check.
Thirty complete records are in READ30.md; I read every sampled question and trace. Visibility was checked numerically, without reading RGB images from NFS.
Wording: authored variants pass normalized character edit distance >0.25 against 1,001 distinct wordings in the local kit/item corpus; 0 variants removed. Minimum distances: 0.619 and 0.573.
Wording scope: 173 kit/mirror JSON or JSONL files scanned, 43 with question text; NFKC, casefold and word-token normalization.

MISSING: /scratch/jjyeung/orch_cd/dose_pool/out/DEV_S1/QIDS.jsonl.gz; no claim of complete external benchmark wording coverage.
MISSING: original room_v4 raster roots /scratch/jjyeung/orch_n30/rows_a2/work/rroot_v3/{new,k1r}; the kit-referenced local GT pool supplies this build instead.
Not done: 600-row target, ARKitScenes coverage, complete dataset census, full benchmark-bank wording audit, RGB-byte verification, store merge or training.
The 600-row target needs at least 150 eligible ≥60 m² scenes at the two-row cap; only six are available here (144 more needed).
Borderline chronology retained: none. Before/after above describes the requested distribution comparison.

Reproduce all reported counts: `python census.py; python find_bindings.py; python prepare.py; python wording.py; python generate.py; python check.py; python finalize.py`.
Use `PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1` for each command; all reads are local after the supplied reference snapshots.
census.py produces pool eligibility and baseline counts; prepare.py checks traces/bindings; generate.py asserts cells; check.py produces validation counts; finalize.py produces histograms and this report.
out/sb_rowLR.tar contains code, row/source snapshots and reports. Its full sha256 is in out/sb_rowLR.tar.sha256.
