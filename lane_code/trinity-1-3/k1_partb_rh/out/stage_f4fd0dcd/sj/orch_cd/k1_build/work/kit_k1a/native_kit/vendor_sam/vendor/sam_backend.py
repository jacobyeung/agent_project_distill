import numpy as np

def make_postprocess(F, torch, FrameDetections, floor, cap):
    """sam3_tower.postprocess with the retention floor and cap as parameters (legacy path unchanged)."""
    def postprocess(outputs, size, *, legacy=False):
        h, w = size
        scores = outputs['pred_logits'].sigmoid().reshape(-1).float()
        presence = float(outputs['presence_logit_dec'].sigmoid().item())
        if not torch.isfinite(scores).all() or not 0 <= presence <= 1:
            raise ValueError('SAM produced nonfinite probabilities')
        joint = scores * presence
        order = torch.argsort(scores, descending=True, stable=True)
        keep = order[(scores if legacy else joint)[order] >= (.3 if legacy else floor)]
        n_above = int(keep.numel())
        keep = keep[:5 if legacy else cap]
        cx, cy, bw, bh = outputs['pred_boxes'].reshape(-1, 4).unbind(-1)
        boxes = torch.stack((cx - .5*bw, cy - .5*bh, cx + .5*bw, cy + .5*bh), -1).float()
        boxes *= boxes.new_tensor([w, h, w, h])
        native = outputs['pred_masks'].reshape(-1, *outputs['pred_masks'].shape[-2:])
        masks = [(F.interpolate(native[i][None, None].float(), (h, w), mode='bilinear', align_corners=False).sigmoid()[0, 0] > .5).cpu()
                 for i in keep.tolist()]
        det = FrameDetections(presence, scores[keep].cpu(), joint[keep].cpu(), boxes[keep].cpu(),
                              torch.stack(masks) if masks else torch.empty((0, h, w), dtype=torch.bool), keep.cpu(), scores.cpu())
        return det, n_above
    return postprocess

def detect_prompt(tower, features, prompt, post, map_tensors):
    """Sam3Tower._detect with the prompt used verbatim (P1 plurals must not be singularised) and the dense postprocess."""
    tower._load()
    out = []
    with tower._autocast():
        text = tower._backend.model.backbone.forward_text([prompt], device=str(tower.device))
    for stored, size in zip(features.frames, features.sizes):
        backbone = map_tensors(stored, lambda t: t.to(tower.device))
        backbone['vision_features'] = backbone['backbone_fpn'][-1]
        backbone.update(text)
        with tower._autocast():
            raw = tower._backend.model.forward_grounding(backbone_out=backbone, find_input=tower._backend.find_stage,
                                                         geometric_prompt=tower._backend.model._get_dummy_prompt(), find_target=None)
            out.append(post(raw, size))
        del raw, backbone
    return out

def prediction(det, n_above, prompt, rle_encode):
    inst = [dict(query=int(q), score=float(s), joint_score=float(j), box=b.tolist(), mask=rle_encode(m.numpy()))
            for q, s, j, b, m in zip(det.query_ids, det.scores, det.joint_scores, det.boxes, det.masks)]
    return dict(presence=det.presence, all_instance_scores=det.all_scores.tolist(), instances=inst,
                joint_score=float(det.joint_scores[0]) if inst else -1., prompt=prompt, n_above_floor=n_above)

def rle_encode(mask):
    a = np.asarray(mask, dtype=np.uint8).ravel(order='F')
    counts = np.diff(np.r_[0, np.flatnonzero(np.diff(a)) + 1, a.size]).tolist()
    if a.size and a[0]:
        counts.insert(0, 0)
    return {'size': list(mask.shape), 'counts': counts}
