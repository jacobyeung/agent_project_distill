# Refute verdict for kit-dryrun
refuted=True
reasons: Claim "3 of 3" is overstated. D0 170050 and K1 170193 would be caught. tower_sam row 7 was run 2 on a GPU; its cap is a code default (k1_phases.run:115), which no config lint sees. K1 170206 is omitted: missing depth files on the GPU-only load_model path ("CPU.own never calls load_model"). Real: 2 of 5. evalx 5 of 9 holds. No IO, provenance or running-job harm.
fix (binding): Restate saving: 2 of 5 session failures, about 5 of 9 pilots; drop tower_sam. Add staging closure: after stage, every pin reachable from prod CONFIG must exist and match, GPU path or not (catches 170206). Flag hard-coded caps or defaults the CLI never sets. Port K1 rh_transport/rh_mounts/rh_coverage/audit_config and the evalx rehearsal, not only trace_runtime.py.
