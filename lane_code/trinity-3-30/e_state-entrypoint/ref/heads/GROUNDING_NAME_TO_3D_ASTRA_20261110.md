# Routed grounding through a shared 3D object memory

Lane d_astra; design only; evidence checked through 2026-11-10 08:45 UTC. M = measured in a cited record; H = hypothesis; E = planning estimate, not a measured throughput or accuracy. No training, GPU work, transfers, or other-lane reads were performed.

**Recommended design.** Build geometry once per clip and maintain an instance-indexed object memory inside the model. Resolve each name with a few high-resolution observations, verify the same instance from another viewpoint, and reuse its masks and geometry across calls. Spend the next GPU allocation on a resolution diagnostic; test identity selection and lifting from existing caches on CPU.

1. Keep Qwen3.5-9B, its direct-answer path, frozen G3T, and V-C metric scale. Use 32 explicit LM frame IDs and 32 or 64 genuinely distinct geometry frames with an exact anchor map.
2. Give each proposed object a clip-local ID, multiple view observations, an appearance descriptor, observed 3D surfaces, geometry provenance, and separate identity/presence/geometry confidence.
3. If SAM is allowed, start from its native joint-confidence gate (>0.5), retain candidate instances, and let a query-conditioned selector choose a persistent object. Use a high-resolution click to disambiguate; class confidence alone does not establish identity.
4. If SAM is disallowed, use the same LM weights for a bounded high-resolution image reread, then prompt the existing mask decoder with the query and click. Add dense V-C/G3T features to that decoder only if the diagnostics justify training.
5. Route only when the complete set of operands is reliable. Preserve direct fallback and report its contribution. Counting, amodal size, and dynamic scenes remain separate capabilities.

The decisive question is whether the system can identify the intended instance at useful coverage. Consistent geometry cannot correct a consistent choice of the wrong chair.

**What the evidence establishes.**

| Evidence checked | What follows; what does not |
|---|---|
| M: GT-mask routed+fallback gains are +24.1/+23.9/+27.3/+39.6 points for direction medium/hard/relative distance/absolute distance on dev 858. [S1] | Object geometry can help this program family. These are harness results with fallback, not integrated-model results or universal spatial competence. |
| M: SAM top-instance gains are −13.0/−22.6/−29.7/−3.8; the GT-presence/GT-instance oracle gives +22.8/+26.1/+24.9/+38.1. Accepted-frame target overlap is 47%; candidate IoU > 0.5 recall is 71.5% of GT-visible label-frames. [S1, S8] | Selection has large headroom, but that oracle also uses presence information. The 71.5% frame recall is neither clip recall nor an achievable selector score. |
| M: base single-image pointing is 66.3/67.1% in-mask/null; T0 is 58.0/58.9%; base video pointing is 47.1 with markers and 19.7 without. T0 video is 61.2/86.9. [S2] | Resolution, addressing, and training lineage require separate controls. The metric accepts any same-label instance and cannot establish reference resolution. |
| M: the cited gate-set area hits are 39.1% below 1% and 85.4% above 5%; the specified 1,000-item audit instead gives 21.9%/80.7%. Pointing-heavy training gives 58.9% video hits. [S2, S14] | The size effect persists, but the cohorts are not interchangeable. Area correlation does not prove that more tokens will fix errors. |
| M: MDG training completed at step 5000; best internal hits are 0.721 and step-4800 hits/null are 0.709/0.806, below 0.84/0.90. [S3] | A query adapter may help semantics; it cannot be assumed to restore missing image detail. Held-out export remains the deciding measurement. |
| M: Qwen ViT probes are near chance; G3T's own held-out ScanNet direction is 3.1°. [S4] | Read G3T's geometry directly. The probe only excludes information readable by its tested small heads and training budget. |
| M: SAM caches use independent image inference at 1008 square resolution, retain at most five masks with raw score ≥0.3, and have no persistent IDs. [S8] | Existing results do not test video tracking, all proposals, or point-prompt segmentation. Source/checkpoint revision is incompletely pinned. |
| M: native joint gate >0.5 yields +1.34/−6.96/+4.85/+17.70 routed points; only absolute distance has CI lower bound >0. Ungated 3D clustering gives −4.91/−11.30/−7.88/+13.26. [S8] | Fix acceptance before attributing the full loss to instance selection. Ungated clustering loses; native gating alone still fails the three-type deployment bar. |
| M: native gate plus the 0.5 m ball selector gives +4.91/−3.48/+6.67/+22.76; relative and absolute distance win significantly. Localization is 47.88% versus 47.20%, +0.68 [−2.59,+3.90]. [S16] | Gated selection is a stronger baseline. Its routed gain does not establish better localization or a three-type win. |

Absolute-distance “points” use the harness MRA score, not binary exact-answer accuracy. The full 84-scene SAM dev result includes its 31 threshold-calibration scenes; report the 517-question non-calibration slice separately. [S8]
The supplied 80.1/58.7/73.0 older comparison was not independently traced to its primary score file and is not used to set any forecast or gate.
