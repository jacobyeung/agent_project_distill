The allowlist names exact leaf paths that preparation may change after entry localisation. The checker rejects any other change; it does not validate the permitted values.

`python out/prep_diff.py pre.json v.json` prints every changed path and exits 1 if any path is outside the allowlist.

The production mode-q path calls refresh, production_proof, native preparation, population and handover. It does not call frame_host; h.py still requires a genuine matching host receipt. entry.frame_host localises u/ paths before preparation and sets routing from routing_base. Those localisation changes belong in the comparison input. N is MINIMAL, so routing_inputs remain absent.

The explicit recipe is already canonical; preparation may not change it. The pose receipt, sampler card, removals, configuration code pin and launch output also remain fixed.

The retained 24f input.json versus v.json comparison has four extra leaf paths: admission.path, admission.sha256, authorization.path and authorization.sha256. fixture_gates.py adds these fixture-only gates after preparation. The raw comparison correctly exits 1; a separate copy omitting those gates passes. The retained files were not edited. A learning-rate mutation also exits 1. See work/build24i/PREP_FIELDS_TESTS.json.

| Field | Reason and code |
|---|---|
| `preparation.path` | Native preparation, population and handover each write a receipt. h.py/rv.py copy it to bind the host/review pins without changing identity. `student_pilot/s1_admission.py:prepare_phase; student_pilot/r1_population.py:bind_prepared; launch_r1/production_proof.py:bind_handover; b/rv.py:sync_preparation` |
| `preparation.sha256` | Native preparation, population and handover each write a receipt. h.py/rv.py copy it to bind the host/review pins without changing identity. `student_pilot/s1_admission.py:prepare_phase; student_pilot/r1_population.py:bind_prepared; launch_r1/production_proof.py:bind_handover; b/rv.py:sync_preparation` |
| `preparation_output` | Native preparation assigns its attempt directory. `student_pilot/s1_admission.py:prepare_phase` |
| `r1_training.continuation_identity` | Bind the prepared target configuration. `student_pilot/r1_handover.py:bind_target; launch_r1/production_proof.py:bind_handover` |
| `r1_training.direction_augmented.path` | Bind the generated direction-twin augmentation. `student_pilot/r1_direction_twins.py:augment` |
| `r1_training.direction_augmented.sha256` | Bind the generated direction-twin augmentation. `student_pilot/r1_direction_twins.py:augment` |
| `r1_training.handover_mapping.path` | Write the authenticated donor-to-prepared-target mapping. `student_pilot/r1_handover.py:bind_target; launch_r1/production_proof.py:bind_handover` |
| `r1_training.handover_mapping.sha256` | Write the authenticated donor-to-prepared-target mapping. `student_pilot/r1_handover.py:bind_target; launch_r1/production_proof.py:bind_handover` |
| `r1_training.host_receipt.path` | Pin a job-private snapshot for the exact prepared identity. identity() excludes this pin. `launch_r1/entry.py:frame_host,admit; b/h.py; b/rv.py:run` |
| `r1_training.host_receipt.sha256` | Pin a job-private snapshot for the exact prepared identity. identity() excludes this pin. `launch_r1/entry.py:frame_host,admit; b/h.py; b/rv.py:run` |
| `r1_training.review.path` | Pin a job-private snapshot for the exact prepared identity. identity() excludes this pin. `launch_r1/entry.py:frame_host,admit; b/h.py; b/rv.py:run` |
| `r1_training.review.sha256` | Pin a job-private snapshot for the exact prepared identity. identity() excludes this pin. `launch_r1/entry.py:frame_host,admit; b/h.py; b/rv.py:run` |
| `r1_training.room_audit.path` | Census and bind the augmented VQA room audit. `launch_r1/production_proof.py:_run` |
| `r1_training.room_audit.sha256` | Census and bind the augmented VQA room audit. `launch_r1/production_proof.py:_run` |
| `r1_training.row_plan_sha256` | Hash the final native population sampler binding. `student_pilot/r1_population.py:bind_prepared; launch_r1/production_proof.py:bind_handover` |
| `r1_training.store_hashes.pointing` | Derive the actual prepared stream identity; pose is the ordered composite-store identity. `student_pilot/r1_handover.py:bind_target; launch_r1/production_proof.py:bind_handover; student_pilot/r1_training.py:target_identity` |
| `r1_training.store_hashes.pose` | Derive the actual prepared stream identity; pose is the ordered composite-store identity. `student_pilot/r1_handover.py:bind_target; launch_r1/production_proof.py:bind_handover; student_pilot/r1_training.py:target_identity` |
| `r1_training.store_hashes.routing` | Derive the actual prepared stream identity; pose is the ordered composite-store identity. `student_pilot/r1_handover.py:bind_target; launch_r1/production_proof.py:bind_handover; student_pilot/r1_training.py:target_identity` |
| `r1_training.store_hashes.vqa` | Derive the actual prepared stream identity; pose is the ordered composite-store identity. `student_pilot/r1_handover.py:bind_target; launch_r1/production_proof.py:bind_handover; student_pilot/r1_training.py:target_identity` |
| `r2_sampling.indices.path` | Bind final admitted native reader offsets and cell counts. `student_pilot/r1_population.py:produce,bind_prepared` |
| `r2_sampling.indices.sha256` | Bind final admitted native reader offsets and cell counts. `student_pilot/r1_population.py:produce,bind_prepared` |
| `r2_sampling.population.path` | Bind final admitted native reader offsets and cell counts. `student_pilot/r1_population.py:produce,bind_prepared` |
| `r2_sampling.population.sha256` | Bind final admitted native reader offsets and cell counts. `student_pilot/r1_population.py:produce,bind_prepared` |
| `routing_vocabulary.path` | Produce the opener witness for the authenticated donor. `launch_r1/production_proof.py:_run; launch_r1/p_opener_witness.py:produce` |
| `routing_vocabulary.sha256` | Produce the opener witness for the authenticated donor. `launch_r1/production_proof.py:_run; launch_r1/p_opener_witness.py:produce` |
| `s1_routing.selection.path` | Refresh the identical selection with the current producer. Row selection must remain identical. `b/a.py:q -> b/i.py:refresh` |
| `s1_routing.selection.sha256` | Refresh the identical selection with the current producer. Row selection must remain identical. `b/a.py:q -> b/i.py:refresh` |
| `streams.pointing.path` | Native preparation rebuilds and filters the stream receipt. `student_pilot/s1_admission.py:prepare_phase` |
| `streams.pointing.sha256` | Native preparation rebuilds and filters the stream receipt. `student_pilot/s1_admission.py:prepare_phase` |
| `streams.routing.path` | Native preparation rebuilds and filters the stream receipt. `student_pilot/s1_admission.py:prepare_phase` |
| `streams.routing.sha256` | Native preparation rebuilds and filters the stream receipt. `student_pilot/s1_admission.py:prepare_phase` |
| `streams.vqa.path` | Native preparation rebuilds and filters the stream receipt. `student_pilot/s1_admission.py:prepare_phase` |
| `streams.vqa.sha256` | Native preparation rebuilds and filters the stream receipt. `student_pilot/s1_admission.py:prepare_phase` |
