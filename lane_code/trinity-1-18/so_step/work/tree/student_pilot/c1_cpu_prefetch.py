"""One CPU producer; admission and every distributed call stay on the training thread."""
from concurrent.futures import ThreadPoolExecutor
import copy
import threading

import torch

MAX_GROUP_ROWS = 8
MAX_GROUP_TENSOR_BYTES = 1 << 30


def tensor_bytes(value):
    if isinstance(value, torch.Tensor):
        return value.untyped_storage().nbytes()
    if isinstance(value, dict):
        return sum(tensor_bytes(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return sum(tensor_bytes(v) for v in value)
    return 0


def _cpu_only(value):
    if isinstance(value, torch.Tensor):
        if value.device.type != 'cpu':
            raise ValueError('C1 CPU prefetch received a non-CPU tensor')
    elif isinstance(value, dict):
        for item in value.values():
            _cpu_only(item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            _cpu_only(item)


class Producer:
    def __init__(self, factory):
        self.factory = factory
        self.rows = None
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='c1-row-cpu')
        self.owner = threading.get_ident()

    def prepare(self, stream, indices, check, model):
        # Connections are opened, queried and closed on this single worker. Keep
        # sqlite's check_same_thread=True; never pass a live main-thread connection.
        if self.rows is None:
            try:
                self.rows = self.factory()
            except Exception as exc:
                return [(False, exc) for _ in indices]
        result = []
        held_bytes = 0
        for index in indices:
            try:
                item = self.rows.get(stream, index)
                _cpu_only(item)
                check(item[0], item[1], stream, model)
                held_bytes += tensor_bytes(item)
                if held_bytes > MAX_GROUP_TENSOR_BYTES:
                    raise ValueError('C1 prefetch group exceeds 1 GiB encoded tensor budget')
                result.append((True, item))
            except Exception as exc:
                # Do not retain failed-row tensors through traceback frames.
                exc.__traceback__ = None
                result.append((False, exc))
            item = None
        return result

    def close(self):
        if threading.get_ident() != self.owner:
            raise RuntimeError('Close the CPU producer on its owning training thread')
        try:
            if self.rows is not None:
                self.pool.submit(self.rows.close).result()
        finally:
            self.pool.shutdown(wait=True)


def for_rows(rows):
    producer = getattr(rows, '_c1_cpu_producer', None)
    if producer is None:
        # Each producer owns its tokenizer, image/video processor and SQLite
        # connections. The main thread retains its processor for own-value routing.
        # No call changes PyTorch's process-wide thread count or global RNG state.
        try:
            factory = rows.cpu_prefetch_factory()
        except Exception as exc:
            # A processor-copy/setup failure is also a local preparation failure.
            # Carry it to the original group admission instead of stranding peers.
            def factory(error=exc):
                raise error
        producer = rows._c1_cpu_producer = Producer(factory)
    return producer


class Replay:
    """Feed prepared values/errors through the unchanged fetch admission code."""
    def __init__(self, rows, stream, indices, values):
        self.rows, self.stream = rows, stream
        self.values = iter(zip(indices, values))

    def count(self, stream):
        return self.rows.count(stream)

    def get(self, stream, candidate):
        index, (ok, value) = next(self.values)
        if stream != self.stream or candidate != index:
            raise RuntimeError('C1 prefetch candidate order changed')
        if not ok:
            raise value
        return value


def fetch_groups(rows, model, groups, rank, device, distributed):
    from .carrier_c1_run import check_row, fetch, fetch_nominal
    from .c1_switches import prefetch_supported
    prefetch_supported(model, [stream for group in groups for stream, _ in group])
    if any(not 1 <= len(group) <= MAX_GROUP_ROWS for group in groups):
        raise ValueError('C1 prefetch requires admission groups of 1..8 rows')
    producer = for_rows(rows)

    def submit(group):
        stream = group[0][0]
        indices = [part[rank] % rows.count(stream) for _, part in group]
        return producer.pool.submit(producer.prepare, stream, indices, check_row, model)

    future = submit(groups[0]) if groups else None
    try:
        for group_id, group in enumerate(groups):
            stream = group[0][0]
            indices = [part[rank] for _, part in group]
            candidates = [index % rows.count(stream) for index in indices]
            replay = Replay(rows, stream, candidates, future.result())
            # Original fetch functions retain the MIN all_reduce, its position,
            # error text, and the repeated cheap CPU validation on the main thread.
            if len(group) == 1:
                admitted = [fetch(replay, stream, indices[0], model, device=device, distributed=distributed)]
            else:
                admitted = fetch_nominal(replay, stream, indices, model, device=device, distributed=distributed)
            replay.values = None
            # Do not speculate past an unadmitted group. A row failure therefore
            # makes precisely the same get calls as the synchronous path, even on
            # the healthy rank, and raises at the same nominal microstep boundary.
            future = submit(groups[group_id + 1]) if group_id + 1 < len(groups) else None
            for slot in range(len(admitted)):
                item = admitted[slot]
                admitted[slot] = None
                yield item
                item = None
    finally:
        # Drain in-flight CPU work on early consumer exit; its exception is data,
        # not an exception raised on the worker or at an earlier microstep.
        if future is not None:
            future.result()


def rows_factory(rows):
    from .carrier_c1_run import Rows
    if any(not hasattr(source, 'conn') for mix in getattr(rows, 'mixes', {}).values()
           for source in mix.sources):
        raise ValueError('C1 CPU prefetch has not audited clip mix sources')
    receipt = copy.deepcopy(rows._cpu_prefetch_receipt)
    processor = copy.deepcopy(rows.processor)
    return lambda: Rows(receipt, processor)
