# Framework behavior used by local checks

The installed CPU package reports torch 2.11.0+cpu at `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/version.py:4`; line 7 records git version `70d99e998b4955e0049d13a98d77ae1b14db1f45`.

The wrapper sets eight CPU intraop threads before native tensor work. The installed definition documents this behavior at `torch/_torch_docs.py:9815` and the requirement to call it before eager/JIT/autograd work at line 9823. Official documentation: https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html.

The native selector rehearsal creates a tensor of scores and zero-valued input, then asserts the selected index. It relies on `torch.tensor` copying supplied values (`torch/_torch_docs.py:9231`), `torch.zeros` returning zeros of the requested shape (`torch/_torch_docs.py:12145`), and `torch.argmax` returning the index of the maximum (`torch/_torch_docs.py:6787`; ties use the first maximum at line 6796). Official documentation: https://docs.pytorch.org/docs/2.11/generated/torch.tensor.html, https://docs.pytorch.org/docs/2.11/generated/torch.zeros.html, https://docs.pytorch.org/docs/2.11/generated/torch.argmax.html.

The native selector uses `no_grad` during selection. Its installed implementation documents disabling gradient calculation, its thread-local scope and decorator use at `torch/autograd/grad_mode.py:21`–37. Official documentation: https://docs.pytorch.org/docs/2.11/generated/torch.no_grad.html. These CPU stub checks establish packaging and selector plumbing; they do not measure GPU execution or production memory use.

All relative torch paths above are under `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/`. The parent reviewer read these exact installed lines and checked the versioned official documentation during this task; no package was downloaded or installed.
