"""Lazy model adapters; importing navrun never loads torch or touches a GPU.

The adapter accepts already-loaded local model/processor objects. Generation is
restricted to one grammar arm after an explicit, empty native thinking block.
Rendered RGB frames are required. CPU proofs do not instantiate this adapter.
"""
from .prompts import prompt, TEMPLATE_SHA256
from .vendor import nav_text as NT

class NativePolicy:
    name = 'native-model'
    def __init__(self, model, processor, output_format='nav', history_frames=32, max_new_tokens=96, checkpoint_sha256=None):
        if output_format not in ('nav', 'click'):
            raise ValueError('Constrained native generation supports nav and click')
        self.model, self.processor = model, processor
        self.output_format, self.history_frames = output_format, history_frames
        self.max_new_tokens = max_new_tokens
        self.tokenizer = getattr(processor, 'tokenizer', processor)
        self.trie = NT.constraint(self.tokenizer, output_format, history_frames)
        self.template_sha256 = TEMPLATE_SHA256
        self.checkpoint_sha256 = checkpoint_sha256

    def resume_identity(self):
        if not self.checkpoint_sha256:
            raise ValueError('Persistent model evaluation requires checkpoint_sha256')
        return dict(checkpoint_sha256=self.checkpoint_sha256, template_sha256=self.template_sha256,
                    output_format=self.output_format, history_frames=self.history_frames,
                    max_new_tokens=self.max_new_tokens, thinking='forced_empty')

    def reset(self, episode_id):
        pass

    def act(self, history_frames, instruction, state):
        if len(history_frames) != self.history_frames or any(x is None for x in history_frames):
            raise ValueError('NativePolicy requires rendered RGB history')
        text = prompt(instruction, state['executed'], self.output_format, self.history_frames)
        messages = [{'role': 'user', 'content': [{'type': 'image', 'image': frame} for frame in history_frames]
                     + [{'type': 'text', 'text': text}]}]
        rendered = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                                     enable_thinking=True)
        # The native template owns all role and image tokens. The action constraint
        # begins after a complete thinking block, never on its closing-token boundary.
        if rendered.rstrip().endswith('<think>'):
            rendered += '\n</think>\n'
        elif '</think>' not in rendered.rsplit('assistant', 1)[-1]:
            rendered += '<think>\n</think>\n'
        inputs = self.processor(text=[rendered], images=history_frames, return_tensors='pt')
        inputs = inputs.to(self.model.device)
        length = inputs['input_ids'].shape[1]
        output = self.model.generate(**inputs, do_sample=False, max_new_tokens=self.max_new_tokens,
                                     prefix_allowed_tokens_fn=NT.prefix_allowed_tokens_fn(self.trie, length))
        return self.tokenizer.decode(output[0, length:], skip_special_tokens=True)

class CallablePolicy:
    """Bridge a local inference process/client through a serializable whitelist.

    transport(payload) returns answer text. It is supplied by the caller; this
    package opens no connections and makes no network requests.
    """
    name = 'callable-model'
    def __init__(self, transport, identity=None):
        self.transport = transport
        self.identity = identity
    def resume_identity(self):
        if self.identity is None:
            raise ValueError('Persistent callable evaluation requires an explicit model/config identity')
        return self.identity
    def act(self, history_frames, instruction, state):
        return self.transport(dict(frames=history_frames, instruction=instruction,
                                   executed=state['executed'], decision_index=state['decision_index'],
                                   constants=state['constants']))
