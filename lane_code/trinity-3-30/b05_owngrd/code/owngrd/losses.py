"""Hungarian instance supervision, identity contrast, and candidate selection losses."""
import torch
from torch.nn import functional as F
from scipy.optimize import linear_sum_assignment


def focal(logits, targets, gamma=2., alpha=.25):
    probability = logits.sigmoid()
    pt = probability*targets + (1-probability)*(1-targets)
    at = alpha*targets + (1-alpha)*(1-targets)
    return F.binary_cross_entropy_with_logits(logits, targets, reduction='none') * (1-pt).pow(gamma) * at


def at_points(masks, points, mode='bilinear'):
    return F.grid_sample(masks[:, None], points[:, :, None]*2-1, mode=mode, align_corners=False)[:, 0, :, 0]


@torch.no_grad()
def sample_points(logits, count, oversample=3., importance=.75):
    batch = len(logits)
    pool = torch.rand(batch, int(count*oversample), 2, device=logits.device)
    k = int(count*importance)
    indices = (-at_points(logits, pool).abs()).topk(k, dim=1).indices
    chosen = pool.gather(1, indices[..., None].expand(-1, -1, 2))
    return torch.cat((chosen, torch.rand(batch, count-k, 2, device=logits.device)), 1)


def mask_iou(a, b):
    a, b = a > .5, b > .5
    return (a & b).sum((-1, -2)).float() / (a | b).sum((-1, -2)).clamp_min(1)


def mask_box(mask):
    y, x = (mask > .5).nonzero(as_tuple=True)
    if not len(x):
        return mask.new_zeros(4)
    h, w = mask.shape
    x0, x1, y0, y1 = x.min()/w, (x.max()+1)/w, y.min()/h, (y.max()+1)/h
    return torch.stack(((x0+x1)/2, (y0+y1)/2, x1-x0, y1-y0))


def corners(box):
    return torch.cat((box[..., :2]-box[..., 2:]/2, box[..., :2]+box[..., 2:]/2), -1)


def giou(a, b):
    a, b = corners(a), corners(b)
    intersect = (torch.minimum(a[..., 2:], b[..., 2:])-torch.maximum(a[..., :2], b[..., :2])).clamp_min(0).prod(-1)
    union = (a[..., 2:]-a[..., :2]).clamp_min(0).prod(-1) + (b[..., 2:]-b[..., :2]).clamp_min(0).prod(-1)-intersect
    enclosing = (torch.maximum(a[..., 2:], b[..., 2:])-torch.minimum(a[..., :2], b[..., :2])).clamp_min(0).prod(-1)
    return intersect/union.clamp_min(1e-8) - (enclosing-union)/enclosing.clamp_min(1e-8)


@torch.no_grad()
def match_queries(masks, match_logits, boxes, targets, points=12544):
    if not targets:
        return [], []
    truth = torch.stack([t['mask'].to(masks) for t in targets])
    coordinates = torch.rand(1, points, 2, device=masks.device)
    pred = at_points(masks, coordinates.expand(len(masks), -1, -1))
    gt = at_points(truth, coordinates.expand(len(truth), -1, -1), 'nearest')
    prob = pred.sigmoid()
    pos, neg = focal(pred, torch.ones_like(pred)), focal(pred, torch.zeros_like(pred))
    cost = 2*(pos @ gt.T + neg @ (1-gt).T)/points
    cost += .5*(1-(2*prob @ gt.T+1)/(prob.sum(-1)[:, None]+gt.sum(-1)[None]+1))
    target_boxes = torch.stack([mask_box(m) for m in truth])
    cost += torch.cdist(boxes.float(), target_boxes.float(), p=1)
    cost += 1-giou(boxes[:, None], target_boxes[None])
    cost -= match_logits.sigmoid()[:, None]
    weights = masks.new_tensor([t['weight'] for t in targets])
    q, t = linear_sum_assignment((cost*weights[None]).float().cpu().numpy())
    return q.tolist(), t.tolist()


def selection_target(candidates, predicted_masks, target):
    """Return (class, reason), with none at len(candidates); ambiguity never trains selection."""
    ids = target['gt_instances']
    if len(ids) > 1:
        return None, 'multiple_instances'
    if target['clip_presence'] == 0:
        return len(candidates), 'absent'
    if len(ids) != 1:
        return None, 'unknown'
    best, best_iou = None, .5
    for k, candidate in enumerate(candidates):
        for f, member in candidate['members']:
            truth = target['decoder'][f]['gt_masks'].get(ids[0])
            if truth is None:
                continue
            mask = predicted_masks[f, member].sigmoid() if candidate['source'] == 'decoder' else member.to(predicted_masks)
            overlap = float(mask_iou(mask.detach(), truth.to(mask)))
            if overlap >= best_iou:
                best, best_iou = k, overlap
    return (best, 'covered') if best is not None else (None, 'uncovered_positive')


def supervised_contrastive(embeddings, ids, frames, weights, temperature, zero):
    if len(embeddings) < 2:
        return zero
    x = torch.stack(embeddings)
    similarity = x @ x.T / temperature
    count = len(x)
    eye = torch.eye(count, device=x.device, dtype=torch.bool)
    same = torch.tensor([[i == j for j in ids] for i in ids], device=x.device)
    cross_frame = torch.tensor([[i != j for j in frames] for i in frames], device=x.device)
    positive = same & cross_frame & ~eye
    valid = positive.any(-1)
    if not valid.any():
        return zero
    # Same-frame copies of an instance are neither positives nor negatives.
    denominator = ~eye & (~same | cross_frame)
    similarity, denominator, positive = similarity[valid], denominator[valid], positive[valid]
    log_prob = similarity - similarity.masked_fill(~denominator, -torch.inf).logsumexp(-1, keepdim=True)
    loss = -(log_prob.masked_fill(~positive, 0).sum(-1)/positive.sum(-1).clamp_min(1))
    return (loss*x.new_tensor(weights)[valid]).mean()


def fp32_tree(value):
    if isinstance(value, torch.Tensor):
        return value.float() if value.is_floating_point() else value
    if isinstance(value, dict):
        return {k: fp32_tree(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(fp32_tree(v) for v in value)
    return value


NO_PRESENCE = {'disputed_absent', 'miss', 'sliver', 'invalid_frame'}


def distill_presence(row, role):
    return row.get('why') in ('uncertain_absent', 'not_annotatable') or (
        role in ('confuser', 'absent') and row.get('why') == 'absent')


def compute_losses(out, targets, cfg):
    # Keep every loss and its floating inputs in fp32, including under an outer autocast.
    with torch.autocast(device_type=out['masks'].device.type, enabled=False), torch.autocast('cuda', enabled=False):
        return _compute_losses(fp32_tree(out), fp32_tree(targets), cfg)


def _compute_losses(out, targets, cfg):
    """targets contains one name record per output name; all frame indices are clip positions."""
    if len(targets) != len(out['masks']):
        raise ValueError('One target record required per name')
    zero = out['masks'].sum()*0 + out['presence'].sum()*0
    parts = {key: [] for key in cfg.weights}
    identity, identity_ids, identity_frames, identity_weights = [], [], [], []
    matches, skipped = [], {}
    for n, target in enumerate(targets):
        name_matches = []
        rows = target['frames']
        if len(rows) != out['presence'].shape[1] or len(target['decoder']) != out['masks'].shape[1]:
            raise ValueError('Targets do not match clip or decoder frame counts')
        valid = [i for i, r in enumerate(rows) if r['presence'] is not None and r.get('why') not in NO_PRESENCE]
        if valid:
            label = out['presence'].new_tensor([rows[i]['presence'] for i in valid])
            parts['presence'].append(F.binary_cross_entropy_with_logits(out['presence'][n, valid], label))
        if target['clip_presence'] is not None:
            parts['clip'].append(F.binary_cross_entropy_with_logits(out['clip'][n], out['clip'].new_tensor(float(target['clip_presence']))))
        distill = [i for i, r in enumerate(rows) if distill_presence(r, target['role'])]
        if distill:
            label = out['presence'].new_tensor([rows[i]['teacher_presence'] for i in distill])
            parts['distill'].append(F.binary_cross_entropy_with_logits(out['presence'][n, distill], label))
        for f, frame in enumerate(target['decoder']):
            row = rows[int(out['frame_ids'][f])]
            masks, logits, boxes = out['masks'][n, f], out['match'][n, f], out['boxes'][n, f]
            truth = [t for t in frame['targets'] if (t['mask'] > .5).any()]
            qi, ti = match_queries(masks, logits, boxes, truth, cfg.points)
            name_matches.append([(q, truth[t]) for q, t in zip(qi, ti)])
            match_target, match_weight = torch.zeros_like(logits), torch.ones_like(logits)
            match_target[qi] = 1
            for q, t in zip(qi, ti):
                match_weight[q] = truth[t]['weight']
            for hard in frame['hardneg']:
                if hard.get('selection_only'):
                    continue
                overlaps = mask_iou(masks.detach().sigmoid(), hard['mask'].to(masks)) > .5
                overlaps[qi] = False
                match_weight[overlaps] = hard['weight']
                for q in overlaps.nonzero().flatten().tolist():
                    identity.append(out['identity'][n, f, q])
                    identity_ids.append(hard['instance'])
                    identity_frames.append(int(out['frame_ids'][f]))
                    identity_weights.append(hard['weight'])
            ignored = [p for p in frame.get('proposals', []) if p.get('cls') == 'DISPUTED']
            ignored += [p for p in frame['hardneg'] if p.get('selection_only')]
            for proposal in ignored:
                overlaps = mask_iou(masks.detach().sigmoid(), proposal['mask'].to(masks)) > .5
                match_weight[overlaps] = 0
            parts['match'].append((focal(logits, match_target)*match_weight).mean())
            if row['presence'] is not None and row.get('why') not in NO_PRESENCE:
                parts['presence'].append(F.binary_cross_entropy_with_logits(out['decoder_presence'][n, f],
                    logits.new_tensor(float(row['presence']))))
            if distill_presence(row, target['role']):
                parts['distill'].append(F.binary_cross_entropy_with_logits(out['decoder_presence'][n, f],
                    logits.new_tensor(row['teacher_presence'])))
            for soft in frame['soft'] if distill_presence(row, target['role']) else []:
                overlaps = mask_iou(masks.detach().sigmoid(), soft['mask'].to(masks))
                q = int(overlaps.argmax())
                log_joint = F.logsigmoid(out['decoder_presence'][n, f]) + F.logsigmoid(logits[q])
                log_absent = torch.log1p(-log_joint.exp().clamp(max=1-1e-6))
                label = logits.new_tensor(soft['joint'])
                parts['distill'].append(-label*log_joint - (1-label)*log_absent)
            if qi:
                pred = masks[qi]
                gt = torch.stack([truth[t]['mask'].to(masks) for t in ti])
                weight = masks.new_tensor([truth[t]['weight'] for t in ti])
                points = sample_points(pred.detach(), cfg.points, cfg.oversample, cfg.importance)
                pred_points, gt_points = at_points(pred, points), at_points(gt, points, 'nearest')
                probability = pred_points.sigmoid()
                parts['mask_focal'].append((focal(pred_points, gt_points).mean(-1)*weight).mean())
                dice = 1-(2*(probability*gt_points).sum(-1)+1)/(probability.sum(-1)+gt_points.sum(-1)+1)
                parts['mask_dice'].append((dice*weight).mean())
                target_boxes = torch.stack([mask_box(m) for m in gt])
                parts['box_l1'].append(((boxes[qi]-target_boxes).abs().sum(-1)*weight).mean())
                parts['box_giou'].append(((1-giou(boxes[qi], target_boxes))*weight).mean())
                target_iou = mask_iou(pred.detach().sigmoid(), gt)
                parts['iou'].append(((out['iou'][n, f, qi]-target_iou).square()*weight).mean())
                for q, t in zip(qi, ti):
                    identity.append(out['identity'][n, f, q])
                    identity_ids.append(truth[t]['instance'])
                    identity_frames.append(int(out['frame_ids'][f]))
                    identity_weights.append(truth[t]['weight'])
        matches.append(name_matches)
        candidates = out['selection_candidates'][n] if 'selection_candidates' in out else [
            dict(source='decoder', members=c, weight=1., native=False) for c in out['candidates'][n]]
        selected, reason = selection_target(candidates, out['masks'][n], target)
        if selected is None:
            skipped[reason] = skipped.get(reason, 0)+1
        else:
            logits = out['selection'][n].float()
            weights = logits.new_tensor([c.get('weight', 1.) for c in candidates] + [1.])
            logits = logits.detach() + weights*(logits-logits.detach())
            distribution = torch.zeros_like(logits)
            distribution[selected] = 1
            native = [i for i, c in enumerate(candidates) if c.get('native')]
            if native and reason != 'absent':
                distribution *= 1-cfg.selection_smoothing
                distribution[native] += cfg.selection_smoothing/len(native)
            parts['selection'].append(-(distribution*logits.log_softmax(-1)).sum())
    parts['identity'].append(supervised_contrastive(identity, identity_ids, identity_frames, identity_weights,
                                                   cfg.identity_temperature, zero))
    result = {k: torch.stack(v).mean() if v else zero for k, v in parts.items()}
    result['total'] = sum(cfg.weights[k]*v for k, v in result.items())
    return result, dict(matches=matches, selection_skipped=skipped)
