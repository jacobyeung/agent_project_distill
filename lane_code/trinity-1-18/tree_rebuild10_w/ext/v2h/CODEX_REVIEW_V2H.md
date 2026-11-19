No verified problems found.

| Check | Verified result |
|---|---|
| **1. Split** | Recomputed deterministically from 21 wordings: 15 failing, 6 other; HELD-OUT = 5 failing + 3 other; TRAIN-DEV = 10; unused = 3. All recorded memberships and item counts match. |
| **2. Held-out exclusion** | **0/6,000** output questions and **0/6,000** supplied source questions match HELD-OUT templates. None of the 50 training templates equals or contains a HELD-OUT wording. Minimum HELD-OUT–NEW normalized edit distance: **0.435897**. |
| **3. NEW wordings** | Filter reproduced exactly: 80 drafted, 3 near-dev rejects, 2 near-draft rejects, 75 passed, 40 chosen. Minimum distance to dev/routed templates: **0.409091**; between chosen templates: **0.25**. Read all 40 across the four units; found no definite grammar or distance-convention ambiguity. All name both objects, closest points, and the unit. |
| **4. Rows versus sources** | **6,000/6,000** preserve every field outside the permitted edits and correctly fill their templates. All 200 cells meet quota: 40 cells × 50 and 160 × 25. Exactly 6,000 distinct sources used once; 6,000 unique output qids. Provenance and published content hashes match. |
| **5. Arithmetic** | **4,500/4,500** non-metre rows pass printed-gap, conversion-factor, HALF_UP rounding, answer/tag, and unit checks. **1,500/1,500** metre answers equal their printed gaps. |
| **6. Kit validation and identities** | Native packing and validation pass for **6,000 outputs and 6,000 sources**, rebuilding distance events as required. All 6,000 candidate IDs match their recorded formula rule; all are unique; none equals a supplied source ID. All 6,000 question identities match. |
| **7. R0 evaluation set** | **290 reworded + 290 twins**, 580 unique IDs. Units: m/ft/in/cm = **73/73/72/72**. All 290 wording assignments, seeded assignments, conversions, and twin relationships pass. Each reworded question matches exactly one HELD-OUT wording. All 580 frame records pass consistency checks. No supplied training-row room overlaps these R0 rooms. |

The closest HELD-OUT–NEW pair is “Using the nearest points, what’s the spacing…” and “Tell me the nearest-point gap…”.

No verified item-field blocker prevents scoring with the specified question-unit-aware `official_vsi_mra` scorer. The scorer itself was not supplied or executed.

Scope: the full bound-N exclusion scan is recorded in `SUMMARY.json` for **16,370 rows**, but those full slices are unavailable here. Original R0 preservation was checked against the supplied twins and generator, not the unavailable upstream file.

**Verdict: GO for the supplied artifacts.**