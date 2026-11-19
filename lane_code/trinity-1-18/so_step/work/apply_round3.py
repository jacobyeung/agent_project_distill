from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TREE=ROOT/'work/b21_final/work/tree_r1'
p=TREE/'student_pilot/c1_switches.py'
s=p.read_text().replace('three optional performance switches','optional performance switches')
s=s.replace('_frozen = None', "FALLBACK = 'C1_CPU_PREFETCH_FALLBACK'\n_frozen = None")
s=s.replace("    return tuple(str(int(value)) for value in values)", """    fallback = os.environ.get(FALLBACK, '0')
    if fallback not in ('0', '1'):
        raise ValueError(FALLBACK + ' must be 0 or 1')
    if fallback == '1' and values[0] != '1':
        raise ValueError(FALLBACK + ' requires C1_CPU_PREFETCH=1')
    values = tuple(str(int(value)) for value in values)
    # Preserve the original three-value startup payload unless fallback is ON.
    return values + ('1',) if fallback == '1' else values""")
s=s.replace("    return (_frozen if _frozen is not None else parse())[NAMES.index(name)]", """    values = _frozen if _frozen is not None else parse()
    if name == FALLBACK:
        return values[3] if len(values) == 4 else '0'
    return values[NAMES.index(name)]


def record():
    values = _frozen if _frozen is not None else parse()
    return {'performance': dict(zip(NAMES + (FALLBACK,), values))} if any(v != '0' for v in values) else {}""")
p.write_text(s)
p=TREE/'student_pilot/c1_cpu_prefetch.py'; s=p.read_text()
s=s.replace('        self.factory = factory', "        from .c1_switches import get, FALLBACK\n        self.fallback = get(FALLBACK) == '1'\n        self.factory = factory")
s=s.replace("                if held_bytes > MAX_GROUP_TENSOR_BYTES:\n                    raise", "                if held_bytes > MAX_GROUP_TENSOR_BYTES:\n                    if self.fallback:\n                        return None  # Release this whole group; the main thread fetches it synchronously.\n                    raise")
s=s.replace('            replay = Replay(rows, stream, candidates, future.result())', """            prepared = future.result()
            future = None  # Drop the future's retained result before synchronous fallback.
            if prepared is None:
                rows._c1_budget_fallback_groups = getattr(rows, '_c1_budget_fallback_groups', 0) + 1
                replay = rows
            else:
                replay = Replay(rows, stream, candidates, prepared)
            prepared = None""")
s=s.replace('            replay.values = None', '            if isinstance(replay, Replay):\n                replay.values = None')
p.write_text(s)
p=TREE/'student_pilot/carrier_c1_run.py';s=p.read_text()
s=s.replace('    cache_record = {}\n', """    from .c1_switches import record as performance_record
    cache_record = performance_record()
    if performance_switch('C1_CPU_PREFETCH_FALLBACK') == '1':
        cache_record['cpu_prefetch'] = dict(budget_fallback_groups=getattr(rows, '_c1_budget_fallback_groups', 0))
""")
p.write_text(s)
p=TREE/'tests/test_carrier_c1_t0.py';s=p.read_text()
a=s.index('class ExportLeg(unittest.TestCase):');b=s.index('    BOUND =',a)
s=s[:a]+'''class ExportLeg(unittest.TestCase):
    """The 'x' leg restores a run's newest resume state under that run's binding and exports m<step>."""

    def setUp(self):
        from tests.so_helpers import reset_switches
        reset_switches(self)

'''+s[b:];p.write_text(s)
# Provenance differs intentionally; numerical parity still compares all numerical fields.
for p in (TREE/'tests/test_so_joint.py',ROOT/'work/test_local_parity.py'):
    s=p.read_text().replace("'peak_reserved_bytes','decoded_cache')", "'peak_reserved_bytes','decoded_cache','performance','cpu_prefetch')")
    p.write_text(s)
print('ROUND3_PRODUCTION_EDITS: fallback, switch provenance, docstring and parity metadata scope')
