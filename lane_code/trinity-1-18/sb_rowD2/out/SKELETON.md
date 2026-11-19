Every admitted direction row uses the same four-line body. Preserve the store's direct-row wrapper and final option letter:

```text
<think>
Seen: {X_evidence}; {Y_evidence}; {Z_evidence}.
Reference heading: standing at the {X} and facing the {Y}, the {Z} {is_or_are} {reference_relation}.
Question clause: "{quoted_clause}." {operation}
The {Z} {is_or_are} {answer_relation}.
</think>

{answer_letter}
```

The third line quotes the question's actual heading clause, preserving its words. This includes toward paraphrases such as `look toward the table` and `with the table ahead of me`. The quote ends before the operation. A terminal period closes the quoted clause; it replaces the question's clause-ending comma.

| Clause | Exact operation text |
|---|---|
| Toward | `This keeps the reference heading.` |
| Away or opposite | `This requires a half turn: front becomes back, back becomes front, left becomes right, and right becomes left.` |

Toward example: `Question clause: "facing the table." This keeps the reference heading.`

Away example: `Question clause: "facing away from the table." This requires a half turn: front becomes back, back becomes front, left becomes right, and right becomes left.`

Opposite example: `Question clause: "facing in the opposite direction of the table." This requires a half turn: front becomes back, back becomes front, left becomes right, and right becomes left.`

Use `{object} in frame {N}` for each evidence entry when the source cites a verified sampled frame. Preserve those source citations; N must be an integer from 1 to 32. Without source citations, each entry is only `{object}`. The w1g opening therefore becomes `Seen: {X}; {Y}; {Z}.` No frame number is inferred from a timestamp or generated from geometry.

`{X}` is the standing object, `{Y}` is the reference-facing object, and `{Z}` is the queried object. A source-bound instance mapping must establish these roles. Select `is` or `are` to agree with the queried noun. The question remains unchanged for replacements; twins change only the facing clause, plus the easy question's referent when needed to state the observer's left/right unambiguously.

Reference relation strings for non-boundary quadrants:

| GT reference quadrant | `{reference_relation}` |
|---|---|
| front-left | `in front of me, on my left` |
| front-right | `in front of me, on my right` |
| back-left | `behind me, on my left` |
| back-right | `behind me, on my right` |

Final relation strings:

| Recomputed answer content | `{answer_relation}` |
|---|---|
| left | `to my left` |
| right | `to my right` |
| back | `behind me` |
| front-left | `at my front-left` |
| front-right | `at my front-right` |
| back-left | `at my back-left` |
| back-right | `at my back-right` |

Compute both relations from GT instance coordinates with the source's signed up axis and coordinate convention. Project the facing vector and target displacement onto the horizontal plane. The reference heading faces Y from X. Toward retains it; away and opposite negate it. Map the recomputed content to the unchanged lettered options.

Easy uses the left/right side. Hard uses the two signs of the target's heading-relative displacement. Medium uses the question's angular definition: back requires a turn of at least 135 degrees; otherwise choose left or right by side. A medium reference label cannot be flipped to derive its answer because left/right labels discard the angle. Its reference quadrant also does not determine its answer.

Refuse missing instance roles, missing geometry or signed-up convention, coincident X/Y or X/Z, nonfinite coordinates, ambiguous instance joins, and unresolved direction boundaries. Boundary tolerance must come from the source geometry policy; it is MISSING in this build. Refuse any row without an option matching the recomputed content. Do not derive GT from an old trace, answer, opposite twin, benchmark wording, or development result.

This specification is ready for review. No generated row is certified: source-bound GT inputs are MISSING. Binding remains the orchestrator's decision.
