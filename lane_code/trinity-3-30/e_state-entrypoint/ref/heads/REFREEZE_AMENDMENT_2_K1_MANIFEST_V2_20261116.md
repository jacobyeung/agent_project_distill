# Re-freeze amendment 2: K1 manifest v2 for the own, convert and table phases (registered 2026-11-16T05:34:43Z, before any own-phase output exists)

**Question.** K1's manifest 91a2dbf9 carries two placeholders in its GPU settings (gpu.data_receipt.sha256 = "REQUIRED", gpu.config.path = REQUIRED_LOCAL_STEP_544_CONFIG). The own phase checks both pins by bytes and cannot run on it; tower_sam ran because it does not read them. How does the own phase run without breaking the rule that all phases share one manifest and code tree?

**Answer.** Manifest v2 equals 91a2dbf9 except for those two pins, which are filled with the prepared config (bytes 78341acb, trainer identity 84ea03af against artifact 1d6eeb28) and the data receipt that the accepted native read (Orchard job 170056, kit C8r) authenticated. A reviewed script builds v2 and asserts that all 300 capture entries and the gpu.artifact pin are byte-equal to v1. convert ties own to tower_sam per capture (capture digest, sources, producer, checkpoint pin), so tower_sam's 300 receipts stay valid under v2. The report states v1 for tower_sam and v2 for own, convert and tables, with both digests.

**Reasons.** The placeholders name inputs that did not exist on the node when the manifest was written; filling them changes no capture, frame, raster or model. The same config and receipt already carried an accepted read of the same export.

**Rejected.** A fresh preparation for K1 (needs the four training streams, lost with trinity-2-18, and would create a second prepared state for one export). Relaxing the own phase's byte check (code change in a registered phase).

**What might be wrong, and how we would notice.** If the script changed any capture entry, convert would refuse on the capture digest; the script's own assertion and the reviewer check it first. If the prepared config did not belong to the export, read_runtime.prepared would refuse on the identity 84ea03af.

**Status.** Registered. Applies with amendment 1 (296-capture primary set).

**v2 digest (recorded 2026-11-16T06:32:41Z by k1_ops5, before any own-phase output exists).** v2 sha256 e684e0c7d8a75e4296e34ba4980aa6d7088f6c2f2053d7850ee790e7cf215146 (built from v1 91a2dbf9 by make_manifest_v2.py sha 08cfba89; copy at trinity-1-18:/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json). Only gpu.config (78341acb) and gpu.data_receipt (ebc2983e) differ; all 300 capture entries and gpu.artifact are canonical-JSON equal to v1.
