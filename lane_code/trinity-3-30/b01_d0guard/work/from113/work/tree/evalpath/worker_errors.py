"""Fail-closed diagnostics: retain technical vocabulary and opaque asset paths."""
import re


AWS_PATH = re.compile(
    r'/(?:scratch|lustre)/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/'
    r'[0-9a-f]{8}(?:/[A-Za-z0-9_.-]+)*')
WORDS = set('''a all allocation allocate allocated already another artifact asset assets
attempt available base binding boolean budget bytes cache camera carrier changed checkpoint
code config configuration context count cpu cuda database depth device differs directory
dtype duplicate errno error exact exceeds expected failed file filename final float frame
frames from full gpu head heads identity in index indices input invalid inventory is item
journal json key layout load loading memory metadata missing mode model must no none not
of on only opener options out output outside parameter parity path pin placement policy
pose preparation prepared processor protocol question rank read receipt required revision
root routing row rows schema selected shard shape size snapshot source staged stream tensor
tensors the this to token trainer training true type unavailable unknown value values verify
vocabulary was weight weights with without worker world would write
example_id ground_truth question_type scene_name video_path group_id answer_type
config_sha256 base_identity carrier_placement frame_layout training_mode frame_markers
max_new_tokens enable_thinking do_sample cuda:0 c1 p1 p2 p3
gb gib mb mib kb kib tried reserved pytorch free total process includes non-pytorch
'''.split())
ASSET_NAMES = set('''runs arm f k o full_weights artifact.json receipt.json heads.pt heads.json
full_weights.json model.safetensors.index.json config.json tokenizer.json tokenizer_config.json
preprocessor_config.json processor_config.json generation_config.json j.json j.tar
'''.split())


def safe_message(exc):
    # Never copy arbitrary prose, paths, prompt fragments or tensor names into logs.
    raw = str(exc)[:500]
    paths = []
    def path(match):
        value = match.group()
        # Opaque project paths cannot contain human-readable scene/question IDs.
        if any(p not in ASSET_NAMES and not re.fullmatch(r'(?:[0-9a-f]+|m\d+|step_\d+|[0-9a-f]+\.(?:json|jsonl|tar|pt|npz)|model-\d+-of-\d+\.safetensors)', p)
               for p in value.split('/ap/', 1)[1].split('/')):
            return '[redacted]'
        paths.append(value)
        return f'@{len(paths)-1}@'
    raw = AWS_PATH.sub(path, raw)
    raw = re.sub(r'(?<!\w)/(?:[^\s\'\"<>]+)', '[redacted]', raw)
    raw = re.sub(r'[A-Za-z_][A-Za-z_0-9.-]*',
                 lambda m: m[0] if m[0].lower() in WORDS else '[redacted]', raw)
    for i, value in enumerate(paths):
        raw = raw.replace(f'@{i}@', value)
    return re.sub(r'(?:\[redacted\][ \t]*)+', '[redacted] ', raw).strip()[:500]


def error_row(rank, exc):
    trace = exc.__traceback__
    while trace and trace.tb_next:
        trace = trace.tb_next
    return dict(phase='error', rank=rank, type=type(exc).__name__,
                message=safe_message(exc), where=trace.tb_frame.f_code.co_name if trace else 'worker')
