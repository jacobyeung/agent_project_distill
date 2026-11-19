from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build18'
text=(L/'work/build17/mutations17.py').read_text().replace('work/build17','work/build18').replace('B17_PROOF','B18_PROOF').replace("B/'test17.py'","B/'test18.py'")
extra="""
 ('thread_repeat','student_pilot/s1_admission.py','if torch.get_num_interop_threads() != 1:', 'if True:', 'tests.test_r1_build18.Admission18.test_repeated_admission_thread_setup'),
 ('v7_gate','student_pilot/r1_rooms.py',"if actual['sha256'] == STORE:",'if False:','tests.test_r1_build18.Rooms18.test_missing_v7_list_refuses'),
 ('v7_count','student_pilot/r1_rooms.py','hashes.count(V7_K1_LIST) != 1','False','tests.test_r1_build18.Rooms18.test_order_and_duplicate_refuse'),
 ('v7_order','student_pilot/r1_rooms.py','hashes.index(V7_K1_LIST) >= hashes.index(N_LIST)','False','tests.test_r1_build18.Rooms18.test_order_and_duplicate_refuse'),
 ('v7_audit_binding','student_pilot/r1_rooms.py',"pin_values(store.get('k1_removal')) != pin_values(pin)",'False','tests.test_r1_build18.Rooms18.test_repin_or_omitted_audit_binding_refuses'),
 ('v7_unremoved','student_pilot/r1_rooms.py',"if store.get('unremoved_hits') != 0:",'if False:','tests.test_r1_build18.Rooms18.test_unremoved_v7_refuses'),
 ('v7_keys','student_pilot/r1_rooms.py',"if store_hits is not None and status == 'k1_heldout':",'if False:','tests.test_r1_build18.Rooms18.test_census_collects_keys_and_retains_unresolved'),
"""
text=text.replace('cases=[','cases=['+extra)
(B/'mutations18.py').write_text(text)
text=(L/'work/build17/final_checks17.py').read_text().replace('work/build17','work/build18').replace('17.py','18.py').replace('B17_PROOF','B18_PROOF')
text=text.replace("['tests.test_r1_build17'","['tests.test_r1_build18','tests.test_r1_build17'")
(B/'final_checks18.py').write_text(text)
