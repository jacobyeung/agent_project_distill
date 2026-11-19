MINIMAL requires `r1_training.routing_slices: "deferred_first_boundary"` in the pinned config.
An absent declaration retains FULL behavior. Unknown values, any supplied `routing_inputs`, and nonzero deferred cells refuse.

Apply MINIMAL_TREE.patch to tree b262e7a7 before merging build 22. The patch changes seven files; TREE_CHANGES.json lists them.
The config and request bind the same authenticated routing-base receipt. S1 regeneration selects the final base; admission retains that exact output as streams.routing.
The population binds the selected base and assigns its retained routing rows to `routing_base` (64 slots per step).
P's existing absolute-distance rows remain in that base. N's distinct absolute-distance slice remains deferred.

Resolve shared files as follows:
- r1_coverage.py: retain build 22's EXTRA_PINS and camera wording exclusions. Keep the new cfg argument and early declared-mode return in source_names before enumerating any sources.
- r1_population.py: retain build 22's twin/source-key logic and FULL camera membership. Keep the MINIMAL branch before FULL classification; it rejects appended-source markers and uses empty membership bound to the regenerated base.
- r1_rooms.py: pass cfg at both source_names calls. Retain every build-22 STORE exception, twin binding, K1 source-key check, removal-order check and unremoved-hit check.
- launch_r1/build.py: pass cfg to source_names and omit routing_inputs from the MINIMAL host request. FULL requests retain their envelope requirement.
- s1_admission.py: skip only compose_native under the declaration. Keep the actual s1_routing.build call and all native preparation and frame audits.
- launch_r1/entry.py and production_proof.py: preserve the explicit declaration guards and all other admission checks. The final entry defers recovery/unit minimums only under this declaration; component evidence still runs first.

The merged MINIMAL card must keep all deferred routing cells at zero, including camera_wording and both coverage families.
The zero guard also rejects a deferred family relabeled into another stream. The only active routing cell is routing_base.
Keep build 22's wording exclusions active even though its new camera rows are deferred.
Keep its 109-row removal list and direction twins in N's VQA input; apply their original admission and room checks.
Bind the reviewed relative-count family only through build 22's reviewed path. This package adds no such rows.
Regenerate the merged room audit, card, source archive and kit seals. Do not reuse this package's room audit for a changed VQA store.

Kit q's resolver preserves N's non-routing streams under MINIMAL and authenticates P's routing base against the runtime config.
Carry this kit-only branch when merging work/build21/joblib.py; copy it to q/b/z.py and reseal the kit.
Carry the kit's incomplete preparation population and indices. They contain no deferred rows and refuse sampler admission until bind_prepared replaces them with complete filtered evidence.
The runtime/kit identity algorithms and checks are unchanged. FULL resolver behavior is unchanged.
The base kit's mount-order fix and P opener policy remain intact. The step-544 lineage and DEFERRED official boundary remain intact.
Build 22's NOT_PRESENT work is separate; this patch does not change component status rules.
No env-alias proposal is applied unless the recorded MINIMAL native proof identifies a reader that needs it.
GO remains false; the production frame-host and GPU proof remains required.
