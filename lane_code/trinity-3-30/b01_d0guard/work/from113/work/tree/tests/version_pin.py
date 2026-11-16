"""The trainer's transformers pin (requirements.txt) for tests that run the student's own Qwen3.5 forward.

The head modules run on any supported transformers; the trainer pins one version, because 5.3.0's Qwen3.5
get_rope_index raises StopIteration on the processor's single [16, h, w] video grid with mm_token_type_ids.
"""
import re
from pathlib import Path

PIN = re.search(r'^transformers==(\S+)$', (Path(__file__).resolve().parents[1] / 'requirements.txt').read_text(), re.M).group(1)


def installed():
    try:
        import transformers
    except ImportError:
        return None
    return transformers.__version__


def on_trainer_pin():
    return installed() == PIN


REASON = f'runs the student forward, which needs the trainer pin transformers=={PIN}'
