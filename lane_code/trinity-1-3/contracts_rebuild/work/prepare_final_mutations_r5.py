from pathlib import Path
L=Path(__file__).resolve().parents[1]
p=L/'work/run_tests_r5.py';s=p.read_text()
s=s.replace("tag=sys.argv[2]", "if '/work/mutation_r5/' in sys.argv[1] and '/round_final/' not in sys.argv[1]:\n    raise SystemExit('Pre-final mutation evidence superseded; no test launched.')\ntag=sys.argv[2]")
p.write_text(s)
p=L/'work/mutation_r5/run.py';s=p.read_text()
s=s.replace("W=L/'work/mutation_r5'", "W=L/'work/mutation_r5/round_final';W.mkdir(exist_ok=True)")
s=s.replace("equivalent={", "equivalent={\n 'R_N3':'The bare legacy scalar parser branch is absent: no sealed POOL row uses it. The revision tuple mutation is therefore obsolete; test_legacy_gap_off_grammar rejects the form in both epochs.',")
s=s.replace("elif short=='N3':\n        a=\"if new_contracts() and program_version in ('3.12', '3.12.1', '3.12.2') and re.fullmatch(\"\n        b=\"if new_contracts() and program_version in ('3.12',) and re.fullmatch(\"", "elif short=='N3':\n        a=b=''" )
s=s.replace("('F_L2C','student_pilot/live_trace313.py',\"if new_contracts() and program_version in ('3.12', '3.12.1', '3.12.2')\", \"if program_version in ('3.12', '3.12.1', '3.12.2')\")", "('F_L2C','student_pilot/live_trace313.py',\"        if body.startswith('distance '):\",\"        if re.fullmatch(f+' m', body):return\\n        if body.startswith('distance '):\")")
s=s.replace(" ('F_L2E',", " ('F_L2D_OFF','student_pilot/phrases.py','for pattern in (ANGLE_PATTERNS if new_contracts() else ()):','for pattern in ANGLE_PATTERNS:'),\n ('F_L2E',")
s=s.replace("tag='MUTATION_'+mid+'_R5'", "tag='MUTATION_FINAL_'+mid+'_R5'")
s=s.replace("env=dict(os.environ,R5_NO_TRACE='1')", "env=dict(os.environ,R5_NO_TRACE='1',R5_MUTATION_FIRST=selectors.get(mid, 'test_confirmation_r5.py'))")
s=s.replace("only=set(sys.argv[1:]);", '''selectors={}
for mid,v in old.items():selectors['B_'+mid]=v['command'][-1]
for mid in originals:
    if mid.startswith('R_M'):selectors[mid]=selectors.get('B_'+mid[2:],'test_confirmation_r5.py')
selectors.update({
 'B_M16':'training_head_substitution_depth','R_M16':'training_head_substitution_depth',
 'B_M17':'shared_binding_served_or_deferred','R_M17':'shared_binding_served_or_deferred',
 'B_M30':'declared_revision_controls_instance_grammar','R_R1':'decode_attacks',
 'R_R2':'decode_attacks','R_R6':'decode_attacks','R_N1':'structured_point_program_admission',
 'R_N2':'paired_text_call_id_mismatch','R_N4':'vocabulary_and_suffix_exclusions',
 'R_N5':'decode_attacks','R_N6':'review_ground_responses',
 'R_N8':'epoch_class_static_api','R_N9':'sensor313_off_provider_and_audit',
 'R_N10':'vocabulary_and_suffix_exclusions','R_N11':'shared_binding_served_or_deferred',
 'F_H2':'calculator_field_scope','F_M1':'shared_binding_served_or_deferred',
 'F_M2':'rerender_depth_arguments','F_L1_IDENTITY':'pose_identity',
 'F_L2A':'standalone_generator_imports','F_L2B':'generator_refusal_type',
 'F_L2B_ORPHAN':'generator_refusal_type','F_L2C':'legacy_gap_off_grammar',
 'F_L2D_OFF':'vocabulary_and_suffix_exclusions','F_L2E':'cache_lookup_preserves_caller',
 'F_MOVE_ROUNDING':'move_nadir_distance_retains_sealed_rounding',
 'F_REPLAY_EPOCH':'sensor313_off_provider_and_audit'})
only=set(sys.argv[1:]);''')
(L/'work/mutation_r5/run_final.py').write_text(s)
