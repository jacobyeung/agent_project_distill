"""Independent ttower reference path, using its unchanged RawProcessor method."""
import ast
import hashlib
from pathlib import Path


def reference_processor(model, source_root, writer_root, *, device, resolution=1008):
    """Load only the reference class; never run its CUDA builder or cache writer."""
    import importlib.util
    import torch
    from sam3.model.sam3_image_processor import Sam3Processor
    from sam3.model.box_ops import box_cxcywh_to_xyxy
    from sam3.model.data_misc import interpolate

    writer_root = Path(writer_root)
    common_path = writer_root/'common.py'
    spec = importlib.util.spec_from_file_location('_sam3_r10_reference_common', common_path)
    common = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(common)
    writer = writer_root/'sam3_tower.py'
    tree = ast.parse(writer.read_text())
    factory = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'make_processor')
    cls = next(n for n in factory.body if isinstance(n, ast.ClassDef) and n.name == 'RawProcessor')
    namespace = dict(torch=torch, Sam3Processor=Sam3Processor, box_cxcywh_to_xyxy=box_cxcywh_to_xyxy,
                     interpolate=interpolate, CONTRACT=common.CONTRACT,
                     rle_encode=common.rle_encode, rle_decode=common.rle_decode, deepest=common.deepest)
    exec(compile(ast.Module(body=[cls], type_ignores=[]), str(writer), 'exec'), namespace)
    processor = namespace['RawProcessor'](model, device=device, resolution=resolution)
    processor.reference_sources = {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (writer, common_path, Path(source_root)/'sam3/model/sam3_image_processor.py')}
    return processor


def reference_records(processor, frames, phrases, *, batch_size, autocast):
    """Run native B1 or B4 encoding and singleton grounding, in frame order."""
    import torch
    records = []
    with torch.inference_mode():
        for start in range(0, len(frames), batch_size):
            group = frames[start:start+batch_size]
            with autocast():
                state = (processor.set_image(group[0]) if batch_size == 1
                         else processor.set_image_batch(group))
                for i, image in enumerate(group):
                    if batch_size == 1:
                        single = state
                    else:
                        # Independent of the tower's offload/reconstruction code.
                        backbone = state['backbone_out']
                        single = dict(original_height=image.height, original_width=image.width,
                            backbone_out=dict(
                                backbone_fpn=[x[i:i+1] for x in backbone['backbone_fpn']],
                                vision_pos_enc=[x[i:i+1] for x in backbone['vision_pos_enc']],
                                vision_features=backbone['vision_features'][i:i+1]))
                    predictions = {}
                    for text in phrases:
                        processor.reset_all_prompts(single)
                        predictions[text] = processor.set_text_prompt(prompt=text, state=single)
                    records.append(predictions)
    return records


def as_detections(record):
    import torch
    from student_pilot.sam3_tower import FrameDetections
    from scripts.sam3_validate import rle_decode
    instances = record['instances']
    scores = torch.tensor([i['score'] for i in instances], dtype=torch.float32)
    masks = [torch.from_numpy(rle_decode(i['mask'])) for i in instances]
    return FrameDetections(record['presence'], scores, scores*record['presence'],
        torch.tensor([i['box'] for i in instances], dtype=torch.float32).reshape(-1, 4),
        torch.stack(masks) if masks else torch.empty((0, 0, 0), dtype=torch.bool),
        torch.tensor([i['query'] for i in instances], dtype=torch.long),
        torch.tensor(record['all_instance_scores'], dtype=torch.float32))


def compact_record(record):
    """Keep scores, ranks and areas; pair checks retain mask IoUs without big masks."""
    return dict(presence=record['presence'], all_instance_scores=record['all_instance_scores'],
        instances=[dict(query=i['query'], score=i['score'], rank=rank+1, box=i['box'],
                        mask_area=sum(i['mask']['counts'][1::2]), mask_size=i['mask']['size'])
                   for rank, i in enumerate(record['instances'])])


def paired_check(reference, fresh):
    from scripts.sam3_validate import compare, compare_noise_aware
    return dict(compare(reference, fresh), noise_aware=compare_noise_aware(reference, fresh))


def measured_floor_proposal(floor_checks, tower_checks):
    """Advisory only: require no excess failures over the observed cross-shape floor.

    A single run measures an empirical floor, not a confidence interval or proof
    of arithmetic causation. The launcher retains its existing acceptance gate.
    """
    from scripts.sam3_validate import aggregate_parity
    keys = lambda checks: [(c['scene'], c['frame'], c['phrase']) for c in checks]
    if not floor_checks or keys(floor_checks) != keys(tower_checks) or len(set(keys(floor_checks))) != len(floor_checks):
        raise ValueError('Floor and candidate must cover identical unique name-frames')
    floor, tower = aggregate_parity(floor_checks), aggregate_parity(tower_checks)
    rates = [('real_identity_changes', 'name_frames'), ('score_failures', 'score_checked_instances'),
             ('mask_failures', 'matched_instances'), ('presence_failures', 'name_frames'),
             ('cap_exchange_failures', 'name_frames')]
    bounds = {num: dict(floor_count=floor[num], floor_denominator=floor[den],
                       candidate_count=tower[num], candidate_denominator=tower[den],
                       within_floor=tower[num]*floor[den] <= floor[num]*tower[den]) for num, den in rates}
    return dict(policy='sam3-observed-cross-shape-floor-proposal-r10', advisory_only=True,
        floor=floor, candidate=tower, bounds=bounds,
        within_measured_floor=not floor['invalid_checks'] and not tower['invalid_checks']
            and all(b['within_floor'] for b in bounds.values()),
        limitation='One same-card B1/B4 reference pair; no statistical confidence or cross-hardware attribution.')
