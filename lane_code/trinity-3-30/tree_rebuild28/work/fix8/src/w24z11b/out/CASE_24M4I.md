CASE b: the input N card requests zero direct-room draws for the whole job; no loader-audit path raises that rate.

The decoded input card sets room_size.rows_per_step=0 at work/build24m4i/N_card.json:102 and room_rows_per_step=0 at work/build24m4i/N_card.json:200. The card hash is c0167f682bd49fce84d1ca447a64131ae1605a345f534ce61ee98aabf7bee9c8; k/c.json binds it as both r1_training.mix and r2_sampling.card (decoded copy work/build24m4i/decoded/c.json:302).

The job calls bind_prepared before production_audit (work/tree_r1/launch_r1/entry.py:317). bind_prepared passes the same card to produce and binds only the resulting indices/population and row-plan hash (work/tree_r1/student_pilot/r1_population.py:202). produce keeps card_pin unchanged in the binding (work/tree_r1/student_pilot/r1_population.py:151).

allocate converts rows_per_step to 1,000-step draw totals and caps them at four repeats (work/tree_r1/student_pilot/r1_mix.py:24). VQA deficits refill direction alone (work/tree_r1/student_pilot/r1_mix.py:35); zero room draws cannot increase. plans excludes zero-total cells (work/tree_r1/student_pilot/r1_mix.py:90). production_audit validates the binding and iterates those same plans; it records draws without editing rates (work/tree_r1/student_pilot/r1_loader.py:51 and :62). The kit host wrapper only checks that the audit completed (work/build24/kits/n/b/h.py:27).

ORCH 0511Z sets room_size.rows_per_step and room_rows_per_step to 1.70. The compensating direction draw entry changes from 36.866 to 35.166 to preserve 128 VQA rows/step. All other card values remain byte-equivalent as decoded values. The inert room_rule annotation is retained solely to satisfy the requested draw-entry-only config delta; its zero-until-audit statement does not control executable behavior.

The configured room population is 425, so 1,700 draws over 1,000 steps meet the four-repeat cap. The first 200 steps yield 340 room draws. Native admission still applies row_check and room trace grammar (work/tree_r1/student_pilot/r1_training.py:27). No production audit or training ran.
