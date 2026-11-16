# Decode-time MDG grounding backend

## Question
Can the existing routed decode loop answer ground calls with MDG masks and fixed geometry, while preserving the printed-point calculator and byte-equal offline replay?

## Implementation
The lane supplies `student_pilot.ground_lifting`, a parameter-free module shared with ground_rows. It follows SPEC v3.12.1: eroded mask interiors, centre-depth lifting, spread gates, one median in the gravity-aligned world, public camera/f1 transforms, rounded P registration, visible-mask size or `size unavailable`, and closest-point gaps. Multi-candidate gaps print every candidate and compute all minimum ties from displayed Decimal distances. Gap frame selection tries common frames first and separate frames after common-frame failures. The private audit retains selected frames.

`student_pilot.mdg_decode` captures LM layers 16/24/final, ViT blocks 9/17/25 and RGB from the existing prefill. Its stream captures layer-24/final call-end query and phrase states while native cache continuation consumes the sampled tokens. The decoder encodes the cached video once. Ground responses register a new P label on every successful call. C2 records raw packed masks, probabilities, frozen tau and the queried V-C depth grids; replay re-lifts the masks through one shared geometry cache.

The decode adapter samples the same 51x51 V-C endpoint grid and applies the same bilinear depth interpolation as rkit. It obtains poses, gravity and FoV through `HeadState.geometry()`, which is the tower lane's interface. This lane does not modify the tower switch. Local artifacts attach through `mdg_decode_attach.attach_mdg` or the existing `mdg_eval` runtime.

The existing camera openers use atomic AddedTokens with mean-initialized input and output rows. The grounding extension appends atomic `<ground` and `<gap` tokens for MDG receipts through the same mechanism. Standalone MDG-A/T0 receipts preserve their tokenizer. Stage-B training and streaming decode gate from the atomic ground opener through the call end. TB-1 owns selective training and persistence of these two input/output rows.

## Alternatives
A click-head backend cannot supply mask extents or surface distances. Phrase embedding queries discard the MDG call-end state. Re-running the LM at dispatch would duplicate work and violate the single-prefill design. Taking separate medians in camera/f1 changes the centroid under rotation. Registering unrounded coordinates makes calculator results disagree with displayed points. The implementation avoids each of these choices.

## Validation and limits
Portable tests cover lifting, P registration, nulls, multiple objects sharing depth grids, scalar/multi-candidate gaps, displayed ties, unchanged legacy dispatch, native-cache query states, MDG export parity and atomic gate positions. A separate check compares the vendored routines against the pinned rkit references. An independent GT-scene test converts native poses to pose9, supplies a metric depth grid and compares public centres within 2 cm before checking C2.

The requested real test uses local T0 m800, MDG-A step 900 and dev scene0011_00 on CPU with eight threads. It scripts one ground call, so it measures backend plumbing rather than learned route choice. Its export comparison reuses the identical prefill with an independent native cache continuation through mdg_eval.predict. The shared mdg_stream module fixes inference to native single-token continuation and batch one per object; mdg_eval and rkit exports pin this as native_single_token_v1. Their run bindings also pin the shared module. Existing exports with a batched BF16 suffix are a different numerical protocol: the measured comparison differs at 19 mask cells while the UV points remain equal. They require regeneration for byte-equality claims. Training keeps its gradient-carrying batched suffix path. It does not establish GPU throughput or a held-out grounding score.

Status: BUILT AND CPU-VERIFIED. Portable verification passes: 45 backend/legacy/export checks; 58 checks in the combined tower tree, including the separately supplied untouched-reference test; 15 checks on the MDG-A base; exact rkit lifting and export-bridge checks. Five real GT objects select identical frames/best, with maximum public-centre error 0.00942 m and C2 byte-equal. The native-protocol T0 m800 + MDG-A step-900 dev-clip test passes: every array is exactly equal, C2 is byte-equal, runtime is 1,379.1 s, and peak CPU RSS is 42.21 GB. The armchair response is not seen; positive P registration is covered by the five real GT objects and the native tiny-C1 decoder stub. Final commands, results and patch hunks are recorded in the lane output ledger and RESULT event.

Artifacts: ground_backend/out/c1mix_sb_ground_backend.patch; c1mix_sb_ground_after_tower.patch; c1mix_mdg_export_parity.patch; rkit_native_export.patch. All apply with zero fuzz to their declared bases. Set RK_MDG_ROOT to a patched model tree. Exact hashes, hunks, commands and results are in ground_backend/out/{PATCHES.json,HUNKS.json,TEST_COMMANDS.json,RESULT.md}. Required PENDING-INPUT tests: none. Stage-B selective embedding-row training/persistence remains the TB-1 owner's integration responsibility.


## Ground backend revision 3.12.2

The backend emits `NAME: frames FRAMES (best K)` without a probability field. It injects the LF between each ground/gap call and its tool response, and uses the same layout for subsequent calculator calls. Shared lifting SHA256: `d5cbafa58ed1107ae5a2768997bd36c35c295e3f5ea7505b5c5dfe7d4c4fae2d`.
