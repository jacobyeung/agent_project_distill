The supplied 24k kit needs a staging-plan adapter as well as the new tree tar and seals. Kits were not edited.

| Location in in24kr/kit_n_go | Required integration |
| --- | --- |
| k/a.json source, k/p.json code/source pins, k/c0.json, BUILD.json and SHA256SUMS.txt | Publish the new tree archive and regenerate its source inventory, code capsule and dependent seals. Keep the existing host-receipt consumption in h.py. |
| b/pl.py:177–200 | Emit the native launch_r2.staging entry format. Every entry key must be a safe `u/...` target. Place n.json, source_code.json, direct-file extras and weight sibling aliases under that namespace; update their config/request paths and relocation map together. Do not rewrite authenticated donor JSON. |
| b/pl.py:186–188; b/z.py:482–503 | The current `e` aggregate uses receipt labels as an inventory and has no retained archive file. For native verification, retain the joined authenticated archive at `q/a/<archive_sha256>`, extract at `q/x/<archive_sha256>`, and describe each `u/...` target with an archive descriptor, its real archive member name, its member SHA256 and the complete member inventory. Direct metadata entries can remain ordinary hashed entries. |
| b/pl.py:204–231 | The hook must leave the bytes/links in the native layout before returning. The tree rehashes the retained archive, every inventoried member and each target; directory targets must resolve to the named extracted directory. Preserve the hook's relocation-scope lifecycle. |

The supplied plan reaches `R1_HOST_STAGING_DIFFERS:e:Staging target escaped the input root` under the new verifier. Its `n.json`, `source_code.json` and `f/...` entries also violate the native `u/...` contract. This is an integration requirement of the requested hook re-verification, not a donor-pin comparison fix. KIT_PLAN_PROBE24LN.json reproduces the plan-shape refusal without payload IO.

The additional host fields need no h.py/u.py schema change: h.py copies host.json after checking its existing assertions, identity and loader audit. They record the selected routing pin/digest, routing substitution, stager and post-twin scene input pins.

The decoded k/c.json and k/n.json also have `r2_all_stream_exclusions=true` with null `r2_scene_rebuild` and `scene_coverage`. The supplied z.resolve/pl flow does not fill these fields. Native carrier_c1_run.prepare calls r2_scene_bindings.verify, which requires an authenticated scene-rebuild pin. This is a pre-existing evidence gap, not a path-only mismatch; supply and validate the required scene evidence before claiming a production PASS. No exclusion gate was weakened.

Routing regeneration still requires the exact runtime paths, staged inputs, source implementation and independent P-row equality approval. ROUTING_DIGEST_STABILITY.json is a CPU-fixture result, not the production selection pin. No production PASS or launch GO is supplied.
