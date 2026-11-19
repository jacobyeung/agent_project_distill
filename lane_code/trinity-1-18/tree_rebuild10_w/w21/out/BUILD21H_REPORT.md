STOP / NO-GO: full native routing requires a sealed-reader change under the naming rules. GO=false.

Required tree change (proposal only; not applied):
In `work/tree_r1/student_pilot/job_env.py`, add `'STUDENT_R2_FRAME_HOST': 'Q_E7'` to `ALIASES`.
In `student_pilot/r2_intake.py`, import `from .job_env import key as env_key` and replace
`os.environ.get('STUDENT_R2_FRAME_HOST')` with `os.environ.get(env_key('STUDENT_R2_FRAME_HOST'))`.
Apply that same lookup replacement in `student_pilot/r2_materialize.py` if using its full producer.
Keep the local-node veto, hostname veto, limit checks and every admission predicate unchanged.
The kit can then set literal `Q_E7=1` after validating its frame-host stage; that assignment passes the scanner.
This changes environment naming only, but it changes sealed source bytes and therefore needs a new tree seal.
No proposed change has been applied. Item 2 explicitly requires reporting and stopping when sealed code must change.

Why a kit-only completion is blocked (`work/build21h/HOST_FLAG_BLOCKER.json`):
`r1_routing.compose_native` calls `r2_intake.intake(..., limit=None)` for every bound family.
The reader accepts this only with literal `STUDENT_R2_FRAME_HOST=1` on a non-Trinity, non-local host.
It ignores both `Q_E7=1` and the older distributed launcher's `K6=1`; `job_env.key` has no corresponding alias.
The real composition function with opaque flags refuses `Local slices must contain at most 2000 rows per family`.
The same intake accepts the native flag. Both literal and concatenated native-name assignments fail the kit scanner.
Encoding that name, weakening the scanner, replacing the reader, or limiting production intake would evade the contract.
Existing `launch_r2.distributed.worker` translates K6 only as part of its separate authorized training path.
Existing `launch_r2.host.run_packet` sets the native flag within its separate packet/materialization path; neither is a standalone mode-q host initializer.

Required routing inputs (`work/tree_r1/launch_r1/entry.py:160`, `student_pilot/r1_routing.py:162`):
`routing_base` is a `{path,sha256}` pin to a `c1-routing-stream-v1` receipt with training division,
zero held-out overlap and a pinned native rows database. It is not the export artifact or its weight manifest.
For P's step-400 run, that receipt is `ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984`;
its database is `4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84`.
Source: `../ext/m400real/r.json` and its pinned runtime config, under `../ext/m400real/files/`.
`joblib.identities` authenticates config/binding/preparation against the pinned runtime identity;
the preparation must bind the same stream receipts, and native readers authenticate nested database/division pins.
Mode q actually reads `cfg.streams.routing`; it does not consume a request-only `routing_base` field.
`s1_admission.prepare_phase` regenerates the S1 routing base, then supplies that receipt to `compose_native`.
The kit must carry the base in both config and request for their respective entry contracts.

`routing_inputs` maps each name returned by `r1_coverage.source_names` to a pinned family envelope:
`recovery`, `absolute_distance`, `units`, `coverage_distance`, `coverage_units`.
Their exact source pins are in `work/build21/inputs/row_sources.json`; the V2H hashes remain
`15387646fd4ac47b43c107129db3109545a981c1bd45a3910ac038d8c5432022` and
`8ec1efd2c1851fb856caa3631653390d76796f8c31cd8366d54df52916c7de82` (`student_pilot/r1_coverage.py`).
Each envelope needs schema `r2-family-manifest-v1`, matching family, stream `routing`, count,
the exact source pin, per-QID `digest(raw)` bindings, contract and validator hashes, all sealed exclusions,
pinned independent scene coverage, upstream accounting when prefiltered, and the exact config extent receipt.
Frame-map, frame-plan and FPS-authority pins support the native RGB join; merged dev exclusions and withheld rooms remain enforced.
`compose_native` checks exact source/extent pin equality and source-catalog membership;
`intake` authenticates the manifest's dependencies, row digests, scene identities, extent evidence and grammar.
The extent pin is `c072905be4405a92d7bb906112209f2d27a8c9b58d291b64373c5551c3e96495`
(`work/build21/inputs/config.json`, `extent.json`); V2H inheritance is recorded in `proofs/v2h/DERIVATIONS.json`.

Row files suffice for row digests, counts, source-catalog membership and wording checks.
Independent scene names require pinned external identity evidence; copying a row's own canonical claim is not independent coverage.
`s1_routing.Frames.resolve` joins exact ordinals, frame hashes, FPS and total counts from pinned metadata.
That join does not itself read RGB rasters. `r2_frames.verify_frame` and `s1_admission.FrameAudit` require staged frame bytes;
the latter checks every retained frame's existence and a fixed hash sample (`student_pilot/s1_admission.py`).
Scene-coverage metadata is not a raster proof. The existing extent receipt can be reused and checked from metadata;
new geometric/raster evidence cannot be fabricated from row files. Full production frame coverage remains unproved here.

P's path (`../inputs/p_runtime/A_runtime_673bc60f.json`, `../ext/pwrap/b/c.sh`, real step-400 config/preparation):
P stages stores, frame-map/plan/FPS metadata and frames, then uses `s1_routing.build` and native preparation/frame audits.
The real step-400 routing receipt records the database, division, materialization pin and per-source scene checks.
P's configs have no `r1_training` block, so P never satisfied or needed N's `routing_inputs` composition contract.
The capacity fixture supplies empty synthetic family envelopes and explicitly sets `STUDENT_R2_FRAME_HOST=1`
while substituting the hostname (`work/build21/native21.py:303`); it therefore does not prove a legal kit environment.
Its request has no `routing_base` field: mode q receives the base and envelopes through its pinned config.

Evidence and limits:
The unchanged kit's own decoded config reproduces `ValueError:R1_PROOF_NATIVE_ROUTING_REQUIRED`
in the build-21g stand-in view (`work/build21h/LOOKAHEAD_BEFORE.json`); config, staged pins and counting card pass.
The host-flag proof uses existing empty fixture envelopes and substitutes only hostname/environment at the host boundary.
It exercises the real intake and composition functions; no production rows, RGB or store database are read.
Native flag passes intake; missing/opaque flags refuse; literal/concatenated native-name assignments refuse scanning.
This is a downstream integration defect, not proof that the production run reached that later stage.
No passing-after kit, new kit seal, upload change or build-21h package is claimed.
Focused/kit/resolver suites and the full decoded scan were not rerun after invoking the mandatory stop rule.
The tree, kit, resolver identity checks, admission, P's opener rows, step-544 lineage and DEFERRED boundary remain unchanged.
Verification and unchanged seals: `work/build21h/FINAL_STATE.json`. No network, scheduler, GPU, Git, SSH or other agent was used.
The before/after discussion is retained because the task explicitly requests regression evidence.
