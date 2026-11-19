# Track blocker

CPU predictor loading is unconfirmed: `ModuleNotFoundError: No module named 'pkg_resources'`.
Source: `/scratch/jjyeung/orch_cd/mdg_next/work/data/sam3src/sam3/model_builder.py`; video predictor factory exists: True.
Weights: `/scratch/jjyeung/orch_cd/ttower/work/sam3_weights/sam3.pt`.
SHA256: `9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e`.
The staged predictor calls `.cuda()` unconditionally; its multi-GPU wrapper also selects a CUDA device.
Command: `bash scripts/track_cpu.sh`. Exact traceback and source line evidence: `TRACK_CPU_CHECK.json`.
No download, GPU execution, or CUDA compatibility monkeypatch was attempted.
