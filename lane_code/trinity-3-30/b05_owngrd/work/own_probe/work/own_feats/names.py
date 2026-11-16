from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import torch
from .core import DEFAULT_BUNDLE, DEFAULT_T0
from provenance import sha256


@dataclass
class NameBatch:
    tokens: torch.Tensor
    mean: torch.Tensor
    mask: torch.Tensor
    token_ids: list
    rows_sha256: str
    tokenizer_sha256: str


class NameEmbedder:
    """Read only the selected frozen token rows, never the 9B language model."""
    def __init__(self, weights=DEFAULT_T0/'full_weights', tokenizer=DEFAULT_BUNDLE/'base'):
        from transformers import AutoTokenizer
        self.weights, self.tokenizer_path = Path(weights), Path(tokenizer)
        self.tokenizer = AutoTokenizer.from_pretrained(str(tokenizer),local_files_only=True)
        index = json.loads((self.weights/'model.safetensors.index.json').read_text())['weight_map']
        self.key = 'model.language_model.embed_tokens.weight'
        self.path = self.weights/index[self.key]
        self.tokenizer_sha256 = sha256(self.tokenizer_path/'tokenizer.json')
        self.cache = {}

    def __call__(self,names):
        from safetensors import safe_open
        if not names or any(not isinstance(n,str) or not n.strip() for n in names):
            raise ValueError('Names must be nonempty strings')
        ids = [self.tokenizer.encode(n,add_special_tokens=False) for n in names]
        if any(not x for x in ids): raise ValueError('Name has no tokens')
        unique = sorted({i for seq in ids for i in seq})
        with safe_open(str(self.path),framework='pt',device='cpu') as f:
            rows = f.get_slice(self.key)
            if rows.get_shape()[1] != 4096: raise ValueError('Expected 4096-d name embeddings')
            for i in unique:
                if i not in self.cache:
                    self.cache[i] = rows[i:i+1].clone()[0]
        raw_hash = hashlib.sha256()
        for i in unique:
            raw_hash.update(str(i).encode()+b'\0')
            raw_hash.update(self.cache[i].contiguous().view(torch.uint8).numpy().tobytes())
        tokens = torch.zeros(len(ids),max(map(len,ids)),4096)
        mask = torch.zeros(tokens.shape[:2],dtype=torch.bool)
        for j,seq in enumerate(ids):
            tokens[j,:len(seq)] = torch.stack([self.cache[i].float() for i in seq])
            mask[j,:len(seq)] = True
        mean = tokens.sum(1)/mask.sum(1)[:,None]
        return NameBatch(tokens,mean,mask,ids,raw_hash.hexdigest(),self.tokenizer_sha256)


_default = None


def name_embed(names):
    global _default
    if _default is None: _default = NameEmbedder()
    return _default(names)
