"""Explicit CPU stand-ins for phase and socket tests, never eligible for submission."""
from pathlib import Path
import re
from types import SimpleNamespace as NS
import numpy as np
from .io import dump, sha, load
from .paths import B04
from .readers import E2EReader
from .frames import sample, dense
from offkit.report import key

class Tokenizer:
    specials = ['<tool_response>','</tool_response>','<move','<turn','<pose','<ground','<gap','<|im_end|>']
    eos_token_id = 263
    def encode(self, text, add_special_tokens=False):
        parts = re.split('('+'|'.join(map(re.escape, self.specials))+')', text)
        return [t for s in parts if s for t in ([256+self.specials.index(s)] if s in self.specials else list(s.encode()))]
    def decode(self, ids, skip_special_tokens=False):
        return ''.join(self.specials[i-256] if i>=256 else chr(i) for i in ids)
    def convert_tokens_to_ids(self, text):
        return 256+self.specials.index(text)

class TinyEntry:
    def __init__(self, artifact, tower, kind):
        import torch
        from transformers import Qwen3Config, Qwen3ForCausalLM
        from e2e_reader.callhook import CallHook
        torch.set_num_threads(1)
        torch.manual_seed(544)
        self.model = Qwen3ForCausalLM(Qwen3Config(vocab_size=264, hidden_size=16,
            intermediate_size=32, num_hidden_layers=1, num_attention_heads=2,
            num_key_value_heads=1, head_dim=8, max_position_embeddings=4096)).eval()
        self.tok = Tokenizer()
        self.hook = CallHook(self.tok, [258,259,260,261,262], error_suffix=False)
        self.artifact, self.tower, self.kind = artifact, tower, kind
        self.tower_calls = 0
        self.records = []

    def generate(self, frames, question, *, served=True):
        import torch
        from e2e_reader.generate import generate
        from e2e_reader.callhook import call_family
        question_type = question['question_type']
        routed = question_type.startswith(('object_abs_distance','room_size_estimation'))
        room = question_type.startswith('room_size_estimation')
        refused = question.get('fixture_refusal', False) and served
        call = '<ground mode="room">' if room else '<ground obj="chair" mode="box">'
        raw_script = '<think>inspect '+(call if routed else '')+'</think>\n'+('7' if refused else '2')
        scripted = self.tok.encode(raw_script) + [self.tok.eos_token_id]
        state = {'i':0}; entry = self
        class Perception:
            def lazy(self, frames, output, timings):
                def serve(text):
                    with np.load(entry.tower, allow_pickle=False) as z:
                        value = float(z['depth'][0,0])
                    entry.tower_calls += 1
                    return ('error: fixture_refusal' if refused else f'distance {value:.2f} m'), {'kind':'error' if refused else 'ground'}
                return ({'ground':serve,'room':serve} if served else {}), {}
        def script(ids, logits):
            token = scripted[state['i']]; state['i'] += 1
            out = torch.full_like(logits, -1e9); out[...,token] = 0
            return out
        result = generate(self.model, self.hook, Perception(), frames, [65], artifact=self.artifact,
                          eos_ids=[self.tok.eos_token_id], max_new_tokens=2048, logits_processor=script)
        decoded = dict(tokens=result['tokens'], text=result['text'], calls=result['hook']['records'],
                       finish='program_refusal' if refused else result['finish'], audit=result['audit'],
                       model_prefills=result['model_prefills'], model_steps=result['model_steps'])
        self.records.append(decoded)
        return decoded

    def replay(self, decoded):
        # Recompute every served response from the pinned synthetic tower.
        with np.load(self.tower, allow_pickle=False) as z:
            text = f"distance {float(z['depth'][0,0]):.2f} m"
        for c in decoded['calls']:
            if c.get('served') and c['response'] != ('error: fixture_refusal' if c.get('kind')=='error' else text):
                return False
        return True

class FixtureHarness:
    kind = 'harness'
    def __init__(self, entry): self.entry = entry
    def generate(self, frames, question, *, served=True):
        return self.entry.generate(frames, question, served=served)
    def replay(self, decoded): return self.entry.replay(decoded)

class Runtime:
    synthetic = True
    def __init__(self, root, items, kind, *, mutate_proof=False, benchmark='revsi999t32'):
        self.root, self.items, self.kind = Path(root), items, kind
        self.mutate_proof = mutate_proof
        self.benchmark = benchmark
        self.root.mkdir(parents=True, exist_ok=True)

    def stage(self, config):
        from e2e_reader.artifact import Artifact, write_manifest
        from .staging import archive
        from .io import tar_bytes
        self.tower = self.root/'1.npz'
        np.savez(self.tower, depth=np.ones((2,2)), pose=np.eye(4), boxes=np.zeros((1,6)))
        bundle=self.root/'0.tar'
        bundle.write_bytes(tar_bytes({'1.npz':self.tower.read_bytes()}))
        staging=archive(bundle,sha(bundle),self.root/'staged',max_bytes=100000)
        self.tower=self.root/'staged/1.npz'
        file = dict(rel='1.npz', sha256=sha(self.tower), bytes=self.tower.stat().st_size)
        manifest = dict(schema='e2e-artifact-v1', components={'fixture':dict(role='fixture',files=[file])}, code=[])
        path, checksum = write_manifest(self.root/'staged', manifest)
        artifact = Artifact(self.root/'staged', path.name, checksum, required_roles=()).verify()
        self.entry = TinyEntry(artifact, self.tower, self.kind)
        if self.kind=='e2e':
            self.reader = E2EReader(self.entry, self.entry.replay)
        else:
            from .native_fixture import NativeTiny, write_geometry
            geometry_path = self.root/'geometry.npz'
            write_geometry(geometry_path)
            self.entry = NativeTiny(geometry_path)
            self.reader = self.entry
        self.videos = []
        import av
        for n in range(2):
            path = self.root/(str(n)+'.mp4')
            with av.open(str(path), 'w') as output:
                stream = output.add_stream('mpeg4',rate=24); stream.width=16; stream.height=16; stream.pix_fmt='yuv420p'
                for i in range(96 if self.benchmark=='vsibench5130' else 64):
                    frame = av.VideoFrame.from_ndarray(np.full((16,16,3),(i+n)%256,dtype=np.uint8),format='rgb24')
                    for packet in stream.encode(frame): output.mux(packet)
                for packet in stream.encode(): output.mux(packet)
            if self.benchmark=='revsi999t32':
                from .media import decode
                original=path;path=self.root/(str(n)+'_32.mp4')
                arrays=decode(original)
                with av.open(str(path),'w') as output:
                    stream=output.add_stream('mpeg4',rate=24);stream.width=16;stream.height=16;stream.pix_fmt='yuv420p'
                    for i in range(32):
                        frame=av.VideoFrame.from_ndarray(arrays[i*63//31],format='rgb24')
                        for packet in stream.encode(frame):output.mux(packet)
                    for packet in stream.encode():output.mux(packet)
            self.videos.append(path)
        return dict(synthetic=True, assets=[dict(path=p.name,sha256=sha(p)) for p in self.videos+[self.tower]],
                    staging=staging,core='C8r native decode and call servers with tiny prefill; b04 e2e generate with tiny model')

    def frames(self, frames):
        self.sampled, receipts = {}, []
        for i,p in enumerate(self.videos):
            a,r = sample(p,frames)
            from .frames import selected, aligned_dense
            if self.benchmark=='revsi999t32':
                dense_images=selected(self.root/(str(i)+'.mp4'),list(range(64)))
                dense_indices=list(range(64));slots=[j*63//31 for j in range(32)]
            else:
                dense_images,dense_indices,slots=aligned_dense(p,r['indices'],r['total'])
            dr = dict(count=len(dense_images), source='original', indices=dense_indices,anchor_slots=slots)
            self.sampled[str(i)] = (dict(native_frames=dense_images,dense_indices=dense_indices,
                anchor_indices=[dense_indices[s] for s in slots],anchor_slots=slots,model_frames=a[::2])
                if self.kind=='e2e' else a)
            receipts.append(dict(model=r,dense=dr))
        return receipts

    def frames_for(self, item):
        return self.sampled[item['scene_name']]

    def towers(self, reader):
        return dict(synthetic=True, lazy=reader['kind']=='e2e',
                    sha256=sha(self.tower), frames='same two synthetic source videos')

    def proof(self):
        refs, actual = [], []
        for i in range(10):
            typ = 'camera_displacement' if i<5 else 'object_abs_distance'
            q = dict(question_type=typ, question='fixture proof', id=str(i),fixture_refusal=i>=5)
            a = self.reader.generate(self.sampled['0'], q)
            b = self.reader.generate(self.sampled['0'], q)
            if self.mutate_proof and i==5:
                b['calls'][0]['response'] += ' changed'
            refs.append(dict(key=str(i),question_type=typ,decode=a))
            actual.append(dict(key=str(i),question_type=typ,decode=b))
        return refs, actual
