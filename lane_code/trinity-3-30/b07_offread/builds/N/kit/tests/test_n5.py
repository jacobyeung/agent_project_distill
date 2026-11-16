"""Current API equivalents and non-reversible naming contracts."""
import base64,hashlib,json,re,subprocess,sys
from pathlib import Path
import pytest
from offnative import opacity as X


def test_R4_current_submit_argv_is_opaque():
    from offnative.transport import submission_argv,FORBIDDEN
    c={'job_name':'a15_cot_ap'+'0'*16,'job':{'time_limit_s':21600}}
    argv=submission_argv(c,'/p/x/1.sh',packet_sha256='0'*64)
    text=' '.join(argv).lower()
    assert not [w for w in FORBIDDEN if w in text]
    assert '--export=A0_PACKET_SHA256='+'0'*64 in argv
    assert '--job-name='+c['job_name'] in argv
    assert '--account=mt01' in argv and '--no-requeue' in argv
    for invalid in ('a0'+'0'*16,'a15_cot_ap'+'g'*16,'a15_cot_ap'+'0'*15):
        with pytest.raises(ValueError):submission_argv(dict(c,job_name=invalid),'/p/x/1.sh')


def test_map_is_random_pinned_and_not_embedded():
    import importlib.util,secrets
    spec=importlib.util.spec_from_file_location('_map_alias_test',X.__file__)
    alias=importlib.util.module_from_spec(spec);spec.loader.exec_module(alias)
    logical='vsi_alias_'+secrets.token_hex(6)
    assert X.component(logical)==alias.component(logical)
    name='vsi'
    token=X.component(name)
    assert re.fullmatch(r'x[0-9a-f]{12}',token)
    assert X.component(name)==token
    assert name.encode().hex() not in token
    table=json.loads(X.runtime_table())
    assert table['tokens'][hashlib.sha256(bytes.fromhex(table['salt'])+name.encode()).hexdigest()]==token
    assert all(re.fullmatch('[0-9a-f]{64}',k) for k in table['tokens'])
    assert all(re.fullmatch('x[0-9a-f]{12}',v) for v in table['tokens'].values())
    X.scan(X.runtime_table())
    assert 'a15_cot_ap' not in X.WORDS
    X.scan('a15_cot_ap'+'0'*16)


@pytest.mark.parametrize('word',X.WORDS)
def test_encoded_forbidden_names_rejected(word):
    for name in (word,word.encode().hex(),base64.b64encode(word.encode()).decode(),
                 base64.b64encode(('xx'+word+'yy').encode()).decode()):
        with pytest.raises(ValueError):X.scan(name)


def test_different_build_maps_have_different_tokens(tmp_path):
    source=Path(X.__file__)
    code="import runpy,json;v=runpy.run_path("+repr(str(source))+ ");v['_TABLE'].clear();v['_NAMES'].clear();v['_REVERSE'].clear();v['configure'](__import__('sys').argv[1]);print(v['component']('vsi'))"
    tokens=[]
    for i in range(2):
        p=tmp_path/(str(i)+'.json');p.write_text('{}\n')
        Path(str(p)+'.sha256').write_text(hashlib.sha256(p.read_bytes()).hexdigest())
        r=subprocess.run([sys.executable,'-B','-c',code,str(p)],capture_output=True,text=True,check=True)
        tokens.append(r.stdout.strip())
    assert tokens[0]!=tokens[1]


def test_binary_encoding_preserves_odd_and_even_hex_runs():
    for raw in (b'VSI',b'vsi',bytes.fromhex('17673690'),b'xxReVsIyy'):
        encoded=X.hex_body(raw)
        X.scan(encoded)
        assert bytes.fromhex(encoded)==raw
