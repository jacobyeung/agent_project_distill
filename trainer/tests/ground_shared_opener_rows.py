"""Verify the owning trainer's shared rows against this decoder's tiny model.

Run with --module pointing at a local copy of stageb_merge's ground_tokens.py.
The production row owner belongs to that lane and is not vendored into decode.
"""
import argparse,importlib.util,json
from pathlib import Path
from types import SimpleNamespace
import torch
from tokenizers import Tokenizer,models,pre_tokenizers,decoders
from transformers import PreTrainedTokenizerFast
from student_pilot import mdg_lora,carrier_c1_routing as routing
from tests.test_mdg_features import fixture


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--module',required=True);parser.add_argument('--out',required=True)
    args=parser.parse_args();source=Path(args.module)
    if not source.exists():
        Path(args.out).write_text(json.dumps(dict(status='PENDING-INPUT',path=str(source))))
        return
    spec=importlib.util.spec_from_file_location('student_pilot._trainer_ground_rows',source)
    rows_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(rows_module)
    torch.manual_seed(4);torch.set_num_threads(8)
    model,_=fixture();chars=sorted(set('<ground obj="chair"><gap a="x" b="y">'))
    vocab={'[UNK]':0,'[PAD]':1,**{c:i+2 for i,c in enumerate(chars)}}
    raw=Tokenizer(models.WordLevel(vocab,unk_token='[UNK]'));raw.pre_tokenizer=pre_tokenizers.Split('',behavior='isolated');raw.decoder=decoders.Fuse()
    tokenizer=PreTrainedTokenizerFast(tokenizer_object=raw,unk_token='[UNK]',pad_token='[PAD]')
    processor=SimpleNamespace(tokenizer=tokenizer);routing.add_routing_tokens(processor)
    rows_module.add(processor);rows_module.initialize(model,processor);model.mdg_tokenizer=tokenizer
    mdg_lora.install(model,2);rows_module.install_rows(model)
    rows=model.auxiliary_heads.mdg_lora['opener_rows'];indices=list(model.ground_token_ids.values())
    embedding,head=model.get_input_embeddings(),model.get_output_embeddings()
    assert embedding._mdg_opener_rows is head._mdg_opener_rows is rows
    for p in model.parameters():p.requires_grad_(False)
    for p in rows.parameters():p.requires_grad_(True)
    all_ids=torch.arange(embedding.weight.shape[0])[None]
    before=embedding(all_ids).detach().clone();original_head=head.weight.detach().clone()
    ids=torch.tensor([indices]);optimizer=torch.optim.SGD(rows.parameters(),lr=.05)
    # Teacher-forced routing loss trains both rows with the adapter gate CLOSED.
    embedded=embedding(ids);logits=head(embedded)
    loss=torch.nn.functional.cross_entropy(logits[0],ids[0].flip(0))
    loss.backward()
    assert (rows.input_rows.grad.norm(dim=1)>0).all()
    assert (rows.output_rows.grad.norm(dim=1)>0).all()
    optimizer.step()
    main_input=embedding(ids);main_logits=head(main_input)
    with mdg_lora.suffix_mask(model,torch.ones_like(ids,dtype=torch.bool)):
        query_input=embedding(ids);query_logits=head(query_input)
    assert torch.equal(main_input,query_input)
    assert torch.equal(main_logits,query_logits)
    after=embedding(all_ids).detach()
    changed=(before!=after).any(-1)[0].nonzero().flatten().tolist()
    assert sorted(changed)==sorted(indices)
    assert torch.equal(head.weight,original_head),'Base rows changed under frozen LM'
    materialized=rows_module.materialize_export_rows(model.state_dict(),model)
    for suffix,value in [('language_model.embed_tokens.weight',rows.input_rows),('lm_head.weight',rows.output_rows)]:
        key=next(k for k in materialized if k.endswith(suffix))
        assert torch.equal(materialized[key][indices],value)
    result=dict(status='PASS',only_changed_embedding_rows=changed,ids=model.ground_token_ids,
                main_and_query_share_rows=True,closed_gate_routing_loss_trains_input_and_output_rows=True,
                materialized_export_contains_shared_rows=True)
    Path(args.out).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
