"""Opt-in adapter observation; original reader files and output dictionaries are untouched."""
import functools
import time
from common228 import append, write

def is_oom(error, torch):
    return isinstance(error,torch.cuda.OutOfMemoryError) or (
        isinstance(error,RuntimeError) and any(token in str(error).lower()
            for token in ('out of memory','alloc_failed')))

def install(parity, launch, torch, out, stop_file, limit, *, enabled=False):
    if enabled is not True:raise ValueError('Observation is OFF; explicit activation required')
    original_factory=parity.make_real;original_commit=launch.commit_record
    original_resolver=getattr(launch,'reader_factory',None)
    committed=[];active={'item':None,'phase':'load'}
    def peaks():
        return dict(max_memory_allocated=torch.cuda.max_memory_allocated(0),
                    max_memory_reserved=torch.cuda.max_memory_reserved(0))
    @functools.wraps(original_factory)
    def factory(*args,**kwargs):
        active.update(phase='load',item=None)
        original=original_factory(*args,**kwargs)
        torch.cuda.synchronize(0)
        append(out/'telemetry/memory.jsonl',dict(phase='load',**peaks()))
        @functools.wraps(original)
        def generate(item):
            active.update(phase='item',item=item['id'])
            torch.cuda.synchronize(0);torch.cuda.reset_peak_memory_stats(0)
            begin=time.monotonic();status='failed'
            try:
                result=original(item)
                torch.cuda.synchronize(0);status='complete'
                return result
            except BaseException as error:
                if is_oom(error,torch):
                    status='oom'
                    write(out/'telemetry/OOM.json',dict(phase='item',item=item['id'],error=str(error),**peaks()))
                    stop_file.write_text('OOM: no retry\n')
                raise
            finally:
                append(out/'telemetry/memory.jsonl',dict(phase='item',item=item['id'],status=status,
                    observed_seconds=time.monotonic()-begin,**peaks()))
        return generate
    @functools.wraps(original_commit)
    def commit(stream,row):
        original_commit(stream,row)
        if row.get('complete') is True and 'output' in row:
            committed.append(row['id'])
            if limit is not None and len(committed)>=limit:
                stop_file.write_text('Requested item prefix reached\n')
    parity.make_real=factory;launch.commit_record=commit
    if original_resolver is not None:
        @functools.wraps(original_resolver)
        def resolve(*args,**kwargs):
            # The sealed resolver checks make_real's source path. Let it inspect the
            # unchanged factory, then observe the returned generator when it is created.
            parity.make_real=original_factory
            try:return original_resolver(*args,**kwargs)
            finally:parity.make_real=factory
        launch.reader_factory=resolve
    def restore():
        parity.make_real=original_factory;launch.commit_record=original_commit
        if original_resolver is not None:launch.reader_factory=original_resolver
    return dict(committed=committed,active=active,peaks=peaks,
                restore=restore)
