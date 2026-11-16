# Facing-away direction supervision

The dataset teaches the student to reverse its facing direction while preserving the existing tool grammar, geometry sources, option order, and scene exclusions.

Labels use the pinned GT-derived centres printed in the admitted source trace. On the (x,z) floor plane, negate F−S, retain Q−S, and classify atan2(cross,dot). Easy uses the sign; medium assigns back at absolute bearings of at least 135 degrees and otherwise uses the sign; hard uses front below 90 degrees and back otherwise, followed by left/right. The existing 5-degree easy and 10-degree medium/hard boundary margins and source admission gates determine membership.

The tool call still faces the named object and returns its forward bearing. Program reasoning adds 180 degrees, wraps to [-180,180), and applies the stated rule. Labels agree with printed centres, the source unrounded angle, and the frozen returned bearing. Medium labels cannot be rotated by swapping strings because its three sectors are unequal.

Easy questions ask whether the queried object is to my left or to my right. Medium and hard retain their observer-relative templates and definitions. The three away phrases are assigned by SHA256 of the source ID. Options inherit the source shuffle without reordering. Geometry, traces, IDs, frames, and membership remain fixed for the away population.

The program leg contains 14,630 easy, 10,567 medium, and 8,788 hard rows. Its admitted files provide the full audit. The optional direct leg contains the same 33,985 away rows and exactly 33,985 forward twins. DIRECT_BOTH_OR_NEITHER.json pins one combined file per kind; consumers must take both directions or neither. Both directions use <think>, a blank line, </think>, a blank line, and the answer letter. Forward questions and answer contents match the pinned pool rows.

No letter weights are supplied or applied. MANIFEST.md and MANIFEST.json include raw letter/content distributions and exact constant-answer baselines for every kind and form. Away direct rows have no released label: dose.released_answer is null and its note states the geometry authority. Forward direct twins also clear the released letter because labels use the displayed pool option order.

Training excludes the held-out dev scenes and all evaluation scenes under the frozen filters and source exclusion lists. Exact twins cover 1,135 of 1,142 source captures; the seven absent captures lack eligible rows under the existing gates. Dev retains 150 fixed source IDs, 50 per kind, selected by the existing ID hash. The independent payload preserves frame/scorer metadata and uses geometric labels with missing-released strata.

The packed files use the frozen program reader. Direct files require the existing direct-source reader after frame resolution; the pool selector’s route-only rows path cannot ingest these direction rows. Validation uses pinned frame metadata without opening images or native annotation archives.

The main behavioural risk is an answer prior associated with the away wording. Dev constant accuracies are 54% for easy right, 36% for medium back (40% for majority right), and 36% for hard back-right. Training away accuracies are 50.9911%, 43.3330%, and 43.0018% respectively. Compare trained dev accuracy against these baselines and retain the forward dev measurement. CPU row validation establishes label and format consistency; it does not establish model improvement.

The facing-away format was motivated by a benchmark diagnosis. Any score on that benchmark’s facing-away items must be reported as adapted to its question format.
