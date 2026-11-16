"""Determinism check: refit the chosen config of HEAD_DIR on all train groups and write OUT_DIR (same format)."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch
from safetensors.torch import save_file
import common as C, train_selector as T
from selector_head import file_sha256
torch.set_num_threads(1); torch.use_deterministic_algorithms(True)
src, out = C.Path(sys.argv[1]), C.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
meta = json.loads((src / 'selector_head.json').read_text())
cfg = json.loads(meta['chosen'])
gs = T.groups(C.load(splits=('train',)), T.names_table())
head = T.fit(gs, cfg)
save_file({k: v.contiguous() for k, v in head.state_dict().items()}, str(out / 'selector_head.safetensors'))
w = file_sha256(out / 'selector_head.safetensors')
(out / 'selector_head.json').write_text(json.dumps(dict(meta, weights_sha256=w, retrain_of=str(src)), indent=1) + '\n')
print(w, w == meta['weights_sha256'])
