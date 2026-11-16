# Trinity read runtime for the step-544 lineage (lane trin_read, trinity-1-3)

**Question.** Can the accepted dev-S1 direct reader (Orchard job 169526, packet e193c2a3c) run on one Trinity 48 GB card with the accepted runtime, and how closely does it reproduce the accepted 20-item proof set?

**Answer (in progress, 2026-11-16 04:30Z).** The accepted vLLM 0.32.0 env runs on Trinity's userland only with one load-time overlay: llguidance's native library needs glibc 2.30 and Trinity has 2.28. With a stub bound over that package inside bwrap, the full vLLM engine import path loads (CPU probe). No card read yet; the base (19.3 GB) and runtime_0/2 still wait in the IO governor.

**Approach.** Rebuild on Trinity the root layout that the reviewed Orchard kit (f42aa1a4) stages, from the same bytes: runtime_0/1/2 (vLLM 0.32.0 env, p1cpu env, reader code), camera package, bwrap, base snapshot f3069074 and the step-544 export; run the unchanged Phase-B path (proof/phase_b.py -> direct.bind/launch) under the same bwrap binds. Frames come from a local k6tk-format store of frames pulled from Orchard, bound at the Orchard store path, so pull.py and phase_b.py stay unchanged.

**Evidence so far.**
- Export: tar-piped over IB from trinity-1-18 in 67 s; stream sha 3ed73aea... equals the accepted archive; artifact.json 1d6eeb28...
- Accepted vLLM = 0.32.0 (engine log of 169526; aws_vl64rt/BUILD_NOTES.md). camera 9eb53a96 and bwrap e3189038 match ORCHARD_ASSETS.json.

- runtime_1 staged and verified (sha 56c7705a): vLLM 0.32.0, torch 2.13.0+cu130, transformers 5.19.0, triton 3.7.1, flashinfer 0.7.0.post1. Driver 595.71 / CUDA 13.2 suits cu130.
- glibc scan of the env's 350 shared objects: only llguidance/_lib.abi3.so (GLIBC_2.30) and cryptography (2.34) exceed 2.28. vllm/v1/request.py imports structured_output/backend_guidance.py, whose dataclass annotations load llguidance at import time, so the engine cannot import without a fix. cryptography is not loaded on the engine path.
- The pinned Orchard bwrap needs glibc 2.38, so the runner executes host /usr/bin/bwrap 0.4.0 (all emitted flags accepted; loopback comes up under --unshare-net).

**Options rejected.**
- Ubuntu 24.04 userland inside bwrap (keeps every Python byte): Triton compiles its launcher stub with the system C compiler at runtime and ubuntu-base has none; the host has gcc 8.5.
- A glibc-2.28 llguidance 1.7.6 wheel: PyPI has only manylinux_2_31 for cp39-abi3 x86_64.
- trinity-1-18 /scratch/jjyeung/envs/vllm: vLLM 0.23.0, torch 2.11.0, transformers 5.12.1; vLLM differs from the accepted 0.32.0.
- trinity-1-13 native_r2/work/base: the 9 non-weight files of Qwen3.5-9B c2022362 only (sha equal to manifest ae9247f7); c1_export reads base safetensors, so it is not enough.
- Whole k6tk store (78 GB, 290,880 frames): too large; pull per item set instead.

**What might not work.** bf16 kernels differ between H100 and Ada, so greedy token sequences can diverge after the first differing argmax; the H100 card check, Slurm token, item filter and llguidance stub are beyond paths/env and need one review; the stub raises on any guidance call, so a structured-output request would fail loudly; vLLM memory settings tuned for 80 GB may not fit 48 GB; all eight trinity-1-3 cards are taken by another user.

**Tests that settle it.** 20-item proof on one Ada card: share of identical token sequences, first divergence index, score equality per arm, tok/s, s/item, peak memory.

- Governed pulls must keep the registered root process's command name: a root that execs another program after its first SIGCONT fails the governor's identity check at its next admission (runtime_0, 06:10Z). The launcher's root now runs the reader as a child (`kill -STOP $$; timeout ... ; exit $?`).
- Cards: trinity-0-13 is unusable for this kit at 226 GB free (the kit keeps 200 GiB free after a ~40 GB per-run model copy); trinity-1-18 card 4 was free with 909 GB.

