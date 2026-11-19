"""CPU first-batch dry run of N at 32 viewpoints and at the nested 64-viewpoint input.

Modes
  encode   every rank's first row of every stream through Rows.row -> fetch -> check_row (real tokenizer
           and processor, synthetic RGB at real resolutions); records tokens and layout facts.
  forward  the real Qwen3.5-9B architecture (32 LM layers, 27 ViT blocks) at random init, base in BF16 and
           heads in FP32 as first_batch_check runs it; no-grad forward of every rank's first batch
           (microstep 0, the pose stream) and of rank 0's first row of each other stream.
  trainmem reduced LM depth (--layers), forward + backward with N's checkpointing and trainability;
           peak RSS above the post-load baseline, per row.

Usage: f64_dryrun.py MODE --config CFG.json --out OUT.json [--clips a43,b169] [--layers 4]
"""
import argparse
import json
import os
import resource
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

TREE = Path(os.environ.get('F64_TREE', '/scratch/jjyeung/orch_n30/sb_f64/pkg/work/tree_f64'))
META = Path('/scratch/jjyeung/orch_n30/sb_f64/in/qwen35_9b_meta')
PREP = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/p_runtime/okh7/x_ee227714/runs/6ed2c7aa/inputs/'
            'prepare_da5580b7d92f490bb3cfe8df447e7820/prepared/receipt.json')
WORK = Path(os.environ.get('F64_WORK', '/scratch/jjyeung/orch_n30/sb_f64/work/dryrun'))
sys.path[:0] = [str(TREE), str(Path(__file__).parent)]
os.environ.setdefault('STUDENT_FRAME_ROOT_MAP', '{}')
os.environ.setdefault('STUDENT_ORCHARD', '1')

import torch  # noqa: E402

# Keys prepare() copies from the config into the run receipt (carrier_c1_run.py:633-636).
RECEIPT_KEYS = ('frame_layout', 'frame_pair_gap_seconds', 'skip_unsupervised_lm', 'depth_fov_source',
                'tool_mode_flag', 'ground_target_filter', 's1_route_policy', 'h1', 'r1_training', 'frame_count',
                'frame_input', 'max_pixels', 'min_pixels', 'frame_markers', 'routing_opener_init')
STAND_INS = ['random-init weights (no 9B weights on /scratch)', 'synthetic RGB at 640x480 and 1280x720',
             'synthetic SQLite stores (one row per rank per stream)', 'sampler: mixed_indices (r2_sampling table absent)',
             'extent_receipt, r2_membership, depth_init, init_artifact and routing-opener init not applied',
             'full_ft.prepare_model without the FP32 master cast (the trainer casts back to BF16 before this forward)']


def rss_kib():
    with open('/proc/self/status') as f:
        for line in f:
            if line.startswith('VmRSS:'):
                return int(line.split()[1])
    return 0


class Peak:
    """Samples VmRSS every 5 ms; ru_maxrss cannot be reset between rows."""
    def __init__(self):
        self.peak, self.running = 0, False

    def __enter__(self):
        self.base = rss_kib()
        self.peak, self.running = self.base, True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        return self

    def _run(self):
        while self.running:
            self.peak = max(self.peak, rss_kib())
            time.sleep(0.005)

    def __exit__(self, *exc):
        self.running = False
        self.thread.join()
        self.peak = max(self.peak, rss_kib())


def receipt_for(cfg, stores):
    prep = json.loads(PREP.read_text())
    receipt = {k: cfg[k] for k in RECEIPT_KEYS if k in cfg}
    receipt.update(streams=stores, camera={**prep['camera'], **cfg.get('camera_overrides', {})}, depth=prep['depth'],
                   carrier_placement=cfg['carrier_placement'], training_mode=cfg['training_mode'],
                   depth_enabled=cfg.get('depth_enabled', True), recipe=cfg['recipe'], pointing_weights=cfg.get('pointing_weights'))
    return receipt


def plan_rows(receipt, world):
    """Each rank's first row of each stream from the native final-mode sampler."""
    from student_pilot import carrier_c1_data as data
    counts = {k: v['count'] for k, v in receipt['streams'].items()}
    plan = next(data.mixed_indices(counts, 1, training_mode='final', mix=receipt['recipe']['mix'], world=world))
    first = {}
    for microstep, (stream, indices) in enumerate(plan):
        first.setdefault(stream, (microstep, indices))
    return first


def prepare_without_cast(model, block):
    from student_pilot import full_ft
    original = torch.Tensor.to
    def keep(self, *a, **k):
        return self if len(a) == 1 and a[0] is torch.float32 and not k else original(self, *a, **k)
    with mock.patch.object(torch.Tensor, 'to', keep):
        return full_ft._f64_original_prepare(model, block)


def build_model(receipt, processor, layers=None):
    from transformers import Qwen3_5Config, Qwen3_5ForConditionalGeneration
    from student_pilot import full_ft
    from student_pilot.camera_targets import carrier_id
    from student_pilot.carrier_c1 import CarrierC1
    raw = json.loads((META / 'config.json').read_text())
    config = Qwen3_5Config.from_dict(raw)
    text = config.text_config
    if layers is not None:
        text.num_hidden_layers = layers
        text.layer_types = list(text.layer_types[:layers])
    vocab = len(processor.tokenizer)
    if vocab > text.vocab_size:
        text.vocab_size = vocab
    for item in (config, text, config.vision_config):
        item._attn_implementation = 'sdpa'
    torch.manual_seed(17)
    previous = torch.get_default_dtype()
    torch.set_default_dtype(torch.bfloat16)
    try:
        base = Qwen3_5ForConditionalGeneration(config)
    finally:
        torch.set_default_dtype(previous)
    full_ft._f64_original_prepare = full_ft.prepare_model
    with mock.patch.object(full_ft, 'prepare_model', prepare_without_cast):
        model = CarrierC1(base, receipt['camera'], receipt['depth'], carrier_id(processor.tokenizer),
                          receipt['carrier_placement'], receipt['training_mode'], receipt['depth_enabled'], receipt['recipe'],
                          receipt.get('skip_unsupervised_lm'), receipt.get('frame_layout', 'spread'),
                          receipt.get('depth_fov_source', 'private'), frame_count=receipt.get('frame_count', 32))
    model.r1_training = receipt.get('r1_training')
    for _, parameter in full_ft.base_parameters(model):
        parameter.data = parameter.data.to(torch.bfloat16)
    # depth_init freezes the private ViT copy (carrier_c1.py:737); N binds a depth_init.
    model.auxiliary_heads.depth.model.visual.requires_grad_(False)
    return model


def setup(cfg_path, clips):
    import f64_rows
    from student_pilot.carrier_c1_run import Rows, processor_for_receipt
    cfg = json.loads(Path(cfg_path).read_text())
    nested = cfg.get('frame_input') is not None
    out = {}
    for name in clips:
        clip = f64_rows.make_clip(WORK, name)
        stores = f64_rows.build(WORK, clip, nested)
        receipt = receipt_for(cfg, stores)
        processor = processor_for_receipt({'root': str(META)}, receipt)
        out[name] = (receipt, processor, Rows(receipt, processor))
    return cfg, out


def describe(batch, targets, audit, processor):
    ids = batch['input_ids'][0]
    tok = processor.tokenizer
    marker = tok.encode('Frame', add_special_tokens=False)[0]
    positions = batch.get('aux_camera_positions')
    labels = batch.get('labels')
    record = dict(tokens=int(ids.shape[0]), attended=int(batch['attention_mask'].sum()),
                  supervised=int((labels != -100).sum()) if labels is not None else 0,
                  visual_tokens=int((ids == processor.video_token_id).sum()) if 'video_grid_thw' in batch else
                  int((ids == processor.image_token_id).sum()),
                  carriers=int((positions >= 0).sum()) if positions is not None else 0,
                  marker_words=int((ids == marker).sum()),
                  grid=batch['video_grid_thw'].tolist() if 'video_grid_thw' in batch else batch['image_grid_thw'].tolist(),
                  anchor_groups=batch['aux_anchor_groups'][0].tolist()[:4] + ['...'] if 'aux_anchor_groups' in batch else None,
                  depth_targets=list(targets['aux_point_depth_mask'].shape) if targets and 'aux_point_depth_mask' in targets else None)
    if audit:
        record.update({k: audit[k] for k in ('prompt_tokens', 'assistant_tokens_including_eos', 'processed_height_width')
                       if k in audit})
    return record


def run_encode(args):
    from student_pilot.carrier_c1_run import check_row, fetch
    cfg, setups = setup(args.config, args.clips)
    records = []
    for name, (receipt, processor, rows) in setups.items():
        first = plan_rows(receipt, cfg['world_size'])
        for stream, (microstep, indices) in first.items():
            for rank in range(cfg['world_size']):
                tick = time.perf_counter()
                batch, targets, audit = rows.get(stream, indices[rank])
                stub = type('M', (), dict(recipe=cfg['recipe'], frame_count=32, training_mode='final'))()
                check_row(batch, targets, stream, stub)
                records.append(dict(clip=name, stream=stream, microstep=microstep, rank=rank, index=int(indices[rank]),
                                    seconds=round(time.perf_counter() - tick, 2), **describe(batch, targets, audit, processor)))
        rows.close()
    return dict(mode='encode', records=records)


def run_forward(args):
    cfg, setups = setup(args.config, args.clips)
    name = args.clips[0]
    receipt, processor, rows = setups[name]
    with Peak() as load:
        tick = time.perf_counter()
        model = build_model(receipt, processor, args.layers)
        model.eval()
        load_seconds = time.perf_counter() - tick
    first = plan_rows(receipt, cfg['world_size'])
    jobs = [(first['pose'][0], 'pose', rank, first['pose'][1][rank]) for rank in range(cfg['world_size'])]
    jobs += [(first[s][0], s, 0, first[s][1][0]) for s in ('vqa', 'routing', 'pointing')]
    records = []
    for microstep, stream, rank, index in jobs[:args.limit]:
        batch, targets, audit = rows.get(stream, index)
        with Peak() as peak:
            tick = time.perf_counter()
            with torch.no_grad():
                result = model(batch, targets, stream=stream)
            seconds = time.perf_counter() - tick
        loss = float(result['loss'])
        parts = {k: float(v) for k, v in result['components'].items()}
        records.append(dict(clip=name, stream=stream, microstep=microstep, rank=rank, index=int(index),
                            seconds=round(seconds, 1), loss=loss, components=parts,
                            finite=all(map(lambda v: v == v and abs(v) != float('inf'), [loss, *parts.values()])),
                            rss_before_gib=round(peak.base / 2**20, 2), rss_peak_gib=round(peak.peak / 2**20, 2),
                            **describe(batch, targets, audit, processor)))
        print(json.dumps(records[-1]), flush=True)
        write(args, dict(mode='forward', partial=True, records=records))
    rows.close()
    params = dict(total=sum(p.numel() for p in model.parameters()),
                  heads=sum(p.numel() for p in model.auxiliary_heads.parameters()),
                  lm_layers=model.config.text_config.num_hidden_layers)
    return dict(mode='forward', parameters=params, load_seconds=round(load_seconds, 1),
                load_rss_gib=round(load.peak / 2**20, 2), threads=torch.get_num_threads(), records=records)


def run_trainmem(args):
    cfg, setups = setup(args.config, args.clips)
    name = args.clips[0]
    receipt, processor, rows = setups[name]
    model = build_model(receipt, processor, args.layers)
    model.train()
    first = plan_rows(receipt, cfg['world_size'])
    records = []
    for stream in args.streams:
        microstep, indices = first[stream]
        batch, targets, audit = rows.get(stream, indices[0])
        model.zero_grad(set_to_none=True)
        with Peak() as peak:
            tick = time.perf_counter()
            with torch.autocast('cpu', enabled=False):
                result = model(batch, targets, stream=stream)
                forward_peak = peak.peak
                result['loss'].backward()
            seconds = time.perf_counter() - tick
        grads = sum(p.grad.numel() * p.grad.element_size() for p in model.parameters() if p.grad is not None)
        records.append(dict(clip=name, stream=stream, layers=args.layers, seconds=round(seconds, 1),
                            loss=float(result['loss']), rss_before_gib=round(peak.base / 2**20, 3),
                            forward_peak_above_gib=round((forward_peak - peak.base) / 2**20, 3),
                            peak_above_gib=round((peak.peak - peak.base) / 2**20, 3), grad_gib=round(grads / 2**30, 3),
                            **describe(batch, targets, audit, processor)))
        print(json.dumps(records[-1]), flush=True)
        model.zero_grad(set_to_none=True)
    rows.close()
    return dict(mode='trainmem', layers=args.layers, threads=torch.get_num_threads(), records=records)


def write(args, value):
    value = dict(config=str(args.config), tree=str(TREE), stand_ins=STAND_INS, torch=torch.__version__, **value)
    Path(args.out).write_text(json.dumps(value, indent=1) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('encode', 'forward', 'trainmem'))
    parser.add_argument('--config', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--clips', default='a43,b169')
    parser.add_argument('--layers', type=int, default=None)
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--streams', default='pose,vqa,routing,pointing')
    args = parser.parse_args()
    args.clips = args.clips.split(',')
    args.streams = args.streams.split(',')
    torch.set_num_threads(int(os.environ.get('OMP_NUM_THREADS', '16')))
    result = dict(encode=run_encode, forward=run_forward, trainmem=run_trainmem)[args.mode](args)
    write(args, result)


if __name__ == '__main__':
    main()
