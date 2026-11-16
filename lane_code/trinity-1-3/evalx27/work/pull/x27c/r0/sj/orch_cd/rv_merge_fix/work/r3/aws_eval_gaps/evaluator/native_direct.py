def native_generate(model, processor, batch):
    """CarrierC1.generate owns prefix embeddings; HF owns the decode/cache."""
    import torch
    from transformers import GenerationConfig
    start = batch['input_ids'].shape[1]
    context = model.config.text_config.max_position_embeddings
    cap = min(16384, context-start)
    if cap < 1:
        raise ValueError('Prompt exhausts context')
    config = GenerationConfig.from_model_config(model.config)
    with torch.no_grad():
        result = model.generate(batch, generation_config=config, do_sample=False, num_beams=1,
            temperature=None, top_p=None, top_k=None, min_p=None, repetition_penalty=1.0,
            length_penalty=1.0, no_repeat_ngram_size=0, min_new_tokens=None,
            early_stopping=False, max_new_tokens=cap, use_cache=True,
            return_dict_in_generate=True, output_scores=False)
    tokens = result.sequences[0,start:].tolist()
    eos = config.eos_token_id
    eos = set(eos if isinstance(eos,(list,tuple)) else [eos])
    finish = 'eos' if tokens and tokens[-1] in eos else ('max_new_tokens' if cap == 16384 else 'context_exhaustion')
    return dict(tokens=tokens, text=processor.tokenizer.decode(tokens,skip_special_tokens=False),
        calls=[], errors=0, finish=finish, prompt_tokens=start, generated_tokens=len(tokens), actual_cap=cap)

