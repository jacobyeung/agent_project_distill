"""Run the five pinned parity-selection keys on CPU and compare call text."""
from pathlib import Path
import time

from parity_kit.common import OLD, OLD_LOAD, key, read, rows, write
from parity_kit.compare import agreement
from parity_kit.run_parity import arguments, run, select


def main():
    a = arguments(cpu=True)
    if a.device != 'cpu' or a.keys or a.types:
        raise ValueError('first batch requires CPU and the pinned five-key selection')
    settings = dict(read(a.settings), arm=a.arm)
    selection = read(settings.get('old_load_receipt', OLD_LOAD))['parity_selection']['items']
    if len(selection) != 5:
        raise ValueError('expected five parity-selection question types')
    selected = select(settings, selection.values())
    if {t['question_type']: key(t) for t in selected} != selection:
        raise ValueError('parity-selection types differ')
    start = time.perf_counter()
    result = run(settings, selected, a.out, device='cpu', settings_path=a.settings)
    baseline = {r['key']: r for r in rows(settings.get('old_items', OLD)) if r.get('arm') == 'unflagged'}
    report = dict(device='cpu', elapsed_s=time.perf_counter() - start,
                  load=read(Path(a.out) / 'LOAD_TIMING.json'),
                  items={r['key']: dict(timings=r.get('timings'), seconds=r['seconds'],
                                         scores=r['scores'], calls=agreement(r, baseline[r['key']])) for r in result})
    write(Path(a.out) / 'FIRST_BATCH.json', report)


if __name__ == '__main__':
    main()
