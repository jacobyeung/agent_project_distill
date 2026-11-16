"""EAT-1 adapter for the real C8r no-MDG routed reader (operator, GPU). UNTESTED on GPU: CPU compile only.

It mirrors the unflagged arm of `nomdg.run` (code_c8r.tar native/out2/nomdg.py:333-500) item by item:
load once with `read_runtime.load_model`, then per item `trainer_row` -> `runtime.prompt_batch` ->
`P.load_geometry` -> `masks.for_item` + `P.backend` for distance/room -> `P.generate`. It adds nothing the
reader does not do and skips the scripted arm, the parity probe and the trace emitter (they score nothing).
Every refusal path stays in place: a geometry or operand refusal returns the reader's own `refusal_decode`
record, and a raised refusal becomes an item error. EAT-1 judges both under A4.

EAT-1 item: {"id": "<task id>", "type": "<question_type>", "frames": "<task key, devrows:...>", "question": ...}.
`frames` carries the task key; the reader resolves the clip from its own request. The operator writes the
claimed artifact manifest (eat1-artifact-v1) at `artifact_manifest`: the export files (full_weights shards,
heads.pt, artifact.json, tokenizer and config) and every frozen tower weight file the read loads (G3T, SAM 3),
each by sha256. A1 then lists every other data file opened during generate().
"""
import sys
from pathlib import Path

FIELDS = {  # call kind/opener -> manifest module names behind its response
    '<pose': ['pose_head'], '<move': ['pose_head'], '<turn': ['pose_head'], '<depth_at': ['pose_head', 'depth_head'],
    '<ground': ['sam3', 'g3t', 'pose_head'], '<gap': ['sam3', 'g3t', 'pose_head'],
}


class C8rNativeReader:
    def __init__(self, out2, request_dir, artifact_manifest, device='cuda:0', grounding_out=None):
        out2 = str(Path(out2).resolve())
        if out2 not in sys.path:
            sys.path.insert(0, out2)
        import nomdg as N
        import perception as P
        import read_runtime
        from common import checked, install_tree, load, local
        install_tree()
        from evalpath import runtime
        from evalpath.items import assert_prompt_equal
        from evalpath.run import official
        from routed import trainer_row
        self.N, self.P, self.runtime, self.official = N, P, runtime, official
        self.trainer_row, self.assert_prompt_equal = trainer_row, assert_prompt_equal
        self.request = request = N.validate_request(load(local(request_dir)/'request.json'), live=True)
        if request['schema'] != 'legs1-routed-nomdg-v1':
            raise ValueError('This adapter wraps the no-MDG routed reader only')
        self.cfg = load(checked(request['config']))
        selected = dict(root=str(N.TREE), sources={n.removeprefix('student_pilot/'): h for n, h in
                                                   request['tree_sources'].items() if n.startswith('student_pilot/')})
        self.model, self.processor, self.info = read_runtime.load_model(
            request['config'], request['artifact'], request['data_receipt'], device=device, selected_trainer=selected)
        self.tokenizer = self.processor.tokenizer
        tasks, self.captures = N.tasks_and_captures(request['inputs'])
        self.tasks = {'devrows:'+t['id']: t for t in tasks}
        self.refs = load(checked(request['inputs']['references']))
        self.geometry = load(checked(request['grounding']['geometry_manifest']))
        self.masks = P.Masks(request['mask_cache'])
        self.device = device
        self.grounding_out = Path(grounding_out or Path(request_dir)/'eat1_grounding')
        self.artifact_manifest = Path(artifact_manifest)

    def lm(self):
        return (self.model.model, self.model.lm_head)

    def generate(self, frames, question):
        from trace_format.program_errors import ProgramRefusal
        N, P, request = self.N, self.P, self.request
        task = self.tasks[frames]
        if question != task['question']:
            raise ValueError('EAT-1 item question differs from the reader task')
        row = self.trainer_row(task, self.captures[task['native']], request['frames_root'], verify=True)
        self.assert_prompt_equal(self.processor, row)
        batch = N.move_batch(self.runtime.prompt_batch(self.processor, row, self.cfg, 'routed'), self.device)
        geo = P.load_geometry(self.geometry, row)
        backend = None
        refusal = request['mask_operand_refusals'].get(task['id'])
        if N.mask_source(task['question_type']) and not refusal:
            source = self.masks.for_item(task['native'], row, batch, operands=P.script_operands(task, self.refs))
            backend = P.backend(row, batch, geo, source, self.grounding_out/N.digest(frames))
        if refusal:
            decoded = N.refusal_decode(refusal)
        else:
            try:
                decoded = P.generate(self.model, self.processor, batch, geo, backend, budget=request['decode_budget'])
            except ProgramRefusal as exc:
                decoded = N.refusal_decode(str(exc))
        calls = [dict(call=c['call'], response=c.get('response'),
                      fields={} if c.get('kind') == 'error' else
                      {c.get('kind', 'value'): next((v for k, v in FIELDS.items() if c['call'].startswith(k)), [])})
                 for c in decoded.get('calls', [])]
        answer, _ = self.official.extract_q35_final_answer(decoded.get('text', ''), enable_thinking=True)
        return dict(text=decoded.get('text', ''), answer=answer, calls=calls, finish=decoded.get('finish'),
                    refusal=decoded.get('refusal'))


def make_reader(**kwargs):
    return C8rNativeReader(**kwargs)
