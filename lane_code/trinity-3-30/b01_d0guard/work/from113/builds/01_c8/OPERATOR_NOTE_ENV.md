# Operator note (trinity-1-13): Python environment
The /scratch/jjyeung/envs/vllm link points into /dev/shm, which your sandbox cannot see. Use instead:
`/scratch/jjyeung/orch_n30/native_r2/env312/bin/python3.12 -I -s -B` (same Python 3.12, torch 2.11.0+cu130, transformers 5.12.1, numpy 2.3.5; vllm/flashinfer/triton removed).
Checked: `import torch,transformers,PIL,numpy,tokenizers` works there. Production numpy 2.2.6/scipy arrive in obj/np226_5204b3a0.tar.
