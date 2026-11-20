"""Reviewed import exclusions and finite dynamic targets for the sealed geometry job."""
# These are import sites, not package-name allowlists. New imports fail closed.
EXCLUSIONS = {}

def exclude(source, scope, names, reason):
    for name in names: EXCLUSIONS[source,scope,name] = reason

training = ('parity.load_native calls only processor_for_receipt, load_model, load_artifact and identity; '
            'the worker calls _prepare_decode under closed_adapters. It never invokes training validation, '
            'row preparation, Rows.get, optimizer steps or training admission.')
for scope, names in [
    ('validate',['student_pilot.h1','student_pilot.h1_faithful']),
    ('prepare',['student_pilot.h1_faithful']),('prepared',['student_pilot.h1_faithful']),
    ('Rows.get',['student_pilot.h1']),('own_values',['student_pilot.h1_faithful']),
    ('optimize_step',['student_pilot.h1']),('run_steps',['student_pilot.h1']),
    ('fla_check',['triton','fla'])]:
    exclude('tree/student_pilot/carrier_c1_run.py',scope,names,training)
exclude('tree/student_pilot/warmstart.py','target_modules',['accelerate'],
        'Training warmstart builds an empty target model; sealed full-weight restore loads the exported model directly.')
exclude('b/work/c8r/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py','unit_report',['r1'],
        'Standalone policy unit_report is never called; policy() supplies ThinkingBudget only.')
for name in ['sam3.model_builder','sam3.model.sam3_image_processor']:
    exclude('tree/student_pilot/sam3_tower.py','Sam3Tower._load',[name],
            'prepare omits sam3 and selector_head settings; g.w.run rejects either. No Sam3Tower is constructed.')
video = 'The worker binds authenticated PNG frames with parity.bind_item; no video file or video-decoding function is used.'
for source,scope in [('student_pilot/admission.py','video_timing'),('student_pilot/c1r_clips.py','decode_selected'),
                     ('student_pilot/recording_pose.py','pyav_preflight'),('student_pilot/recording_pose.py','decode_pyav_pool'),
                     ('evalpath/sampling.py','sample_video'),('evalpath/pointing_markers.py','decode_anchors'),
                     ('evalpath/vqa_direct.py','trainer_row')]:
    exclude('tree/'+source,scope,['av'],video)
for scope,names in [('tool_observations',['student_pilot.detailed_audit']),
                    ('native_transport',['google','google.genai',"importlib.util.spec_from_file_location('student_native_google_telemetry', REFERENCE / 'native_google_telemetry.py')"]),
                    ('main',['google','google.genai'])]:
    exclude('tree/student_pilot/conversion.py',scope,names,
            'Offline dataset conversion and remote API generation are not called by pinned model loading or capture_one.')
for source,scope,call,reason in [
 ('student_pilot/orchard_eval/contracts.py','import_file','importlib.util.spec_from_file_location(name, resolve_read(path))','Offline scoring/training contract loader; this worker supplies neither a scoring file nor that CLI.'),
 ('student_pilot/benchmark_eval/contracts.py','import_file','importlib.util.spec_from_file_location(name, path)','Offline benchmark contract loader; capture_one has no scoring or benchmark CLI call.'),
 ('student_pilot/admission.py','load_scorer',"importlib.util.spec_from_file_location('student_pilot_offline_scoring', SCORER_LIB)",'Training admission scorer; this job never calls load_scorer or evaluates answers.'),
 ('student_pilot/mdg_eval.py','module_at','importlib.util.spec_from_file_location(name, path)','Offline MDG export/scoring CLI; served tower geometry is built in memory.'),
 ('student_pilot/grounding_eval.py','pointing_module',"importlib.util.spec_from_file_location(name, root / 'evalpath/__init__.py', submodule_search_locations=[str(root / 'evalpath')])",'External pointing evaluation CLI; this job processes only distance captures.'),
 ('student_pilot/grounding_eval.py','pointing_module',"importlib.import_module(name + '.pointing_markers')",'External pointing evaluation CLI; this job processes only distance captures.'),
 ('verifykit/io.py','module','importlib.util.spec_from_file_location(name, path)','Offline verification artifact loader; no verifykit tower or scorer is called.')]:
    exclude('tree/'+source,scope,[call],reason)
geometry = ('Legacy file-backed mask/reference executors are not used. capture_one sets perception.socket=None, '
            'calls the geometry constructor and catches Unserved; it never executes a selector, mask proposal or reference program.')
for source,scope,names in [
 ('ofs/core.py','lift',['rk.sam3mask']),('ofs/core.py','ground_from_values',['rk.ground']),('ofs/core.py','export',['rk.ground']),
 ('student_pilot/routed_candidates.py','ground_from_values',['rk.ground']),('student_pilot/routed_candidates.py','export',['rk.ground']),
 ('student_pilot/ground_profiles.py','load_geometry',['rk.programs']),
 ('generator/derivgen_v7/derivgen/ground_v312_io.py','reference',['rk','rk.ground','rk.scheme'])]:
    exclude('tree/'+source,scope,names,geometry)
for scope,names in [('balance_gap_positions',['trace_format.ground_v312_balance','trace_format.ground_v312_quality'])]:
    exclude('tree/trace_format/ground_v313.py',scope,names,'Training-row generation/rebalancing; no rows are rendered or balanced by the GPU worker.')
for scope,names in [('load_backend',["importlib.util.spec_from_file_location('v312_decode_lifting', path)"]),
                    ('direct_continuation',['trace_format.ground_v312_quality']),('parse_roles',['trace_format.paraphrase']),
                    ('render',['trace_format.ground_v312_degenerate']),('select_balanced',['trace_format.ground_v312_balance'])]:
    exclude('tree/trace_format/ground_v312.py',scope,names,'Training-row generator; capture_one uses the served geometry directly and performs no generation/rendering.')
exclude('tree/generator/derivgen_v7/derivgen/ground_v312.py','load_backend',
        ["importlib.util.spec_from_file_location('v312_decode_lifting', path)"],
        'Training-row backend loaded from a caller-supplied file; the worker has no row-generation invocation.')
exclude('h1eval/cli.py','run',['importlib.import_module(module)'],
        'Generic evaluator CLI factory; sealed numeric action 3 calls g.w.run directly, never this CLI.')
DYNAMIC = {
 ('tree/student_pilot/c1r_dense.py','runtime_identity','importlib.import_module(encode_target.__module__)'):['student_pilot.c1r_targets'],
 ('tree/student_pilot/ground_v3.py','GroundV3._resolve',"import_module(O.__name__ + '.core')"):['ofs.core'],
 ('tree/headcall/phase1.py','_module',"importlib.import_module('student_pilot.' + name)"):
     ['student_pilot.'+n for n in ('head_api','camera_targets','gate_eval','gate_driver','auxiliary_losses')],
 ('h1eval/h10/launch.py','reader_factory','importlib.import_module(module)'):['e2e_reader.parity'],
 ('b/parity_kit/common.py','module','importlib.util.spec_from_file_location(name, path)'):
     ['@b/work/c8r/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py',
      '@b/heads/selector/selector_head.py','@b/heads/scale/scale_head.py']
}
for source,scope,names in [
 ('student_pilot/gate_driver.py','load_checkpoint',['student_pilot.runner']),
 ('student_pilot/ddp_core.py','row_losses',['student_pilot.runner']),
 ('student_pilot/adapters.py','attach_adapters',['peft']),
 ('student_pilot/adapters.py','attach_ddp_adapters',['peft']),
 ('student_pilot/warmstart.py','lora_identity',['peft','peft.tuners.tuners_utils']),
 ('student_pilot/warmstart.py','initialize_adapters',['peft'])]:
    exclude('tree/'+source,scope,names,
            'LoRA/training loss path; parity.load_native restores the pinned full-weight export with carrier_c1_run.load_artifact and never constructs LoRA adapters or training losses.')
