# Counting proposal and release gate

This kit tests a per-frame instance count under a K1-training freeze. `KIT_SPEC_count_pricing.md` defines the protocol; `kit/files/FROZEN_CONFIG.json` provides its executable configuration and input hashes.

The selector compares raw and duplicate-suppressed frame counts, maximum and second maximum, and the six registered joint-score thresholds. It uses only K1 TRAINING captures. It chooses constant 5, 6, or 7 on those same training captures. The bootstrap policy, zero-gain gate, response format, row filter, and launch decision are frozen before any new dev output is read.

A proposal may request R0-dev inference only when its training MRA exceeds the frozen constant with a positive paired capture-bootstrap lower bound. Its single R0-dev comparison tests the frozen proposal against direct S1_544 and that constant. dev-S1 is diagnostic only. No pooled decision or dev-selected response, floor, row form, constant, or threshold is authorized.

A training rejection disables the proposed response and rows and requires zero GPU-hours. Count-first formatting, grouping, forced-close limits, answer-frequency limits, identity features, and learned counting heads have no release gate in this kit. Any such proposal needs its own K1-training selection receipt; it cannot reuse or extend this category's R0-dev look.

`out/MISSING_INPUTS.json` records the unavailable pilot artifacts and fixture frames. The kit does not claim to reproduce learned merge, geometry, or learned regression rows without those inputs. The supplied pilot scripts and tables under `kit/work` are diagnostic source records, not executable release policy.

The ledger binds authorized IDs, code, manifest, settings, and configuration before inference. It consumes the category's one look before scoring real outputs. Official item files are excluded, and all inference inputs must resolve to pinned local scratch paths.
