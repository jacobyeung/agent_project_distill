# Box provider interface — SPEC v3.13

The backend calls `provider(name, grounded_instance, geometry, best_frame)` and records its immutable `provider_id` in every response audit. Return a mapping with `centre`, `lengths`, and `axes`, or `None` on an ordinary estimation failure. Never return a placeholder cube, nonfinite fields, nonpositive lengths, a surface centroid in place of a box centre, or annotations during inference.

| Provider field | Private shape and meaning | Model-visible representation |
|---|---|---|
| centre | float64 [3], full-box centre in f1 metres | `(x, y, z)` with two decimals |
| lengths | float64 [3], full lengths associated with ordered axis rows | Two horizontal lengths in provider slot order, then height; two decimals in metres |
| axes | float64 [3,3], original ordered signed orthonormal axes in f1 | One whole-degree yaw; no matrix |

f1 originates at camera 1: x horizontal right, y up, z camera-1 heading projected onto the floor. For a gravity-aligned z-up source, form F = [heading cross up, up, heading]. Convert the centre as `(C - camera1_origin) @ F` and axes as `A @ F`. First map native annotations into the adapter's W frame if needed. Use float64 throughout and reject undefined heading.

Validate finite fields, shapes, strictly positive private lengths, orthonormal axes within 1e-8, and gravity alignment within 1e-8. Preserve the private axis slots, signs, handedness and length-axis associations. They associate random draws with directions in the benchmark sampler. The printed representation is deliberately lossy and must never overwrite private operands.

Print centre and lengths with Python `.2f`, normalizing negative zero. Choose the first horizontal provider axis for yaw; remove the vertical slot only in the public layout. Yaw zero is +x, positive turns +x toward -z about the upward +y axis. Round with `.0f`, then wrap into [-180, 180). Print `yaw Y deg (0 = +x; positive +x toward -z about +y)`. Positive private lengths may print 0.00. Tilted boxes fail closed as `box unavailable`.

The default `fit_gbox_best_v1` fits eligible points from the largest accepted raw mask, breaking ties by earliest frame. Keep that frame fixed if fitting fails. Use the minimum-area horizontal rectangle and 2nd/98th height percentiles. The estimate does not claim that the full shape was observed. GT construction explicitly selects `annotation_full_box_v1`; its private operands are the annotated boxes. Learned providers need separate versioned IDs and must retain the same private ordering contract, serializer and sampler.

The session owns visibility and identity. No eligible support returns `NAME: not seen`; ambiguous binding returns `NAME: unresolved`; observed support without a valid estimate returns `NAME: box unavailable`. Failures allocate no B or P label. Successful box grounding allocates a consecutive B label and privately registers the unrounded box; re-grounding replaces the name binding, and failures or enumeration invalidate it. Box calls allocate no P label.

`<gap a="X" b="Y" rule="sampled_box_512">` measures the private registered boxes. For every ordered pair reset `Generator(PCG64(0))`, draw `uniform(-1,1,(512,3))` for X then Y, construct `(U * (lengths / 2)) @ axes + centre`, and take the full pairwise Euclidean minimum. Print only `distance D m`, with D formatted `.2f`. Relative calls print each candidate's two-decimal distance and the printed minimum. Reset per candidate, preserving target-first and shuffled option order. The model compares these printed distances and copies the answer at printed precision. The printed boxes do not generally reproduce the measurement.

Each box-ground event's private `audit` must carry `full_precision_box` (centre, lengths, signed ordered axes), `box_label`, `box_provider`, and `numpy_version`. Each gap audit must carry `sampler` (rule, RNG, seed, samples, dtype, draw order, reset policy), `ordered_box_labels`, provider ID and NumPy version. Serialize float64 arrays as JSON numbers without decimal truncation. Store audit outside the suffix, under `events[*].audit` in the emitted row artifact; persist it with the row. Review fixtures store it in `out/fixtures_r4/*.jsonl`; all 491 numeric pairs store it in `out/AUDIT_REPLAY_r4.jsonl`.

`derivgen.box_v313.sampled_box_512`, `BoxRegistry`, and `replay_audit` share the measurement implementation. Replay requires the audit and reproduces every printed gap. Altered seed, draw order, or axis signs must fail tests. `parse` reconstructs rounded boxes only for the informational rounding diagnostic. Its canonical axes are `(cos(Y),0,-sin(Y))`, `(sin(Y),0,cos(Y))`, `(0,1,0)`; public text carries no signed slot permutation.

Validate every candidate before emitting numbers. Ambiguity takes precedence as `unresolved`; missing observations return `not seen`; invalid estimates return `box unavailable`. Display all tied winners. Unique-answer training rows refuse ties; inference uses the admitted direct fallback. Keep source admission, exact instance binding, overlap, raw and printed margins, independent GT agreement and token limits. Training admission remains NO-GO pending the orchestrator's ruling.
