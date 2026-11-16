"""Grounding and presence from the frozen student's MDG path in the integ_v3 tree (`<ground obj="...">`).

One student row per observation holds two temporal groups, group 0 = the agent view and group 1 = the wrist view
(the tree's 'duplicate' frame layout: each view fills both temporal patches of its group). The row's prefill is
captured once (mdg_features.capture_prefix); every phrase then runs the training-format call suffix through the native
decode stream (mdg_stream.stream_suffix_states) and the frozen MDG decoder (mdg_decode.predict), which gives per-group
presence prob = sigmoid(clip) x sigmoid(frame) and a mask at a quarter of the student frame's resolution.

The tree's ground_admission.qualification refuses benchmark-style qualified references ("wooden cabinet"); the
provider's phrases come from the sha-pinned, hand-checked LIBERO table, so this backend does not apply it and records
the audit flag instead (MDGPerception.audit).

Row building is injected: `row_builder(obs) -> batch` must give the student's batch for the two-group row
(input_ids, attention_mask, mm_token_type_ids, video_grid_thw, pixel_values_videos and the carrier fields).
FixtureRows serves the tree's tiny CPU fixture; on a GPU host the student's processor builds it (carrier_c1_run).
"""
import hashlib

import numpy as np
import torch

from .base import Grounding

VIEW_GROUP = {'agent': 0, 'wrist': 1}


def patchify(pixels, *, patch_size=16, temporal_patch_size=2, merge_size=2, image_mean=(.5, .5, .5),
             image_std=(.5, .5, .5)):
    """[T, 3, H, W] RGB in [0, 1] -> Qwen3-VL video patches [T*h*w, 3*tp*p*p], each frame filling both temporal
    patches; the exact inverse of student_pilot.mdg_features.unpatchify."""
    pixels = torch.as_tensor(pixels, dtype=torch.float32)
    t, c, H, W = pixels.shape
    p, tp, m = patch_size, temporal_patch_size, merge_size
    h, w = H // p, W // p
    if c != 3 or H % (p * m) or W % (p * m):
        raise ValueError('Frame size must be a multiple of patch_size x merge_size')
    mean = pixels.new_tensor(image_mean).reshape(1, 3, 1, 1)
    std = pixels.new_tensor(image_std).reshape(1, 3, 1, 1)
    x = ((pixels - mean) / std)[:, None].expand(t, tp, 3, H, W)
    x = x.reshape(t, tp, 3, h // m, m, p, w // m, m, p)
    return x.permute(0, 3, 6, 4, 7, 2, 1, 5, 8).reshape(t * h * w, 3 * tp * p * p).contiguous()


def resize_rgb(image, height, width):
    """uint8 HWC -> float [3, height, width] in [0, 1], bilinear (antialiased when shrinking)."""
    x = torch.as_tensor(np.asarray(image), dtype=torch.float32).permute(2, 0, 1)[None] / 255.
    return torch.nn.functional.interpolate(x, size=(height, width), mode='bilinear', align_corners=False,
                                           antialias=True)[0].clamp(0, 1)


def resize_mask(mask, height, width):
    """Nearest resize of a boolean mask by normalised coordinates (pixel centres)."""
    mask = np.asarray(mask, dtype=bool)
    mh, mw = mask.shape
    rows = np.minimum(((np.arange(height) + .5) * mh / height).astype(int), mh - 1)
    cols = np.minimum(((np.arange(width) + .5) * mw / width).astype(int), mw - 1)
    return mask[np.ix_(rows, cols)]


class FixtureRows:
    """Row builder for the tree's tiny CPU fixture: the fixture batch with the observation's two views patchified
    into its 2-group video grid."""
    def __init__(self, model, batch):
        t, h, w = map(int, batch['video_grid_thw'][0])
        if t != 2:
            raise ValueError('The where row needs exactly two temporal groups (agent, wrist)')
        vision = model.config.vision_config
        self.template, self.p, self.tp, self.m = batch, vision.patch_size, vision.temporal_patch_size, vision.spatial_merge_size
        self.H, self.W = h * self.p, w * self.p
        processor = getattr(model, 'mdg_video_processor', None)
        self.mean = getattr(processor, 'image_mean', (.5, .5, .5))
        self.std = getattr(processor, 'image_std', (.5, .5, .5))

    def __call__(self, obs):
        frames = torch.stack([resize_rgb(obs.agent, self.H, self.W), resize_rgb(obs.wrist, self.H, self.W)])
        batch = dict(self.template)
        batch['pixel_values_videos'] = patchify(frames, patch_size=self.p, temporal_patch_size=self.tp,
                                                merge_size=self.m, image_mean=self.mean, image_std=self.std)
        return batch


class MDGPerception:
    """Presence gate and grounder over the student's MDG path. One object serves both provider slots."""

    def __init__(self, model, row_builder, *, weights_sha=None, chunk=1):
        from student_pilot import mdg_decode
        self.model, self.rows, self.chunk = model.eval(), row_builder, chunk
        self.head = mdg_decode.decoder(model)
        self.tau = mdg_decode.threshold(model)
        self._weights_sha = weights_sha
        self._prefix_key, self._prefix, self._batch, self._memory = None, None, None, None
        self._values = {}
        self.audit = []

    def sha(self):
        if self._weights_sha is None:
            digest = hashlib.sha256()
            for key, value in sorted(self.model.state_dict().items()):
                digest.update(key.encode() + b'\0' + value.detach().float().cpu().numpy().tobytes())
            self._weights_sha = digest.hexdigest()
        return hashlib.sha256(f'mdg|{self._weights_sha}|{self.tau}'.encode()).hexdigest()

    @staticmethod
    def _obs_key(obs):
        h = hashlib.sha256()
        for a in (obs.agent, obs.wrist):
            h.update(np.ascontiguousarray(a).tobytes())
        return h.hexdigest()

    @torch.no_grad()
    def _predict(self, obs, phrase):
        from student_pilot import mdg_decode, mdg_features, mdg_stream
        from student_pilot.ground_admission import outside_vocabulary, qualification
        key = self._obs_key(obs)
        if key != self._prefix_key:
            self._batch = self.rows(obs)
            self._prefix = mdg_features.capture_prefix(self.model, self._batch)
            self._prefix_key, self._memory, self._values = key, None, {}
        if phrase not in self._values:
            states = mdg_stream.stream_suffix_states(self.model, self._prefix, self._batch, [phrase], chunk=self.chunk)
            values, self._memory = mdg_decode.predict(self.head, self._prefix, states, self._memory)
            self._values[phrase] = dict(prob=values['prob'][0], mask=values['mask'][0])
            labels = getattr(self.model, 'mdg_meta', {}).get('labels')
            self.audit.append(dict(phrase=phrase, prob=values['prob'][0].tolist(),
                                   qualified=bool(qualification(phrase, labels) if labels else qualification(phrase)),
                                   outside_vocabulary=bool(outside_vocabulary(phrase, labels) if labels else outside_vocabulary(phrase))))
        return self._values[phrase]

    def presence(self, obs, view, phrase):
        return float(self._predict(obs, phrase)['prob'][VIEW_GROUP[view]])

    def ground(self, obs, view, phrase):
        values = self._predict(obs, phrase)
        mask = values['mask'][VIEW_GROUP[view]]
        if not mask.any():
            return Grounding('none', score=float(values['prob'][VIEW_GROUP[view]]))
        h, w = obs.image(view).shape[:2]
        return Grounding('mask', mask=resize_mask(mask, h, w), score=float(values['prob'][VIEW_GROUP[view]]))


WHERE_QUESTION = ('Frame 1 is the agent-view camera and frame 2 is the wrist camera, taken at the same instant. '
                  'Where are the objects named in the task?')


class ProcessorRows:
    """Row builder for a GPU host: the student's processor encodes the two views as a 4-frame video in the 'duplicate'
    layout (agent, agent, wrist, wrist -> 2 temporal groups) with the generation prompt, then the tree inserts the
    frame carriers (carrier_c1_data.insert_frame_carriers). UNVERIFIED on CPU (no Qwen3.5 processor on this host):
    the first GPU smoke must check that the row's prefill equals carrier_c1_decode's prefill for the same frames."""

    def __init__(self, processor, *, carrier_placement=None, question=WHERE_QUESTION, pixels=(128 * 128, 384 * 384)):
        from student_pilot.carrier_c1_data import C1_A
        self.processor, self.question, self.pixels = processor, question, pixels
        self.placement = C1_A if carrier_placement is None else carrier_placement

    def __call__(self, obs):
        from transformers.video_utils import VideoMetadata
        from student_pilot.carrier_c1_data import insert_frame_carriers
        h, w = obs.agent.shape[:2]
        wrist = obs.wrist if obs.wrist.shape[:2] == (h, w) else (
            resize_rgb(obs.wrist, h, w).permute(1, 2, 0).numpy() * 255).round().astype(np.uint8)
        arrays = np.repeat(np.stack([obs.agent, wrist]), 2, axis=0)
        metadata = VideoMetadata(total_num_frames=4, fps=1.0, frames_indices=[0, 1, 2, 3], width=w, height=h)
        messages = [dict(role='user', content=[dict(type='video'), dict(type='text', text=self.question)])]
        prompt = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        batch = self.processor(text=[prompt], videos=[arrays], video_metadata=[metadata], do_sample_frames=False,
                               size={'shortest_edge': 4 * self.pixels[0], 'longest_edge': 4 * self.pixels[1]},
                               return_tensors='pt')
        if int(batch['video_grid_thw'][0, 0]) != 2:
            raise ValueError('The where row must have two temporal groups')
        return insert_frame_carriers(dict(batch), self.processor.tokenizer, self.processor.video_processor.merge_size,
                                     self.placement, 'duplicate')
