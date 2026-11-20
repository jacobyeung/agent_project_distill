"""Observe the first forward without changing its inputs, outputs or admission."""
from contextlib import contextmanager
from pathlib import Path


def snapshot(processor):
    from student_pilot.pose_samples import DEFAULT_PIXELS
    tokenizer = processor.tokenizer if hasattr(processor, 'tokenizer') else None
    present = hasattr(processor, '_b7_layout')
    layout = processor._b7_layout if present else {}
    pixels = (layout['min_pixels'], layout['max_pixels']) if present else DEFAULT_PIXELS
    return dict(_c1_frame_count=tokenizer._c1_frame_count if hasattr(tokenizer, '_c1_frame_count') else None,
                _c1_frame_markers=tokenizer._c1_frame_markers if hasattr(tokenizer, '_c1_frame_markers') else None,
                _b7_layout=present,
                frame_count=tokenizer._c1_frame_count if hasattr(tokenizer, '_c1_frame_count') else 32,
                frame_markers=tokenizer._c1_frame_markers if hasattr(tokenizer, '_c1_frame_markers') else False,
                pixel_bounds=list(pixels), pixel_source='layout' if present else 'default')


def grouped(records):
    streams = {}
    for row in records:
        value = streams.setdefault(row['stream'], dict(rows=[], frame_count=[], pixel_bounds=[],
                                                       token_counts=[], loss=[], finite=True))
        value['rows'].append(row)
        count = (row.get('processor') or {}).get('frame_count')
        if count not in value['frame_count']:
            value['frame_count'].append(count)
        observed = [call['pixel_bounds'] for call in row['calls'] if call['kind'] == 'frames']
        for pixels in observed or [None]:
            if pixels not in value['pixel_bounds']:
                value['pixel_bounds'].append(pixels)
        value['token_counts'].append(dict(tokens=row.get('tokens'), effective_tokens=row.get('effective_tokens')))
        value['loss'].append(row.get('loss'))
        value['finite'] = value['finite'] and row.get('finite') is True
    return streams


@contextmanager
def recording(kit, root, job):
    from student_pilot import carrier_c1_run as run, carrier_c1_data as data, pose_samples as samples
    from rv import location, put, encoded
    original = run.first_batch_check

    def checked(cfg, ranks, out_path, steps=1, device='cpu', progress_dir=None, rank_limit=None, encode_only=False, start_step=0):
        factory, fetch, check = run.processor_for_receipt, run.fetch, run.check_plan_rows
        frames, layout_fn = samples.encode_frames, data.encode_layout_row
        processors, active, observations, errors = [], [], [], []
        local = Path(root) / 'f1.json'

        def observe(fn):
            # Evidence collection cannot add an admission condition.
            try:
                return fn()
            except Exception as error:
                errors.append(type(error).__name__)
                return None

        def make(manifest, receipt):
            processor = factory(manifest, receipt)
            processors.append(processor)
            return processor

        def get(rows, stream, index, model, tries=8, device=None, distributed=False):
            item = dict(stream=stream, index=index, calls=[])
            observations.append(item)
            active.append(item)
            def capture():
                item['processor'] = snapshot(rows.processor)
                item['same_processor'] = any(rows.processor is p for p in processors)
            observe(capture)
            try:
                return fetch(rows, stream, index, model, tries, device, distributed)
            finally:
                active.pop()

        def encode_frames(processor, question, options, arrays, metadata, target, pixels=samples.DEFAULT_PIXELS, max_length=16384):
            if active:
                def capture():
                    active[-1]['calls'].append(dict(kind='frames', processor=snapshot(processor),
                        same_processor=any(processor is p for p in processors), pixel_bounds=list(pixels),
                        encoded_frame_count=len(arrays)))
                observe(capture)
            return frames(processor, question, options, arrays, metadata, target, pixels, max_length)

        def encode_layout(processor, row, layout, gap, native_g3t=False, gf1=None):
            if active:
                observe(lambda: active[-1]['calls'].append(dict(kind='layout', processor=snapshot(processor),
                    same_processor=any(processor is p for p in processors))))
            return layout_fn(processor, row, layout, gap, native_g3t, gf1)

        def check_rows(model, rows, plans, ranks, sink=None, device=None):
            offset = len(observations)
            def report(records):
                if sink:
                    sink(records)
                def publish():
                    enriched = []
                    for row, obs in zip(records, observations[offset:]):
                        # Preserve the native record and attach only observations from its fetch.
                        enriched.append(dict(row, processor=obs.get('processor'),
                            same_processor=obs.get('same_processor', False), calls=obs['calls'],
                            pixels_observed=any(c['kind'] == 'frames' for c in obs['calls'])))
                    value = dict(schema='f1-v1', source='same_processor', reconstructed=False,
                                 rows=len(enriched), streams=grouped(enriched), observation_errors=list(errors))
                    raw = encoded(value)
                    put(local, raw)
                    live, _ = location(Path(kit), Path(root), job)
                    put(live / 'f1.json', raw)
                observe(publish)
            return check(model, rows, plans, ranks, sink=report, device=device)

        run.processor_for_receipt, run.fetch, run.check_plan_rows = make, get, check_rows
        samples.encode_frames, data.encode_layout_row = encode_frames, encode_layout
        try:
            return original(cfg, ranks, out_path, steps, device, progress_dir, rank_limit, encode_only, start_step)
        finally:
            run.processor_for_receipt, run.fetch, run.check_plan_rows = factory, fetch, check
            samples.encode_frames, data.encode_layout_row = frames, layout_fn
    run.first_batch_check = checked
    try:
        yield
    finally:
        run.first_batch_check = original
