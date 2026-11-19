from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');p=L/'out/kit_parity50/README.md';s=p.read_text()
s=s.replace('Apply all three diffs to a fresh full copy of A4/src or B5/src.', 'Apply reader patches 01–03 to a fresh full copy of A4/src or B5/src. Apply patch 04 separately to a copy of A4/tower_sequence.py, outside src, for the A4 operator route.')
s=s.replace('Prepare approved original and extended source roots, checkpoint/export/artifact inputs, and settings under neutral staged paths.', 'Prepare approved original and extended source roots, checkpoint/export/artifact inputs, and settings under neutral staged paths. Transport each source root as one archive and extract it only on node-local disk. Keep both parity source roots pristine: no build outputs, extra files or symlinks. Build production packages in a separate source copy because the builder writes its output inside that copy.')
s=s.replace('u0.json through u3.json. The u3.json inventory binds every extension file to MANIFEST;', 'u0.json through u4.json. The u3.json inventory binds every extension file to MANIFEST. The u4.json base pin authenticates the complete non-u0 inventory of both roots against all 927 input files;')
s=s.replace('Before adoption at step 600 or later, pass the original/OFF/OFF-repeat/ON/journal/sharded GPU gates, useful-hit checks, net seconds/item checks including hashing/copying, and real persistent-storage preemption/requeue. Live weight-content hashes protect replacements and raw-storage edits, but may outweigh cache savings.', 'Before adoption at step 600 or later, pass the ORIGINAL/OFF/OFF_REPEAT/ON/journal/sharded GPU gates with every switch ON, useful-hit checks, and net seconds/item checks including hashing/copying. Require a real persistent-storage preemption/requeue before any sharded or preempt adoption. Weight guards hash at install and at type-journal entry/exit; calls check every parameter/buffer identity, pointer and version. Tracked mutations fail immediately; persistent untracked writes fail at the next boundary. A fatal mismatch rejects the run. WEIGHTS.json blocks resume, merge and comparison until a boundary validates the journal. Graceful deadlines validate before recovery; a hard kill during an unchecked type requires a fresh journal. This policy assumes frozen models: an untracked write restored before the next boundary cannot be detected. Inference tensors without counters are refused. Boundary hashes and copies still need GPU measurement.')
s=s.replace('Run it in a **full staged source tree** after applying all three diffs:', 'Run it in a **separate full build source copy** after applying reader patches 01–03:')
s=s.replace('"$SOURCE/u0/a12.py"','"$BUILD_SOURCE/u0/a12.py"').replace('"$SOURCE/b"','"$BUILD_SOURCE/b"').replace('"$SOURCE/orchard_h10/vendor"','"$BUILD_SOURCE/orchard_h10/vendor"').replace('"$SOURCE/u9"','"$BUILD_SOURCE/u9"')
s=s.replace('The output must be inside SOURCE, as the original builder requires.', 'The output must be inside BUILD_SOURCE, as the original builder requires. Do not use BUILD_SOURCE as a parity-kit source root afterward.')
pos=s.index('\n## Array generation and approval')
s=s[:pos]+'''
For the A4/B5 operator route, use A4's authenticated bootstrap (the delivered operator/0.py is byte-identical to the decoded A4 bootstrap) and the patched A4 sequence. The optional arguments below explicitly choose that route. Build the step-600 candidate as single-card caches only:

```bash
nice -n 10 "$READ_PYTHON" -I -s -B "$BUILD_SOURCE/u0/a12.py" \\
  --enable-extensions --caches-only --reader-source "$BUILD_SOURCE/b" \\
  --template-source "$BUILD_SOURCE/orchard_h10/vendor" --out "$BUILD_SOURCE/u9" \\
  --operator-bootstrap "$DELIVERY/operator/0.py" \\
  --operator-source "$DELIVERY/operator/tower_sequence.py"
```

Add `--processor-only` to enable just the processor cache; it also disables atomic journals and scene sharding. In direct settings, `read_processor_only="on"` overrides both model cache flags. Every new switch defaults OFF. Generic ON without either cache profile still enables all three caches, atomic journals and scene sharding; use that for the separate validation gates.

The A4 bootstrap routes action 0 to the pinned preparation entry and action 1 to 7.py. The sequence activates overlays in its own fresh process. Its default-OFF memory proof is unchanged; ON adds the effective read_cache_bytes allowance to host_budget_bytes. Rebuild the CPU proof, payload, plan, inputs and operator pins before launch. The proof must attest bundle_guard_passed, entry_sequence_passed and the new operator hash, with memory basis fixed_g3t_shapes and fits=true. The operator preserves A4's fixed 636-item descriptors; the owner must bind the target read's item counts/schedule and regenerate its proof when building step 600.

With atomic journals enabled for validation, the merge lands at metadata/reads/0/metadata/u0/answer_trace_return.tgz inside the outer return. The existing fetch/unpack layout therefore stays intact; unpack still authenticates operator_sha256. With --caches-only, results stay in the ordinary per-type journals and no canonical merge is requested. The CPU integration test executes real preparation/settings construction with stubbed restore/admission/weight-manifest work, then dispatches a stub model worker across all 636 A4 items. It verifies overlays, pins, counts and nested return membership in fresh action-0/action-1 processes.

No multi-card operator variant is delivered. Sharded reads require one that binds card count, per-read identities, memory and CPU proof. Step 600 uses single-card ON with caches only; the two/four-shard forecasts are conditional estimates.
''' +s[pos:]
pos=s.index('\n## Review round 2: finding -> fix -> test')
s=s[:pos]+'''
## Review round 3: finding -> fix -> test

1. Per-call weight hashing: install/boundary hashes, fatal live-identity guards and processor-only adoption; mutation, boundary, resume, public-merge and model-sized CPU timing tests.
2. Operator integration: A4 bootstrap/sequence CPU execution, fresh-process overlays, nested merge and default-OFF cache memory accounting; test_operator_round3.py.
3. Base authentication: both complete inventories match BASE_PIN.json from MANIFEST before any arm; corrupt/equal-wrong/extra-file regressions and full 927-file checks.
4. Weak tests: the identical lock regression plus the real type-deadline path fail on round-1-before a4; the worker environment regression fails on the F16 baseline and passes on the delivery.
7. OFF guard: a0–a18 are all forbidden; direct import-guard regression and original/OFF byte tests.

The earlier key, parity-schema, memory, public-boundary, atomic-journal and array-policy regressions remain in the suites and are rerun. Exact outputs and limits are in REPORT.md.
'''
p.write_text(s)
p=L/'out/FRAMEWORK_EVIDENCE.md';s=p.read_text()
s=s.replace('Keys include live tensor identity and content, so replacements and raw-storage edits invalidate entries even when a version counter does not change.', 'Calls check live tensor identities/pointers/counters; install and type-boundary hashes reject persistent raw-storage edits. A mismatch aborts the run rather than refreshing a lookup.')
s=s.replace('Keys bind live parameter/buffer identities and contents, model/configuration options, attention implementation, and backend execution settings.', 'Keys bind the guarded install-time weight hash, live parameter/buffer metadata, model/configuration options, attention implementation, and backend execution settings.')
pos=s.index('The official 2.11 Module, Tensor.to, numerical-accuracy, and increment_version pages')
s=s[:pos]+'''## Round-3 weight guards

The installed source defines counters as mutation counters, not content hashes. [TensorImpl.h:291](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/include/c10/core/TensorImpl.h:291) states that tracked in-place data or size operations increment them; views and detach share them. [TensorImpl.h:303](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/include/c10/core/TensorImpl.h:303) identifies .data and set_data as counter-sharing exceptions. [TensorImpl.h:2051](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/include/c10/core/TensorImpl.h:2051) explains that shallow_copy_from preserves the destination counter. Thus assigning weight.data to new storage need not change weight._version; its changed pointer is checked instead.

The increment itself appears at [TensorImpl.h:392](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/include/c10/core/TensorImpl.h:392), and autograd delegates to it at [VariableTypeUtils.h:159](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/include/torch/csrc/autograd/VariableTypeUtils.h:159). The installed SGD implementation updates parameters in place at [optim/sgd.py:379](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/optim/sgd.py:379); the CPU test verifies a counter increase for SGD.step with foreach=False. This is not a claim about arbitrary custom optimizer implementations.

Raw .data.add_ and NumPy storage writes can change bytes without changing the parameter's id, pointer or version. These paths retain full-content boundary guards. External/custom pointer writes require an explicit increment if callers want autograd to notice them: [autograd/graph.py:242](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/autograd/graph.py:242), also documented in the official [increment_version page](https://docs.pytorch.org/docs/2.11/generated/torch.autograd.graph.increment_version.html). Frozen model ownership remains required: a raw write followed by restoration between boundaries can escape both guards. The implementation does not claim to detect that sequence.

Inference tensors lack counters and are refused for model caching: [TensorImpl.h:413](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/include/c10/core/TensorImpl.h:413), [official inference_mode reference](https://docs.pytorch.org/docs/2.11/generated/torch.autograd.grad_mode.inference_mode.html). The processor-only profile does not install a model guard. The two official pages were read on 2026-11-19 during this round.

[checks/TORCH_VERSIONS3.json](checks/TORCH_VERSIONS3.json) records the measured operation-by-operation counter/pointer behavior and SHA256 pins of the installed source files. [checks/CACHE_COST3.json](checks/CACHE_COST3.json) records CPU overhead on two explicitly sized stubs; neither receipt measures CUDA speed or production memory.
'''
p.write_text(s)
