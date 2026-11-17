Fix 4 delta against `/scratch/jjyeung/orch_n30/r1_ops/work/snap_841f0637`.

Config identity: `a6b70ef26dff31e8c212f94eb6193ced75929ea8b035769f1fe87eb4657766c9`. Archive: `p_084ba70f.tar`. SHA256: `88a55761b7acb59c6213b846681c6dceee0e69332d7c4b913bf3084ec45bfa91`.

The full v7 census checks 204,413 rows. Traced room counts: {"eligible": 0, "qualitative_trace_pass": 0, "rows": 431, "sealed_row_checks_pass": 431}. Reworded away counts and markers: {"eligible": 8511, "pool": "r1_away_opp", "qid_suffix": "_away_opp", "rows": 8511}.

The room cell requests 1.72 rows per step. The current literal Locate/Relate/Estimate predicate rejects the v7 Seen/relation/numeric-answer traces; eligible room count is zero and the required-family gate fails. No predicate change or room-zero fallback is silently approved. R1P_PACKET.md documents both one-command fallbacks.

No unit source is bound. The read-only v2 candidate has 1,224 rows (ft 1,130; in 94; cm 0), but lacks top-level events and frame pins; the real rebind command refuses its unchanged fixture copy. Successful packed-source native binding/regeneration and feet-only population/cap behavior are separate fixtures. The default unit request is 1.00 row per step, capped at 4 × allowlisted eligible / 1,000; freed routing slots go pro rata to the four native program cells.

The proof main() fixture writes a receipt with all eight evaluated checks: disk_plan, routing_selection, empty_root, temporary_paths, runtime_binaries, directory_modes, loader_audit and required_families. Its fixture admission/runtime boundaries do not certify Orchard production preparation.

File / change / reason:

- `tools/admission_census.py`: Count traced-room sealed checks and qualitative eligibility separately, and identify the exact reworded-away marker during the full store census.
- `tools/finalize.py`: Publish current v7 counts, blockers, complete fallback and unit rebind commands, proof scope and FIX4 checksums.
- `tools/make_proof.py`: Call temporary_paths after command construction; require directory_modes; run the loader audit through stdin so argv remains opaque.
- `tools/package_operator.py`: Require the same eight named receipt checks in the submitter.
- `tools/rebind.py`: Bind v7; parameterize room dose, away-QID exclusion, feet allowlist and unit dose; cap allowlisted units and redistribute routing pro rata; isolate fixture outputs; compare both config diffs against deployed H1-1.
- `tools/run_local_checks.py`: Generate the FIX4 snapshot delta and current packet after tests pass.
- `tools/selection_check.py`: Allow the sampler-only vehicle_p module in the authenticated selector import closure; preserve all sealed admission predicates.
- `tools/unit_binding.py`: Reject unpacked unit inputs with an explicit missing-events/frame-pins error; never regenerate their payload.
- `tools/write_fix4.py`: Generate the file/what/why inventory and unified delta against snap_841f0637.
- `tests/test_packet.py`: Exercise the generated proof main() receipt, v7 census and cap, unit allowlist and named absences, the real read-only unit candidate refusal, deployed config baseline, and fallback filters.
- `configs/diff_against_deployed.json`: Bind the current config and sampler policy against deployed H1-1.
- `configs/diff_against_h1_1.json`: Use the deployed H1-1 baseline, byte-identical to diff_against_deployed.json.
- `configs/mix.json`: Request room 1.72 and size zero; send freed VQA slots to direction; default units to feet only and zero while unbound.
- `configs/r1p.json`: Bind the current tree, v7 receipt, selection and mix identity.
- `work/tree/student_pilot/loader_audit.py`: Audit the exact filtered populations and report total unit counts separately from feet sampling eligibility.
- `work/tree/student_pilot/type_mix.py`: Apply the unit allowlist and 100-row threshold to sampler populations; filter the configured away-QID suffix; retain the four-repeat cap.
- `work/tree/student_pilot/vehicle_p.py`: List unbound units and low-count bound units under absent_on_P; keep required-family failures for actual required populations.
- `out/SAMPLER_REVIEW.patch`: Refresh the review patch against its declared baseline.
- `out/DEPLOYMENT_REVIEW.patch`: Refresh the review patch against its declared baseline.

Generated outputs: out/BINDING.json, config.json, records/, ADMISSION_BY_TYPE.json, MIX.md, proof inputs and audits, operator archive, OPERATOR.json, REPORT.md, R1P_PACKET.md, proof/GATES.json, SHA256SUMS and STATUS.md bind the current v7 identity and keep production blocked. All command output and test results remain in out/logs/.

No Git, SSH, Orchard, GPU, deletion or write outside this lane was used. The requested FIX4 comparison is the only historical narrative added; packet prose describes current state.
