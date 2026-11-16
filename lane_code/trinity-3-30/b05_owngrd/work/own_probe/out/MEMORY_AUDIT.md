# G3T intermediate retention

The integration fork's full aggregator retains 24 concatenated frame/global block tensors. Its DPT heads read zero-based blocks 4, 11, 17 and 23; both camera heads read the final block. The probe reads blocks 5, 11, 17 and 23. Retaining their union with the head inputs keeps five concatenations and preserves every existing head input.

The audited source is `integ_v3/work/tree/student_pilot/g3t_vendor/vggt/models/aggregator.py`. `g3t_sparse.patch` changes only retention: unused entries become `None`, preserving list indices and all forward computation. It keeps all entries during training. `g3t_taps.py` also provides an inference-only context that applies this change to one model instance and restores its forward method afterward. No weight or state-dict key changes.

At 392×518, each frame has 28×37 spatial tokens and five special tokens. A concatenation has 2,048 channels. Dropping 19 bf16 concatenations saves the following retained tensor storage:

| Frames | Retained bytes removed | GiB removed | Measured peak before | Measured peak after |
|---|---:|---:|---|---|
| 32 | 2,592,473,088 | 2.414 | Pending weights/GPU | Pending weights/GPU |
| 64 | 5,184,946,176 | 4.829 | Pending weights/GPU | Pending weights/GPU |

These are storage calculations, not measured peak savings. Attention workspace, the patch backbone, current frame/global states and head activations still consume memory. The patch avoids redundant concatenation storage; it does not remove attention blocks or claim upstream VGGT's reported frame-capacity factor.

The existing `student_pilot/g3t_online.py::G3TEncoder._lean` path already keeps only the final camera input, plus final patch features when requested. The 24-to-five change applies to the full aggregator path. It does not promise a similar reduction for that lean path.

The tiny CPU test uses the actual vendor aggregator, both camera heads, depth head and point head with small random dimensions. Every output tensor is byte-equal with capture off, full capture, sparse capture, and the delivered static patch. Every retained map is also byte-equal. A separate test verifies spatial order and an explicit permutation into LM frame order. Block 23 and `trunk` alias the same map. `CPU_R3_FINAL.log` records both passing tests.

The separate `work/g3t_memory_smoke.py` audit performs four full forwards: 32 and 64 frames, each before and after sparse retention. It compares hashes of every head output and records CUDA peak allocated bytes and elapsed time. It repeats one admitted 32-frame training clip for the 64-frame stress test. Expected allocation: up to 18 minutes on one 48 GB card. This is O11's separate 0.3 GPU-hour allowance; schedule it after E-A unless it fits the same allocation. A failure or system kill must stop the run; the script does not retry.

The complete G3T checkpoint is not visible in this lane's private `/dev/shm`. Its required SHA256 is `d460957bb1c8a8c228d83ab10bad8a6dbcf80b03f29d7fbebf9c0f2c1c25f702`. The live audit remains pending.
