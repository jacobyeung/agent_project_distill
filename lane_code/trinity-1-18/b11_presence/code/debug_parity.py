"""Debug: decode the first differing region of vLLM-observed vs trainer-expected prompt ids for one K1 item."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import direct as D
from transformers import AutoProcessor
from vllm import LLM, SamplingParams
from parity import trainer_encode
def show(ids, tok):
    out, run = [], None
    for x in ids:
        s = tok.decode([x])
        if s in ('<|video_pad|>',):
            run = (run or 0) + 1; continue
        if run:
            out.append(f'[pad x{run}]'); run = None
        out.append(s)
    if run: out.append(f'[pad x{run}]')
    return ''.join(out)

def main():
    model = str(D.LANE / 'work/model_m544')
    processor = AutoProcessor.from_pretrained(model, local_files_only=True)
    processor._student_pilot_student = 'qwen35'
    tok = processor.tokenizer
    caps = {c['canonical']: c for c in map(json.loads, open(D.LANE / 'out/prep/CAPTURES.jsonl'))}
    it = D.select('heldout', ['obj_appearance_order'], 1)[0]
    t = D.task_for(it); arrays, meta = D.media(caps[it['capture']])
    req = D.request(processor, t, arrays, meta, shim=True)
    batch, audit = trainer_encode(processor, t, arrays, meta, D.CELL)
    exp = batch['input_ids'][0, :audit['prompt_tokens']].tolist()
    llm = LLM(model=model, dtype='bfloat16', max_model_len=24576, gpu_memory_utilization=0.85, max_num_seqs=4,
              limit_mm_per_prompt={'video': 1, 'image': 0}, seed=17, enable_prefix_caching=False)
    obs = list(llm.generate([req], SamplingParams(temperature=0, max_tokens=1))[0].prompt_token_ids)
    diff = [i for i, (a, b) in enumerate(zip(exp, obs)) if a != b]
    print('LEN', len(exp), len(obs), 'NDIFF', len(diff), 'FIRST', diff[:10])
    print('EXP', repr(show(exp, tok)[:700]))
    print('OBS', repr(show(obs, tok)[:700]))


if __name__ == '__main__':
    main()
