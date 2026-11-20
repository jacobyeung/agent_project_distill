# Reference reproduction tolerance

Registered UTC: 2026-11-20T19:54:15Z, before any rebuilt/reference array comparison.
Every key, shape and dtype must match. Every element must pass; no percentile or average acceptance.
Integer, boolean and string arrays (inst, valid, ids, labels, frame_indices): exact equality.
K and K_frames (float64): exact equality; parsed calibration and fixed raster scaling are deterministic.
obb_centroid, obb_lengths and obb_axes (float64): exact equality; annotation decoding and the declared extent conversion are deterministic. Re-estimated boxes are not equivalent annotation arrays.
c2w (float32): absolute error <= 8 * eps(float32) * max(1, abs(reference element)), relative tolerance zero otherwise. This allows eight float32 rounding units for inversion, axis conversion and final casting, but no geometric alignment fit.
depth (float32): absolute error <= 8 * eps(float32) * max(1, abs(reference element)) for floating ray intersections followed by casting. Both arrays must have exactly the same zero/nonzero support. ARKit PNG scaling and nearest resize are deterministic and require exact equality instead.
All arrays must be finite. Exact equality is also reported for every array. Record differing-element count, maximum absolute difference and RMSE for numeric arrays; count unequal values for categorical arrays. Any failure rejects that dataset and all its new captures. Tolerances will not be widened after comparison.
