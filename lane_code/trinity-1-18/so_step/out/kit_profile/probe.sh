#!/usr/bin/env bash
# Same production venv and overlay, with CUDA visible; no model construction.
set -euo pipefail
date -u
KIT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
nice -n 10 "${PYTHON:-python}" -c 'import hashlib, torch; from transformers.models.qwen3_5 import modeling_qwen3_5 as m; from transformers.utils.import_utils import is_flash_linear_attention_available as f, is_causal_conv1d_available as c; h=lambda x:hashlib.sha256(str(x).encode()).hexdigest(); print({"torch":torch.__version__,"cuda_available":torch.cuda.is_available(),"source_sha256":h(m.__file__),"linear_kernel_accepted":f(),"conv_kernel_accepted":c(),"fast_path":m.is_fast_path_available,"bindings":{str(i):None if (v:=getattr(m,k)) is None else h(v.__module__+"."+v.__name__) for i,k in enumerate(("causal_conv1d_fn","causal_conv1d_update","chunk_gated_delta_rule","fused_recurrent_gated_delta_rule","FusedRMSNormGated"))}})' 2>&1 | "${PYTHON:-python}" "$KIT/privacy.py"
