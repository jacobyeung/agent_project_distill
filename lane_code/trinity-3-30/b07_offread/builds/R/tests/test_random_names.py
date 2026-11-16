import base64,hashlib,json,re,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'kit'))
import xnames as X


def test_random_name_table_and_required_prefix():
    import importlib.util,secrets
    spec=importlib.util.spec_from_file_location('_map_alias_test',X.__file__)
    alias=importlib.util.module_from_spec(spec);spec.loader.exec_module(alias)
    logical='vsi_alias_'+secrets.token_hex(6)
    assert X.component(logical)==alias.component(logical)
    token=X.component('vsi')
    assert re.fullmatch(r'x[0-9a-f]{12}',token)
    assert X.component('vsi')==token
    table=json.loads(X.runtime_table())
    assert table['tokens'][hashlib.sha256(bytes.fromhex(table['salt'])+b'vsi').hexdigest()]==token
    assert all(re.fullmatch('[0-9a-f]{64}',k) for k in table['tokens'])
    assert all(re.fullmatch('x[0-9a-f]{12}',v) for v in table['tokens'].values())
    assert 'a15_cot_ap' not in X.WORDS
    X.scan('a15_cot_ap'+'0'*16)


def test_encoded_forbidden_words():
    for word in X.WORDS:
        for text in (word.encode().hex(),base64.b64encode(word.encode()).decode(),
                     base64.b64encode(('xx'+word+'yy').encode()).decode()):
            with pytest.raises(ValueError):X.scan(text)


def test_binary_encoding_preserves_odd_and_even_hex_runs():
    for raw in (b'VSI',b'vsi',bytes.fromhex('17673690'),b'xxReVsIyy'):
        encoded=X.hex_body(raw)
        X.scan(encoded)
        assert bytes.fromhex(encoded)==raw
