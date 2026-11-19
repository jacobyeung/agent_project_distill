import time

started = time.monotonic()


def stage(name):
    print(f'{time.monotonic() - started:.2f}s {name}', flush=True)


stage('before torch')
import torch
stage('after torch')
import transformers
stage('after transformers')
from transformers import AutoProcessor
stage('after AutoProcessor')
from student_pilot.batches import load_processor
stage('after batches')
processor = load_processor('qwen35')
stage('after real processor')
print(processor.tokenizer.encode('<think>\n</think>\n\n3<|im_end|><|endoftext|>', add_special_tokens=False), flush=True)
