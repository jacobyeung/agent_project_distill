from common import *
s=(D/'census_final_tests.py').read_text().replace("F=D/'census_final'","F=D/'census_bytes'").replace("D/'CENSUS_FINAL_TESTS.json'","D/'CENSUS_BYTE_TESTS.json'")
s=s.replace("  report=J.load(root/'c5.json')","  report=J.load(root/'c5.json')\n  assert J.sha(root/'c5.json')==J.sha(target/'o/91/live/c4.json')")
s=s.replace("replace(root/'c5.json',json.dumps(bad));check('wrong_store'", "replace(root/'c5.json',json.dumps(bad));(target/'o/91/live/c4.json').write_bytes((root/'c5.json').read_bytes());check('wrong_store'")
s=s.replace("  # Preflight is diagnostic only;", "  (target/'o/91/live/c4.json').write_bytes((root/'c5.json').read_bytes())\n  # Preflight is diagnostic only;")
(D/'census_byte_tests.py').write_text(s)
s=(D/'discovery_census_setup.py').read_text().replace("discovery_shell_protected_final","discovery_shell_protected_bytes")
(D/'discovery_byte_setup.py').write_text(s)
