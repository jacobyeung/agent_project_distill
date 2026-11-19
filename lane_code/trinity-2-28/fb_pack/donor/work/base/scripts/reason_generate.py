"""Greedy generation whose query tokens call the student's perception heads.

In reason mode, decoding stops whenever the model emits a query token. One extra
forward over the whole sequence reads the final language-norm state at that
token, the matching head predicts the value, and its formatted text is appended
before decoding resumes. Plain mode decodes with no query handling, as a control.
The prompt is the exact packed prompt token list; frames come from the cohort.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from student_pilot import auxiliary_reason as reason  # noqa: E402

ROOT = Path('/opt/r')
RUNS = ROOT / 'runs/aws128p_20261025'
SIZE = {'shortest_edge': 524288, 'longest_edge': 4718592}
MAX_NEW = 4096
HEAD_PREFIX = 'auxiliary_heads.'
DISPLAYED_TIME = re.compile(r'<(\d+(?:\.\d+)?) seconds>')


def setup_env():
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1', TOKENIZERS_PARALLELISM='false')


def first_match(pattern):
    found = sorted(RUNS.glob(pattern))
    if not found:
        raise SystemExit('Nothing matches ' + str(RUNS / pattern))
    return found[0]


def decode_with_queries(generate, readout, prompt_ids, eos_ids, query_ids=None, max_new=MAX_NEW, encode_value=None):
    """Core loop. generate(ids, budget, stop_ids) returns new ids ending at a stop id or the budget;
    readout(ids, kind) returns the value text for the query token that ends ids."""
    query_ids = query_ids or {}
    generated, calls = [], []
    stops = list(eos_ids) + [token for token in query_ids if token not in eos_ids]
    while len(generated) < max_new:
        new = list(generate(list(prompt_ids) + generated, max_new - len(generated), stops))
        generated += new
        if not new or new[-1] in eos_ids or new[-1] not in query_ids:
            break
        kind = reason.KINDS[query_ids[new[-1]]]
        text = readout(list(prompt_ids) + generated, kind)
        value = encode_value(text)[:max_new - len(generated)]
        calls.append({'kind': kind, 'value': text, 'query_index': len(generated) - 1, 'value_tokens': len(value)})
        generated += value
    return generated, calls


def group_times(tokenizer, prompt_ids, row):
    """The 16 timestamps the model reads in its prompt; the packed group times are the fallback."""
    found = [float(match) for match in DISPLAYED_TIME.findall(tokenizer.decode(prompt_ids, skip_special_tokens=False))]
    if len(found) == reason.GROUPS:
        return found
    if not row.get('group_times'):
        raise ValueError('Prompt lacks 16 displayed temporal-group timestamps')
    return reason.displayed_times(row['group_times'])


def load_model(args):
    import torch
    import transformers

    snapshot = Path(args.snapshot) if args.snapshot else first_match('models/models--*/snapshots/*')
    arch = json.loads((snapshot / 'config.json').read_text())['architectures'][0]
    model = getattr(transformers, arch).from_pretrained(
        str(snapshot), local_files_only=True, dtype=torch.bfloat16, attn_implementation='sdpa', device_map={'': 'cuda:0'})
    adapter = Path(args.adapter)
    head_weights = {}
    if adapter.is_dir():
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, str(adapter), is_trainable=False, local_files_only=True)
    else:
        from peft import LoraConfig, get_peft_model
        config_path = Path(args.lora_config) if args.lora_config else first_match('parents/ST9/adapter-*/adapter_config.json')
        cfg = json.loads(config_path.read_text())
        keep = {k: v for k, v in cfg.items() if k in LoraConfig.__dataclass_fields__
                and k not in ('peft_type', 'task_type', 'base_model_name_or_path', 'revision', 'auto_mapping')}
        model = get_peft_model(model, LoraConfig(**keep))
        weights = torch.load(adapter, map_location='cpu', weights_only=True)
        head_weights = {k[len(HEAD_PREFIX):]: v for k, v in weights.items() if k.startswith(HEAD_PREFIX)}
        weights = {k: v for k, v in weights.items() if not k.startswith(HEAD_PREFIX)}
        params = dict(model.named_parameters())
        missing = [k for k in weights if k not in params]
        extra = [k for k in params if 'lora_' in k and k not in weights]
        if missing or extra:
            raise SystemExit(f'adapter key mismatch: missing {missing[:3]} ({len(missing)}), extra {extra[:3]} ({len(extra)})')
        with torch.no_grad():
            for k, v in weights.items():
                if params[k].shape != v.shape:
                    raise SystemExit(f'shape mismatch {k}')
                params[k].data = v.to(device=params[k].device, dtype=v.dtype)
    model.eval()
    model.requires_grad_(False)
    return model, head_weights


def head_settings(payload):
    """(auxiliary settings, camera settings) from a trainer run header or an auxiliary_heads.json manifest."""
    if payload.get('schema') == 'provisional-ddp-training-run-v2':
        return payload['settings'].get('auxiliary'), payload.get('camera')
    return payload['settings'], payload.get('camera', {}).get('settings')


def load_heads(args, model, head_weights, tokenizer, require_reason=True):
    """Heads from auxiliary_heads.pt (+ sibling auxiliary_heads.json) or from a trainer checkpoint."""
    import torch
    from student_pilot.auxiliary_losses import AuxiliaryHeads

    if args.heads:
        path = Path(args.heads)
        settings, camera = head_settings(json.loads(path.with_suffix('.json').read_text()))
        head_weights = torch.load(path, map_location='cpu', weights_only=True)
    elif head_weights:
        source = Path(args.head_settings) if args.head_settings else Path(args.adapter).parent / 'artifacts/run.json'
        settings, camera = head_settings(json.loads(source.read_text()))
    else:
        raise SystemExit('Head readout needs --heads or a trainer checkpoint that holds head weights')
    text = model.get_base_model().config.text_config if hasattr(model, 'get_base_model') else model.config.text_config
    heads = AuxiliaryHeads(text.hidden_size, settings, camera)
    if require_reason and not heads.has_reason:
        raise SystemExit('The saved heads have no query-token readouts')
    heads.load_state_dict(head_weights, strict=True)
    heads.reason_table = reason.token_table(tokenizer) if heads.has_reason else None
    return heads.to(device='cuda:0', dtype=torch.float32).eval()


def head_readout(model, heads, feed, times):
    """Return readout(ids, kind): one forward over ids, the head reads the last position."""
    import torch
    from student_pilot.auxiliary_losses import final_norm, video_features

    settings = model.get_base_model().config if hasattr(model, 'get_base_model') else model.config
    norm = final_norm(model)

    def readout(ids, kind):
        batch = sequence_feed(feed, ids)
        captured = []

        def hook(module, args, output):
            view = {**batch, 'labels': torch.full_like(batch['input_ids'], -100)}
            frames = video_features(output, view, settings.video_token_id,
                                    settings.vision_config.spatial_merge_size).float().mean(dim=(2, 3))
            positions = torch.tensor([[batch['input_ids'].shape[1] - 1]], device=output.device)
            outputs, scores = heads.reason_outputs(output, frames, positions)
            captured.append(heads.format(kind, outputs[0, 0], scores[0, 0], times))
        handle = norm.register_forward_hook(hook)
        try:
            with torch.inference_mode():
                model(**batch, logits_to_keep=1, use_cache=False, return_dict=True)
        finally:
            handle.remove()
        if len(captured) != 1:
            raise ValueError('Head readout must run the final norm exactly once')
        return captured[0]
    return readout


def sequence_feed(feed, ids):
    import torch

    prompt = feed['input_ids']
    tensor = torch.tensor([ids], dtype=prompt.dtype, device='cuda:0')
    batch = {k: v.to('cuda:0') for k, v in feed.items() if k not in ('input_ids', 'attention_mask', 'mm_token_type_ids')}
    batch['input_ids'] = tensor
    batch['attention_mask'] = torch.ones_like(tensor)
    if 'mm_token_type_ids' in feed:
        mm = feed['mm_token_type_ids']
        batch['mm_token_type_ids'] = torch.cat([mm, torch.zeros((1, len(ids) - mm.shape[1]), dtype=mm.dtype)], dim=1).to('cuda:0')
    return batch


def hf_generate(model, feed, pad_token_id):
    import torch

    def generate(ids, budget, stop_ids):
        batch = sequence_feed(feed, ids)
        with torch.inference_mode():
            out = model.generate(**batch, do_sample=False, num_beams=1, max_new_tokens=budget, eos_token_id=list(stop_ids),
                                 pad_token_id=pad_token_id, temperature=None, top_p=None, top_k=None)
        return out[0, len(ids):].tolist()
    return generate


def frames_for(row, cohort_dir):
    import numpy as np
    from PIL import Image
    from transformers.video_utils import VideoMetadata

    base = cohort_dir / 'prepared/generation/frames' / row['frames_id']
    sel = json.loads((base / 'selection.json').read_text())
    arrays = []
    for fr in sel['frames']:
        with Image.open(base / Path(fr['png']['path']).name) as im:
            arrays.append(np.asarray(im.convert('RGB')).copy())
    arrays = np.stack(arrays)
    h, w = arrays.shape[1:3]
    meta = VideoMetadata(total_num_frames=sel['total_num_frames'], fps=sel['fps'], frames_indices=sel['frame_indices'], width=w, height=h)
    return arrays, meta


def build_inputs(processor, row, cohort_dir):
    """Pixels from the processor; ids are the exact packed prompt ids and must match it."""
    import torch

    arrays, meta = frames_for(row, cohort_dir)
    batch = processor(text=[row['prompt']], videos=[arrays], video_metadata=[meta], do_sample_frames=False, size=SIZE,
                      return_tensors='pt', return_metadata=True, truncation=False, padding=False)
    batch.pop('video_metadata', None)
    check = {'ids_match': batch['input_ids'][0].tolist() == row['input_token_ids']}
    px = batch['pixel_values_videos']
    check['pixel_sha256'] = hashlib.sha256(px.detach().cpu().contiguous().numpy().tobytes()).hexdigest()
    check['pixel_match'] = check['pixel_sha256'] == row['pixel_sha256']
    batch = dict(batch)
    batch['input_ids'] = torch.tensor([row['input_token_ids']], dtype=batch['input_ids'].dtype)
    return batch, check


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pack', required=True)
    ap.add_argument('--cohort_dir', required=True)
    ap.add_argument('--adapter', required=True, help="trainer checkpoint adapters.pt or a published PEFT adapter directory")
    ap.add_argument('--heads', default='', help='auxiliary_heads.pt (settings from the sibling .json)')
    ap.add_argument('--head-settings', default='', help='run.json or auxiliary_heads.json when heads come from adapters.pt')
    ap.add_argument('--mode', choices=('reason', 'plain'), default='reason')
    ap.add_argument('--snapshot', default='')
    ap.add_argument('--lora-config', default='')
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--shards', type=int, default=1)
    ap.add_argument('--out', required=True)
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()
    setup_env()
    import glob
    import torch
    from transformers import AutoProcessor

    torch.manual_seed(17)
    rows = [json.loads(line) for line in open(args.pack) if line.strip()]
    rows = [r for i, r in enumerate(rows) if i % args.shards == args.shard]
    if args.limit:
        rows = rows[:args.limit]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    res_path = out / f'results_{args.mode}_{args.shard:02d}.jsonl'
    done = set()
    if res_path.exists():
        done = {json.loads(line)['qid'] for line in open(res_path) if line.strip()}
    snapshot = Path(args.snapshot) if args.snapshot else first_match('models/models--*/snapshots/*')
    processor = AutoProcessor.from_pretrained(str(snapshot), local_files_only=True)
    tok = processor.tokenizer
    model, head_weights = load_model(args)
    heads = load_heads(args, model, head_weights, tok) if args.mode == 'reason' else None
    query_ids = heads.reason_table['query'] if heads is not None else {}
    gc = model.generation_config
    eos = gc.eos_token_id if isinstance(gc.eos_token_id, list) else [gc.eos_token_id]
    for name in ('<|im_end|>', '<|endoftext|>'):
        tid = tok.convert_tokens_to_ids(name)
        if isinstance(tid, int) and tid not in eos:
            eos.append(tid)
    if set(eos) & set(query_ids):
        raise SystemExit('A query token is also a stop token')
    cohort_dir = Path(sorted(glob.glob(args.cohort_dir))[0])
    with open(res_path, 'a') as w:
        for row in rows:
            if row['qid'] in done:
                continue
            t0 = time.time()
            rec = {'qid': row['qid'], 'mode': args.mode, 'type': row.get('type')}
            try:
                feed, check = build_inputs(processor, row, cohort_dir)
                rec['check'] = check
                if not check['ids_match']:
                    raise ValueError('Processor prompt ids differ from the packed prompt ids')
                prompt_ids = row['input_token_ids']
                readout = None
                if heads is not None:
                    readout = head_readout(model, heads, feed, group_times(tok, prompt_ids, row))
                ids, calls = decode_with_queries(hf_generate(model, feed, tok.pad_token_id), readout, prompt_ids, eos,
                                                 query_ids, MAX_NEW, lambda text: reason.value_ids(text, heads.reason_table))
                rec.update(generation=tok.decode(ids, skip_special_tokens=False), tokens=len(ids), calls=calls)
            except Exception as exc:  # recorded, never retried silently
                rec.update(error=f'{type(exc).__name__}: {exc}')
            rec['seconds'] = round(time.time() - t0, 2)
            w.write(json.dumps(rec) + '\n')
            w.flush()
    (out / f'DONE_{args.mode}_{args.shard:02d}').write_text('ok\n')


if __name__ == '__main__':
    main()
