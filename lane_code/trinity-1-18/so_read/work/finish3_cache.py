from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');p=L/'work/src/u0/a0.py';s=p.read_text()
s=s.replace("    return (id(model),tuple((kind,name,tensor_stamp(tensor))\n            for kind,iterator in (('p',model.named_parameters()),('b',model.named_buffers()))\n            for name,tensor in iterator))", "    h=hashlib.sha256(str(id(model)).encode())\n    for kind,iterator in (('p',model.named_parameters()),('b',model.named_buffers())):\n        for name,tensor in iterator:h.update(digest((kind,name,tensor_stamp(tensor))).encode())\n    return h.hexdigest()")
s=s.replace("if any(tensor_version(t) is None for t in (*model.parameters(),*model.buffers())):", "if any(tensor_version(t) is None for iterator in (model.parameters(),model.buffers()) for t in iterator):")
s=s.replace('    def guard_weights(self, provider):\n        guard',"    def guard_weights(self, provider):\n        if len(self.weight_guards)>=2:raise ValueError('At most two frozen modules per read cache')\n        guard",1)
p.write_text(s)
