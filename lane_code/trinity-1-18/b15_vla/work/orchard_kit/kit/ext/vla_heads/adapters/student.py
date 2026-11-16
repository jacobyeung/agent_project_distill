"""StudentAdapter: the tree's Qwen3.5 student (or base Qwen3.5-9B) behind the adapter contract.

Wraps the class `student_pilot.students.model_class('qwen35')` returns
(transformers `Qwen3_5ForConditionalGeneration`) or a `student_pilot.carrier_c1.CarrierC1` around
it; both expose `.model` (Qwen3_5Model with .visual and .language_model) and `.lm_head`.
Loading. B0: `from_pretrained(<Qwen/Qwen3.5-9B snapshot>)`. B1: `from_export(<same base>, <export>)`,
which loads the base in bf16 and then replaces every base tensor with the student's full-weights
export through `student_pilot.full_ft.load_export` (manifest `full_weights.json`, verified file by
file); a milestone directory (`MILESTONE.json`) is first verified by `full_ft.read_milestone`. The
VLA reads the LM and vision tower only: the export's `auxiliary_heads.pt` (pose, depth and readout
heads), its `geometry/` modules and MDG grounding artifacts (`mdg_decode_attach.attach_mdg`) are not
loaded, and the routed decoder (`headcall`) is not used; spatial outputs enter as `cond` tensors
computed by the provider.

batch: the processor outputs, input_ids [B, T], attention_mask [B, T] and optionally
pixel_values + image_grid_thw, pixel_values_videos + video_grid_thw, mm_token_type_ids (derived from
the image and video token ids when absent). Appended positions enter as `placeholder_id` (the pad
token) and a forward hook on the input embedding substitutes their embeddings (the carrier-hook
pattern), so M-RoPE positions, image placement and the hybrid DeltaNet / full attention run natively.
Taps below the last layer come from forward hooks on `language_model.layers[i - 1]`.
"""
import torch

from .base import BackboneBase, inject_lora, left_pad


class StudentAdapter(BackboneBase):
    def __init__(self, model, taps=(-1,), tap_norm=False, placeholder_id=None):
        super().__init__()
        self.student = model
        cfg = model.config
        self.text_config = getattr(cfg, 'text_config', cfg)
        self.hidden_size = self.text_config.hidden_size
        self.vocab_size = self.text_config.vocab_size
        self.n_layers = len(self.language_model.layers)
        self.image_token_id = getattr(cfg, 'image_token_id', None)
        self.video_token_id = getattr(cfg, 'video_token_id', None)
        pad = getattr(self.text_config, 'pad_token_id', None)
        self.placeholder_id = placeholder_id if placeholder_id is not None else (0 if pad is None else pad)
        self.taps, self.tap_norm = self.resolve_taps(taps), tap_norm
        self._subst = None
        self._tapped = {}
        self.input_module().register_forward_hook(self._substitute)
        for t in self.taps:
            if t < self.n_layers:
                self.language_model.layers[t - 1].register_forward_hook(self._capture(t))

    @classmethod
    def for_config(cls, model, cfg, **kw):
        return cls(model, taps=cfg.taps, tap_norm=cfg.tap_norm, **kw)

    @classmethod
    def from_pretrained(cls, path, cfg=None, student='qwen35', dtype=torch.bfloat16, **kw):
        try:
            from student_pilot.students import model_class
            klass = model_class(student)
        except ImportError:
            from transformers import Qwen3_5ForConditionalGeneration as klass
        model = klass.from_pretrained(path, dtype=dtype, local_files_only=True)
        return cls.for_config(model, cfg, **kw) if cfg is not None else cls(model, **kw)

    @classmethod
    def from_export(cls, base, export_dir, cfg=None, student='qwen35', **kw):
        """B1: `base` (a path to the base snapshot, or an already loaded bf16 base model) with every base
        tensor replaced by the export in `export_dir` (a milestone directory or its full_weights/)."""
        from pathlib import Path
        from student_pilot import full_ft
        directory = Path(export_dir)
        if (directory / 'MILESTONE.json').exists():
            full_ft.read_milestone(directory)
            directory = directory / full_ft.EXPORT_DIRECTORY
        if isinstance(base, (str, Path)):
            from student_pilot.students import model_class
            base = model_class(student).from_pretrained(base, dtype=torch.bfloat16, local_files_only=True)
        full_ft.load_export(base, directory)
        return cls.for_config(base, cfg, **kw) if cfg is not None else cls(base, **kw)

    @property
    def inner(self):
        return self.student.model

    @property
    def language_model(self):
        return self.inner.language_model

    def input_module(self):
        return self.inner.get_input_embeddings()

    def output_module(self):
        return self.student.lm_head

    def _substitute(self, module, args, output):
        if self._subst is None:
            return output
        mask, values = self._subst
        if mask.shape != output.shape[:2]:
            return output  # a call with another shape (not ours) passes through
        return torch.where(mask[..., None], values.to(output.dtype), output)

    def _capture(self, layer):
        def hook(module, args, output):
            self._tapped[layer] = output[0] if isinstance(output, tuple) else output
        return hook

    def _inputs(self, batch, ext):
        ids = batch['input_ids']
        mask = batch.get('attention_mask')
        mask = torch.ones_like(ids, dtype=torch.bool) if mask is None else mask.bool()
        tt = batch.get('mm_token_type_ids')
        if tt is None:
            tt = torch.zeros_like(ids)
            if self.image_token_id is not None:
                tt = tt + (ids == self.image_token_id).long()
            if self.video_token_id is not None:
                tt = tt + 2 * (ids == self.video_token_id).long()
        mask, ids, tt = left_pad(mask, ids, tt)
        kwargs = {k: batch[k] for k in ('pixel_values', 'image_grid_thw', 'pixel_values_videos', 'video_grid_thw')
                  if batch.get(k) is not None}
        subst = None
        if ext is not None:
            b, e = ext.shape[:2]
            ids = torch.cat([ids, ids.new_full((b, e), self.placeholder_id)], 1)
            tt = torch.cat([tt, tt.new_zeros(b, e)], 1)
            mask = torch.cat([mask, mask.new_ones(b, e)], 1)
            where = torch.zeros(ids.shape, dtype=torch.bool, device=ids.device)
            where[:, -e:] = True
            values = ext.new_zeros(*ids.shape, ext.shape[-1])
            values[:, -e:] = ext
            subst = (where, values)
        return ids, mask, tt, kwargs, subst

    def _run(self, subst, **kw):
        self._subst, self._tapped = subst, {}
        self.inner.rope_deltas = None  # never reuse M-RoPE deltas across calls
        try:
            return self.inner(**kw)
        finally:
            self._subst = None

    def _taps(self, out):
        states = []
        for t in self.taps:
            if t == self.n_layers:
                states.append(out.last_hidden_state)
            else:
                h = self._tapped[t]
                states.append(self.language_model.norm(h) if self.tap_norm else h)
        return torch.stack(states)

    def encode(self, batch, ext=None):
        ids, mask, tt, kwargs, subst = self._inputs(batch, ext)
        out = self._run(subst, input_ids=ids, attention_mask=mask.long(), mm_token_type_ids=tt,
                        use_cache=False, **kwargs)
        return self._taps(out), mask

    def decoder(self, batch, ext, use_cache=True):
        """KV-cached decoder (one LM step per token after the prefill); use_cache=False re-encodes."""
        if not use_cache:
            return super().decoder(batch, ext)
        ids, mask, tt, kwargs, subst = self._inputs(batch, ext)
        state = dict(mask=mask.long(), cache=None)

        def step(new):
            if new is None:
                out = self._run(subst, input_ids=ids, attention_mask=state['mask'], mm_token_type_ids=tt,
                                use_cache=True, **kwargs)
            else:
                b = new.shape[0]
                one = new.new_full((b, 1), self.placeholder_id)
                state['mask'] = torch.cat([state['mask'], state['mask'].new_ones(b, 1)], 1)
                # As transformers' generate(): text position from the mask, plus the prefill's M-RoPE deltas.
                text = (state['mask'].cumsum(-1) - 1).clamp(min=0)[:, -1:]
                deltas = self.inner.rope_deltas
                pos = (text + (0 if deltas is None else deltas.to(text.device)))[None].expand(3, -1, -1)
                self._subst = (torch.ones(b, 1, dtype=torch.bool, device=new.device), self.embed_ids(new[:, None]))
                try:
                    out = self.inner(input_ids=one, attention_mask=state['mask'], past_key_values=state['cache'],
                                     position_ids=pos, use_cache=True)
                finally:
                    self._subst = None
            state['cache'] = out.past_key_values
            return out.last_hidden_state[:, -1]
        return step

    def lm_parameters(self):
        return list(self.language_model.parameters()) + list(self.student.lm_head.parameters())

    def set_trainable(self, cfg):
        self.student.requires_grad_(False)
        if cfg.train_mode == 'full':
            for p in self.lm_parameters():
                p.requires_grad_(True)
        if cfg.train_mode == 'lora':
            names = '|'.join(cfg.lora_targets)
            inject_lora(self.inner, cfg, rf'.*language_model\.layers\.\d+\..*\.({names})$')
        if cfg.train_vision:
            self.inner.visual.requires_grad_(True)
        self._unfreeze_extra()
