from pathlib import Path
import shutil
L=Path(__file__).resolve().parents[1]; S=L/'work/src_r5'
def edit(rel,old,new):
    p=S/rel;s=p.read_text();assert s.count(old)==1,(rel,s.count(old),old);p.write_text(s.replace(old,new))
edit('trace_format/box_v313.py',"    if geometry_mode == 'sensor':\n", "    if geometry_mode == 'sensor' and new_contracts():\n")
edit('trace_format/box_v313.py',"    if geometry_mode == 'sensor' and new_contracts():\n", "    from .contracts import new_contracts\n    if geometry_mode == 'sensor' and new_contracts():\n")
edit('trace_format/calculator.py','            text = (f"u {_vec_text(u)}; v {_vec_text(v)}; dot {dot:.4f}; "', '''            vectors = ("u heading unavailable; v heading unavailable" if
                       any(not points[p].get('heading_defined', True) for p in refs)
                       else f"u {_vec_text(u)}; v {_vec_text(v)}")
            text = (f"{vectors}; dot {dot:.4f}; "''')
# Importing the standalone generator must not require the repository root.
edit('generator/derivgen_v7/derivgen/calculator.py', '''from trace_format.contracts import epoch_class
from trace_format import calculator as _runtime

CalculatorError = _runtime.CalculatorError
PrintedPointRegistry = epoch_class(PrintedPointRegistry, _runtime.PrintedPointRegistry)''', '''_SealedPointRegistry = PrintedPointRegistry


class PrintedPointRegistry(_SealedPointRegistry):
    def __new__(cls, *args, **kwargs):
        import sys
        contracts = sys.modules.get('trace_format.contracts')
        if contracts is not None and contracts.new_contracts():
            from trace_format import calculator as runtime
            return runtime.PrintedPointRegistry(*args, **kwargs)
        return super().__new__(cls)
''')
# Keep the generator's exception API while sharing ON implementations.
edit('generator/derivgen_v7/derivgen/calculator.py','            return runtime.PrintedPointRegistry(*args, **kwargs)', '''            class Registry(runtime.PrintedPointRegistry):
                def register(self, **kw):
                    try:
                        return super().register(**kw)
                    except runtime.CalculatorError as exc:
                        raise CalculatorError(exc.reason) from exc

                def execute(self, command):
                    try:
                        return super().execute(command)
                    except runtime.CalculatorError as exc:
                        raise CalculatorError(exc.reason) from exc
            return Registry(*args, **kwargs)''')
edit('student_pilot/phrases.py','def candidate_phrases(question, options=(), cache_phrases=None):', '''def candidate_binding(row, batch=None, manifest=None):
    """Use the mask cache universe before source-row declarations.

    Materializers persist batch cache phrases as batch_cache_phrases. A manifest
    supplied separately is a fallback for rows without a runtime binding.
    """
    batch = batch or {}
    entry = batch.get('cache_phrases', row.get('batch_cache_phrases'))
    if entry is None:
        for key in ('candidate_phrases', 'cache_phrases', 'candidate_manifest'):
            if row.get(key) is not None:
                entry = row[key]
                break
    if entry is None and manifest is not None:
        entry = manifest.get(str(row.get('qid')))
    return entry.get('phrases', []) if isinstance(entry, dict) else entry


def candidate_phrases(question, options=(), cache_phrases=None):''')
edit('student_pilot/s1_grounding.py', '''    binding = batch.get("cache_phrases", row.get("candidate_phrases"))
    if binding is None:
        binding = row.get('cache_phrases', row.get('candidate_manifest'))
    if isinstance(binding, dict):
        binding = binding.get('phrases')''', '''    from .phrases import candidate_binding
    binding = candidate_binding(row, batch)''')
edit('student_pilot/training_contract.py','from .phrases import candidate_phrases, normalize_phrase, phrase_set','from .phrases import candidate_phrases, normalize_phrase, phrase_set, candidate_binding')
edit('student_pilot/training_contract.py',"entry = manifest.get(str(row.get('qid'))) if manifest is not None else row.get('candidate_manifest', row.get('cache_phrases', row.get('candidate_phrases')))","entry = candidate_binding(row, manifest=manifest)")
edit('student_pilot/training_contract.py', '''            partial_ground = status == 'heading unavailable' and bool(re.match(
                re.escape(match[1])+r': (?:frames |[1-9][0-9]* (?:instances|found)\n)', body)) if match else False
            if call.startswith('<ground') and status != 'ok' and not partial_ground:'''.replace('(?:instances|found)\n)', '(?:instances|found)\\n)'), "            if call.startswith('<ground') and status != 'ok':")
edit('student_pilot/s1_routing.py',"('candidate_phrases', 'candidate_manifest', 'cache_phrases', 'uses_mask_cache', 'mask_source')", "('batch_cache_phrases', 'candidate_phrases', 'candidate_manifest', 'cache_phrases', 'uses_mask_cache', 'mask_source')")
edit('student_pilot/carrier_c1_routing.py','''        from trace_format.contracts import heading_available, partial_f1
        if not heading_available(self):''','''        from trace_format.contracts import heading_available, partial_f1, new_contracts
        if new_contracts() and k == 1:
            return 'f1 centre (0.00, 0.00, 0.00) m, yaw 0 deg'
        if not heading_available(self):''')
edit('student_pilot/carrier_c1_routing.py',"partial_f1(self.camera_pose(k)['camera_t_L1'], f2)","vec(self.camera_pose(k)['camera_t_L1'])")
edit('student_pilot/carrier_c1_routing.py',"if not recorded and (not heading_available(geometry) or", "if name != 'depth_at' and not recorded and (not heading_available(geometry) or")
edit('student_pilot/carrier_c1_routing.py',"actual_frame=p['actual_frame'], label=p['label'])['line'])", "actual_frame=p['actual_frame'], label=p['label'],\n                                                       **({'heading_defined': heading_available(geometry)}\n                                                          if new_contracts() and not recorded else {}))['line'])")
edit('student_pilot/carrier_c1_routing.py','                from trace_format.contracts import heading_available\n','                from trace_format.contracts import heading_available, new_contracts\n')
edit('student_pilot/live_trace313.py',"if program_version in ('3.12', '3.12.1', '3.12.2') and re.fullmatch(", "if new_contracts() and program_version in ('3.12', '3.12.1', '3.12.2') and re.fullmatch(")
edit('generator/derivgen_v7/derivgen/trace.py', '''            call = calls[e["call_id"]]
            args, name = call["arguments"], call["name"]''', '''            if e.get("call_id") not in calls:
                raise Refusal("unbacked_tool_response")
            call = calls[e["call_id"]]
            args, name = call["arguments"], call["name"]''')
edit('generator/derivgen_v7/derivgen/trace.py', '''            token, text = structured_tool_pair(call, e)''', '''            try:
                token, text = structured_tool_pair(call, e)
            except ValueError as exc:
                raise Refusal(str(exc)) from exc''')
# Key lookup is pure. Consumers merge aliases in a private copy.
edit('student_pilot/phrases.py','def cache_key(cache, name):', '''def cache_key(cache, name):
    wanted = normalize_phrase(name)
    keys = [key for key in cache['phrases'] if normalize_phrase(key) == wanted]
    return min(keys, key=lambda key: (key != wanted, key.casefold(), key)) if keys else wanted


def cache_view(cache, name):
    import copy
    cache = copy.deepcopy(cache)''')
edit('student_pilot/phrases.py','''    if not keys:
        return wanted''','''    if not keys:
        return cache, wanted''')
edit('student_pilot/phrases.py','    return canonical','    return cache, canonical')
edit('ofs/core.py','from student_pilot.phrases import cache_key','from student_pilot.phrases import cache_view')
edit('ofs/core.py','        phrase = cache_key(cache, name)','        cache, phrase = cache_view(cache, name)')
edit('student_pilot/ground_sources.py','from .phrases import cache_key','from .phrases import cache_key, cache_view')
edit('student_pilot/ground_sources.py','    phrase = cache_phrase(cache, name, codec)','    cache, phrase = cache_view(cache, name) if new_contracts() else (cache, codec.phrase(name))')
edit('student_pilot/ground_sources.py',"        record=self.cache['frames'][str(proposal.frame-1)]['phrases'][cache_phrase(self.cache, name, self.reader)]", "        cache, phrase = cache_view(self.cache, name) if new_contracts() else (self.cache, self.reader.phrase(name))\n        record=cache['frames'][str(proposal.frame-1)]['phrases'][phrase]")
# Redirect evidence writes in copied harnesses; retain module names for imports.
for directory in ('tests_r5','row_families_r5'):
    for p in (L/'work'/directory).glob('*.py'):
        s=p.read_text()
        for old,new in [('tests_r4','tests_r5'),('src_r4','src_r5'),('test_artifacts_r4','test_artifacts_r5'),('row_families_r4','row_families_r5'),('trees/r4','trees/r5'),("'r4_base'","'r5_base'"),("'r4_applied'","'r5_applied'"),('_R4','_R5')]:s=s.replace(old,new)
        p.write_text(s)
for name in ('build_packet','regenerate','run_tests','real_audit','replay_run'):
    s=(L/f'work/{name}_r4.py').read_text().replace('_r4','_r5').replace('_R4','_R5')
    (L/f'work/{name}_r5.py').write_text(s)
for p in (L/'work/review2_inputs').glob('*.py'):
    s=p.read_text().replace('/scratch/jjyeung/orch_n30/review_contracts2/work/rr/work/tests_r4',str(L/'work/tests_r5')).replace('/scratch/jjyeung/orch_n30/review_contracts2/work/mytests',str(L/'work/review2_inputs'))
    p.write_text(s)
shutil.copyfile(L/'work/generator_baseline_r4.json',L/'work/generator_baseline_r5.json')
