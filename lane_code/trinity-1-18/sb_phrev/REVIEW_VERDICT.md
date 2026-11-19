REJECT — the cached W1 result reproduces, but the required pre-score registration failed.

1. Registration: BARS.json self-dates 10:12:21Z and has mtime 10:12:42.900718Z; stale PER_ITEM scores have mtime 10:11:28.513851Z. HANDOFF_STOPPED_SESSION.md corroborates that scores existed without the bars file. The bars hash 150d16a232b42d86… matches DECISION.json, and the governing spec already contained the numeric thresholds.

Correction: set `written_before_any_score` to false, remove the pre-score-freeze certification, and label the results diagnostic. The claim that the replacement session had not read scores is unverified. A subsequent hash check cannot establish prospective registration.

2. Rerun: P0 matches A0 on 1,037/1,037 predictions, boxes, member-frame lists and refusal codes. W1 also matches its published output on every row: 60.5014 versus 56.7695, +3.7319 [2.0462, 5.4778]. Its safe contrast is +0.4605 [0, 1.2160] on 456 rows. Both numeric bars pass as written: gain ≥1.5 with lower bound >0; safe lower bound >−1.

All gain comes from the 84 heater rows across 20 captures; ScanNet++ gains +6.2319 [3.6442, 9.2039], and the other datasets gain zero. These numbers use 10,000 room draws, seed 20261119.

3. Reader contract: the rerun checks 1,471 priced pools with zero score/presence mismatches, identity failures or reader exceptions. Every priced frame has one presence. Mixed P_all/P_cf pools remain unpriced. Changed pools rebuild links, candidate identities, selector inputs and labels; all 770 raw label sets match the reference. An independent radiator probe also reproduces rebuilt selector vectors.

W1 represents one written prompt; W2c represents separate calls with object-level fallback. W2 combines raw and alias frames and needs tool support absent from the current call syntax. Correction: remove W2 from `shippable_passing` and label it a tool-change diagnostic. W2's +3.5873 passes numerically; W2c's +1.0897 fails phrase_worth. W1 remains the chosen eligible arm.

4. Fold rule: independent selection reproduces every saved W1/W2/W2c policy. Each fit excludes its held-out room fold, counts distinct capture/name objects using priced-frame raster IoU, and reads no distance label. The minimum-five and raw-on-tie rules hold. All five W1 folds and the all-room refit choose heater → radiator; coat hanger stays raw.

5. Cache provenance: all 209 caches are non-stub `dense_aliases`; their hashes match DECISION, conversion receipts and upstream tower receipts. The pinned producer preserves 1,066 radiator proposals across 20 captures, each with `source_query` and `source_presence`; none is tiled. The alias producer actually calls the radiator prompt, so these are retained radiator-call proposals.

Correction: replace “W1 understates the alias called alone” with “W1 prices a deduplicated subset; the exact serving score is unverified.” IoU >0.95 deduplication removes proposals against earlier retained instances. Restoring them can change linking and selection in either direction. Exact standalone rerun evidence is MISSING at the spec's `out/pool_part2/<key>/candidates.json`; CPU part 1 does not establish that result.

6. Withheld rooms: scene0201_02, scene0478_00, scene0478_01, scene0614_02 and scene0692_03 contribute 25 rows, with zero heater rows. Excluding those captures from both scoring and phrase fitting, while retaining the registered fold assignments, changes no policy. On the remaining 1,012 rows, W1 scores 60.7510 versus 56.9269, +3.8241 [2.1629, 5.6281]; safety is +0.4751 [0, 1.2269] on 442 rows. Both bars still pass.

Correction: disclose this overlap and sensitivity result in PHRASE_REPORT/DECISION; K1 train membership alone does not certify downstream teaching eligibility. The routed training-row rewrite count remains MISSING, owned by tree_rebuild.

7. Tests and package: all 24 shipped tests and two independent probes pass. The shipped suite exercises real cache_for/lift behavior and synthetic pool/fold decisions; its output-parity tests compare saved files, which this review supplements with a full rerun. The freeze test checks hash equality, not chronology. Archive SHA256 6e5dd8f48e653f97… matches the requested package; all 504 archived files match the source tree.

Reproduction, from this workspace:

`bash run_review.sh audit_static.py` produces STATIC_AUDIT.json: chronology, hashes, archive and cache-provenance counts.

`bash run_review.sh rerun.py` rebuilds all 209 captures from source caches into rerun_caps/; `bash run_review.sh analyze_rerun.py` produces RERUN_AUDIT.json: parity, contracts, policies, scores and exclusions above.

`bash run_review.sh check_tests.py` produces TEST_AUDIT.json: the 26 behavioral-test results. Every evidence JSON records input SHA256 hashes.

Scope: CPU only on trinity-1-18, at most eight CPU affinity slots for the four rerun workers; source lanes stayed read-only. No GPU, network, SSH, Git, process termination or deletion. Registration chronology is retained because check (1) explicitly requires it.
