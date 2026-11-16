"""CPU stand-in for SAM 3's processor and model (path test only): deterministic proposals from the image and the
prompt, through the real Sam3Tower.encode / postprocess code paths. Never used for any reported number."""
import hashlib

import numpy as np
import torch
import torch.nn.functional as F

Q = 200


def seed(*parts):
    return int(hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()[:8], 16)


class Text(torch.nn.Module):
    def forward_text(self, phrases, device='cpu'):
        return {'language_features': torch.tensor([[seed(phrases[0]) % 9973 / 9973.]], device=device)}


class Model(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = Text()
        self.lin = torch.nn.Linear(1, 1)

    def _get_dummy_prompt(self):
        return None

    def forward_grounding(self, backbone_out, find_input, geometric_prompt, find_target):
        img = backbone_out['vision_features']
        key = round(float(img.sum()), 3), round(float(backbone_out['language_features'].sum()), 6)
        g = torch.Generator().manual_seed(seed(*key))
        logits = torch.randn(1, Q, 1, generator=g)*2 - 2.5
        c = torch.rand(Q, 2, generator=g)*torch.tensor([36., 48.])
        r = torch.rand(Q, 1, 1, generator=g)*8 + 2
        yy, xx = torch.meshgrid(torch.arange(36.), torch.arange(48.), indexing='ij')
        masks = (r - ((yy[None]-c[:, 0, None, None])**2 + (xx[None]-c[:, 1, None, None])**2).sqrt())[None]
        boxes = torch.rand(1, Q, 4, generator=g)*.5 + .25
        return {'pred_logits': logits, 'presence_logit_dec': torch.randn(1, 1, generator=g)+1.,
                'pred_boxes': boxes, 'pred_masks': masks}


class StubBackend:
    def __init__(self):
        self.model = Model()
        self.find_stage = None

    def set_image(self, image):
        a = torch.from_numpy(np.asarray(image.resize((48, 36)), dtype=np.float32)/255.).permute(2, 0, 1)[None]
        fpn = [a, F.avg_pool2d(a, 2), F.avg_pool2d(a, 4)]
        return {'backbone_out': {'backbone_fpn': fpn, 'vision_pos_enc': [torch.zeros_like(t) for t in fpn]}}
