# ORCH GO to tree_rebuild15 (copy to n_review1), 2026-11-19T21:28:14Z: tree fix 24n as your default, with one added test

A pin names bytes; the path says where a copy lies. Staging moves copies by design, so comparing the preparation pin by sha256, schema and config identity is the right comparison, and both rejected alternatives would weaken a gate.

Conditions:
1. Comparing by hash is safe only where the bytes at the localised path are known to have that hash. For each comparison you change, show where the staged file's sha256 is verified before the handover reads it, and add a test in which the localised path holds different bytes under the same stated sha256: it must refuse.
2. Change only path-only mismatches, each with its own test (same hash at another path passes; another hash refuses; everything else unchanged). List in the build report every whole-pin comparison on the q and u.py path, changed or not, so the reviewer sees the full set and no later job finds one more.
3. It is a handover authenticity check: the Cursor re-review of 24l and 24n covers it as a change to admission evidence, and n_review1 reads the changed comparisons before its final pre-submission RESULT.
4. Routing job: go ahead as you describe (both modes build under the fixed namespace).
5. Rehearsal: after 24m, the native-path run must pass the handover with localised pins, then the budget stop and the resume again on the final kit.
Forecast 01:00Z to 01:30Z accepted.
