`navrun` evaluates R2R-CE navigation under habitat-sim 0.2.4. CPU mode uses a navmesh and a sensor-free agent. Rendering is opt-in and needs a CUDA EGL device.

Run commands from this directory with `./run.sh`. The wrapper sets the supplied Python environment, both external package paths, eight-thread limits, scratch caches and `nice -n 19`.

```
./run.sh -m unittest discover -s tests
./run.sh -m navrun.proofs lists
./run.sh -m navrun.proofs tracks
./run.sh -m navrun.proofs plans
./run.sh -m navrun.proofs eval
./run.sh -m navrun.controller_proofs
./run.sh -m navrun.audit --output out/tables/scene_audit_cli.json
```

`eval --policies oracle` selects one proof; other names are `random`, `forward-only`, `instruction-prior` `oracle-click` and `oracle-gt-click`. Full-list results also yield the identical 600-episode subset. Each table includes per-episode results and aggregate metrics. Journals resume completed episodes after a deliberate invocation. A partial episode restarts from its initial state with the same episode RNG. A file at `out/STOP` stops evaluation; the user must remove it before resuming.

A policy implements `act(history_frames, instruction, state)`. `state` has only executed primitives, the decision index and sensor constants. `Runner(Environment(Config(...)))` runs a policy. `Config.output_format` selects text, nav, click, waypoint or chunk. `Config.render=True` enables RGB. `ClickTranslator` receives only frames, instruction, executed actions, decision index and constants; its odometry callback receives commanded forward metres. It never receives simulator displacement. The runner uses displacement privately for `controller_version='v2'`, the click/NU default; `'v1'` preserves the external controller exactly. The config-file field is `vla.nav.eval.controller_version`.

V2 keeps v1's lift and normal commands. A forward displacement below 1e-6 m cancels the rest of the leg. Each recovery decision turns one 15-degree quantum and probes one 0.25 m forward step until a probe moves. The direction follows the blocked leg's bearing (left for an exactly centered click), then stays fixed despite bearing changes. STOP takes precedence. The 1e-6 m tolerance comes from the existing blocked-motion diagnostics; the turn and step come from schema 8.2. The runner applies this rule after either its default or an injected vla_where `ClickTranslator`, without changing the backend's observation whitelist. Waypoint and training-row primitive conversion retain schema 8.2 behavior.

Waypoint JSON uses `heading_deg` (positive left), `distance_m` and boolean `stop`. Physical chunks use `[forward_metres, left_degrees, stop_probability]`, with STOP at 0.5. Normalised chunks map clipped [-1,1] values through `Config.chunk_min/max`. Fractional turns and travel accumulate residuals across decisions. Text options A/B/C/D map to forward/left/right/stop. Empty decoded movement consumes a decision; a separate decision cap prevents an infinite loop.

Nav and click parsing use the vendored `nav_grammar_v1`. A parse failure repeats the same policy input once; two failures execute one left turn and log both attempts. History indices are `i*t//(L-1)`; with L=1 the current state is used. `NativePolicy` applies the model's native thinking template and constrains the answer after an explicit empty thinking block. Real tokenizer/model integration is unverified here.

Official R2R-CE preprocessed GT supplies episode-id keyed actions and dense locations for all 10,819 training episodes. The loader validates coverage, start positions and action/location alignment, and refreshes cached tracks from this source. Verified R2RIE GT and the greedy reference follower remain labelled fallbacks when official files are absent. `out/tables/replay.json` records codec replay; `location_replay.json` compares every forward endpoint and final position against official locations.

Training rows contain `id`, `episode_id`, `trajectory_id`, `scene_id`, `split`, `output_format`, `decision_step`, `history_indices`, `frames`, `instruction`, `executed`, `prompt`, `answer`, `template_id`, `template_sha256`, `gt_source` and `render_status`. Click rows add `label_reason`. Frame paths are plans, not existing images. One 10% build also writes the nested 1% rows. A scene-overlap audit runs before writing any rows.

`navrun.compare` accepts two JSON arrays of episode results. It joins unique episode ids, checks scene parity, and computes scene-stratified paired bootstrap intervals and an exact McNemar test. `family()` applies Holm across predeclared comparisons. The four outcomes are GAIN, HARM, EQUIVALENT and INCONCLUSIVE; equivalence requires the 90% interval strictly inside ±0.03.

`navrun.audit` accepts `--student`, `--g3t`, and `--sam3` scene manifests. Unknown paths produce “provenance unknown.” Known overlaps are excluded before evaluation lists are frozen. Manifests contain a `scenes`, `episodes` or `rows` list. `load_rand100` accepts Open-Nav's local release (plain JSON despite its .gz suffix) or a verified manifest. The loader checks 100 unique ids, scenes and trajectories; release inputs also check start positions against val-unseen. `proofs lists` and `controller_proofs` freeze source-file order and the ordered-id SHA256 in `out/lists/rand100.json`.

FastDTW uses recursive pair averaging, radius-1 path expansion and Euclidean distance, independently implemented from the algorithm. Exact DTW is also available. As in VLN-CE, repeated stationary predicted positions are omitted. All 1,839 val-unseen reference paths use official dense GT locations in the proof and evaluation CLIs. R2RIE proofs use their supplied dense GT. SR requires STOP strictly within 3 m. OSR does not require STOP; TL measures actual displacement including sliding.

R2RIE pairs match on old episode id and verify scene, trajectory, start pose, reference path and primitive GT. Detection AUC handles tied scores. `detection_atd` defines delay in primitive steps from a caller-supplied onset; misses are censored at the episode horizon and early alarms are counted separately. Token-error offsets are not treated as action-time onsets. Blind policies supply no detection scores, so actual AUC/ATD remain unmeasured.

`./run.sh -m navrun.evaluate --config configs/N1.json --list out/lists/val_unseen_600_s0.json --policy my_local_adapter:make_policy --journal out/model.jsonl --output out/model_results.json --render` loads a caller-supplied local factory. Pass model/provider scene manifests to exclude overlap before freezing that run's list. N0 requires explicit `--allow-control`. Persistent custom policies implement `resume_identity()`; `NativePolicy` requires a checkpoint SHA256, and `CallablePolicy` takes an explicit identity. Journals also pin execution source, dataset content and metric references.

`./run.sh -m navrun.policy_server --factory my_local_adapter:make_policy` serves stateless model calls as JSON lines over stdin/stdout. Each request contains exactly the five schema-8.4 fields, and frames are RGB arrays. The factory initializes any model state; the worker opens no sockets. `navrun.compare --family family.json` accepts a list of `{name, a, b}` result-file paths and applies Holm to that family. Result inputs may be raw arrays or the proof command's `{summary, results}` objects.

The no-occlusion click proofs share the supplied floor-plane lift and configured controller version. `oracle-click` uses a 2 m navmesh-geodesic lead and a 1 m STOP threshold. `oracle-gt-click` uses the nearest GT location and a 2 m arc-length lead (`CLICK.max_leg_m`), with STOP strictly inside the configured 3 m success radius. `proofs eval --controller-version v1` selects parity behavior. `controller_proofs` measures both versions on the same 600 ids and runs oracle/random/forward/instruction policies on rand100. `click_diagnostics` records v1 geodesic decision traces. The 102-episode fixture under `tests/fixtures` checks exact v1 streams/tails and absence of stationary last-20-decision tails with v2.
