Audited every source file, the tests, and the build report without modifying files or running Git. **All 8 supplied tests pass** (`1.53 s`, CPU), but targeted checks reproduce several blockers.

1. **BLOCKER — Goal conditioning cannot learn.**  
   [vla_expert.py:101](/scratch/jjyeung/orch_home_distill/spatial_v2/vla_expert.py:101) zero-initializes the subgoal projection’s final layer; line 103 also zero-initializes its multiplicative gate. Their product at [line 162](/scratch/jjyeung/orch_home_distill/spatial_v2/vla_expert.py:162) gives both branches zero gradient indefinitely. Reproduced: every subgoal parameter’s gradient is exactly zero after `compute_loss().backward()`. Initialize only one side to zero.

2. **BLOCKER — TT-BA can “improve” by putting observations behind the camera.**  
   [ttba.py:82](/scratch/jjyeung/orch_home_distill/spatial_v2/ttba.py:82) recomputes visibility for each candidate; lines 91–94 remove invalid-depth observations from its cost. Lines 230–233 accept that reduced cost without penalizing lost observations.  
   Reproduced with identity poses, one central correspondence, and valid input depths **1.0 m / 0.06 m**: the solver returns **`committed=True`, destination Z = −0.3997 m, cost = 0**, without `force_run`. Reprojection remains zero, satisfying [line 261](/scratch/jjyeung/orch_home_distill/spatial_v2/ttba.py:261). Reject cheirality violations or retain a penalty for observations lost during optimization.

3. **BLOCKER — Cross-camera temporal-patch isolation is not implemented in the adapter path.**  
   [epi_adapter.py:139](/scratch/jjyeung/orch_home_distill/spatial_v2/epi_adapter.py:139) defines a standalone averaging helper. Neither `forward` nor [apply_residual, line 220](/scratch/jjyeung/orch_home_distill/spatial_v2/epi_adapter.py:220) calls it. More fundamentally, their inputs are already-computed ViT taps and merged tokens: this helper cannot undo upstream temporal patch embedding across cameras.  
   [tests/test_spatial_v2.py:46](/scratch/jjyeung/orch_home_distill/spatial_v2/tests/test_spatial_v2.py:46) merely verifies that the helper leaves non-video tokens unchanged. Enforce isolation in image packing **before** temporal embedding and test that actual path.

4. **BLOCKER — Padding and invalid targets contaminate losses.**  
   [losses.py:213](/scratch/jjyeung/orch_home_distill/spatial_v2/losses.py:213) averages pointmap loss over padded views; [line 234](/scratch/jjyeung/orch_home_distill/spatial_v2/losses.py:234) does the same for reversal. Reproduced: errors confined to a masked view produce pointmap loss **12.484375**. Line 233 masks sparsity’s numerator but averages over padded elements, so padding changes its effective weight.  
   Separately, [lines 110–120](/scratch/jjyeung/orch_home_distill/spatial_v2/losses.py:110) evaluate invalid depth targets before masking. A single **masked-out NaN target produces NaN loss**. Select or sanitize invalid entries before arithmetic and normalize by valid support. Composite depth loss also does not intersect `depth_valid` with `view_mask` at line 265.

5. **BLOCKER — Composite training bypasses unlocked-scale isolation.**  
   `DecoupledDepthLoss` itself correctly gives zero scene-scale gradient when `metric_scale_locked=0`. However, [losses.py:213](/scratch/jjyeung/orch_home_distill/spatial_v2/losses.py:213) applies absolute pointmap supervision without scale alignment or the lock mask; [line 279](/scratch/jjyeung/orch_home_distill/spatial_v2/losses.py:279) includes it in the composite loss.  
   With pointmaps unprojected from predicted depth, reproduced gamma gradients were **0.0 from unlocked depth loss**, but **0.1134 from pointmap loss**. Gate or scale-align this path for uncalibrated samples.

6. **BLOCKER — The π-rotation logarithm is wrong and can poison training gradients.**  
   [geo_heads.py:59](/scratch/jjyeung/orch_home_distill/spatial_v2/geo_heads.py:59) reconstructs the axis using positive square roots, losing relative component signs. For a π rotation about `(1,−1,0)/√2`, `exp(log(R))` differs from `R` by **2.0 maximum element error**.  
   The square roots at zero also cause NaN derivatives. Reproduced through the actual 6D rotation and geodesic-loss path: **all six rotation-parameter gradients become NaN**. The loss uses this logarithm at [losses.py:184](/scratch/jjyeung/orch_home_distill/spatial_v2/losses.py:184).

7. **BLOCKER — DeltaGeoBias defaults to enabled.**  
   [config.py:138](/scratch/jjyeung/orch_home_distill/spatial_v2/config.py:138) sets `use_delta_geo_bias=True`, contrary to the stated disabled-default ruling. No supplied integration code consumes the flag. Bypassing this optional bias preserves the base gates; zero initialization does not substitute for disabling it after training starts.

8. **WARNING — Degenerate geometry returns invalid transformations.**  
   [geo_heads.py:99](/scratch/jjyeung/orch_home_distill/spatial_v2/geo_heads.py:99) returns determinant-zero matrices for zero or collinear 6D vectors. These cases had finite gradients in my checks, but are not rotations. Zero gravity similarly produces a singular canonical transform at [line 186](/scratch/jjyeung/orch_home_distill/spatial_v2/geo_heads.py:186). Add explicit fallback behavior.  
   The analytic Plücker constructor is correct, but the learned head at [line 412](/scratch/jjyeung/orch_home_distill/spatial_v2/geo_heads.py:412) does not enforce `direction · moment = 0`.

9. **WARNING — Static-flow and horizon validity are insufficiently constrained.**  
   [losses.py:233](/scratch/jjyeung/orch_home_distill/spatial_v2/losses.py:233) weights flow sparsity by **`1−p_stat`**: identical nonzero flow receives penalty 1 for dynamic pixels and 0 for static pixels. Thus this term supplies no static-zero-motion constraint; clarify whether dynamic sparsity was intentional.  
   Flow supervision at lines 223–229 has only view-level validity, with no per-pixel/per-horizon validity for unavailable or occluded targets. Reversal at line 234 also assumes its input already represents corresponding points and horizons.

10. **WARNING — RoPE’s numerical and backbone-parity guarantees are overstated.**  
    [metric_3d_rope.py:67](/scratch/jjyeung/orch_home_distill/spatial_v2/metric_3d_rope.py:67) computes coordinate-frequency products in fp32, which handles ordinary bf16 coordinates, but does not prevent large-origin precision loss. With nonzero beta, shifting coordinates by `10³`, `10⁵`, and `10⁶` changed attention logits by approximately **0.0059, 0.446, and 4.01**, respectively. Finite bf16 coordinates around `10³⁸` overflow intermediate products and produce NaNs even at beta zero.  
    Initialization exactly matches **this module’s rotary helper** for finite intermediates. [tests/test_spatial_v2.py:79](/scratch/jjyeung/orch_home_distill/spatial_v2/tests/test_spatial_v2.py:79) does not compare against the actual backbone’s M-RoPE implementation or channel layout.

11. **WARNING — Camera identifiers silently collide above 16 streams.**  
    [epi_adapter.py:134](/scratch/jjyeung/orch_home_distill/spatial_v2/epi_adapter.py:134) clamps every stream ID ≥15 to embedding 15, while [config.py:235](/scratch/jjyeung/orch_home_distill/spatial_v2/config.py:235) assigns distinct IDs to arbitrary-N multiview inputs. The 48-view test checks metadata construction, not this collision.

The following mathematics checked out:

- For nondegenerate inputs, column-based 6D Gram–Schmidt, world-to-camera pose composition/inversion, signed-`fx` projection/unprojection, and analytic Plücker rays are consistent. Gravity canonicalization is right-handed and maps the **supplied vector** to +Z; that input must represent **up**, rather than physical downward gravity.
- TT-BA’s analytic Jacobian matches an independent autograd calculation to **1.14×10⁻¹³**, including `fx<0`. Weighted normal-equation assembly and diagonal damping are consistent with its local pose update. The verified failure concerns candidate visibility and acceptance.
- SpatialForcing² uses unit-normalized feature Gram matrices and a valid-pair mean without mixing batch elements. Its masks work for finite padding.
- Depth NLL exponentials are bounded by the head’s variance clamps and evaluated in fp32. `detach_backbone=True` correctly detaches both taps and geometry tokens.
- Flow matching consistently uses `x_t=(1−t)noise+t·action`, target `action−noise`, and positive-time Euler integration. An independent constant-velocity endpoint check passed.

The tests and receipt do **not** establish deployment readiness:

- **TT-BA is a privileged synthetic recovery test:** [tests/test_spatial_v2.py:226](/scratch/jjyeung/orch_home_distill/spatial_v2/tests/test_spatial_v2.py:226) constructs exact correspondences and depth shapes; line 236 supplies oracle outlier downweights; line 246 adds only per-view multiplicative depth error. The relative case anchors an accurate first view, and [line 265](/scratch/jjyeung/orch_home_distill/spatial_v2/tests/test_spatial_v2.py:265) supplies **GT translation priors** for global-scale recovery. Negative `fx` **is covered**. Real monocular shape noise, matching errors, and unanchored global metric-scale recovery are not demonstrated.
- The backward test uses fully valid batches and random ordinary rotations. Its reversal target is `−prediction.detach()` at [line 365](/scratch/jjyeung/orch_home_distill/spatial_v2/tests/test_spatial_v2.py:365), guaranteeing zero reversal residual. The goal test checks initial inactivity, not learnability.
- **13.51 ms is action-head timing with supplied memory, not perception-to-action latency.** [vla_expert.py:210](/scratch/jjyeung/orch_home_distill/spatial_v2/vla_expert.py:210) projects supplied features and integrates actions; it never runs perception. The [receipt’s line 74](/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/build_spatial_v2_core.md:74) reports a CUDA-graph benchmark whose harness is absent from the audited files. I did not independently reproduce that GPU number.

**VERDICT: BLOCKER**