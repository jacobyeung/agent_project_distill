The kits require a reviewed native routing-selection digest before mode q. The default request refuses R1_ROUTING_SELECTION_PIN_MISSING.
Run out/jr.sh on Orchard as a CPU-only job with the resolved request and kit path. It stages the exact runtime inputs and publishes routing_selection.json to <n_root>/o/<jobid>/.
P receipt ca0616db is present and authenticated locally, but contains no regenerated_sha256. Its production stores are required for the native computation and P-row equality check.
After independent review, out/arm_routing.py binds u/<sha256 of routing_selection.json> in fresh q and N GO copies, reseals and scans them, and emits a separate upload delta. It does not upload or launch.
The native q path emits its host receipt only after final-config audit and host assertions pass. The training job then publishes the prepared identity and waits up to 120 minutes for the independent matching review.
No production routing digest, native host PASS, independent review, upload, scheduler submission or launch is claimed by this package.
