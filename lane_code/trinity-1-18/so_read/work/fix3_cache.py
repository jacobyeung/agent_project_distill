from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');E=L/'work/src/u0'
p=E/'a0.py';s=p.read_text()
s=s.replace("    return result\n\n\ndef cache_bytes", "    only=settings.get('read_processor_only','off')\n    if only not in ('off','on'):raise ValueError('read_processor_only must be off or on')\n    if only=='on':result=dict(read_processor_cache='on',read_vision_cache='off',read_sam_cache='off')\n    return result\n\n\ndef cache_bytes",1)
s=s.replace('        self.stats = {}','        self.stats = {}\n        self.weight_guards = []',1)
pos=s.index('\n    def _room(')
s=s[:pos]+'''
    def guard_weights(self, provider):
        guard = WeightGuard(provider)
        self.weight_guards.append(guard)
        return guard

    def weight_boundary(self):
        for guard in self.weight_guards:guard.boundary()

'''+s[pos:]
s=s.replace('except RuntimeError:return None  # inference tensors still bind content below','except RuntimeError:return None')
s=s.replace('def module_identity(model):\n    """Stream live model identity/content; never assemble a model-sized key."""','def module_identity(model, *, weights=True):\n    """Bind runtime options; production calls omit weight bytes after guard.check()."""')
s=s.replace('digest((name,id(tensor),tensor.data_ptr(),tensor_version(tensor),digest(tensor)))','digest((name,id(tensor),tensor.data_ptr(),tensor_version(tensor),\n                             digest(tensor) if weights else tensor_stamp(tensor)))')
pos=s.index('\ndef has_hooks(')
s=s[:pos]+'''
class ModelMutationError(BaseException):
    """Fatal cache contract failure; item-level Exception handlers must not hide it."""


def tensor_stamp(tensor):
    return (id(tensor),tensor.data_ptr(),tensor_version(tensor),str(tensor.dtype),
            str(tensor.device),tuple(tensor.shape),tuple(tensor.stride()),tensor.requires_grad)


def weight_stamp(model):
    return (id(model),tuple((kind,name,tensor_stamp(tensor))
            for kind,iterator in (('p',model.named_parameters()),('b',model.named_buffers()))
            for name,tensor in iterator))


def weight_digest(model):
    h=hashlib.sha256()
    for kind,iterator in (('p',model.named_parameters()),('b',model.named_buffers())):
        for name,tensor in iterator:h.update(digest((kind,name,tensor)).encode())
    return h.hexdigest()


class WeightGuard:
    """Hash at install/boundaries; check identities and counters on every call.

    TensorImpl.h:291-305,2051-2054: .data does not share the counter and
    set_data preserves it. Boundary hashing guards untracked persistent writes.
    Inference tensors have no counter (TensorImpl.h:413-418); refuse them.
    """
    def __init__(self, provider):
        self.provider=provider;self.failed=False
        model=provider()
        if any(tensor_version(t) is None for t in (*model.parameters(),*model.buffers())):
            raise ModelMutationError('Cache weights require version counters')
        self.stamp=weight_stamp(model)
        self.content=weight_digest(model)

    def fail(self):
        self.failed=True
        raise ModelMutationError('Cache weights changed; reject this run and its journals')

    def check(self):
        if self.failed or weight_stamp(self.provider())!=self.stamp:self.fail()
        return self.content

    def boundary(self):
        self.check()
        if weight_digest(self.provider())!=self.content:self.fail()
        return self.content

'''+s[pos:]
s=s.replace('    original = visual.forward','    guard = cache.guard_weights(lambda:model.model.visual)\n    original = visual.forward',1)
s=s.replace('    def forward(*args, **kwargs):\n        if torch.is_grad_enabled()', '    def forward(*args, **kwargs):\n        guard.check()\n        if torch.is_grad_enabled()',1)
s=s.replace('# Bind identity and content: replacements and raw-storage writes must miss.','# Weight mutations fail the run; runtime-option changes produce distinct keys.')
s=s.replace('module_identity(visual),args,kwargs','module_identity(visual,weights=False),guard.content,args,kwargs')
p.write_text(s)
p=E/'a3.py';s=p.read_text();s=s.replace('    from .grounding import StageOneSocket\n','''    from .grounding import StageOneSocket
    guard = None
    if read_cache is not None:
        sam3_tower._load()
        guard = read_cache.guard_weights(lambda:sam3_tower._backend.model)
''',1)
s=s.replace('        def detect(name):\n','        def detect(name):\n            if guard is not None:guard.check()\n',1)
s=s.replace('try:live = module_identity(model)','try:live = (guard.content,module_identity(model,weights=False))')
p.write_text(s)
p=E/'a1.py';s=p.read_text().replace('    gen.generator, gen.load_info = generator, info','    gen.generator, gen.load_info = generator, info\n    if read_cache is not None and read_cache.weight_guards:\n        gen.weight_boundary = read_cache.weight_boundary')
p.write_text(s)
p=E/'a4.py';s=p.read_text();pos=s.index('\ndef run(args,')
s=s[:pos]+'''
@contextmanager
def weight_journal(generator, out):
    """A journal with unchecked weight-dependent rows cannot resume or merge."""
    boundary=getattr(generator,'weight_boundary',None)
    if boundary is None:
        yield
        return
    from .atomic_journal import atomic_write
    receipt=out/'WEIGHTS.json'
    def state(value):atomic_write(receipt,(json.dumps({'verified':value})+'\\n').encode())
    state(False)
    try:
        boundary()
        yield
    finally:
        # A fatal mismatch leaves verified=False, even across process restarts.
        boundary()
    state(True)

'''+s[pos:]
# After normal exception/deadline with unchanged weights, finally verifies but state(True) is skipped:
# intentionally fail closed on interrupted weighted journals; documented in NOTE.
s=s.replace("    with writer_guard(out,binding,atomic=getattr(args,'atomic_journal',False),", "    receipt=out/'WEIGHTS.json'\n    if receipt.exists() and json.loads(receipt.read_text()).get('verified') is not True:\n        raise ValueError('Unchecked cache weights; use a fresh journal')\n    with writer_guard(out,binding,atomic=getattr(args,'atomic_journal',False),",1)
start=s.index('                    try:\n                        for item in todo:')
end=s.index('                    timings.append(',start)
chunk=s[start:end]
s=s[:start]+"                    with weight_journal(generator,out):\n"+''.join('    '+line if line.strip() else line for line in chunk.splitlines(True))+s[end:]
p.write_text(s)
p=E/'a6.py';s=p.read_text().replace("    for root in map(Path,roots):\n", "    for root in map(Path,roots):\n        receipt=root/'WEIGHTS.json'\n        if receipt.exists() and json.loads(receipt.read_text()).get('verified') is not True:\n            raise ValueError('Unchecked cache weights; cannot merge journal')\n",1);p.write_text(s)
p=E/'a18.py';s=p.read_text().replace("('read_processor_cache','read_vision_cache','read_sam_cache')","('read_processor_cache','read_vision_cache','read_sam_cache','read_processor_only')");p.write_text(s)
p=E/'tests/test_off.py';p.write_text(p.read_text().replace('range(11)','range(19)'))
with (L/'work/STATUS.md').open('a') as f:
 import subprocess
 f.write(subprocess.check_output(['date','-u'],text=True)+'Round 3: out copied to out_round3; cache guards and processor-only switch implemented. Weight-dependent journals fail closed on incomplete validation.\n')
