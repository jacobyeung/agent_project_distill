# From an object's name to its 3D position: one object per clip, verified at high resolution, carried by geometry

Design lane d_fable, 2026-11-10 08:45Z, trinity-2-18, read-only. Nothing was trained or launched. FACT = measured, source named. E = estimate. HYP = hypothesis that an experiment in section 4 settles. **dev** = 858 GT-generated questions on 84 held-out ScanNet scenes, 589 (scene, object name) pairs. Gains are routed-or-direct minus T0 m800 direct, in points, in the order direction medium / direction hard / relative distance / absolute distance.

## Question
How should the 9B student turn an object's name into a 3D position and extent inside its own generate pass, robustly over 32 to 64 frames, whether or not SAM 3 may sit inside as a frozen tower?

## Answer
1. **Ground the object, not the frame.** `<ground obj="NAME">` resolves one 3D object per clip and name in four fixed steps: propose candidate objects, verify the few best on zoomed crops with the LM's own vision encoder, accept one or abstain, and carry the accepted object to the other frames with pose and depth. I call this SVP (seed, verify, propagate). The trace text of SPEC v3.12.2 does not change; only the mask source behind the call changes.
2. **The gate is choice, and choice fails on presence.** SAM 3's proposals already hold the target (an oracle choice recovers +22.8 / +26.1 / +24.9 / +38.1). Its most confident detection in the clip lands on the target for 78.4% of objects, and 95 of the 127 misses sit in a frame where the target is not visible. Voting across frames does not repair this, because look-alikes persist across frames (four rules measured, none passed). A semantic check at high resolution is the untested lever.
3. **With SAM 3 inside (branch S)** the grounder needs no training: SAM 3 proposes, the LM verifies, geometry propagates. I expect 84-90% of objects grounded on target with zero training (HYP) and routed wins on 3 to 4 of the 4 types. **Without SAM 3 (branch N)** the LM's native boxes on its best frames replace the proposals and depth supplies the extent. I expect absolute distance to win and the other three types to wait for adapters trained on GT masks (E).
4. **Representation:** the unit is (clip, object name), cached in a per-clip object memory that grows on demand. A full scene table built up front loses on recall, cost and name matching.
5. **Bars:** object-level, on benchmark operands: on-target selection >= 88%, accepted precision >= 93%, coverage >= 85%. The frame-level in-mask bar on the 1,000-item set should go: a frontier model scores 70% on it.

## 1. Recommended design

### 1.1 What the evidence says
| Fact | Value | Source |
|---|---|---|
| GT masks, own depth, G3T x s pose | +24.1 / +23.9 / +27.3 / +39.6 | mdg_next 0236Z card |
| Oracle picks among SAM 3's instances | +22.8 / +26.1 / +24.9 / +38.1 | same |
| SAM 3 top instance, frozen accept rule (joint >= 0.035) | -13.0 / -22.6 / -29.7 / -3.8 | same |
| SAM 3 top instance, official gate (joint > 0.5) | +1.3 / -7.0 / +4.8 / +17.7 | sam3_audit 0825Z |
| 3D cluster seen in the most frames (0.5 m linkage) | -4.9 / -11.3 / -7.9 / +13.3 | sam3_audit 0825Z |
| Score x persistence | -12.5 / -17.0 / -21.2 / +4.2 | sam3_audit 0825Z |
| Objects visible in >= 1 of the 32 frames; median visible frames | 589 of 589; 8 | my read of `sam3_audit/out/cache_audit/name_frames.csv` (`work/pairstats.py`) |
| Best view of the object covers >= 5% / 2-5% / 1-2% / < 1% of the frame | 411 / 117 / 49 / 12 objects (70 / 20 / 8 / 2%) | same |
| SAM 3's most confident detection in the clip overlaps the target | 78.4% of objects; 95 of 127 misses lie in a frame without the target | same (`work/pairstats2.py`) |
| An on-target top detection among the 2 / 3 / 5 most confident frames | 84.0 / 87.4 / 90.2% | same |
| Some cached proposal reaches IoU > 0.5 in some frame | 92.4% of objects | same |
