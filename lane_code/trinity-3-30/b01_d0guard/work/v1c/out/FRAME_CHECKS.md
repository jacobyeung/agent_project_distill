Full adaptation passed on 311 scenes, 450 items and 9,952 PNGs. The adapter checked every selection and PNG SHA, preserved the fixed canary, and matched V1b's capture manifests and item order. Evidence: `out/FULL_ADAPT.json` and `work/input_full/BOUND.json`.

The own selected-frame list is absent from `/scratch/jjyeung/orch_n30/native_r4/in/vsti/`, including its subdirectories. `out/INDEX_CHECK.json` therefore records a pending comparison across the 311 scenes. The review's reported 309 matching scenes is not claimed as a measurement by this build.

After the operator stages `agent/selected_frames_vstibench.json` at the path below, run the comparison without copying frame pixels again:

```bash
cd /scratch/jjyeung/orch_n30/native_r4/builds/03_vsti_c
./work/py code/indices.py --items /scratch/jjyeung/orch_n30/native_r4/in/vsti/vstibench_repr_450_v3.json --media /scratch/jjyeung/orch_n30/native_r4/in/vsti/media.json --frames /scratch/jjyeung/orch_n30/native_r4/in/vsti/frames --selected /scratch/jjyeung/orch_n30/native_r4/in/vsti/selected_frames_vstibench.json --out out/INDEX_CHECK.json
```

The reference maps scene names to 32 index values, either directly or under `frame_indices`. Every differing slot records its one-based slot number and both zero-based video ordinals. The adapter also accepts `--selected-frames` and binds the comparison receipt into its inputs. Supply that option during a fresh adaptation if the comparison must travel in the bound read; existing receipts remain unchanged.

The five release videos were checked with av 17.1. `out/RELEASE_CHECK.json` records matching full frame counts for every scene and 0/160 byte-identical selected frames. Per-scene mean absolute differences across selected frames are about 1.53–2.58 pixel levels; per-frame maxima reach 75. These are pixel differences, not a claim about their effect on answers. The reproducible command is:

```bash
./work/py code/pixels.py --videos /scratch/jjyeung/orch_n30/native_r4/in/vsti/release5 --frames /scratch/jjyeung/orch_n30/native_r4/in/vsti/frames --media /scratch/jjyeung/orch_n30/native_r4/in/vsti/media.json --pins /scratch/jjyeung/orch_n30/native_r4/work/orchard_small/videos.json --out out/RELEASE_CHECK.json
```

The check verifies SHA pins, av 17.1, full decoded frame count, selected pixels, fps and per-frame differences. A mismatched full frame count now fails even when every selected index exists. Synthetic tests also cover exact pixels, changed pixels and a rejected full frame count. The real check establishes the differences recorded above.
