"""Match the pinned production embedding ownership at the CPU model boundary."""
from pathlib import Path
import json
import torch

D = Path(__file__).resolve().parent


def untie(model):
    spec = json.loads((D/'rehearsal2/model_override.json').read_text())
    assert spec['tie_word_embeddings'] is False
    assert spec['text_config.tie_word_embeddings'] is False
    assert model.config.text_config.hidden_size == 4
    assert model.config.text_config.vocab_size == 248064
    embed, head = model.get_input_embeddings(), model.get_output_embeddings()
    assert head.weight is embed.weight, 'Expected the authenticated tied tiny donor'
    original = head.weight
    head.weight = torch.nn.Parameter(original.detach().clone(), requires_grad=original.requires_grad)
    model.config.tie_word_embeddings = False
    model.config.text_config.tie_word_embeddings = False
    assert head.weight is not embed.weight
    assert head.weight.data_ptr() != embed.weight.data_ptr()
    assert torch.equal(head.weight, embed.weight)
    # Recompute native parameter accounting for the extra independent LM tensor.
    # The temporary base container has no attached heads; native preparation
    # preserves the configured trainability and FP32 master policy.
    if hasattr(model, 'full_ft_report'):
        from student_pilot import full_ft
        base = torch.nn.Module()
        base.model, base.lm_head = model.model, model.lm_head
        old = model.full_ft_report
        block = full_ft.normalize({k:old[k] for k in ('train', 'learning_rates')})
        _, model.full_ft_report = full_ft.prepare_model(base, block)
    return model


def install(trainer):
    native = trainer.load_model
    def load_model(*args, **kwargs):
        # Native authentication and exact donor inventory loading finish first.
        model = untie(native(*args, **kwargs))
        import os
        print(json.dumps(dict(event='fixture_embedding_ownership',rank=os.environ.get('RANK'),
            tied=False,shape=list(model.lm_head.weight.shape),
            parameters=model.full_ft_report['base_parameters'])),flush=True)
        return model
    trainer.load_model = load_model
