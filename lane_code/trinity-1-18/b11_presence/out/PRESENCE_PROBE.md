# Presence probe on K1 (step 544): draft — numbers pending the GPU run

## Call spec `<seen obj=NAME>`
- Call: the model emits `<seen obj=NAME>` inside its CoT. Inside the same forward pass the presence head reads, for each of the 32 anchors k, the model's own next-token presence logit for NAME at frame k (arm chosen by train CV: V = in-video "Point to the NAME in frame k" query against the clip already in context; I/Y = per-frame single-image query), feeds the 32 logits to the 7-weight hazard head, and returns `first seen in frame k` (or `not seen`) as the tool response tokens.
- No threshold, rule table or fallback outside weights: the head's argmax over {1..32, never} is the answer.
- Cost per item: arm V = 32 query tails against the cached clip prefix per object; I/Y = 32 single-image prefixes per object set. Measured seconds per query and per 4-object item: [from journal timing, pending].

## Results: pending
