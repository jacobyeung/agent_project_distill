#!/usr/bin/env bash
# Run inside the actual production venv, AFTER the FLA overlay, with CUDA visible.
# This script imports libraries; it does not instantiate a model or train.
set -euo pipefail
date -u
"${PYTHON:-python}" -c 'import importlib.util as u, torch, transformers; from transformers.models.qwen3_5 import modeling_qwen3_5 as m; from transformers.utils.import_utils import is_flash_linear_attention_available as f, is_causal_conv1d_available as c; print({"torch":torch.__version__,"transformers":transformers.__version__,"cuda_available":torch.cuda.is_available(),"modeling_file":m.__file__,"fla_spec":str(u.find_spec("fla")),"causal_spec":str(u.find_spec("causal_conv1d")),"fla_accepted":f(),"causal_accepted":c(),"fast_path":m.is_fast_path_available,"bindings":{k:None if (v:=getattr(m,k)) is None else v.__module__+"."+v.__name__ for k in ("causal_conv1d_fn","causal_conv1d_update","chunk_gated_delta_rule","fused_recurrent_gated_delta_rule","FusedRMSNormGated")}})'
