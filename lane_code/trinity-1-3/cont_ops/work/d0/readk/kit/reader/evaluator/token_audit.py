"""Decode prefixes with the request's pinned tokenizer, then recompute scores."""
import json
from pathlib import Path
from evalpath.items import digest
from provenance import sha
from scoring import score_item


def load_tokenizer(cfg, directory=None, manifest_path=None):
    spec=cfg['models']['base']
    pin=spec['manifest']
    manifest_path=Path(manifest_path or pin['path'])
    if sha(manifest_path)!=pin['sha256']:
        raise ValueError('Tokenizer manifest pin differs')
    directory=Path(directory or spec['path'])
    files={r['path']:r['sha256'] for r in json.loads(manifest_path.read_text())['files']}
    names=('config.json','tokenizer.json','tokenizer_config.json','special_tokens_map.json',
           'added_tokens.json','merges.txt','vocab.json','chat_template.jinja')
    for name in names:
        path=directory/name
        if path.exists() and (name not in files or sha(path)!=files[name]):
            raise ValueError('Tokenizer file pin differs: '+name)
    if not all((directory/n).exists() and n in files for n in ('tokenizer.json','tokenizer_config.json')):
        raise ValueError('Pinned tokenizer files missing')
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(directory,local_files_only=True,trust_remote_code=False)


def token_ids(row, tokenizer):
    ids=row.get('token_ids')
    if not isinstance(ids,list) or any(type(i)is not int or i<0 for i in ids):
        raise ValueError('Prefix rescore requires generated token IDs')
    if len(ids)!=row['output_tokens']:
        raise ValueError('Generated token count differs')
    if row.get('token_ids_sha256') and digest(ids)!=row['token_ids_sha256']:
        raise ValueError('Generated token digest differs')
    if tokenizer.decode(ids,skip_special_tokens=True)!=row['raw_generation']:
        raise ValueError('Raw generation differs from generated token IDs')
    if 'token_text' in row and tokenizer.decode(ids,skip_special_tokens=False)!=row['token_text']:
        raise ValueError('Token text differs')
    return ids


def prefix_score(row, task, cell, tokenizer):
    ids=token_ids(row,tokenizer)
    raw=tokenizer.decode(ids[:4096],skip_special_tokens=True)
    scored=score_item(dict(task,thinking=cell['thinking']),raw,min(len(ids),4096),
        cap=min(cell['max_tokens'],4096),finish='length' if len(ids)>=4096 else row['finish_reason'])
    result=dict(raw_generation=raw,**scored)
    if row.get('at_4096')!=result:
        raise ValueError('Journal 4096-token prefix score/diagnostics differ')
    return result


def check_score(row, scored):
    for name,value in scored.items():
        if row.get(name)!=value:
            raise ValueError('Journal score/diagnostics differ: '+name+': '+row['key'])
