# SPEC v3.12.1: ground and gap

Frozen interface, 2026-11-10; ORCH 0529Z ruling. Owner: ground_rows. Any change to this file requires a NOTE event. This extension preserves the v3.11 calculator and its point registry. Grounding rows are build artifacts; the route-table verdict controls training admission.

## Calls and exact response text

Calls occupy one line. NAME, X and Y are nonempty literal object names from the question, with no double quote, newline, angle bracket or control character. Names retain their spelling. No implicit object aliases or instance suffixes are invented. Attribute order is fixed.

```text
<ground obj="NAME">
<tool_response>
NAME: frames 3,4,9 (best 4, p 0.97)
P5: cam4 (0.41, 0.22, 1.83) m; f1 (1.12, -0.35, 2.47) m; spread 0.08
size 0.60 x 0.45 x 0.90 m
</tool_response>
```

The three body lines are mandatory on success. The frame list is ascending, comma-separated, with no spaces. `best K` names the frame supplying the centroid, spread and size. The point label comes from the shared calculator registry: allocate the next unused P integer, starting at P1 in an empty registry. Every successful call allocates one point; failed calls allocate none. Other tools share this sequence. The example's P5 assumes four points already exist.

```text
<ground obj="NAME">
<tool_response>
NAME: not seen
</tool_response>
```

`not seen` means no frame has accepted presence and a nonempty eligible lifted mask, or the coordinate basis is invalid. An unknown name has the same response. Size failure alone never means not seen. This observation does not prove physical absence or a count of zero.

Training excludes any row whose target operands are genuinely invisible in the student's 32 frames. The miss branch uses visible single-instance operands: at a configurable per-row probability, default 0.10, replace one ground response by the same `NAME: not seen` line to simulate a decoder miss. Select misses deterministically from the pinned seed and qid, and record the intervention explicitly; GT masks themselves remain unchanged. Stop geometric reasoning and continue that question's supplied VQA direct canonical derivation, ending on its independent GT option letter or number. The exact bridge line is `The tool did not find NAME, so I estimate from the frames.` Replace NAME by the failed ground operand. The own-tool-output rule governs the trace through the miss response. After the bridge, use only the question-matched derivation from the already-admitted VQA source, byte for byte, or its same canonical generator with the same frame-visibility rule; the continuation never refers to a tool value. A fixed sentence followed by a bare answer is not a canonical continuation. Diagnostic source continuations without that VQA admission remain review-only. Report selected, rendered and missing-canonical miss counts per type and review five misses per available type before launch. Drop the row when no question-matched direct canonical continuation exists. Report the configured rate, selected misses, missing-continuation refusals, and realized rate; reset the parameter to measured present-object MDG miss rate when available. No row ends with `<answer>not seen</answer>`.

The normal suffix uses `<answer>VALUE</answer>`. The miss suffix uses the same envelope around the canonical continuation's GT answer; its reasoning body must preserve the supplied canonical direct trace. Do not insert a made-up geometry value after a miss.

The gap call requires successful ground calls for both names in the same example. It measures mask surfaces, not the printed centroids.

```text
<gap a="X" b="Y">
<tool_response>
0.97 m
</tool_response>
```

For relative distance, use two or more distinct candidates in one call:

```text
<gap a="X" b="Y1" b="Y2">
<tool_response>
Y1: 0.97 m
Y2: 1.42 m
min "Y1" 0.97 m
</tool_response>
```

Candidate lines follow call order. The minimum uses the displayed two-decimal distances. Displayed ties print every tied name in call order, for example `min "Y1","Y2" 0.97 m`; a training row with a tied decision refuses. A missing candidate makes the entire body `not seen`. The LM selects the option matching the printed minimum and performs no set minimum.

If either operand has no successful grounding, or the eligible pair cannot be lifted, the body is exactly `not seen`. No point is allocated by gap. Malformed calls are parser errors, never geometric observations. Every response uses LF newlines; no blank lines inside the wrapper. The wrapper ends on its own line.

## Geometry and frame convention

Frames are 1-based displayed video indices, never seconds or source timestamps. Training has 32 recorded frames. Geometry and masks must match those exact source-frame indices; never silently substitute an odd frame. The `frames` list contains only frames passing presence >= frozen tau, with at least one eligible lifted point. GT presence is 1 for an annotated visible mask and 0 otherwise, using the source's declared visibility rule. Tau and that rule belong in the build receipt.

Use rkit `MaskGround.pixels/lifted`: one 3x3 binary erosion, pixel centres on the 0..1000 image grid, inclusive [20,980] crop; centre depth; finite world/camera points, positive camera depth; finite patch spread <=0.10 within 40 grid units of an image edge and <=0.25 elsewhere. Do not subsample eligible points. GT masks and GT geometry replace predictions without changing lifting or formatting code.

Choose `best` by largest pre-erosion mask area among eligible frames, then smallest frame number. Compute the componentwise median of its eligible points in the geometry's gravity-aligned, z-up world frame W. GT adapters must first transform native dataset coordinates into the same frame-1 gravity world that decode uses (horizontal right, heading, up), because componentwise medians are not invariant to yaw rotations. Transform that same centroid into both public frames; do not take separate medians after rotation. `camK` means camera K: x right, y up, z optical forward. For OpenCV coordinates, negate camera y. `f1` is the gravity-level frame at camera 1: x horizontal right, y up, z camera-1 heading projected onto the floor. Its origin is camera 1, even when best is another frame. Form its right vector as heading cross up. Reject an undefined level basis. Never print arbitrary dataset/world coordinates as f1.

Spread is the median patch spread over the retained pixels of best. Size is rkit `fit_gbox` on the same best-frame point set: its full `axesLengths`, with the larger fitted horizontal extent first, the smaller second and the vertical extent last. This is visible-mask extent, not a benchmark size label. A failed box fit prints exactly `size unavailable` as the third body line; the centroid and P registration still succeed. Never invent dimensions or turn a size failure into a grounding miss.

Gap follows rkit `V311Scene.pair_points`: rank common visible frames by decreasing minimum raw mask area, then frame number; take the first pair with nonempty eligible sets. If there is no common visible frame, rank all visible-frame pairs by (absolute frame gap, frame of X, frame of Y) and take the first eligible pair. After exhausting common frames, try every remaining visible pair in (absolute frame gap, frame of X, frame of Y) order. The private tie-break follows argument order; canonical a/b swapping is not implicit. Compute the complete minimum Euclidean distance with rkit `closest_sets`. Retain the selected frames privately in the audit. The response prints only the distance.

## Numbers, calculator and evidence

All new ground/gap real numbers print exactly two decimals using Python fixed-point formatting, with negative zero normalized to `0.00`; never scientific notation, NaN or infinity. Probabilities and spread are dimensionless; coordinates, size and gap are metres. Angles are whole degrees. Existing v3.11 calculator response text is unchanged, including its four-decimal dot/cross fields; the two-decimal cap applies to the new ground/gap fields. Register the rounded camera and f1 triples, so all calculator outputs derive from the displayed numbers.

The existing calls are `<dist P1 P2>`, `<angle S=P1 F=P2 Q=P3 rule=medium>` (or hard), and `<turn from=P1 at=P2 to=P3>`; their exact v3.11 response formatter remains authoritative. Ground rows must not invent a point, frame, instance identity or geometry claim absent from their own tool output. Direction rows print the sign convention: `On the floor, cross > 0 means left; cross < 0 means right.` Gap prose may name its operands because their ground responses printed those names. It must not claim a witnessing point pair, which gap does not print. Plans must not name unobserved frames.

## Row and admission contract

The suffix begins with `<think>\n`, contains plan, calls, forced responses and conclusion, and ends with `<answer>VALUE</answer>`. No tool-mode prompt flag. Count the complete suffix including tool responses and answer with the pinned local student tokenizer; reject lengths above 5,000 tokens, without truncation. Record prompt and total token counts when the multimodal prompt tokenizer is available; the world-4 consumer must enforce its approximately 10,000-token total budget.

Build the four routed candidates: object_abs_distance, object_rel_distance, object_rel_direction_medium and object_rel_direction_hard, plus explicit simulated-miss examples with direct canonical continuations. Counting, size and other direct types do not acquire a ground route from this extension. Record answer histograms per type and select unique examples against pinned benchmark aggregates: direction by answer content, relative distance by answer letter, absolute distance by the natural independent GT distribution of admitted scenes, with a cap per log-spaced distance bin (ORCH 0533Z). Report that numeric policy separately from benchmark matching; do not read benchmark answer files to construct bins. Never use the candidate generator's histogram as its own target. Report shortages. Counting rows, if supplied by a direct stream, require a separate benchmark-matched histogram; this branch produces zero counting rows.

Admission requires exactly one native instance per direction/absolute-distance operand and relative-distance target; relative candidates also require exactly one. A colour or other qualifier must resolve to that instance or the row refuses. Refuse a qualified phrase that matches several instances. The direction label and relative-distance winner must agree before and after printing/rounding. Refuse floor vectors shorter than 0.50 m, directions within 10 degrees of a decision boundary, and relative-distance margins below 0.10 m or 10% on either unrounded or printed values. Printed margins use Decimal arithmetic. Numeric object-distance agreement is at most 5% of the independent GT magnitude, without an additive floor; zero GT requires exact zero. Categorical labels match exactly.

GT replay must reproduce every forced response byte for byte through the decode backend. The program answer must meet or exceed v3.11's agreement with independently supplied GT on the same rows and scoring rule. Report coverage and refusals separately. Never use the generated program answer as its own GT label. Five real rows per type require visual text review before launch; synthetic fixtures cannot satisfy that gate.

## Atomic openers and span gating

The CP1 routing openers are atomic added tokens. Append `<ground` and `<gap` after the existing `<depth_at`, `<move`, `<pose`, `<turn`, `<box_3d` tokens using `AddedToken(normalized=False, special=False)`. Preserve all existing IDs. Initialize both input and output embedding rows from the mean of each opener's constituent-token embeddings, as `mdg_decode_tokens.add_ground_tokens` does. The MDG span gate opens on the atomic `<ground` token and includes the call's closing token in training and decode. `<gap` invokes fixed geometry and does not query MDG. The two embedding rows are trainable in TB-1; that trainer owns saving/reloading them. Count suffix tokens with this extended tokenizer. Emit the row's ground-call token positions and verify equality with QueryStream decode positions before launch.
