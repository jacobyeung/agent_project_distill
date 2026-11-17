# Build 8 decisions

- Retain input-hash-bound base receipts; rerun only groups whose inputs change. The copied test runner retains its bytes.
- Fix BF16 parity only if the computation has a defect. Otherwise retain the original failing assertion and the kit refusal.
- Skills stored outside this lane are not read: this build restricts external reads to its named files. Apply the supplied prose rules directly.

- BF16 disposition: the same BF16 tower/base passes with FP32 cache storage, while BF16 storage exceeds the original gradient tolerance (`proofs/regressions/BF16_PARITY.json`). Retain the lossy-storage blocker and the original assertion. Changing online computation or the stored representation to force this fixture through would require a separate cache design decision; this build does not enable BF16.

- Use the existing native scratch census (`R2_FAST_CENSUS=1`) during the final package suite. It measures the same files before and after each test; the test runner retains its build-7 bytes and base receipt identity. This choice changes neither test assertions nor coverage collection.

- Keep camera-row selection blocked without the exact sealed goal-scene exclusion file. Test the real pose adapter, per-row producer, C1 packer and model reader with synthetic inputs; do not replace the exclusion check. The canonical GTScene loader still binds a fixed legacy frame inventory, so its full 64-frame path remains unqualified.

- Retain the native production allocation/admission checks. The stop rehearsal executes the extracted native r.sh trap and native h.forward/i.relay chain around a two-rank CPU run_steps entry. It does not qualify the GPU admission wrapper. The sandbox refused socket creation before rank launch; no multi-rank pass is claimed.

- Frame-count shape checks validate input dimensions only. The inference selector, response computation, thresholds and fallback behavior remain unchanged. The outside-weight source inventory is supplied for the independent acceptance review.

- Packet setup options: retain broken relocated references, copy the row slices, or reference their existing lane-local source files. Default: use read-only symlinks with the existing hashes, and use a fresh pytest directory so retained process IDs cannot collide. Run the corrected packet once before package groups; retain the failed setup evidence. No assertion changes.

- The dense-pose admission predicate still binds the legacy all_frames32 contract. Options: invent a longer-clip contract, or retain the guard pending its admitted source manifest. Default: retain the guard and name FRAME64_DENSE_POSE_ADMISSION_UNQUALIFIED.
