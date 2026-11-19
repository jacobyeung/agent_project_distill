# Framework evidence

The wrapper uses the Python standard library. Native operator rehearsal uses the installed CPU torch package and tiny stubs; it does not restore weights or establish CUDA behavior.

| Behavior used by a local test | Installed torch 2.11 source | Official 2.11 documentation |
|---|---|---|
| Limit CPU intra-op threads before tensor operations | `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/_torch_docs.py:9815`, warning at 9822; signature `_C/__init__.pyi:1238` | [set_num_threads](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html) |
| Create the tiny selector-logit tensor from `[1., 2., 100.]` in the native rehearsal | Same `_torch_docs.py:9231` | [tensor](https://docs.pytorch.org/docs/2.11/generated/torch.tensor.html) |
| Create the native rehearsal's two-candidate zero feature matrix | Same `_torch_docs.py:12145` | [zeros](https://docs.pytorch.org/docs/2.11/generated/torch.zeros.html) |
| Return the index of the largest candidate logit; the native selector excludes the final null logit under its selected rule | Same `_torch_docs.py:6787`; application code in payload `b/e2e_reader/stage1.py:150` | [argmax](https://docs.pytorch.org/docs/2.11/generated/torch.argmax.html) |
| Run the native selector's `no_grad` decorator without recording gradients | `torch/autograd/grad_mode.py:21`, context entry at 80 | [no_grad](https://docs.pytorch.org/docs/2.11/generated/torch.no_grad.html) |

These installed source ranges and the linked versioned documentation were read during this task. No claim about CUDA 12.9, H100 kernels, allocator peaks, multi-rank training, or real model inference rests on this CPU test. Memory numbers in native `memory_bound()` results are source-derived bounds, not measured memory use.
