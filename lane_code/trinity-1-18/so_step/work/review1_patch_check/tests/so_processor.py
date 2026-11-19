"""Portable copies of the existing test_r2_data_path processor fixtures; no external fixture imports."""
from types import SimpleNamespace
import torch

class TinyTokenizer:
    """Lossless stand-in for the unavailable pretrained tokenizer."""
    pad_token_id, eos_token_id, eos_token = 0, 1, '<eos>'
    special = {'<eos>': 1, '<|fim_middle|>': 5, '<|video_pad|>': 61}

    def encode(self, text, **kwargs):
        return self(text)['input_ids']

    def __call__(self, text, **kwargs):
        ids, offsets, i = [], [], 0
        while i < len(text):
            token = next((t for t in self.special if text.startswith(t, i)), text[i])
            ids.append(self.special.get(token, ord(token[0])+100))
            offsets.append((i, i+len(token)))
            i += len(token)
        return dict(input_ids=ids, offset_mapping=offsets)

    def decode(self, ids, **kwargs):
        reverse = {v: k for k, v in self.special.items()}
        return ''.join(reverse.get(int(i), chr(int(i)-100) if int(i) >= 100 else '<visual>') for i in ids)

    def convert_tokens_to_ids(self, token):
        return self.special.get(token, self.eos_token_id)

class TinyProcessor:
    """Only the pretrained processor boundary stands in; actual RGB loaders run."""
    video_token_id = 61

    def __init__(self):
        self.tokenizer = TinyTokenizer()
        self.video_processor = SimpleNamespace(merge_size=2, temporal_patch_size=2)

    def apply_chat_template(self, messages, **kwargs):
        prefix = 'Question: '+messages[0]['content'][1]['text']+'\n<think>\n'
        return prefix if len(messages) == 1 else prefix+messages[-1]['content'].removeprefix('<think>\n')+'<eos>\n'

    def __call__(self, text, videos, video_metadata, **kwargs):
        metadata, arrays = video_metadata[0], videos[0]
        ids = self.tokenizer.encode(text[0])
        for i in range(0, len(arrays), 2):
            timestamp = sum(metadata.frames_indices[i:i+2])/(2*metadata.fps)
            ids += self.tokenizer.encode(f'<{timestamp:.1f} seconds>') + [62, 61, 63]
        pixels = arrays[:, ::8, ::8].reshape(len(arrays)//2, 2, 2, 2, 2, 2, 3)
        pixels = pixels.transpose(0, 2, 4, 6, 1, 3, 5).reshape(-1, 24)
        token_ids = torch.tensor([ids])
        return dict(input_ids=token_ids, mm_token_type_ids=torch.where(token_ids == 61, 2, 0), video_grid_thw=torch.tensor([[len(arrays)//2, 2, 2]]),
                    pixel_values_videos=torch.tensor(pixels, dtype=torch.float32)/255)
