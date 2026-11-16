The production read is blocked by inputs and unfinished integration.

The P8 owner must supply `ROUTED_PATH_FROZEN_<date>.md` with the registered values. ReVSI requires a K1-refit selector that passed its kill rules. The launcher imports the existing `offkit.bind` checks and does not fabricate a freeze record for production.

All 41 additional video names appear in `NEED_302.json` with `upload_required: true`. Of those names, 24 appear in `REVSI_PUSH_FILES.json` without content hashes. The other 17 have no entry in that manifest. This build does not infer that those files are already on Orchard. The owner must supply hashes, sizes, and uploaded-object receipts.

The official ReVSI input consists of 32-frame clips. The accepted sampler refuses to select 64 distinct frames from a 32-frame clip. The dense G3T path therefore needs a registered original-video mapping and exact anchor correspondence. Repeating or interpolating these clips would change the registered tower input; this build does not do that.

The SAM 3 checkpoint has C8r SHA256 `9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e`. Its Orchard location and transfer receipt remain open. The b04 owner must supply the complete artifact manifest, its EAT-1 report, and an audited loaded entry. The existing b04 generic function takes model, hook, perception, frames, and prompt arguments; it does not yet expose the requested loaded two-argument entry directly.

The production stage, C8r context builder, proposal/cache bridge, and opaque Orchard bootstrap are unfinished code in this build. Those are implementation gaps, not merely missing input paths. The CPU harness fixture uses the b04 decode loop with a synthetic serving socket and does not certify C8r generation. The production CONFIG with only transport changed has not run.

The ten selected distance proof records store ground queries as digests. Their token protocol can replay recorded responses, but their response values cannot be independently reconstructed from those digests. An independent mask/backend proof still needs the pinned 170056 mask cache and original runtime context.
