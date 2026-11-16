"""Which tensor is hidden_states[-1] for Qwen3.5 in this transformers? Compares it with last_hidden_state (post final
norm) and with the last decoder layer's raw output. Also reports whether the gated-delta fast path is available."""
import sys, torch
from transformers import Qwen3_5ForConditionalGeneration
import transformers.models.qwen3_5.modeling_qwen3_5 as Q
m = Qwen3_5ForConditionalGeneration.from_pretrained(sys.argv[1], torch_dtype=torch.float32).eval()
lm = m.model.language_model
raw = {}
lm.layers[-1].register_forward_hook(lambda mod, i, o: raw.setdefault("last", o[0] if isinstance(o, tuple) else o))
ids = torch.randint(0, 1000, (1, 12))
with torch.no_grad():
    out = m(input_ids=ids, output_hidden_states=True, return_dict=True)
    lh = lm(input_ids=ids).last_hidden_state
h = out.hidden_states
print("n hidden_states", len(h), "| layers", len(lm.layers))
print("hidden_states[-1] == post-norm last_hidden_state:", torch.allclose(h[-1], lh, atol=1e-5),
      "| == raw last-layer output:", torch.allclose(h[-1], raw["last"], atol=1e-5))
print("fast path available:", getattr(Q, "is_fast_path_available", "n/a"))
