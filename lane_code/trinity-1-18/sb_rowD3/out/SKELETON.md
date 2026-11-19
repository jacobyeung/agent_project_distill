The question clause selects the operation under either opening. X is the standing object, Y the reference-facing object, and Z the queried object. Bind these roles to GT instances before rendering any row.

| Opening | First line |
|---|---|
| Seen | `Seen: {X} in frame {a}; {Y} in frame {b}; {Z} in frame {c}.` |
| Step 1 | `Step 1: find the {X}, the {Y} and the {Z}.` |

The Seen frame numbers require source-bound evidence and must index the supplied sampled frames (1–32). The Step 1 sources have no object-frame citations. Their Seen variants remain MISSING until that evidence is supplied.

Each opening has the following three clause variants. The reference line is conditional so it cannot imply that the question already faces Y.

```
Step 2: if I stood at the {X} facing the {Y}, the {Z} would be {GT_reference_relation}.
```

| Question clause | Operation line, as its own step |
|---|---|
| Toward | `Step 3: the question says "{exact_toward_clause}". I keep that heading; no turn applies.` |
| Away | `Step 3: the question says "{exact_away_clause}". I make a half turn: front and back swap, and left and right swap.` |
| Opposite | `Step 3: the question says "{exact_opposite_clause}". I make a half turn: front and back swap, and left and right swap.` |

Both openings finish with `Step 4: in the question's heading, the {Z} is {GT_question_relation}.` Select `is` or `are` to agree with Z. The final option letter must match the recomputed relation. Preserve the direct-VQA think block and answer format from the store.

Compute the reference and question headings independently from source-bound GT coordinates, signed up axis, coordinate convention, and instance roles. Toward retains the horizontal X-to-Y vector; away and opposite negate it. Recompute the target relation in that heading. Never obtain a new answer by swapping an old label.

Easy uses the side sign. Hard uses front/back and left/right signs. Medium uses the actual horizontal angle and its question's stated back threshold (135 degrees where specified); a left/right label or reference quadrant alone cannot determine the answer after a half turn. Refuse ambiguous roles, degenerate vectors, missing conventions, and unresolved boundaries.

Balance GT reference quadrants separately from answer quadrants. Include both front and back reference relations in both turn wordings. Widen object coverage by selecting the room-eligible Step 1 scenes and triples. Never use a benchmark name list to create training wordings.

These are templates, not training rows. No GT-certified rendered example is available in this build.
