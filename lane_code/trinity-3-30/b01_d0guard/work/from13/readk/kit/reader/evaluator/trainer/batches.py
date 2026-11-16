import math
import torch
def assistant_labels(input_ids, attention_mask, prompt_length, answer_length):
    if input_ids.ndim != 2 or input_ids.shape[0] != 1 or attention_mask.shape != input_ids.shape:
        raise ValueError("The smoke uses one example per microbatch")
    end = prompt_length + answer_length
    if prompt_length < 1 or answer_length < 1 or end > input_ids.shape[1]:
        raise ValueError("A complete prompt and nonempty assistant target are required")
    if not torch.all(attention_mask[:, :end] == 1) or torch.any(attention_mask[:, end:] != 0):
        raise ValueError("Only right padding after the complete assistant target is allowed")
    labels = torch.full_like(input_ids, -100)
    labels[:, prompt_length:end] = input_ids[:, prompt_length:end]
    labels[attention_mask == 0] = -100
    return labels

def training_stop_token(processor):
    tokenizer = processor.tokenizer
    from .students import same_student
    if not same_student(getattr(processor, "_student_pilot_student", None), "qwen35"):
        return tokenizer.eos_token, tokenizer.eos_token_id
    if tokenizer.eos_token_id != 248046 or tokenizer.encode("<|endoftext|>", add_special_tokens=False) != [248044]:
        raise ValueError("Pinned Qwen3.5 generation-stop token changed")
    return "<|endoftext|>", 248044

def training_text(processor, question, options, target):
    if not isinstance(question, str) or not isinstance(options, list) or not all(isinstance(option, str) for option in options):
        raise ValueError("Question and options must be unchanged source strings")
    if not target or any(token in target for token in ("<|im_start|>", "<|im_end|>", "<|video_pad|>", "<|image_pad|>")):
        raise ValueError("Target is empty or contains conversation/media control tokens")
    from .trace_contract import ANSWER_FORMAT_INSTRUCTION

    text = question + ("\n" + "\n".join(options) if options else "") + "\n\n" + ANSWER_FORMAT_INSTRUCTION
    messages = [{"role": "user", "content": [{"type": "video"}, {"type": "text", "text": text}]}]
    prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    full = processor.apply_chat_template(messages + [{"role": "assistant", "content": target}], tokenize=False, add_generation_prompt=False)
    eos = processor.tokenizer.eos_token
    if (target.endswith("\n") and not target.endswith("\n\n")
            and prompt.endswith("<|im_start|>assistant\n<think>\n\n</think>\n\n")
            and full == prompt + target[:-1] + eos + "\n"):
        full = prompt + target + eos + "\n"
    if (target.endswith("\n") and not target.endswith("\n\n")
            and prompt.endswith("<|im_start|>assistant\n<think>\n")
            and full == prompt + "\n</think>\n\n" + target[:-1] + eos + "\n"):
        full = prompt + "\n</think>\n\n" + target + eos + "\n"
    if not full.startswith(prompt) or not full.endswith(target + eos + "\n"):
        raise ValueError("Pinned chat-template assistant boundary changed")
    stop, stop_id = training_stop_token(processor)
    if stop_id != processor.tokenizer.eos_token_id and stop in target:
        raise ValueError("Target contains the generation-stop token")
    return prompt, full[len(prompt):-1] + (stop if stop_id != processor.tokenizer.eos_token_id else "")
