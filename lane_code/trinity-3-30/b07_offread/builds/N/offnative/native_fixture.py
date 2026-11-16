"""A tiny prefill boundary drives C8r's unchanged decode loop and call servers."""
from contextlib import contextmanager
from types import SimpleNamespace as NS
import numpy as np
from .fixture import Tokenizer
from .c8 import install


@contextmanager
def tiny_prefill(model, geometry, backend=None):
    import torch
    from student_pilot import carrier_c1_decode as D, trace_format313 as F
    original = D._prepare_decode
    def prepare(wrapper, processor, batch, **kwargs):
        output = model(**batch, use_cache=True)
        heads = NS(pose9=np.zeros((32,9)), gravity=np.array([0.,0.,1.]), queries=[],
                   grounding_head=None, mdg_states=None, mdg_backend=backend)
        state = NS(native=model, output=output, heads=heads, geometry=None, geometry_error=None,
                   prompt_length=batch['input_ids'].shape[1], cap=4096,
                   tokenizer=processor.tokenizer, openers=set(processor._routing_tokens['ids'].values()),
                   mdg=None, stream=None, ground_backend=backend, tool_context=NS(),
                   verify_session=None, rereader=None)
        F.bind_state(state)
        return state
    D._prepare_decode = prepare
    try:
        yield
    finally:
        D._prepare_decode = original


class NativeTiny:
    kind = 'harness'
    def __init__(self, tower):
        import torch
        from transformers import Qwen3Config, Qwen3ForCausalLM
        self.P = install()
        torch.set_num_threads(1)
        torch.manual_seed(544)
        self.model = Qwen3ForCausalLM(Qwen3Config(vocab_size=265, hidden_size=16,
            intermediate_size=32, num_hidden_layers=1, num_attention_heads=2,
            num_key_value_heads=1, head_dim=8, max_position_embeddings=4096,
            eos_token_id=263)).eval()
        self.model.trace_program_version = '3.14'
        self.model.carrier_id = 0
        class NativeTokenizer(Tokenizer):
            specials = Tokenizer.specials+['</think>']
            def convert_ids_to_tokens(self,token):return self.decode([token])
        tok = NativeTokenizer()
        self.processor = NS(tokenizer=tok, _routing_tokens={'ids':{s:tok.convert_tokens_to_ids(s)
                            for s in ('<move','<turn','<pose','<ground','<gap')}})
        self.tower = tower
        self.tower_calls = 0
        self.contexts = {}
        from student_pilot.ground_profiles import load_geometry
        from student_pilot.scene_state import FrameMap
        self.geo = load_geometry(tower, FrameMap(tuple(range(32))), 'tower_scaled')
        from .cache_fixture import backend
        from pathlib import Path
        self.backend = backend(self.geo,Path(tower).parent/'ground_audit')

    def generate(self, frames, question, *, served=True):
        import torch
        typ = question['question_type']
        if typ.startswith('room_size_estimation'):
            call = '<ground mode="room">'
        elif typ.startswith('object_abs_distance'):
            # C8r records its native refusal when no mask source exists.
            call = '<ground obj="unknown" mode="box">' if question.get('fixture_refusal') else '<ground obj="chair" mode="box">'
        elif typ in ('camera_displacement','camera_movement_direction','camera_rotation'):
            call = '<move from=1 to=2>'
        else:
            call = ''
        if not served: call = ''
        text = '<think>'+call+'</think>\n2'
        tokens = self.processor.tokenizer.encode(text)+[263]
        cursor = iter(tokens)
        def tap(ids, logits):
            value = torch.full_like(logits, -float('inf'))
            value[:,next(cursor)] = 0
            return value
        batch = {'input_ids':torch.tensor([[65]]), 'attention_mask':torch.ones((1,1),dtype=torch.long)}
        self.backend.begin_question()
        with tiny_prefill(self.model, self.geo, self.backend):
            result = self.P.generate(self.model, self.processor, batch, self.geo, self.backend, tap=tap,
                                     budget=__import__('reader_policy').DECODE_BUDGET)
        if any(('mask_source_unavailable' in str(c.get('code','')) or 'mask_cache_operand_missing' in str(c.get('code',''))) for c in result.get('calls',[])):
            result['strict_no_answer'] = True
            result['operand_refusal'] = True
        self.tower_calls += bool(call)
        self.contexts[id(result)] = self.geo
        return result

    def replay(self, decoded):
        return self.P.replay(decoded, self.contexts[id(decoded)], self.backend)['byte_equal']


def write_geometry(path):
    camera = np.repeat(np.eye(4)[None],32,axis=0)
    camera[:,:3,:3] = np.array([[1.,0,0],[0,0,1.],[0,-1.,0]])
    camera[:,0,3] = np.arange(32)*.03
    K = np.repeat(np.array([[16.,0,8],[0,16.,8],[0,0,1.]])[None],32,axis=0)
    uv = np.linspace(0,1000,51)
    np.savez(path,profile='scaled_g3t_depth',depth_unit='unscaled',pose_unit='unscaled',
             reference_source_frame=0,K=K,canvas_to_source=np.repeat(np.diag([.016,.016,1.])[None],32,axis=0),
             camera_to_world=camera,scale=1.,depth_scale_count=0,pose_scale_count=0,
             anchor_frame_indices=np.arange(32),depth_grid=np.broadcast_to(2+np.linspace(0,.2,51)[None,:,None]+np.linspace(0,.1,51)[None,None,:],(32,51,51)),grid_uv=uv)
