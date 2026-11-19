import math
import random
from contextlib import nullcontext

import torch
import torch.nn.functional as F

from .ddp_config import SEGMENT_LOSS_REDUCTION

# Token IDs of </think> (Qwen3.5-9B: 248069, OneThinker-8B: 151668) and of "\n" and "\n\n" (198, 271).
THINK_END_TOKEN_IDS = (248069, 151668)
NEWLINE_TOKEN_IDS = (198, 271)
TRACE_LOSS_WEIGHT = 0.5

# Auxiliary targets aligned with the token axis, or with a variable query axis, and their pad values.
SEQUENCE_AUXILIARY = {"aux_category_tokens": False}
QUERY_AUXILIARY = {"aux_reason_pos": -1, "aux_reason_kind": -1, "aux_reason_value": 0.0, "aux_reason_span": 0}
CAMERA_GROUP_AUXILIARY = {"aux_camera_positions": -1, "aux_camera_target": 0.0, "aux_camera_mask": False,
                          "aux_point_depth_uv": 0.0, "aux_point_depth_gt": 0.0, "aux_point_depth_mask": False,
                          "aux_g3t_cam_tokens": 0.0, "aux_g3t_pose_9d": 0.0}
AUXILIARY = ({"aux_pose", "aux_pose_mask", "aux_depth", "aux_depth_mask", "aux_group_count", "aux_group_count_mask",
              "aux_scene_count", "aux_scene_count_mask", "aux_object", "aux_object_mask", "aux_group_times",
              "aux_camera_positions", "aux_camera_target", "aux_camera_mask", "aux_camera_scale", "aux_lm_weight",
              "aux_gravity_target", "aux_gravity_mask",
              "aux_point_depth_uv", "aux_point_depth_gt", "aux_point_depth_mask",
              "aux_g3t_cam_tokens", "aux_g3t_pose_9d", "aux_g3t_gravity_up", "aux_g3t_step_scale"}
             | SEQUENCE_AUXILIARY.keys() | QUERY_AUXILIARY.keys())


def pad_last(tensor, length, fill):
    return torch.cat((tensor, tensor.new_full((*tensor.shape[:-1], length - tensor.shape[-1]), fill)), dim=-1)


def epoch_order(row_count, epoch, seed=17, pose_only=None):
    """The epoch's row order. Question rows follow random.Random(seed + epoch).shuffle over the question rows alone, so a
    run that adds pose-only rows (Cambrian-P's beta = 1 samples) sees its question rows in exactly the order of the same
    question rows without them. The pose-only rows, shuffled, take uniformly drawn slots of the merged order (a separate
    seeded generator). Without pose-only rows the order is the plain shuffle of every row, as before."""
    if pose_only is not None and (len(pose_only) != row_count or any(type(flag) is not bool for flag in pose_only)):
        raise ValueError("pose_only must flag every row with a bool")
    if pose_only is None or not any(pose_only):
        order = list(range(row_count))
        random.Random(seed + epoch).shuffle(order)
        return order
    questions = [index for index, flag in enumerate(pose_only) if not flag]
    poses = [index for index, flag in enumerate(pose_only) if flag]
    if not questions:
        raise ValueError("Pose-only rows need question rows to interleave with")
    permutation = list(range(len(questions)))
    random.Random(seed + epoch).shuffle(permutation)
    question_order = iter([questions[index] for index in permutation])
    slots_rng = random.Random(f"pose-only-slots {seed} {epoch}")
    slots_rng.shuffle(poses)
    slots = set(slots_rng.sample(range(row_count), len(poses)))
    pose_order = iter(poses)
    return [next(pose_order) if position in slots else next(question_order) for position in range(row_count)]


def question_order(qids, epoch, seed=17, pose_only=None):
    """The question rows' qids in the epoch's order, pose-only rows removed."""
    return [qids[index] for index in epoch_order(len(qids), epoch, seed, pose_only) if not (pose_only and pose_only[index])]


def global_batches(row_count, epoch, batch_size=32, seed=17, pose_only=None):
    if type(row_count) is not int or row_count < 1 or batch_size < 1 or epoch < 0:
        raise ValueError("Training requires a nonempty dataset and positive batch size")
    order = epoch_order(row_count, epoch, seed, pose_only)
    for start in range(0, row_count, batch_size):
        indices = order[start:start + batch_size]
        source_rows = len(indices)
        indices += [order[index % row_count] for index in range(batch_size - source_rows)]
        yield {"indices": indices, "source_rows": source_rows, "padding_rows": batch_size - source_rows}


def rank_slots(indices, rank, world_size, microbatch):
    if not indices or not 0 <= rank < world_size or microbatch < 1:
        raise ValueError("Invalid distributed batch layout")
    width = world_size * microbatch
    total = math.ceil(len(indices) / width) * width
    slots = [(index, 1.0) for index in indices] + [(indices[0], 0.0)] * (total - len(indices))
    return slots[rank::world_size]


def schedule_lr(step, total_steps, settings, base_lr=None):
    if total_steps < 1 or not 0 <= step < total_steps:
        raise ValueError("Scheduler step is outside its frozen training plan")
    warmup = min(math.ceil(total_steps * settings["warmup_ratio"]), max(0, total_steps - 1))
    if warmup and step < warmup:
        factor = (step + 1) / warmup
    else:
        progress = (step - warmup + 1) / max(1, total_steps - warmup)
        factor = 0.5 * (1 + math.cos(math.pi * progress)) if total_steps > 1 else 1.0
    rate = settings["learning_rate"] if base_lr is None else base_lr
    return rate * factor


def build_optimizer(groups, auxiliary_heads, settings):
    if not settings.get("unfreeze_vision_blocks") and "head_learning_rate" not in settings:
        parameters = [parameter for group in groups.values() for _, parameter in group]
        if auxiliary_heads is not None:
            parameters.extend(p for p in auxiliary_heads.parameters() if p.requires_grad)
        return torch.optim.AdamW(parameters, lr=settings["learning_rate"], weight_decay=settings["weight_decay"],
                                 betas=tuple(settings["betas"]), foreach=False)
    adapter_params = [parameter for name, group in groups.items() if name != "vision_blocks" for _, parameter in group]
    param_groups = [{"params": adapter_params, "lr": settings["learning_rate"], "base_lr": settings["learning_rate"],
                     "group_name": "adapter"}]
    if "vision_blocks" in groups:
        vision_lr = settings["vision_learning_rate"]
        param_groups.append({"params": [parameter for _, parameter in groups["vision_blocks"]],
                             "lr": vision_lr, "base_lr": vision_lr, "group_name": "vision_blocks"})
    if auxiliary_heads is not None:
        head_params = [p for p in auxiliary_heads.parameters() if p.requires_grad]
        if head_params:
            head_lr = settings.get("head_learning_rate", 1e-4)
            param_groups.append({"params": head_params, "lr": head_lr, "base_lr": head_lr, "group_name": "heads"})
    return torch.optim.AdamW(param_groups, lr=settings["learning_rate"], weight_decay=settings["weight_decay"],
                             betas=tuple(settings["betas"]), foreach=False)


def collate_rows(rows, pad_token_id):
    fields = {"input_ids", "attention_mask", "labels"}
    # geometry_features: per-row merged-video-token features, concatenated in row order like the videos' tokens.
    optional = {"mm_token_type_ids", "pixel_values_videos", "video_grid_thw", "geometry_features"} | AUXILIARY
    if (not rows or any(not fields <= row.keys() or set(row) - fields - optional for row in rows)
            or any(set(row) != set(rows[0]) for row in rows)):
        raise ValueError("Micro-batches require matching, assistant-masked RGB tensor fields")
    if any(row["input_ids"].ndim != 2 or row["input_ids"].shape[0] != 1 for row in rows):
        raise ValueError("Collation accepts independently audited single-row encodings")
    length = max(row["input_ids"].shape[1] for row in rows)
    batch = {}
    for key in rows[0]:
        if key in fields or key == "mm_token_type_ids":
            if any(row[key].shape != row["input_ids"].shape for row in rows):
                raise ValueError("Token tensors changed shape during collation")
            fill = -100 if key == "labels" else pad_token_id if key == "input_ids" else 0
            batch[key] = torch.cat([F.pad(row[key], (0, length - row[key].shape[1]), value=fill) for row in rows])
        elif key in SEQUENCE_AUXILIARY:
            if any(row[key].shape[-1] != row["input_ids"].shape[1] for row in rows):
                raise ValueError("Token-aligned auxiliary targets changed length during collation")
            batch[key] = torch.cat([pad_last(row[key], length, SEQUENCE_AUXILIARY[key]) for row in rows])
        elif key in QUERY_AUXILIARY:
            width = max(row[key].shape[-1] for row in rows)
            batch[key] = torch.cat([pad_last(row[key], width, QUERY_AUXILIARY[key]) for row in rows])
        elif key in CAMERA_GROUP_AUXILIARY:
            width = max(row[key].shape[1] for row in rows)
            batch[key] = torch.cat([torch.cat((row[key], row[key].new_full(
                (1, width - row[key].shape[1], *row[key].shape[2:]), CAMERA_GROUP_AUXILIARY[key])), dim=1) for row in rows])
        else:
            batch[key] = torch.cat([row[key] for row in rows])
    if torch.any(batch["labels"][batch["attention_mask"] == 0] != -100):
        raise ValueError("Padding tokens must never receive assistant supervision")
    return batch


def segment_row_losses(targets, supervised, losses, row_indices, counts, trace_weight=TRACE_LOSS_WEIGHT):
    """mean(answer tokens after </think>) + trace_weight * mean(trace tokens up to and including </think>) on traced rows.

    A direct row (<think>\\n\\n</think>, only newlines before </think>) or a row without </think> keeps the
    default reduction, so its loss is bitwise the default even inside a mixed batch.
    """
    direct = losses.new_zeros(targets.shape[0]).index_add(0, row_indices, losses) / counts
    is_close = supervised & ((targets == THINK_END_TOKEN_IDS[0]) | (targets == THINK_END_TOKEN_IDS[1]))
    closes_seen = is_close.cumsum(dim=1)
    before_close = supervised & (closes_seen == 0)
    non_newline_before_close = before_close & (targets != NEWLINE_TOKEN_IDS[0]) & (targets != NEWLINE_TOKEN_IDS[1])
    in_trace = before_close | (is_close & (closes_seen == 1))
    in_answer = supervised & ~in_trace
    trace_counts, answer_counts = in_trace.sum(dim=1), in_answer.sum(dim=1)
    has_trace = (is_close.any(dim=1) & non_newline_before_close.any(dim=1)
                 & (trace_counts > 0) & (answer_counts > 0))
    if not torch.any(has_trace):
        return direct
    token_in_trace = in_trace[supervised]
    trace_sums = losses.new_zeros(targets.shape[0]).index_add(0, row_indices[token_in_trace], losses[token_in_trace])
    answer_sums = losses.new_zeros(targets.shape[0]).index_add(0, row_indices[~token_in_trace], losses[~token_in_trace])
    segmented = answer_sums / answer_counts.clamp(min=1) + trace_weight * (trace_sums / trace_counts.clamp(min=1))
    return torch.where(has_trace, segmented, direct)


def row_losses(model, batch, loss_reduction=None, parts=None, lm_scale=None):
    from .runner import supervised_logits

    if isinstance(loss_reduction, dict) and parts is None:
        parts, loss_reduction = loss_reduction, None
    labels = batch["labels"]
    if labels.ndim != 2 or torch.any(labels[:, 0] != -100):
        raise ValueError("Every row must start with an unsupervised causal prompt")
    positions = torch.where((labels[:, 1:] != -100).any(dim=0))[0]
    targets = labels[:, positions + 1]
    counts = (targets != -100).sum(dim=1)
    if not positions.numel() or torch.any(counts == 0):
        raise ValueError("Every real or padding row requires a nonempty assistant target")
    supervised = targets != -100
    auxiliary = None
    if any(key.startswith('aux_') for key in batch):
        logits, auxiliary = supervised_logits(model, batch, positions, return_auxiliary=True)
    else:
        logits = supervised_logits(model, batch, positions)
    losses = F.cross_entropy(logits.float(), targets[supervised], reduction="none")
    row_indices = torch.where(supervised)[0]
    if loss_reduction == SEGMENT_LOSS_REDUCTION:
        result = segment_row_losses(targets, supervised, losses, row_indices, counts)
    else:
        result = losses.new_zeros(labels.shape[0]).index_add(0, row_indices, losses) / counts
    if "aux_lm_weight" in batch:
        # Pose-only rows carry weight 0: their text target trains nothing, the camera term still does.
        result = result * batch["aux_lm_weight"].to(result)
    if lm_scale is not None and lm_scale != 1.0:
        # Pose-only rows leave the language-model mean: the LM term divides by the step's QA rows, not all rows.
        result = result * lm_scale
    if parts is not None:
        parts["lm"] = result.detach()  # per-row language-model loss, before the auxiliary terms
    return result if auxiliary is None else result + auxiliary


def backward_batch(model, batch, weights, world_size, global_batch_size, synchronize=True, forward_context=None,
                   loss_reduction=None, parts=None, lm_scale=None):
    if isinstance(loss_reduction, dict) and parts is None:
        parts, loss_reduction = loss_reduction, None
    context = model.no_sync() if not synchronize and hasattr(model, "no_sync") else nullcontext()
    with context:
        with forward_context if forward_context is not None else nullcontext():
            losses = row_losses(model, batch, loss_reduction=loss_reduction, parts=parts, lm_scale=lm_scale)
        weights = torch.as_tensor(weights, dtype=losses.dtype, device=losses.device)
        if weights.shape != losses.shape or not torch.all((weights == 0) | (weights == 1)):
            raise ValueError("Distributed row weights must be exact active/padding indicators")
        if not torch.isfinite(losses).all():
            raise ValueError("Nonfinite assistant-token loss")
        (losses.mul(weights).sum() * (world_size / global_batch_size)).backward()
    return losses.detach()


def select_microbatch(reports, world_size, global_batch_size=32):
    if len(reports) != world_size:
        raise ValueError("The memory probe must report every rank")
    candidates = set.intersection(*[{trial["microbatch"] for trial in report["trials"] if trial["fits"]}
                                    for report in reports])
    if not candidates:
        raise ValueError("No micro-batch of at least one row fits on every leased GPU")
    timings = [{trial["microbatch"]: trial["seconds"] for trial in report["trials"] if trial["fits"]}
               for report in reports]
    return min(candidates, key=lambda size: (math.ceil(global_batch_size / (world_size * size))
                                            * max(rank[size] for rank in timings), -size))
