# SPEC v3.13: benchmark box distance, surface observations and instance grounding

Review interface, 2026-11-10. Owner: spec313_kp. This interface preserves the v3.11 calculator and the v3.12.2 lifting and frame choice; admission follows the rules below. Benchmark absolute- and relative-distance rows use full-box grounding and the sampled_box_512 tool measurement. Visible-surface calls retain registered witnesses. Training admission is NO-GO until the orchestrator rules; ADOPTION_RULE.md remains a separate prerequisite. A session with enabled=False uses v3.12.2 exactly; it rejects successor calls and allocates no gap points. Keypoint calls require keypoint_calls=True as well as enabled=True.

## Calls and exact response text

Calls occupy one line. NAME, X and Y are nonempty literal object names from the question, with no double quote, newline, angle bracket or control character. Names retain their spelling. No implicit object aliases or instance suffixes are invented. Attribute order is fixed.

```text
<ground obj="NAME">
<tool_response>
NAME: frames 3,4,9 (best 4)
P5: cam4 (0.41, 0.22, 1.83) m; f1 (1.12, -0.35, 2.47) m; spread 0.08
size 0.60 x 0.45 x 0.90 m
</tool_response>
```

The three body lines are mandatory on ordinary ground success; mode="box" uses its own four-line grammar below. The frame list is ascending, comma-separated, with no spaces. `best K` names the frame supplying the centroid, spread and size. The point label comes from the shared calculator registry: allocate the next unused P integer, starting at P1 in an empty registry. Every successful ordinary ground call allocates one point; failed calls allocate none. Other tools share this sequence. The example's P5 assumes four points already exist.

```text
<ground obj="NAME">
<tool_response>
NAME: not seen
</tool_response>
```

`not seen` means no frame has accepted presence and a nonempty eligible lifted mask, or the coordinate basis is invalid. An unknown name has the same response. Size failure alone never means not seen. This observation does not prove physical absence or a count of zero.

Training excludes any row whose target operands are genuinely invisible in the student's 32 frames. The miss branch uses visible single-instance operands: at a configurable per-row probability, default 0.10, replace one ground response by the same `NAME: not seen` line to simulate a decoder miss. Select misses deterministically from the pinned seed and qid, and record the intervention explicitly; GT masks themselves remain unchanged. Stop geometric reasoning and continue that question's supplied VQA direct canonical derivation, ending on its independent GT option letter or number. The exact bridge line is `The tool did not find NAME, so I estimate from the frames.` Replace NAME by the failed ground operand. The own-tool-output rule governs the trace through the miss response. After the bridge, use only the question-matched derivation from the already-admitted VQA source, byte for byte, or its same canonical generator with the same frame-visibility rule; the continuation never refers to a tool value. A fixed sentence followed by a bare answer is not a canonical continuation. Diagnostic source continuations without that VQA admission remain review-only. Report selected, rendered and missing-canonical miss counts per type and review five misses per available type before launch. Select simulated misses only from rows with an admitted exact scene/frame/question/options/answer-matched continuation whose wording agrees with its answer under the question rule. A row without one stays normal; its normal geometry gates still apply. Report the configured rate, selected misses, missing-continuation refusals, and realized rate; reset the parameter to measured present-object MDG miss rate when available. No row ends with `<answer>not seen</answer>`.

The normal suffix uses `<answer>VALUE</answer>`. The miss suffix uses the same envelope around the canonical continuation's GT answer; its reasoning body must preserve the supplied canonical direct trace. Do not insert a made-up geometry value after a miss.

The implicit surface-gap call below requires successful ordinary ground calls for both names in the same example. It serves visible-surface observation targets. Benchmark distance targets use the explicit box rule specified below.

```text
<gap a="X" b="Y">
<tool_response>
0.97 m
P3: X nearest point cam3 (0.00, 0.00, 2.00) m; f1 (0.00, 0.00, 2.00) m
P4: Y nearest point cam9 (0.97, 0.00, 2.00) m; f1 (0.97, 0.00, 2.00) m
</tool_response>
```

For relative distance, use two or more distinct candidates in one call:

```text
<gap a="X" b="Y1" b="Y2">
<tool_response>
Y1: 0.97 m
Y2: 1.42 m
min "Y1" 0.97 m
P4: X nearest point cam3 (0.00, 0.00, 2.00) m; f1 (0.00, 0.00, 2.00) m
P5: Y1 nearest point cam9 (0.97, 0.00, 2.00) m; f1 (0.97, 0.00, 2.00) m
P6: X nearest point cam3 (0.00, 0.00, 2.00) m; f1 (0.00, 0.00, 2.00) m
P7: Y2 nearest point cam4 (1.42, 0.00, 2.00) m; f1 (1.42, 0.00, 2.00) m
</tool_response>
```

Candidate lines follow call order. The minimum uses the displayed two-decimal distances. Displayed ties print every tied name in call order, for example `min "Y1","Y2" 0.97 m`; a training row with a tied decision refuses. A missing candidate makes the entire body `not seen`. The LM selects the option matching the printed minimum and performs no set minimum.

If either operand has no successful grounding, or the eligible pair cannot be lifted, the body is exactly `not seen`. A successful v3.13 surface gap allocates two points per candidate, in candidate order, after validating all endpoints. A failed call allocates none. Malformed calls are parser errors, never geometric observations. Every response uses LF newlines; no blank lines inside the wrapper. The wrapper ends on its own line.

## Geometry and frame convention

Frames are 1-based displayed video indices, never seconds or source timestamps. Training has 32 recorded frames. Geometry and masks must match those exact source-frame indices; never silently substitute an odd frame. The `frames` list contains only frames passing presence >= frozen tau, with at least one eligible lifted point. GT presence is 1 for an annotated visible mask and 0 otherwise, using the source's declared visibility rule. Tau and that rule belong in the build receipt.

Use rkit `MaskGround.pixels/lifted`: one 3x3 binary erosion, pixel centres on the 0..1000 image grid, inclusive [20,980] crop; centre depth; finite world/camera points, positive camera depth; finite patch spread <=0.10 within 40 grid units of an image edge and <=0.25 elsewhere. Do not subsample eligible points. GT masks and GT geometry replace predictions without changing lifting or formatting code.

For ordinary ground, choose `best` by largest pre-erosion mask area among eligible frames, then smallest frame number. Compute the componentwise median of its eligible points in the geometry's gravity-aligned, z-up world frame W. GT adapters must first transform native dataset coordinates into the same frame-1 gravity world that decode uses (horizontal right, heading, up), because componentwise medians are not invariant to yaw rotations. Transform that same centroid into both public frames; do not take separate medians after rotation. `camK` means camera K: x right, y up, z optical forward. For OpenCV coordinates, negate camera y. `f1` is the gravity-level frame at camera 1: x horizontal right, y up, z camera-1 heading projected onto the floor. Its origin is camera 1, even when best is another frame. Form its right vector as heading cross up. Reject an undefined level basis. Never print arbitrary dataset/world coordinates as f1.

Spread is the median patch spread over the retained pixels of best. Ordinary-ground size is rkit `fit_gbox` on the same best-frame point set: its full `axesLengths`, with the larger fitted horizontal extent first, the smaller second and the vertical extent last. This is visible-mask extent, not a benchmark size label. A failed box fit prints exactly `size unavailable` as the third body line; the centroid and P registration still succeed. Never invent dimensions or turn a size failure into a grounding miss.

The implicit surface gap follows rkit `V311Scene.pair_points`: rank common visible frames by decreasing minimum raw mask area, then frame number; take the first pair with nonempty eligible sets. If there is no common visible frame, rank all visible-frame pairs by (absolute frame gap, frame of X, frame of Y) and take the first eligible pair. After exhausting common frames, try every remaining visible pair in (absolute frame gap, frame of X, frame of Y) order. The private tie-break follows argument order; canonical a/b swapping is not implicit. Compute the complete minimum Euclidean distance with rkit `closest_sets`. Retain the selected frames privately in the audit. The response prints the selected pair as registered witness points and computes its displayed distance from their printed f1 coordinates using the existing calculator. The geometry remains the selected-frame visible-surface minimum; it is not a merged-surface or full-object minimum.

## Numbers, calculator and evidence

All ordinary ground and surface-gap real numbers print exactly two decimals using Python fixed-point formatting, with negative zero normalized to `0.00`; never scientific notation, NaN or infinity. Presence probabilities remain private and do not appear in a response. Spread is dimensionless; coordinates, size and gap are metres. Angles are whole degrees. Existing v3.11 calculator response text is unchanged, including its four-decimal dot/cross fields; the two-decimal cap applies to ordinary ground and surface-gap fields. Box centres and lengths also use two decimals; box orientation uses one whole-degree yaw, as specified below. Register the rounded camera and f1 triples, so all calculator outputs derive from the displayed numbers.

The existing calls are `<dist P1 P2>`, `<angle S=P1 F=P2 Q=P3 rule=medium>` (or hard), and `<turn from=P1 at=P2 to=P3>`; their exact v3.11 response formatter remains authoritative. Ground rows must not invent a point, frame, instance identity or geometry claim absent from their own tool output. Direction rows print the sign convention: `On the floor, cross > 0 means left; cross < 0 means right.` Gap prose may name its operands because their ground responses printed those names. It may refer to its printed witness P labels. It must not infer a full-surface minimum or an unobserved corner from those points. Plans must not name unobserved frames.

## Row and admission contract

The suffix begins with `<think>\n`, contains plan, calls, forced responses and conclusion, and ends with `<answer>VALUE</answer>`. No tool-mode prompt flag. Count the complete suffix including tool responses and answer with the pinned local student tokenizer; reject lengths above 5,000 tokens, without truncation. Record prompt and total token counts when the multimodal prompt tokenizer is available; the world-4 consumer must enforce its approximately 10,000-token total budget.

Build the four routed candidates: object_abs_distance, object_rel_distance, object_rel_direction_medium and object_rel_direction_hard, plus explicit simulated-miss examples with direct canonical continuations. Counting and appearance order use the separate instance-mode branch below. Size and other direct types retain their direct route. Record answer histograms per type and select unique examples against pinned benchmark aggregates: direction by answer content with uniform letters, relative distance by uniform letters within each option count, absolute distance by the natural independent GT distribution of admitted scenes, with a cap per log-spaced distance bin (ORCH 0533Z). Report that numeric policy separately from benchmark matching; do not read benchmark answer files to construct bins. Never use the candidate generator's histogram as its own target. Deduplicate across types by scene, exact frames, normalized question and operands before balancing. Shuffle options deterministically from row ID and re-render choice lists and answer letters. Report rows, unique questions and shortages. Counting rows require a separately pinned benchmark-matched count histogram. Instance fixture counts do not satisfy that training gate.

Admission requires exactly one native instance per direction/absolute-distance operand and relative-distance target; relative candidates also require exactly one. Each operand phrase must equal a matched GT label after case/whitespace normalization. Refuse pairwise mask overlap or containment. Refuse oriented-box overlap except for relative-distance rows using sampled_box_512, which must pass the measured winner and margin gate below. Direction rows also refuse a facing vector shorter than the larger projected full-box width. The direction label and relative-distance winner must agree before and after printing/rounding. Refuse floor vectors shorter than 0.50 m, directions within 10 degrees of a decision boundary, and visible-surface relative-distance margins below 0.10 m or 10% on either unrounded or printed values. Sampled-box relative rows require the independent labelled option to match both the unrounded winner and the unique printed minimum, with a printed runner-up margin of at least 0.02 m; no additional raw-margin threshold applies. Printed margins use Decimal arithmetic. Numeric object-distance agreement is at most 5% of the independent GT magnitude, without an additive floor; zero GT requires exact zero. Categorical labels match exactly.

GT replay must reproduce every forced response byte for byte through the decode backend. The program answer must meet or exceed v3.11's agreement with independently supplied GT on the same rows and scoring rule. Report coverage and refusals separately. Never use the generated program answer as its own GT label. Five real rows per type require visual text review before launch; synthetic fixtures cannot satisfy that gate.

## Atomic openers and span gating

The CP1 routing openers are atomic added tokens. Append `<ground` and `<gap` after the existing `<depth_at`, `<move`, `<pose`, `<turn`, `<box_3d` tokens using `AddedToken(normalized=False, special=False)`. Preserve all existing IDs. Initialize both input and output embedding rows from the mean of each opener's constituent-token embeddings, as `mdg_decode_tokens.add_ground_tokens` does. Routing teacher forcing and the main decode stream keep span LoRA closed. Separate prompt-plus-call MDG queries open it for every call token, including the atomic `<ground` opener and closing token. Packed call spans are annotations and do not authorize opening routing adapters. `<gap` invokes fixed geometry and does not query MDG. The two embedding rows are trainable in TB-1; that trainer owns saving/reloading them. Count suffix tokens with this extended tokenizer. Emit ground-call token positions as annotations. Before training, verify full generated token equality and the consumer's adapter scope against the same packed row.

## Witness precision and semantics

All examples assume the preceding singular ground calls have allocated their points; example cameras share an orientation and origin for arithmetic clarity. Actual calls use recorded transforms. Append witness lines after the complete legacy distance body, including its `min` line. Each candidate contributes A then B, even when A repeats. Register every point anew in the shared P sequence. A witness line has exactly this grammar:

```text
P7: chair nearest point cam9 (0.41, 0.22, 1.83) m; f1 (1.12, -0.35, 2.47) m
```

`NAME nearest point` states the object and role; it is not an invented instance alias. The line has no spread field. The registry stores a zero reliability placeholder internally and the same rounded camera/f1 triples as printed. The unrounded endpoints must be members of the selected eligible lifted sets and their Euclidean distance must equal the backend gap within 1e-9 m. Resolve exact ties by B point order then A point order. Store raw endpoints, frame indices and surface indices privately.

The printed gap is the existing calculator `<dist PA PB>` result for the two registered, printed f1 triples. Compute coordinate differences and squared distances with Decimal arithmetic, then round the square root to two decimals using the calculator's half-even rule. Apply the same rule to each relative candidate before computing the printed minimum, ties, margins, answer and GT-agreement checks. The raw minimum and raw surface membership remain separate audit facts; quantized points need not lie exactly on the raw surface. No rounding-error allowance excuses disagreement between printed coordinates and the printed distance. With `enabled=False`, or with witness lines explicitly disabled, the legacy distance formatter remains byte-identical. All witness-bearing traces use printed-point arithmetic.

The visible-surface distance is an observation. With exact surfaces it can exceed the true full-surface gap. A target for the full-surface gap is unavailable unless an independent complete-surface reference supplies a closest pair and both endpoints are visible in the recorded clip. A visible alternative does not make a hidden true pair visible. For nonunique minima, any jointly valid closest pair whose endpoints are visible suffices. Visibility can occur in different frames; all points use one W frame and the same f1 origin.

## Ambiguity and instances

```text
<ground obj="chair">
<tool_response>
chair: unresolved
</tool_response>
```

`unresolved` means multiple accepted instances remain compatible with the phrase and no verified binding selects one. It never means absent. `not seen` retains its observation meaning. Neither response allocates P labels. A surface gap or keypoint call depending on an unresolved singular name returns the single body line `unresolved`, before checking missing names. Malformed calls remain parser errors. Generated geometry rows with unresolved operands refuse admission; direct continuation needs its own independently admitted source.

```text
<ground obj="chair" mode="instances">
<tool_response>
chair: 2 found
P1: chair instance 1 cam4 (0.41, 0.22, 1.83) m; f1 (1.12, -0.35, 2.47) m; first 2
P2: chair instance 2 cam9 (0.51, 0.32, 2.83) m; f1 (2.12, -0.25, 3.47) m; first 7
</tool_response>
```

The first line is `NAME: n found`, with a nonnegative integer. It is followed by exactly n P lines, one centroid per distinct native GT instance. Each instance uses the unchanged eligible-frame, best-frame and median rules. Sort by earliest eligible displayed frame, then the string form of the stable native ID. The public `instance J` is a response-local ordinal, not a new callable name. Private native IDs persist across frames. `first K` is the earliest eligible observed frame, never a claim about entry into the physical scene. Enumeration invalidates a cached singular binding for that name. It does not authorize a subsequent bare-name gap.

With no eligible instance, print only `NAME: 0 found`; this is not proof of a full-scene count of zero. The counting generator accepts only when the observed count equals independent task GT. Appearance-order rows enumerate each candidate, compare their `first` values, and refuse missing candidates or ties. Question wording must reproduce the benchmark template exactly; do not append an eligible-frame qualification to its text. A question about the first object compares the smallest first value. The benchmark appearance-order template asks for the complete category order: sort every candidate by its first eligible frame, refuse any tie, and map the complete comma-separated order to an option. Full-video appearance order or full-scene counts require independent agreement between that benchmark rule and the observed-frame result; an observed result alone does not establish this agreement. Record the rule and its authority outside the question. Balance counting by a separately pinned benchmark count distribution. Author singular text as `The tool found 1 observed instance.` and plural text as `The tool found N observed instances.` for zero or more than one. An unresolved-reference fixture concludes `The singular reference is unresolved. The tool found N observed instances.` with the same singular rule when N = 1. Apply the inherited `qid-sha256-v1` option shuffle to appearance and relative-distance rows before rendering; remap the independent GT letter as well as the displayed options. Select equal letter counts within each option count, report shortages, and never change the shuffle seed to force a letter. Relative gap candidate order follows the shuffled options. Fixture balance is diagnostic and does not satisfy benchmark distribution or deduplication gates.

The fixture families `gap_witness`, `relative_gap_witness`, `surface_pair` and `extent_ends` retain benchmark questions for diagnostic review only. Every row must set `training_admitted=false`, `excluded_from_benchmark_scoring=true`, and `training_exclusion_reason` to `Observation-only surface or endpoint measurements do not answer the full-object benchmark question; exclude from training and benchmark scoring.` The packer rejects these families even if a caller asserts GT agreement or training admission. Observation metadata does not make a visible-surface or endpoint answer valid for a full-object question. The `surface_pair_full` family sets the same false training flag and true scoring exclusion, with `training_exclusion_reason` equal to `Analytic complete-surface geometry is a synthetic fixture, not the source scene geometry; exclude from training and benchmark scoring.` Its family guard also prevents promotion into training.

## Opt-in surface and extent calls

```text
<surface_pair a="chair" b="table" mode="closest_visible">
<tool_response>
P3: chair support centroid cam3 (-0.50, 0.00, 2.00) m; f1 (-0.50, 0.00, 2.00) m
P4: table support centroid cam9 (1.47, 0.00, 2.00) m; f1 (1.47, 0.00, 2.00) m
P5: chair nearest point cam3 (0.00, 0.00, 2.00) m; f1 (0.00, 0.00, 2.00) m
P6: table nearest point cam9 (0.97, 0.00, 2.00) m; f1 (0.97, 0.00, 2.00) m
visible pair distance 0.97 m
full surface gap unavailable
</tool_response>
```

The call requires successful singular grounding of both names. It reuses `hrp.selector.select_keypoints` and `keypoint_gap`; reciprocal nearest_surface roles retain the counterpart's stable identity. Use observed best positions, never cluster medians as surface witnesses. The output is the calculator distance between the two printed f1 witness triples. A successful surface call allocates four points: A support centroid, B support centroid, A witness, B witness. `closest_visible` states the requested role; a predicted pair is an estimate and does not certify global optimality. GT targets use the reference's closest visible pair. When a named independent full-surface authority supplies a matching visible true minimum, the last line is `full surface gap 0.97 m`. If that authority is absent or every true closest pair is hidden, the last line remains `full surface gap unavailable` and the full-distance target is null. A call lacking either visible keypoint, supporting surface, verified membership or the printed facing-side check below returns only `unavailable` and allocates no points; missing grounding returns `not seen`; ambiguity returns `unresolved`.

Each support centroid is the componentwise W-frame median of the same instance-bound surface samples that support its witness in that witness's displayed frame. Transform that centroid and witness through the same recorded calibration into camera K and the common frame-1 gravity frame `f1`. Print both frame names. Ground centroids summarize their own `best` masks; the pair-specific support lines supply the centroids for the facing check. Never combine an unrelated synthetic point provider with ground records from another surface.

Let CA and CB be the printed support centroids in f1, PA and PB the printed witnesses, and D = CB - CA. Require D != 0, `(PA - CA) dot D >= 0` and `(PB - CB) dot (-D) >= 0`, evaluated exactly from printed decimal coordinates. These inequalities define the trace's centroid-relative facing-side statement. They do not prove surface normals or global optimality. A concave object's true closest pair can fail this conservative gate; return `unavailable` and use the fallback policy instead of moving a witness to force the sign. Independently require each raw witness to belong to its instance's supporting surface within 1e-6 m and pass the provider's visibility checks. Session uses the grounded object's eligible samples in the witness frame; the hrp conversion uses that target owner's native centre-depth samples in the witness frame. Their different surface eligibility rules remain explicit in the audit. Copy the registry before validating the whole pair, so a refusal allocates no points.

The numeric `full surface gap` uses the same printed-point distance as `visible pair distance`; its authority check compares the independent reference to the raw pair within the pinned tolerance. A reference value alone, an observed-surface set, or a hidden true pair never authorizes a numeric full-surface claim. Synthetic complete discrete surfaces are a fixture authority only, not a complete real mesh.

```text
<extent_ends obj="table" axis="longest_observed">
<tool_response>
P2: table extent start cam3 (0.00, 0.00, 2.00) m; f1 (0.00, 0.00, 2.00) m
P3: table extent end cam9 (1.20, 0.00, 2.00) m; f1 (1.20, 0.00, 2.00) m
observed endpoint distance 1.20 m
</tool_response>
```

This call reuses `keypoint_extent`. The provider must bind a stable object/world axis and its two observed extrema. For this prototype, longest_observed means the longer axis of the minimum-area horizontal box over the observed union, using hrp_rows/work/keypoints.py:extent_ends and its deterministic hull-edge tie rule. Flip its sign so the largest-magnitude horizontal component is positive. Start and end minimize and maximize projection onto that fixed axis; input order breaks endpoint ties. The provider records the world axis and the target-owner code hash; image-left and image-right are not stable roles. The response reports the 3D Euclidean distance between the printed f1 endpoints, not a projected box dimension or full-object size. The conclusion is exactly `The Euclidean distance between the observed endpoints is {d} m, or {cm} cm. This does not establish the full object size.`, with d at two decimals and cm = 100 times that printed distance as an integer. The endpoint-selection axis remains horizontal; this call does not claim the longest axis among all three dimensions. Hidden full-box corners never become observed labels. A full size requires separate full-extent supervision. Box mode supplies an estimate or an explicitly substituted full-box target; it does not turn hidden corners into visible endpoints.

The provider owns keypoint prediction and validated visible targets; this patch does not add a trained head. New calls remain disabled by default and in every legacy session. Keypoint candidate grouping, singleton/support policy and ambiguity follow the existing selector API. Append atomic `<surface_pair` then `<extent_ends` only for an opt-in tokenizer after the seven v3.12.2 openers. Preserve old IDs and initialize the new embedding rows by the same constituent mean rule. Routing and main-decode adapters stay closed; separate keypoint prediction queries may open their explicitly annotated call spans. A schema/parser change alone does not authorize training.

## Distance rules and box provider

**Benchmark distance contract**

For `object_abs_distance` and `object_rel_distance` examples whose independent target authority is the annotated-box sampler, ground each operand with `<ground obj="NAME" mode="box">`. Compute every distance with `<gap ... rule="sampled_box_512">`. Training and inference use the same serializer and tool measurement operation.

The absolute-distance plan is exactly `I will ground the boxes and ask the tool to measure their sampled-box distance.` The relative-distance plan is exactly `I will ground the boxes and ask the tool to measure their sampled-box distances.`

The absolute conclusion inserts exactly `The sampled-box gap is the smallest distance between points sampled inside the two objects' full boxes, which is how this benchmark defines the answer.` before `The sampled-box distance is {d} m.` The relative conclusion inserts exactly `Each sampled-box gap is the smallest distance between points sampled inside the two objects' full boxes, which is how this benchmark defines the answer.` once for all gaps before `The sampled-box minimum is {name}, so the answer is {letter}.` These sentences belong to student prose, outside the tool response.

The result is a sampled-box distance. It is not an exact box-to-box minimum, a centre distance, or a visible-surface minimum. Samples lie inside the estimated boxes; they are not observed surface points. Do not describe them as visible witnesses. Box overlap does not force this finite-sample distance to zero.

The ground provider estimates the object's full box from the recorded clip. GT substitution supplies the independently annotated full box as the supervision target. A frozen best-frame point fit is the evaluated initial inference provider; a learned full-box provider may replace it under a separately pinned evaluation. The tool must never fetch an annotated box, a benchmark answer, or a GT instance selection at inference. A size prior, if enabled, comes only from the pinned training-scene prior. The evaluated recommendation uses the best-frame fit without the prior.

A GT replay that tests full-box supervision substitutes the annotation at the box-provider interface. A replay that tests fitting from GT masks and depth must actually run the fitter and report its lower label-agreement rate. These are distinct experiments.

**Box grounding**

The call occupies one line:

```text
<ground obj="NAME" mode="box">
```

A successful response has exactly four body lines:

```text
<tool_response>
NAME: frames K1,K2 (best K)
Bj: f1 centre (CX, CY, CZ) m
size L1 x L2 x L3 m
yaw Y deg (0 = +x; positive +x toward -z about +y)
</tool_response>
```

The centre uses f1: x horizontal right, y up, z camera-1 heading projected onto the floor, with origin at camera 1. Gravity-aligned boxes print two horizontal full lengths followed by height. The first horizontal axis follows the provider's first horizontal slot; the second is perpendicular to it. Yaw describes the first horizontal axis, rounded to a whole degree in [-180, 180). Zero points along +x; positive yaw turns +x toward -z about the upward +y axis. No axes matrix appears in the response.

Centre coordinates and lengths use Python binary64 fixed-point `.2f`; yaw uses `.0f` followed by wrapping into [-180, 180). Normalize negative zero. Keep all transforms and provider values in float64. A positive extent smaller than half a centimetre can print 0.00 without invalidating its private positive length.

`frames` lists accepted frames with nonempty eligible support. Choose `best` by largest pre-erosion mask area among accepted nonempty masks, then earliest frame. Keep that choice fixed: if its eligible points cannot produce a valid box, return `box unavailable`. On success, `best` belongs to `frames`. These fields identify observed support for the estimate; they do not assert that every corner was visible. Each operand binds one instance. Retain all safeguards against genuinely invisible training operands.

Allocate consecutive B labels, starting at B1, only after successful validation. Store the full-precision provider box under its B label privately. A box centre is distinct from an observed-point median; this branch allocates no P label. Successful grounding replaces the name's box binding; failed grounding or instance enumeration invalidates it.

Validate finite values, positive private lengths, correct shapes, orthonormal axes within 1e-8, and gravity alignment within 1e-8. Preserve every private axis slot, sign, handedness and length-axis association. The public horizontal/height layout does not reorder the private box used by the sampler.

No eligible support returns `NAME: not seen`; ambiguous binding returns `NAME: unresolved`; observed support without a valid estimate returns `NAME: box unavailable`. Each failure has one body line and allocates no label.

**Sampled-box tool measurement**

```text
<gap a="X" b="Y" rule="sampled_box_512">
<tool_response>
distance D m
</tool_response>
```

The multi-candidate response prints one measurement per candidate in call order, then its minimum:

```text
<gap a="X" b="Y1" b="Y2" rule="sampled_box_512">
<tool_response>
Y1: D1 m
Y2: D2 m
min "Y1" D1 m
</tool_response>
```

Every distance prints exactly two decimals. The gap is a tool measurement from its own unrounded boxes and cannot in general be recomputed from the printed box fields. The model copies a printed distance or compares printed distances to choose an answer. Compute displayed minima, ties and margins using Decimal arithmetic on those printed distances. List all tied names in call order; unique-answer training rows refuse ties and inference uses the admitted direct fallback.

Require successful same-session box bindings for every operand. Ambiguity takes precedence as `unresolved`; missing observation returns `not seen`; missing box geometry returns `box unavailable`. Validate the whole call before emitting any numeric result. The gap allocates no labels. Never substitute a surface observation and describe it as the same benchmark measurement.

**Measurement and audit replay**

For each ordered pair, initialize NumPy `Generator(PCG64(0))`. Draw `uniform(-1.0, 1.0, size=(512,3))` for A, then a second array for B. Reset for every relative candidate. A is the first operand/target; B is the second operand/candidate. Preserve question-role order and shuffled candidate order.

For each full-precision box with centre C, full lengths L and ordered signed axis-row matrix A, compute `P = (U * (L / 2.0)) @ A + C` in float64. Take the minimum Euclidean distance over all 512 × 512 point pairs. A nearest-neighbour implementation must reproduce this complete reference. Pin NumPy 2.2.6 in the executable receipt. Format the resulting float64 distance with `.2f`, normalizing negative zero. Never round box fields before measurement, and never use the independent answer to adjust it.

`derivgen.box_v313.sampled_box_512` implements the shared sampler; `BoxRegistry` holds private operands and `replay_audit` verifies the forced responses. The audit is outside the model's suffix: each box-ground event's `audit.full_precision_box` stores the float64 centre, lengths and original ordered signed axes in f1; its audit also stores the B label, provider identifier and NumPy version. Each gap event stores `audit.sampler` (rule, PCG64, seed 0, 512 samples, float64, A-then-B draw order, per-pair reset) and `audit.ordered_box_labels`. Preserve these fields when packaging. The reviewer replays them without providers, masks, poses or independent labels. Missing or altered audit fields fail replay.

Audit records reside in `out/fixtures_r6/*.jsonl` under each row's `events[*].audit`; the complete numeric pool is `out/AUDIT_REPLAY_r6.jsonl`. Neither is inserted into the model-visible `suffix`. `out/AUDIT_REPLAY_r6.json` records summary statistics and source hashes. Tests replay every successful sampled-box gap in both artifacts, and reject draw-order, axis-sign and seed mutations. Existing point calculators retain their own printed-point arithmetic.

**Independent labels and admission**

GT construction explicitly uses `annotation_full_box_v1`: the tool's unrounded boxes are the annotated boxes transformed rigidly into f1. Keep the independent benchmark label and original ordered annotation boxes separate from tool values. The canonical benchmark answer is `format(independent_label, '.2f')`. Require the measured two-decimal answer to equal that answer and pass the inherited 5% check against the unrounded target; zero requires exact zero. Record unrounded discrepancy privately. Numeric label agreement does not establish visibility or production admission.

For relative rows, require the independent sampled-box winner, unrounded measurement winner and printed winner to agree. Require a unique printed minimum and a Decimal runner-up margin of at least 0.02 m. Oriented-box overlap alone, whether target–candidate or candidate–candidate, does not refuse a sampled-box relative row that passes this gate. Keep instance checks, exact-name binding, visibility, mask-overlap and containment refusals, source admission, deduplication, canonical continuations and token limits. Other distance rules and direction rows retain their own gates. Builders must set `item.target_distance_rule="sampled_box_512"` before calling `GTClip.validate_operands`; an unmarked relative row retains the overlap refusal. A failed measurement or agreement check uses only an independently admitted, exact question-matched direct continuation, or refuses the row. Keep the default fitted provider and the explicit GT provider switch in every response audit.

The numeric overlap audit covers all 710 benchmark relative questions: raw and unique printed winners match 710/710 labels. Among 371 rows with any operand-box overlap, all 371 pass the 0.02 m printed-margin gate; their printed margins have minimum 0.02 m, median 0.60 m, p90 1.69 m and maximum 3.24 m. All benchmark overlaps are between candidates, so the labelled winner overlaps the target in 0/371 rows. Only 13 overlap rows have single instances for every operand; 4 of those retain a containment refusal. Multi-instance results are diagnostic and use the reference RNG across instance pairs. Seventeen benchmark rows use the pinned reference alias `coat rack` → `coat hanger` for this audit only; production exact-name binding is unchanged.

The training audit covers 60 relative inputs: 50 have exact-name bindings and all 50 reproduce their labels; 10 retain unresolved-name refusals. Among the 50 measured rows, 31 have operand-box overlap, all 31 pass the distance gate, and 10 labelled winners overlap the target. The 14 rows specifically refused for overlap all have unique labelled minima and pass the gate, with printed margins from 0.19 to 1.41 m (median 0.375 m); 7/14 labelled winners overlap the target. These 14 pass operand validation, rendering and audit replay under this contract. Their eligibility for the distance route does not authorize training. Source hashes and per-row results are in `out/OVERLAP_r6.json` and `out/OVERLAP_r6.jsonl`.

Tool measurements match 252/252 training and 239/239 dev canonical answers; audit replay reproduces all 491 printed gaps. Printed-box replay is informational:

| Pool | Median absolute error | 95th percentile absolute error | Within 5% |
|---|---|---|---|
| training | 0.33 cm | 0.91 cm | 247/252 (98.02%) |
| dev | 0.79 cm | 2.68 cm | 235/239 (98.33%) |

Reversing draw order changes 148/239 dev answers; flipping the second box's first private axis sign changes 116/239. Both mutations fail audit replay. These counts describe the pinned numeric pools, not production-admission yield.

The printed-box diagnostic reconstructs axes from the printed yaw as `(cos(Y), 0, -sin(Y))`, `(sin(Y), 0, cos(Y))`, `(0, 1, 0)`, with the two printed horizontal lengths and printed height in that order. It then applies the same ordered sampler to the two printed centres. Report absolute error against the unrounded independent label before final gap rounding; within 5% means error <= 0.05 times its magnitude, with exact zero for a zero label. This diagnostic includes the loss of private axis signs/slots as well as decimal and degree rounding. It does not define the tool measurement or its admission gate.

**Arithmetic fixture**

These cubes have private ordered axes equal to the identity matrix. Their public orientation has yaw zero and their full lengths are all 1.00 m. This is a grammar example, not a real-frame review.

```text
<ground obj="chair" mode="box">
<tool_response>
chair: frames 1 (best 1)
B1: f1 centre (0.00, 0.00, 2.00) m
size 1.00 x 1.00 x 1.00 m
yaw 0 deg (0 = +x; positive +x toward -z about +y)
</tool_response>
<ground obj="table" mode="box">
<tool_response>
table: frames 1 (best 1)
B2: f1 centre (2.00, 0.00, 2.00) m
size 1.00 x 1.00 x 1.00 m
yaw 0 deg (0 = +x; positive +x toward -z about +y)
</tool_response>
<gap a="chair" b="table" rule="sampled_box_512">
<tool_response>
distance 1.02 m
</tool_response>
The sampled-box gap is the smallest distance between points sampled inside the two objects' full boxes, which is how this benchmark defines the answer.
The sampled-box distance is 1.02 m.
<answer>1.02</answer>
```

## Fixture text conformance

The following contract lists permitted tool-response body lines and the required student sentences for the reviewed fixes. Each body line must match a complete template; wrappers are exactly `<tool_response>` and `</tool_response>`. Placeholders denote literal object names (`name`), positive integers (`n`), nonnegative integers (`count`, `cm`), signed integers (`integer`), signed two-decimal coordinates (`f`), nonnegative two-decimal measurements (`d`), ascending comma-separated frame integers (`frames`), and comma-separated double-quoted object names (`names`). Sentence placeholders use the corresponding printed measurement or observed count. These student sentences occur outside the response wrapper.

<!-- fixture-text-contract -->
```json
{
  "tool_body_lines": [
    "{name}: frames {frames} (best {n})",
    "P{n}: cam{n} ({f}, {f}, {f}) m; f1 ({f}, {f}, {f}) m; spread {d}",
    "size {d} x {d} x {d} m",
    "size unavailable",
    "{name}: not seen",
    "{name}: unresolved",
    "{name}: box unavailable",
    "{name}: {count} found",
    "P{n}: {name} instance {n} cam{n} ({f}, {f}, {f}) m; f1 ({f}, {f}, {f}) m; first {n}",
    "B{n}: f1 centre ({f}, {f}, {f}) m",
    "yaw {integer} deg (0 = +x; positive +x toward -z about +y)",
    "{d} m",
    "distance {d} m",
    "{name}: {d} m",
    "min {names} {d} m",
    "P{n}: {name} nearest point cam{n} ({f}, {f}, {f}) m; f1 ({f}, {f}, {f}) m",
    "P{n}: {name} support centroid cam{n} ({f}, {f}, {f}) m; f1 ({f}, {f}, {f}) m",
    "P{n}: {name} extent start cam{n} ({f}, {f}, {f}) m; f1 ({f}, {f}, {f}) m",
    "P{n}: {name} extent end cam{n} ({f}, {f}, {f}) m; f1 ({f}, {f}, {f}) m",
    "visible pair distance {d} m",
    "full surface gap {d} m",
    "full surface gap unavailable",
    "observed endpoint distance {d} m",
    "not seen",
    "unresolved",
    "unavailable"
  ],
  "student_sentences": {
    "absolute_plan": "I will ground the boxes and ask the tool to measure their sampled-box distance.",
    "relative_plan": "I will ground the boxes and ask the tool to measure their sampled-box distances.",
    "extent": "The Euclidean distance between the observed endpoints is {d} m, or {cm} cm. This does not establish the full object size.",
    "count_singular": "The tool found 1 observed instance.",
    "count_plural": "The tool found {count} observed instances.",
    "unresolved_prefix": "The singular reference is unresolved. ",
    "absolute_measurement": "The sampled-box gap is the smallest distance between points sampled inside the two objects' full boxes, which is how this benchmark defines the answer.",
    "relative_measurement": "Each sampled-box gap is the smallest distance between points sampled inside the two objects' full boxes, which is how this benchmark defines the answer."
  }
}
```
