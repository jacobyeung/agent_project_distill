"""Frozen SAM 3 text-encoder embedding of each K1 name as written (lowercase/strip only), CPU, computed once.

Embedding = mean over non-padding tokens of backbone.forward_text([name])['language_features'] (the 256-d text
memory SAM 3's grounding decoder consumes). The call hook computes the same with `sam3_name_embedding`.
"""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='8')
import sys, json, hashlib, time
sys.dont_write_bytecode = True
from pathlib import Path
import torch
torch.set_num_threads(8)
from torch.overrides import TorchFunctionMode


class _CPUOnly(TorchFunctionMode):
    # SAM 3's builder hard-codes device="cuda" in precomputed position caches; the text path never reads them.
    def __torch_function__(self, func, types, args=(), kwargs=None):
        kwargs = dict(kwargs or {})
        if 'cuda' in str(kwargs.get('device', '')):
            kwargs['device'] = 'cpu'
        args = tuple('cpu' if (isinstance(a, (str, torch.device)) and 'cuda' in str(a)) else a for a in args)
        return func(*args, **kwargs)


_CPUOnly().__enter__()
CKPT = '/scratch/jjyeung/orch_cd/ttower/work/sam3_weights/sam3.pt'
MANIFEST = '/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json'


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


@torch.inference_mode()
def sam3_name_embedding(model, name):
    out = model.backbone.forward_text([name], device='cpu')
    feats, mask = out['language_features'], out['language_mask']   # [L,1,D], [1,L] (True = padding)
    valid = ~mask[0].bool()
    return feats[valid, 0].float().mean(0), int(valid.sum()), out


def main():
    out = Path(sys.argv[1])
    t0 = time.time()
    ck = sha(CKPT)
    assert ck.startswith('9999e234'), ck
    m = json.load(open(MANIFEST))
    names = sorted({n.strip().lower() for c in m['captures'] for n in c['gt_name_ids']})
    from sam3.model_builder import build_sam3_image_model
    model = build_sam3_image_model(checkpoint_path=CKPT, load_from_HF=False, device='cpu', eval_mode=True,
                                   enable_inst_interactivity=False)
    embs, ntok = [], {}
    for i, n in enumerate(names):
        e, k, raw = sam3_name_embedding(model, n)
        if i == 0:
            print('shapes', {k2: (tuple(v.shape), str(v.dtype)) for k2, v in raw.items() if hasattr(v, 'shape')},
                  'mask', raw['language_mask'][0].tolist(), flush=True)
        embs.append(e)
        ntok[n] = k
    E = torch.stack(embs)
    from safetensors.torch import save_file
    save_file({'name_emb': E.contiguous()}, str(out / 'NAME_EMB_SAM3.safetensors'))
    meta = dict(names=names, n_valid_tokens=ntok, dim=int(E.shape[1]), checkpoint=CKPT, checkpoint_sha256=ck,
                pooling='mean of language_features over non-padding tokens (language_mask False)',
                normalization='lowercase+strip only', seconds=time.time() - t0, torch=torch.__version__)
    (out / 'NAME_EMB_SAM3.json').write_text(json.dumps(meta, indent=1) + '\n')
    print(json.dumps({k: v for k, v in meta.items() if k != 'n_valid_tokens'})[:800], flush=True)


if __name__ == '__main__':
    main()
