"""Test-only checkpoint loader: real tiny LM and reader, scripted sampled tokens."""
from pathlib import Path
from types import SimpleNamespace
from transformers import AutoTokenizer
from tests.test_eval import generated, reader
from h1eval.items import sha


def load(root,settings,*,frames,gt,items):
    assert settings['fixture'] is True and frames==32
    tok=AutoTokenizer.from_pretrained(root/'tokenizer',local_files_only=True)
    from student_pilot.carrier_c1_routing import OPENERS
    openers={name:tok.convert_tokens_to_ids(name) for name in OPENERS}
    kit=dict(root=root,digest=sha(root/'E2E_MANIFEST.json'),tok=tok,openers=openers)
    def factory(arm,mode,item):
        if arm!='own':raise ValueError('Tiny fixture supports own arm')
        def run(_):
            out,_=generated(kit,mode,kind='move')
            out['seconds']=out['timings']['total_s']
            return out
        return run
    return factory
