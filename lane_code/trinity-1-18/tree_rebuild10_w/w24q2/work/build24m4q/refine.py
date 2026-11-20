from pathlib import Path
import time
L=Path.cwd()
def edit(name,fn):
 p=L/name;s=fn(p.read_text());old=L/'attic/build24m4q'/name;old.parent.mkdir(parents=True,exist_ok=True)
 if old.exists():old=old.with_name(old.name+'.'+str(time.time_ns()))
 p.rename(old);p.write_text(s)
edit('out/rcj/x.py',lambda s:s.replace('def observed(cfg, directory, **kwargs):','def observed(cfg, directory, *, compare=True):').replace('original_regenerate(cfg, directory, **kwargs)','original_regenerate(cfg, directory, compare=compare)'))
def ch(s):
 s=s.replace('def observed(*args, **kwargs):','def observed(*args):').replace('function(*args, **kwargs)','function(*args)')
 s=s.replace("for name, obj, attr in [('wording', WordingExclusion, 'check'),\n                ('text', row_text_audit, 'check'), ('extents', Extents, 'check'),\n                ('r1', r1_training, 'row_check'), ('reserve', Reserve, 'check'),\n                ('r2', Admission, 'check')]:\n            stack.enter_context(patch.object(obj, attr, self.wrap(name, getattr(obj, attr))))", "for name, obj, attr, fn in [('wording', WordingExclusion, 'check', WordingExclusion.check),\n                ('text', row_text_audit, 'check', row_text_audit.check), ('extents', Extents, 'check', Extents.check),\n                ('r1', r1_training, 'row_check', r1_training.row_check), ('reserve', Reserve, 'check', Reserve.check),\n                ('r2', Admission, 'check', Admission.check)]:\n            stack.enter_context(patch.object(obj, attr, self.wrap(name, fn)))")
 s=s.replace("receipt = dict(cfg, streams={stream: dict(database=source['database'], count=count)})", "database = dict(source['database'], path=str(pinned(source['database'])))\n            receipt = dict(cfg, streams={stream: dict(database=database, count=count)})")
 return s
edit('out/rcj/ch.py',ch)
