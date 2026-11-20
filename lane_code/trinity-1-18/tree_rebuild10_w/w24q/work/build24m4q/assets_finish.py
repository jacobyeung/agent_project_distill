import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));from common import *
from transformers import LlavaProcessor,CLIPImageProcessorPil,AutoTokenizer,AutoProcessor
root=D/'assets3';root.mkdir()
tok=AutoTokenizer.from_pretrained(D/'assets2',local_files_only=True)
template="{{ 'user\\n' + messages[0]['content'][1]['text'] + '\\nassistant\\n' }}{% if not add_generation_prompt %}{{ messages[-1]['content'] + '<|im_end|>\\n' }}{% endif %}"
proc=LlavaProcessor(image_processor=CLIPImageProcessorPil(),tokenizer=tok,chat_template=template)
proc.save_pretrained(root);write(root/'config.json',dict(model_type='llava'))
p=AutoProcessor.from_pretrained(root,local_files_only=True,trust_remote_code=False)
print(type(p).__name__,p.tokenizer.eos_token_id,p.tokenizer.encode('<|endoftext|>'),p.chat_template)
assert p.chat_template==template
print([(f.name,f.stat().st_size) for f in root.iterdir()])
