from common import *
(D/'upload').rename(L/'attic/build24m4n/upload_initial')
p=D/'docs_l.py';s=p.read_text().replace('The native dense encoder supplies pixel bounds and frame layout;', 'Each tree applies its native routing flag and target renderer before tokenization. The native dense encoder supplies pixel bounds and frame layout;')
replace(p,s)
v=J.load(D/'TREE_FIXTURE_TESTS.json')
v['fixture_only_edits'].append(dict(source='tests/test_carrier_c1_single_image.py',old='No code record in fixture',new="Create code.json with schema=fixture and set code=file_pin(codepath)"))
v['fixture_script_sha256']=J.sha(D/'tree_fixture_tests.py')
J.write(D/'TREE_FIXTURE_TESTS.json',v)
print('Archived superseded upload stream; completed fixture evidence')
